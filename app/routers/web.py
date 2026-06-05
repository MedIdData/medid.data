"""
Rotas da interface web (HTML/Jinja2).
Auth protege /buscar, /analise, /painel, /chaves, /consumo.
"""
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import ValidationError

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.analise import AnaliseEntrada
from app.services import busca_medicamento, analise_risco
from app.middleware.auth_middleware import (
    get_usuario_atual,
    requer_usuario_web,
    RedirectParaLogin,
)
from app.repositories import usuario_repo, convite_repo
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

    senha_valida = False

    if usuario:
        senha_valida = auth_service.verificar_senha(
            senha,
            usuario.senha_hash
        )

    if not usuario or not senha_valida:
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
    preco_informado: str = Query("0"),  # Recebe como string para validar conversão
    tratamento: str = Query(""),
    cid: str = Query(""),
    procedimento: str = Query(""),
    quantidade: str = Query("1"),  # Recebe como string para validar conversão
    usuario: Optional[Usuario] = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    if not usuario:
        return _redir_login("/analise")

    resultado = None
    entrada = None
    erro = None

    # Converte e valida inputs numéricos antes de criar AnaliseEntrada
    if medicamento.strip():
        try:
            # Validação e conversão de preço
            try:
                preco_float = float(preco_informado.replace(',', '.'))
                if preco_float < 0:
                    raise ValueError("Preço não pode ser negativo")
                if preco_float > 999999.99:
                    raise ValueError("Preço muito alto (máximo R$ 999.999,99)")
            except ValueError as e:
                if "could not convert" in str(e):
                    raise ValueError(f"Preço inválido: '{preco_informado}' não é um número válido")
                raise

            # Validação e conversão de quantidade
            try:
                quantidade_int = int(quantidade)
                if quantidade_int < 1:
                    raise ValueError("Quantidade deve ser pelo menos 1")
                if quantidade_int > 9999:
                    raise ValueError("Quantidade muito alta (máximo 9999)")
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Quantidade inválida: '{quantidade}' não é um número válido")
                raise

            # Valida e cria entrada
            entrada = AnaliseEntrada(
                medicamento=medicamento,
                preco_informado=preco_float,
                tratamento=tratamento,
                cid=cid,
                procedimento=procedimento,
                quantidade=quantidade_int,
            )

            # Executa análise
            resultado = analise_risco.analisar(db, entrada)

            # Registra consumo
            from datetime import date
            usuario_repo.incrementar_consumo(db, usuario.id, date.today(), "ANALISE")

        except ValidationError as e:
            # Erro de validação Pydantic - extrai mensagens amigáveis
            erros = []
            for err in e.errors():
                campo = err['loc'][-1] if err['loc'] else 'campo'
                msg = err['msg']

                # Traduz mensagens comuns
                if 'String should match pattern' in msg:
                    if campo == 'cid':
                        erros.append('CID-10 inválido (formato: A00 ou A00.0)')
                    elif campo == 'procedimento':
                        erros.append('Código SIGTAP inválido (formato: 00.00.00.000-0)')
                    else:
                        erros.append(f'{campo.title()}: formato inválido')
                elif 'should have at least' in msg:
                    erros.append(f'{campo.title()} muito curto')
                elif 'should have at most' in msg:
                    erros.append(f'{campo.title()} muito longo')
                else:
                    # Usa mensagem original se não houver tradução
                    erros.append(msg)

            erro = ' | '.join(erros)

        except ValueError as e:
            # Erros de conversão ou validação customizada
            erro = str(e)

        except Exception as e:
            # Outros erros inesperados
            erro = f"Erro ao processar análise: {str(e)}"

    return templates.TemplateResponse(
        request, "analise.html",
        {
            "pagina_ativa": "analise",
            "usuario": usuario,
            "entrada": entrada,
            "resultado": resultado,
            "erro": erro,
        },
    )


@router.get("/buscar", response_class=HTMLResponse)
async def pagina_buscar(
    request: Request,
    q: str = Query("", alias="q"),
    apenas_ativos: bool = Query(True),
    pagina: int = Query(1, ge=1),
    limite: int = Query(50, ge=1, le=100),  # 50 por página (performance)
    usuario: Optional[Usuario] = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    if not usuario:
        return _redir_login("/buscar")

    resultados = []
    total = 0
    sugestao = None
    termo_busca = q.strip() if q else ""

    # Busca na BASE COMPLETA (não apenas primeiros 500)
    resposta = busca_medicamento.buscar(db, termo_busca, apenas_ativos, pagina, limite)
    resultados = resposta.resultados
    total = resposta.total
    sugestao = resposta.sugestao

    # Registra consumo se houve resultados
    if resultados:
        from datetime import date
        usuario_repo.incrementar_consumo(db, usuario.id, date.today(), "MEDICAMENTOS")

    # Calcula paginação
    total_paginas = (total + limite - 1) // limite if total > 0 else 0

    return templates.TemplateResponse(
        request, "buscar.html",
        {
            "pagina_ativa": "buscar",
            "usuario": usuario,
            "q": termo_busca,
            "apenas_ativos": apenas_ativos,
            "pagina": pagina,
            "limite": limite,
            "resultados": resultados,
            "total": total,
            "total_paginas": total_paginas,
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


@router.get("/perfil", response_class=HTMLResponse)
async def pagina_perfil(
    request: Request,
    usuario: Usuario = Depends(requer_usuario_web),
    db: Session = Depends(get_db),
):
    plano = usuario_repo.obter_plano_usuario(db, usuario)
    return templates.TemplateResponse(
        request, "perfil.html",
        {
            "pagina_ativa": "perfil",
            "usuario": usuario,
            "plano": plano.nome if plano else "Gratuito",
        },
    )


@router.get("/alterar-senha", response_class=HTMLResponse)
async def pagina_alterar_senha(
    request: Request,
    sucesso: str = Query(""),
    erro: str = Query(""),
    usuario: Usuario = Depends(requer_usuario_web),
):
    return templates.TemplateResponse(
        request, "alterar_senha.html",
        {
            "pagina_ativa": "alterar_senha",
            "usuario": usuario,
            "sucesso": sucesso,
            "erro": erro,
        },
    )


@router.post("/alterar-senha")
async def processar_alterar_senha(
    request: Request,
    senha_atual: str = Form(...),
    senha_nova: str = Form(...),
    senha_confirmar: str = Form(...),
    usuario: Usuario = Depends(requer_usuario_web),
    db: Session = Depends(get_db),
):
    # Validações
    if senha_nova != senha_confirmar:
        return RedirectResponse(
            url="/alterar-senha?erro=As senhas não coincidem",
            status_code=status.HTTP_302_FOUND
        )
    if len(senha_nova) < 6:
        return RedirectResponse(
            url="/alterar-senha?erro=A senha deve ter pelo menos 6 caracteres",
            status_code=status.HTTP_302_FOUND
        )
    if not auth_service.verificar_senha(senha_atual, usuario.senha_hash):
        return RedirectResponse(
            url="/alterar-senha?erro=Senha atual incorreta",
            status_code=status.HTTP_302_FOUND
        )

    # Atualizar senha
    nova_senha_hash = auth_service.hash_senha(senha_nova)
    usuario_repo.atualizar_senha_usuario(db, usuario.id, nova_senha_hash)
    usuario_repo.revogar_refresh_tokens_usuario(db, usuario.id)

    return RedirectResponse(
        url="/alterar-senha?sucesso=Senha alterada com sucesso",
        status_code=status.HTTP_302_FOUND
    )


# ── Administração ──────────────────────────────────────────────────────────

def requer_admin(usuario: Usuario = Depends(requer_usuario_web)):
    """Middleware que valida se usuário é administrador."""
    # Aceita ADMINISTRADOR e ADMIN (compatibilidade)
    if usuario.perfil not in ('ADMINISTRADOR', 'ADMIN'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores podem acessar esta área."
        )
    return usuario


@router.get("/admin", response_class=HTMLResponse)
async def pagina_admin(
    request: Request,
    usuario: Usuario = Depends(requer_admin),
    db: Session = Depends(get_db),
):
    from datetime import date

    # Estatísticas
    total_usuarios = usuario_repo.contar_usuarios(db)
    usuarios_ativos = usuario_repo.contar_usuarios_ativos(db)
    total_chaves = usuario_repo.contar_chaves_total(db)
    requisicoes_hoje = usuario_repo.obter_consumo_sistema_dia(db, date.today())

    # Lista de usuários com suas chaves
    usuarios = usuario_repo.listar_todos_usuarios(db)

    # Mapear chaves e consumo por usuário
    chaves_por_usuario = {}
    consumo_por_usuario = {}

    for u in usuarios:
        chaves = usuario_repo.listar_chaves_usuario(db, u.id)
        chaves_por_usuario[u.id] = chaves

        # Calcular % de consumo do dia
        consumo_hoje = usuario_repo.obter_consumo_total_dia(db, u.id, date.today())

        if u.limite_diario and u.limite_diario > 0:
            percentual = (consumo_hoje / u.limite_diario) * 100
        else:
            percentual = 0  # Ilimitado

        consumo_por_usuario[u.id] = {
            "consumo_hoje": consumo_hoje,
            "percentual": min(percentual, 100),  # Cap at 100%
        }

    return templates.TemplateResponse(
        request, "admin.html",
        {
            "pagina_ativa": "admin",
            "usuario": usuario,
            "total_usuarios": total_usuarios,
            "usuarios_ativos": usuarios_ativos,
            "total_chaves": total_chaves,
            "requisicoes_hoje": requisicoes_hoje,
            "usuarios": usuarios,
            "chaves_por_usuario": chaves_por_usuario,
            "consumo_por_usuario": consumo_por_usuario,
        },
    )


@router.post("/admin/usuarios/criar")
async def admin_criar_usuario(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    perfil: str = Form(...),
    limite_diario: int = Form(100),
    limite_mensal: int = Form(2000),
    usuario: Usuario = Depends(requer_admin),
    db: Session = Depends(get_db),
):
    # Validações
    email_normalizado = email.strip().lower()
    if usuario_repo.buscar_por_email(db, email_normalizado):
        return RedirectResponse(url="/admin?erro=Email já cadastrado", status_code=status.HTTP_302_FOUND)

    # Criar usuário com senha temporária (será alterada no primeiro acesso)
    senha_temp = auth_service.gerar_senha_temporaria()
    senha_hash = auth_service.hash_senha(senha_temp)
    novo_usuario = usuario_repo.criar_usuario(db, nome, email_normalizado, senha_hash)

    # Atualizar perfil e limites
    usuario_repo.atualizar_perfil_usuario(db, novo_usuario.id, perfil)
    usuario_repo.atualizar_limites_usuario(db, novo_usuario.id, limite_diario, limite_mensal)

    # Gerar convite (válido por 72h)
    convite = convite_repo.gerar_convite(db, novo_usuario.id, validade_horas=72)

    # Construir link de ativação (usa /convite para preview com OG tags)
    base_url = str(request.base_url).rstrip('/')
    link_ativacao = f"{base_url}/convite/{convite.token}"

    # Redirecionar para página com o link
    return RedirectResponse(
        url=f"/admin/usuario-criado?link={link_ativacao}&nome={nome}&email={email_normalizado}",
        status_code=status.HTTP_302_FOUND
    )


@router.post("/admin/usuarios/{usuario_id}/editar")
async def admin_editar_usuario(
    usuario_id: int,
    nome: str = Form(...),
    email: str = Form(...),
    perfil: str = Form(...),
    ativo: str = Form(...),
    limite_diario: Optional[int] = Form(None),
    limite_mensal: Optional[int] = Form(None),
    usuario: Usuario = Depends(requer_admin),
    db: Session = Depends(get_db),
):
    # Atualizar dados
    ativo_bool = ativo == 'true'
    usuario_repo.atualizar_usuario(db, usuario_id, nome, email, perfil, ativo_bool)

    # Atualizar limites (sempre atualiza, mesmo que seja None = ilimitado)
    usuario_repo.atualizar_limites_usuario(db, usuario_id, limite_diario, limite_mensal)

    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)


@router.post("/admin/usuarios/{usuario_id}/resetar-senha")
async def admin_resetar_senha(
    usuario_id: int,
    senha: str = Form(...),
    usuario: Usuario = Depends(requer_admin),
    db: Session = Depends(get_db),
):
    if len(senha) < 6:
        return RedirectResponse(url="/admin?erro=Senha deve ter pelo menos 6 caracteres", status_code=status.HTTP_302_FOUND)
    
    senha_hash = auth_service.hash_senha(senha)
    usuario_repo.atualizar_senha_usuario(db, usuario_id, senha_hash)
    usuario_repo.revogar_refresh_tokens_usuario(db, usuario_id)
    
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)


@router.post("/admin/usuarios/{usuario_id}/toggle-status")
async def admin_toggle_status(
    usuario_id: int,
    usuario: Usuario = Depends(requer_admin),
    db: Session = Depends(get_db),
):
    usuario_repo.toggle_status_usuario(db, usuario_id)
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)


# ── Convites e Ativação de Conta ──────────────────────────────────────────

@router.get("/admin/usuario-criado", response_class=HTMLResponse)
async def pagina_usuario_criado(
    request: Request,
    link: str = Query(...),
    nome: str = Query(...),
    email: str = Query(...),
    usuario: Usuario = Depends(requer_admin),
):
    return templates.TemplateResponse(
        request, "usuario_criado.html",
        {
            "pagina_ativa": "admin",
            "usuario": usuario,
            "link": link,
            "nome": nome,
            "email": email,
        },
    )


@router.get("/ativar-conta/{token}", response_class=HTMLResponse)
async def pagina_ativar_conta(
    request: Request,
    token: str,
    db: Session = Depends(get_db),
):
    convite = convite_repo.buscar_convite_valido(db, token)

    if not convite:
        return templates.TemplateResponse(
            request, "convite_expirado.html", {}
        )

    usuario = usuario_repo.buscar_por_id(db, convite.usuario_id)

    return templates.TemplateResponse(
        request, "ativar_conta.html",
        {
            "token": token,
            "usuario": usuario,
        },
    )


@router.post("/ativar-conta/{token}")
async def ativar_conta(
    request: Request,
    token: str,
    senha: str = Form(...),
    confirmar_senha: str = Form(...),
    db: Session = Depends(get_db),
):
    convite = convite_repo.buscar_convite_valido(db, token)

    if not convite:
        return templates.TemplateResponse(
            request, "convite_expirado.html", {}
        )

    # Validações
    if senha != confirmar_senha:
        usuario = usuario_repo.buscar_por_id(db, convite.usuario_id)
        return templates.TemplateResponse(
            request, "ativar_conta.html",
            {
                "token": token,
                "usuario": usuario,
                "erro": "As senhas não coincidem",
            },
        )

    if len(senha) < 6:
        usuario = usuario_repo.buscar_por_id(db, convite.usuario_id)
        return templates.TemplateResponse(
            request, "ativar_conta.html",
            {
                "token": token,
                "usuario": usuario,
                "erro": "A senha deve ter pelo menos 6 caracteres",
            },
        )

    # Atualizar senha do usuário
    senha_hash = auth_service.hash_senha(senha)
    usuario_repo.atualizar_senha_usuario(db, convite.usuario_id, senha_hash)

    # Marcar convite como usado
    convite_repo.marcar_convite_usado(db, convite.id)

    # Fazer login automático
    usuario = usuario_repo.buscar_por_id(db, convite.usuario_id)
    access_token = auth_service.criar_access_token(
        usuario.id, usuario.email, usuario.perfil
    )

    response = RedirectResponse(url="/buscar", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        samesite="lax",
    )

    return response


@router.get("/convite/{token}", response_class=HTMLResponse)
async def preview_convite(
    request: Request,
    token: str,
    db: Session = Depends(get_db),
):
    """Preview do convite com Open Graph tags para WhatsApp/Email."""
    convite = convite_repo.buscar_convite_valido(db, token)

    if not convite:
        return templates.TemplateResponse(
            request, "convite_expirado.html", {}
        )

    return templates.TemplateResponse(
        request, "convite_preview.html",
        {
            "token": token,
            "request": request,
        },
    )


@router.get("/admin/usuarios/{usuario_id}/detalhes", response_class=HTMLResponse)
async def admin_usuario_detalhes(
    request: Request,
    usuario_id: int,
    admin: Usuario = Depends(requer_admin),
    db: Session = Depends(get_db),
):
    """Página completa de detalhes do usuário."""
    # Buscar usuário
    usuario = usuario_repo.buscar_por_id(db, usuario_id)
    if not usuario:
        return RedirectResponse(url="/admin?erro=Usuário não encontrado", status_code=status.HTTP_302_FOUND)
    
    # Dados gerais
    plano = usuario_repo.obter_plano_usuario(db, usuario)
    ultimo_login = usuario_repo.obter_ultimo_login(db, usuario_id)
    ultimo_uso_api = usuario_repo.obter_ultimo_uso_api(db, usuario_id)
    
    # Estatísticas
    stats = usuario_repo.obter_estatisticas_usuario(db, usuario_id)
    
    # Chaves API
    chaves = usuario_repo.listar_chaves_usuario(db, usuario_id)
    
    # Histórico
    historico = usuario_repo.obter_historico_consumo_usuario(db, usuario_id, limite=30)
    
    # Auditoria
    auditoria = usuario_repo.obter_auditoria_usuario(db, usuario_id, limite=20)
    
    return templates.TemplateResponse(
        request, "admin_usuario_detalhes.html",
        {
            "pagina_ativa": "admin",
            "usuario": usuario,
            "plano": plano,
            "ultimo_login": ultimo_login,
            "ultimo_uso_api": ultimo_uso_api,
            "stats": stats,
            "chaves": chaves,
            "historico": historico,
            "auditoria": auditoria,
        },
    )


@router.post("/admin/api/usuarios/{usuario_id}/revogar-chave/{chave_id}")
async def admin_revogar_chave(
    usuario_id: int,
    chave_id: int,
    admin: Usuario = Depends(requer_admin),
    db: Session = Depends(get_db),
):
    """Revogar uma chave API específica."""
    usuario_repo.revogar_chave_acesso(db, chave_id, usuario_id)
    return RedirectResponse(
        url=f"/admin/usuarios/{usuario_id}/detalhes",
        status_code=status.HTTP_302_FOUND
    )
