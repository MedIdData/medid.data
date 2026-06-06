"""
Middleware de controle de limites de uso (rate limiting).
"""
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.models.usuario import Usuario
from app.repositories import usuario_repo


class LimiteExcedidoException(HTTPException):
    """Exception customizada para limite excedido."""
    def __init__(self, mensagem: str, tipo: str = "diario"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=mensagem
        )
        self.tipo = tipo


def verificar_limite_usuario(db: Session, usuario: Usuario) -> None:
    """
    Verifica se o usuário atingiu o limite diário ou mensal TOTAL.
    Os limites são globais (somam MEDICAMENTOS + ANALISE).
    Lança LimiteExcedidoException se limite atingido.

    Args:
        db: Sessão do banco
        usuario: Usuário atual

    Raises:
        LimiteExcedidoException: Se limite diário ou mensal foi atingido
    """
    # Administradores não têm limites (0 = ilimitado)
    if usuario.limite_diario == 0 or usuario.limite_mensal == 0:
        return

    hoje = date.today()

    # Verificar limite diário
    consumo_hoje = usuario_repo.obter_consumo_total_dia(db, usuario.id, hoje)
    if consumo_hoje >= usuario.limite_diario:
        raise LimiteExcedidoException(
            mensagem="Você atingiu seu limite de uso. Verifique seus limites e consumo no painel de uso.",
            tipo="diario"
        )

    # Verificar limite mensal
    consumo_mes = usuario_repo.obter_consumo_mensal(db, usuario.id, hoje.year, hoje.month)
    if consumo_mes >= usuario.limite_mensal:
        raise LimiteExcedidoException(
            mensagem="Você atingiu seu limite de uso. Verifique seus limites e consumo no painel de uso.",
            tipo="mensal"
        )


def registrar_consumo(db: Session, usuario: Usuario, modulo: str) -> None:
    """
    Registra consumo do usuário.

    Args:
        db: Sessão do banco
        usuario: Usuário atual
        modulo: Módulo (MEDICAMENTOS ou ANALISE)
    """
    hoje = date.today()
    usuario_repo.incrementar_consumo(db, usuario.id, hoje, modulo)
