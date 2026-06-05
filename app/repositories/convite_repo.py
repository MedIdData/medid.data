"""
Repositório de convites de usuário.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.convite import ConviteUsuario


def gerar_convite(db: Session, usuario_id: int, validade_horas: int = 72) -> ConviteUsuario:
    """
    Gera um token de convite para o usuário definir senha.
    Padrão: válido por 72 horas (3 dias).
    """
    token = secrets.token_urlsafe(32)
    expira_em = datetime.now(timezone.utc) + timedelta(hours=validade_horas)

    convite = ConviteUsuario(
        usuario_id=usuario_id,
        token=token,
        usado=False,
        expira_em=expira_em,
    )
    db.add(convite)
    db.commit()
    db.refresh(convite)
    return convite


def buscar_convite_valido(db: Session, token: str) -> Optional[ConviteUsuario]:
    """Busca convite válido (não usado e não expirado)."""
    agora = datetime.now(timezone.utc)
    return db.query(ConviteUsuario).filter(
        ConviteUsuario.token == token,
        ConviteUsuario.usado == False,
        ConviteUsuario.expira_em > agora,
    ).first()


def marcar_convite_usado(db: Session, convite_id: int) -> None:
    """Marca o convite como usado."""
    convite = db.query(ConviteUsuario).filter(ConviteUsuario.id == convite_id).first()
    if convite:
        convite.usado = True
        convite.usado_em = datetime.now(timezone.utc)
        db.commit()


def invalidar_convites_usuario(db: Session, usuario_id: int) -> None:
    """Invalida todos os convites pendentes de um usuário."""
    db.query(ConviteUsuario).filter(
        ConviteUsuario.usuario_id == usuario_id,
        ConviteUsuario.usado == False,
    ).update({"usado": True, "usado_em": datetime.now(timezone.utc)})
    db.commit()
