"""
Repositório de planos.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.empresa import Plano


def listar_todos(db: Session) -> list[Plano]:
    """Lista todos os planos."""
    return db.query(Plano).order_by(Plano.valor_mensal_centavos).all()


def listar_ativos(db: Session) -> list[Plano]:
    """Lista apenas planos ativos."""
    return db.query(Plano).filter(Plano.ativo == True).order_by(Plano.valor_mensal_centavos).all()


def buscar_por_id(db: Session, plano_id: int) -> Optional[Plano]:
    """Busca plano por ID."""
    return db.query(Plano).filter(Plano.id == plano_id).first()


def buscar_por_nome(db: Session, nome: str) -> Optional[Plano]:
    """Busca plano por nome."""
    return db.query(Plano).filter(Plano.nome == nome).first()


def criar(
    db: Session,
    nome: str,
    descricao: str,
    limite_diario: int,
    limite_mensal: int,
    valor_mensal_centavos: int
) -> Plano:
    """Cria um novo plano."""
    plano = Plano(
        nome=nome,
        descricao=descricao,
        limite_diario=limite_diario,
        limite_mensal=limite_mensal,
        valor_mensal_centavos=valor_mensal_centavos,
        ativo=True,
    )
    db.add(plano)
    db.commit()
    db.refresh(plano)
    return plano


def atualizar(
    db: Session,
    plano_id: int,
    nome: str,
    descricao: str,
    limite_diario: int,
    limite_mensal: int,
    valor_mensal_centavos: int,
    ativo: bool
) -> Optional[Plano]:
    """Atualiza um plano existente."""
    plano = buscar_por_id(db, plano_id)
    if not plano:
        return None

    plano.nome = nome
    plano.descricao = descricao
    plano.limite_diario = limite_diario
    plano.limite_mensal = limite_mensal
    plano.valor_mensal_centavos = valor_mensal_centavos
    plano.ativo = ativo

    db.commit()
    db.refresh(plano)
    return plano


def toggle_ativo(db: Session, plano_id: int) -> Optional[Plano]:
    """Ativa/desativa um plano."""
    plano = buscar_por_id(db, plano_id)
    if not plano:
        return None

    plano.ativo = not plano.ativo
    db.commit()
    db.refresh(plano)
    return plano


def contar_usuarios_por_plano(db: Session, plano_id: int) -> int:
    """Conta quantos usuários estão usando este plano."""
    from app.models.usuario import Usuario
    from app.models.empresa import Empresa

    return db.query(Usuario).join(
        Empresa, Usuario.empresa_id == Empresa.id
    ).filter(
        Empresa.plano_id == plano_id
    ).count()
