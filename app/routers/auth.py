"""
Endpoints de autenticação: cadastro, login, logout, refresh de token.
"""
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.auth import CadastroEntrada, LoginEntrada, RefreshEntrada, TokenSaida
from app.schemas.usuario import UsuarioPerfil
from app.services import auth_service
from app.repositories import usuario_repo
from app.middleware.auth_middleware import requer_usuario
from app.config import settings

router = APIRouter()

_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _set_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    secure = settings.is_production
    response.set_cookie(
        "access_token", access_token,
        httponly=True, samesite="lax", secure=secure,
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        "refresh_token", refresh_token,
        httponly=True, samesite="lax", secure=secure,
        max_age=settings.refresh_token_expire_days * 86400,
        path="/auth/refresh",
    )


@router.post(
    "/cadastro",
    response_model=TokenSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Criar conta de usuário",
)
def cadastrar(
    entrada: CadastroEntrada,
    response: Response,
    db: Session = Depends(get_db),
):
    if not _RE_EMAIL.match(entrada.email):
        raise HTTPException(400, "E-mail inválido.")
    if usuario_repo.buscar_por_email(db, entrada.email):
        raise HTTPException(400, "E-mail já cadastrado. Faça login ou use outro e-mail.")

    senha_hash = auth_service.hash_senha(entrada.senha)
    usuario = usuario_repo.criar_usuario(db, entrada.nome, entrada.email, senha_hash)

    access = auth_service.criar_access_token(usuario.id, usuario.email, usuario.perfil)
    refresh, expira = auth_service.criar_refresh_token(usuario.id)
    usuario_repo.salvar_refresh_token(
        db, usuario.id, auth_service.hash_refresh_token(refresh), expira
    )
    _set_cookies(response, access, refresh)
    return TokenSaida(
        access_token=access,
        refresh_token=refresh,
        expira_em=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/login",
    response_model=TokenSaida,
    summary="Autenticar usuário",
)
def login(
    entrada: LoginEntrada,
    response: Response,
    db: Session = Depends(get_db),
):
    usuario = usuario_repo.buscar_por_email(db, entrada.email)
    if not usuario or not auth_service.verificar_senha(entrada.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )
    if not usuario.ativo:
        raise HTTPException(403, "Conta desativada. Entre em contato com o suporte.")

    access = auth_service.criar_access_token(usuario.id, usuario.email, usuario.perfil)
    refresh, expira = auth_service.criar_refresh_token(usuario.id)
    usuario_repo.salvar_refresh_token(
        db, usuario.id, auth_service.hash_refresh_token(refresh), expira
    )
    _set_cookies(response, access, refresh)
    return TokenSaida(
        access_token=access,
        refresh_token=refresh,
        expira_em=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenSaida,
    summary="Renovar access token usando refresh token",
)
def renovar_token(
    entrada: RefreshEntrada,
    response: Response,
    db: Session = Depends(get_db),
):
    payload = auth_service.decodificar_token(entrada.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "Refresh token inválido ou expirado.")

    token_hash = auth_service.hash_refresh_token(entrada.refresh_token)
    token_salvo = usuario_repo.buscar_refresh_token(db, token_hash)
    if not token_salvo:
        raise HTTPException(401, "Refresh token revogado ou não encontrado.")

    if token_salvo.expira_em.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(401, "Refresh token expirado. Faça login novamente.")

    usuario = usuario_repo.buscar_por_id(db, int(payload["sub"]))
    if not usuario or not usuario.ativo:
        raise HTTPException(401, "Usuário não encontrado ou inativo.")

    access = auth_service.criar_access_token(usuario.id, usuario.email, usuario.perfil)
    novo_refresh, expira = auth_service.criar_refresh_token(usuario.id)

    # Rotação: revoga o antigo, salva o novo
    token_salvo.revogado = True
    db.commit()
    usuario_repo.salvar_refresh_token(
        db, usuario.id, auth_service.hash_refresh_token(novo_refresh), expira
    )
    _set_cookies(response, access, novo_refresh)
    return TokenSaida(
        access_token=access,
        refresh_token=novo_refresh,
        expira_em=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Encerrar sessão",
)
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/auth/refresh")
    return None


@router.get(
    "/me",
    response_model=UsuarioPerfil,
    summary="Perfil do usuário autenticado",
)
def perfil_me(usuario: Usuario = Depends(requer_usuario)):
    return UsuarioPerfil.model_validate(usuario)
