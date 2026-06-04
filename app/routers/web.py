"""
Rotas da interface web (HTML/Jinja2).
Auth protege /buscar, /analise, /painel, /chaves, /consumo.
"""
from fastapi import APIRouter, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.analise import AnaliseEntrada
from app.services import busca_medicamento, analise_risco
from app.middleware.auth_middleware import (
    get_usuario_atual,
    requer_usuario_web,
    RedirectParaLogin,
)
from app.repositories import usuario_repo
from app.services import auth_service
from app.config import settings

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


def _redir_login(proxima: str = "") -> RedirectResponse:
    url = "/login"
    if proxima:
        url += f"?proxima={proxima}"
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


# ── Páginas públicas ───────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def raiz(request: Request):
    return RedirectResponse("/buscar", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def pagina_login(
    request: Request,
    proxima: str = Query(""),
    erro: str = Query(""),
):
    return templates.TemplateResponse(
        request, "login.html",
        {"erro": erro or None, "proxima": proxima, "email_preenchido": ""},
    )


@router.post("/login")
async def processar_login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    proxima: str = Form(""),
    db: Session = Depends(get_db),
):
    # Normalizar email antes de buscar (mesmo que em criar_usuario)
    email_normalizado = email.strip().lower()

    usuario = usuario_repo.buscar_por_email(db, email_normalizado)
    if not usuario or not auth_service.verificar_senha(senha, usuario.senha_hash):
        return templates.TemplateResponse(
            request, "login.html",
            {"erro": "E-mail ou senha incorretos.", "email_preenchido": email, "proxima": proxima},
            status_code=401,
        )
    if not usuario.ativo:
        return templates.TemplateResponse(
            request, "login.html",
            {"erro": "Conta desativada. Entre em contato com o suporte.", "email_preenchido": email, "proxima": proxima},
            status_code=403,
        )

    # Criar tokens
    access = auth_service.criar_access_token(usuario.id, usuario.email, usuario.perfil)
    refresh, expira = auth_service.criar_refresh_token(usuario.id)
    usuario_repo.salvar_refresh_token(
        db, usuario.id, auth_service.hash_refresh_token(refresh), expira
    )

    # Redirecionar e setar cookies
    destino = proxima if proxima else "/painel"
    resp = RedirectResponse(url=destino, status_code=status.HTTP_302_FOUND)

    # Configurar cookies (mesmo que auth.py)
    secure = settings.is_production
    resp.set_cookie(
        "access_token",
        access,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=settings.access_token_expire_minutes * 60,
    )
    resp.set_cookie(
        "refresh_token",
        refresh,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=settings.refresh_token_expire_days * 86400,
        path="/auth/refresh",
    )

    return resp


@router.get("/cadastro", response_class=HTMLResponse)
async def pagina_cadastro(request: Request, erro: str = Query("")):
    return templates.TemplateResponse(
        request, "cadastro.html",
        {"erro": erro or None, "nome_preenchido": "", "email_preenchido": ""},
    )


@router.post("/cadastro")
async def processar_cadastro(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    senha_confirmar: str = Form(...),
    db: Session = Depends(get_db),
):
    # Normalizar email
    email_normalizado = email.strip().lower()

    if senha != senha_confirmar:
        return templates.TemplateResponse(
            request, "cadastro.html",
            {"erro": "As senhas não coincidem.", "nome_preenchido": nome, "email_preenchido": email},
            status_code=400,
        )
    if len(senha) < 6:
        return templates.TemplateResponse(
            request, "cadastro.html",
            {"erro": "A senha deve ter pelo menos 6 caracteres.", "nome_preenchido": nome, "email_preenchido": email},
            status_code=400,
        )
    if usuario_repo.buscar_por_email(db, email_normalizado):
        return templates.TemplateResponse(
            request, "cadastro.html",
            {"erro": "E-mail já cadastrado. Faça login.", "nome_preenchido": nome, "email_preenchido": email},
            status_code=400,
        )

    # Criar usuário (criar_usuario já normaliza email internamente)
    usuario = usuario_repo.criar_usuario(db, nome, email_normalizado, auth_service.hash_senha(senha))

    # Criar tokens
    access = auth_service.criar_access_token(usuario.id, usuario.email, usuario.perfil)
    refresh, expira = auth_service.criar_refresh_token(usuario.id)
    usuario_repo.salvar_refresh_token(
        db, usuario.id, auth_service.hash_refresh_token(refresh), expira
    )

    # Redirecionar e setar cookies
    resp = RedirectResponse(url="/painel", status_code=status.HTTP_302_FOUND)

    # Configurar cookies (mesmo que login)
    secure = settings.is_production
    resp.set_cookie(
        "access_token",
        access,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=settings.access_token_expire_minutes * 60,
    )
    resp.set_cookie(
        "refresh_token",
        refresh,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=settings.refresh_token_expire_days * 86400,
        path="/auth/refresh",
    )

    return resp


@router.post("/sair")
async def sair():
    resp = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token", path="/auth/refresh")
    return resp


# ── Páginas autenticadas ───────────────────────────────────────────────────

@router.get("/painel", response_class=HTMLResponse)
async def pagina_painel(
    request: Request,
    usuario: Usuario = Depends(requer_usuario_web),
    db: Session = Depends(get_db),
):
    from datetime import date
    hoje = date.today()
    plano = usuario_repo.obter_plano_usuario(db, usuario)
    consumo_hoje = usuario_repo.obter_consumo_total_dia(db, usuario.id, hoje)
    consumo_mes = usuario_repo.obter_consumo_mensal(db, usuario.id, hoje.year, hoje.month)
    por_modulo = usuario_repo.obter_consumo_por_modulo(db, usuario.id, hoje)
    limite_diario = plano.limite_diario if plano else 100
    limite_mensal = plano.limite_mensal if plano else 2000

    return templates.TemplateResponse(
        request, "painel.html",
        {
            "pagina_ativa": "painel",
            "usuario": usuario,
            "plano": plano.nome if plano else "Gratuito",
            "consumo_hoje": consumo_hoje,
            "consumo_mes": consumo_mes,
            "limite_diario": limite_diario,
            "limite_mensal": limite_mensal,
            "pct_dia": round(consumo_hoje / limite_diario * 100, 1) if limite_diario else 0,
            "pct_mes": round(consumo_mes / limite_mensal * 100, 1) if limite_mensal else 0,
            "por_modulo": por_modulo,
        },
    )


@router.get("/analise", response_class=HTMLResponse)
async def pagina_analise(
    request: Request,
    medicamento: str = Query(""),
    preco_informado: float = Query(0),
    tratamento: str = Query(""),
    cid: str = Query(""),
    procedimento: str = Query(""),
    quantidade: int = Query(1, ge=1),
    usuario: Optional[Usuario] = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    if not usuario:
        return _redir_login("/analise")

    resultado = None
    entrada = None
    if medicamento.strip() and preco_informado > 0:
        entrada = AnaliseEntrada(
            medicamento=medicamento,
            preco_informado=preco_informado,
            tratamento=tratamento,
            cid=cid,
            procedimento=procedimento,
            quantidade=quantidade,
        )
        resultado = analise_risco.analisar(db, entrada)

        # Registra consumo
        from datetime import date
        usuario_repo.incrementar_consumo(db, usuario.id, date.today(), "ANALISE")

    return templates.TemplateResponse(
        request, "analise.html",
        {
            "pagina_ativa": "analise",
            "usuario": usuario,
            "entrada": entrada,
            "resultado": resultado,
        },
    )


@router.get("/buscar", response_class=HTMLResponse)
async def pagina_buscar(
    request: Request,
    q: str = Query("", alias="q"),
    apenas_ativos: bool = Query(True),
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
    usuario: Optional[Usuario] = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    if not usuario:
        return _redir_login("/buscar")

    resultados = []
    total = 0
    sugestao = None

    if q and len(q.strip()) >= 2:
        resposta = busca_medicamento.buscar(db, q.strip(), apenas_ativos, pagina, limite)
        resultados = resposta.resultados
        total = resposta.total
        sugestao = resposta.sugestao

        # Registra consumo
        from datetime import date
        usuario_repo.incrementar_consumo(db, usuario.id, date.today(), "MEDICAMENTOS")

    return templates.TemplateResponse(
        request, "buscar.html",
        {
            "pagina_ativa": "buscar",
            "usuario": usuario,
            "q": q.strip(),
            "apenas_ativos": apenas_ativos,
            "pagina": pagina,
            "limite": limite,
            "resultados": resultados,
            "total": total,
            "sugestao": sugestao,
        },
    )


# ── Chaves de Acesso ───────────────────────────────────────────────────────

@router.get("/chaves", response_class=HTMLResponse)
async def pagina_chaves(
    request: Request,
    usuario: Usuario = Depends(requer_usuario_web),
    db: Session = Depends(get_db),
):
    chaves = usuario_repo.listar_chaves_usuario(db, usuario.id)
    return templates.TemplateResponse(
        request, "chaves.html",
        {
            "pagina_ativa": "chaves",
            "usuario": usuario,
            "chaves": chaves,
            "chave_criada": None,
        },
    )


@router.post("/chaves/criar")
async def criar_chave_web(
    request: Request,
    nome: str = Form(...),
    usuario: Usuario = Depends(requer_usuario_web),
    db: Session = Depends(get_db),
):
    token, prefixo, token_hash = auth_service.gerar_chave_acesso()
    usuario_repo.criar_chave_acesso(db, usuario.id, nome, prefixo, token_hash)
    chaves = usuario_repo.listar_chaves_usuario(db, usuario.id)
    return templates.TemplateResponse(
        request, "chaves.html",
        {
            "pagina_ativa": "chaves",
            "usuario": usuario,
            "chaves": chaves,
            "chave_criada": token,
        },
    )


@router.post("/chaves/revogar/{chave_id}")
async def revogar_chave_web(
    chave_id: int,
    usuario: Usuario = Depends(requer_usuario_web),
    db: Session = Depends(get_db),
):
    usuario_repo.revogar_chave_acesso(db, chave_id, usuario.id)
    return RedirectResponse(url="/chaves", status_code=status.HTTP_302_FOUND)


# ── Histórico de Consumo ───────────────────────────────────────────────────

@router.get("/consumo", response_class=HTMLResponse)
async def pagina_consumo(
    request: Request,
    usuario: Usuario = Depends(requer_usuario_web),
    db: Session = Depends(get_db),
):
    from datetime import date, timedelta
    import json

    hoje = date.today()
    plano = usuario_repo.obter_plano_usuario(db, usuario)
    limite_diario = plano.limite_diario if plano else 100
    limite_mensal = plano.limite_mensal if plano else 2000
    nome_plano = plano.nome if plano else "Gratuito"

    consumo_hoje = usuario_repo.obter_consumo_total_dia(db, usuario.id, hoje)
    consumo_mes = usuario_repo.obter_consumo_mensal(db, usuario.id, hoje.year, hoje.month)

    por_modulo_hoje = usuario_repo.obter_consumo_por_modulo(db, usuario.id, hoje)
    por_modulo_mes = usuario_repo.obter_consumo_por_modulo_mes(db, usuario.id, hoje.year, hoje.month)

    pct_dia = round(consumo_hoje / limite_diario * 100, 1) if limite_diario else 0
    pct_mes = round(consumo_mes / limite_mensal * 100, 1) if limite_mensal else 0

    # Calcular média diária do mês
    dias_no_mes = hoje.day
    media_diaria = round(consumo_mes / dias_no_mes) if dias_no_mes > 0 else 0

    # Tendência (comparação com mês anterior - simulado)
    tendencia = 0

    # Histórico últimos 30 dias para gráfico
    historico = {"labels": [], "medicamentos": [], "analise": []}
    for i in range(29, -1, -1):
        dia = hoje - timedelta(days=i)
        historico["labels"].append(dia.strftime("%d/%m"))

        consumo_dia = usuario_repo.obter_consumo_por_modulo(db, usuario.id, dia)
        med = next((c["total"] for c in consumo_dia if c["modulo"] == "MEDICAMENTOS"), 0)
        ana = next((c["total"] for c in consumo_dia if c["modulo"] == "ANALISE"), 0)

        historico["medicamentos"].append(med)
        historico["analise"].append(ana)

    return templates.TemplateResponse(
        request, "consumo.html",
        {
            "pagina_ativa": "consumo",
            "usuario": usuario,
            "plano": nome_plano,
            "limite_diario": limite_diario,
            "limite_mensal": limite_mensal,
            "consumo_hoje": consumo_hoje,
            "consumo_mes": consumo_mes,
            "pct_dia": pct_dia,
            "pct_mes": pct_mes,
            "media_diaria": media_diaria,
            "tendencia": tendencia,
            "por_modulo_hoje": por_modulo_hoje,
            "por_modulo_mes": por_modulo_mes,
            "historico_json": json.dumps(historico),
        },
    )
