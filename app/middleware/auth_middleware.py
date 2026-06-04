"""
Dependências de autenticação e controle de acesso para FastAPI.

Suporta dois mecanismos:
  - JWT no cookie HTTP-only (canal WEB)
  - JWT Bearer no header Authorization (canal API)
  - Chave de acesso "med_..." no header Authorization ou X-API-Key (canal API)

Uso nos routers:
  usuario: Usuario = Depends(requer_usuario)
  usuario: Usuario = Depends(requer_acesso("MEDICAMENTOS"))
"""
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.services import auth_service
from app.repositories import usuario_repo


class RedirectParaLogin(Exception):
    """Lançada quando rota web exige autenticação e usuário não está logado."""
    pass


# ── Extração do usuário ────────────────────────────────────────────────────

def _token_do_request(request: Request) -> tuple[Optional[str], str]:
    """Retorna (token, canal). Canal = 'WEB' ou 'API'."""
    # 1. Cookie (web)
    cookie = request.cookies.get("access_token")
    if cookie:
        return cookie, "WEB"

    # 2. Header Authorization: Bearer <token>
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:], "API"

    # 3. Header X-API-Key (alternativa)
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        return api_key, "API"

    return None, "API"


async def get_usuario_atual(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[Usuario]:
    """Retorna o usuário autenticado ou None (não lança exceção)."""
    token, canal = _token_do_request(request)
    if not token:
        return None

    # Chave de acesso (começa com "med_")
    if token.startswith("med_"):
        chave_hash = auth_service.hash_chave(token)
        chave = usuario_repo.buscar_chave_ativa(db, chave_hash)
        if not chave:
            return None
        # Atualiza último uso
        chave.ultimo_uso_em = datetime.now(timezone.utc)
        db.commit()
        return chave.usuario

    # JWT
    payload = auth_service.decodificar_token(token)
    if not payload or payload.get("type") != "access":
        return None
    usuario_id = payload.get("sub")
    if not usuario_id:
        return None
    return usuario_repo.buscar_por_id(db, int(usuario_id))


async def requer_usuario(
    request: Request,
    db: Session = Depends(get_db),
) -> Usuario:
    """Exige autenticação. Retorna 401 se não autenticado (para rotas API)."""
    usuario = await get_usuario_atual(request, db)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada. Entre em contato com o suporte.",
        )
    return usuario


async def requer_usuario_web(
    request: Request,
    db: Session = Depends(get_db),
) -> Usuario:
    """Exige autenticação. Lança RedirectParaLogin se não autenticado (para rotas web)."""
    usuario = await get_usuario_atual(request, db)
    if not usuario:
        raise RedirectParaLogin()
    if not usuario.ativo:
        raise RedirectParaLogin()
    return usuario


# ── Controle de acesso com limite de plano ────────────────────────────────

def _canal_do_request(request: Request) -> str:
    if request.cookies.get("access_token"):
        return "WEB"
    return "API"


def _chave_id_do_request(request: Request, db: Session) -> Optional[int]:
    auth = request.headers.get("Authorization", "") or request.headers.get("X-API-Key", "")
    token = auth[7:] if auth.startswith("Bearer ") else auth
    if token.startswith("med_"):
        chave_hash = auth_service.hash_chave(token)
        chave = usuario_repo.buscar_chave_ativa(db, chave_hash)
        return chave.id if chave else None
    return None


def requer_acesso(modulo: str):
    """
    Dependência que:
    1. Exige autenticação (JWT ou chave)
    2. Verifica o limite diário e mensal do plano
    3. Incrementa o contador de consumo
    4. Registra na auditoria
    """
    async def _check(
        request: Request,
        usuario: Usuario = Depends(requer_usuario),
        db: Session = Depends(get_db),
    ) -> Usuario:
        hoje = date.today()
        plano = usuario_repo.obter_plano_usuario(db, usuario)
        limite_diario = plano.limite_diario if plano else 100
        limite_mensal = plano.limite_mensal if plano else 2000

        consumo_hoje = usuario_repo.obter_consumo_total_dia(db, usuario.id, hoje)
        if consumo_hoje >= limite_diario:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Limite diário de {limite_diario} consultas atingido. "
                       "Aguarde o próximo dia ou faça upgrade do plano.",
            )

        consumo_mes = usuario_repo.obter_consumo_mensal(
            db, usuario.id, hoje.year, hoje.month
        )
        if consumo_mes >= limite_mensal:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Limite mensal de {limite_mensal} consultas atingido. "
                       "Aguarde o próximo mês ou faça upgrade do plano.",
            )

        # Incrementa consumo
        usuario_repo.incrementar_consumo(db, usuario.id, hoje, modulo)

        # Registra auditoria
        canal = _canal_do_request(request)
        chave_id = _chave_id_do_request(request, db)
        ip = request.client.host if request.client else None
        usuario_repo.registrar_auditoria(
            db=db,
            usuario_id=usuario.id,
            chave_acesso_id=chave_id,
            canal=canal,
            modulo=modulo,
            endpoint=str(request.url.path),
            metodo=request.method,
            parametros=dict(request.query_params) or None,
            ip=ip,
        )

        return usuario

    return _check
