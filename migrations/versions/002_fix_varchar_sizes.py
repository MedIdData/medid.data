"""Ajuste de tamanhos VARCHAR em medicamentos_anvisa

Revision ID: 002
Revises: 001
Create Date: 2026-06-03
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("medicamentos_anvisa", "forma_fisica", type_=sa.String(100))
    op.alter_column("medicamentos_anvisa", "data_finalizacao_processo", type_=sa.String(50))
    op.alter_column("medicamentos_anvisa", "data_vencimento_registro", type_=sa.String(50))
    op.alter_column("medicamentos_anvisa", "situacao_apresentacao", type_=sa.String(100))
    op.alter_column("medicamentos_anvisa", "situacao_registro", type_=sa.String(50))


def downgrade() -> None:
    op.alter_column("medicamentos_anvisa", "forma_fisica", type_=sa.String(20))
    op.alter_column("medicamentos_anvisa", "data_finalizacao_processo", type_=sa.String(30))
    op.alter_column("medicamentos_anvisa", "data_vencimento_registro", type_=sa.String(30))
    op.alter_column("medicamentos_anvisa", "situacao_apresentacao", type_=sa.String(50))
    op.alter_column("medicamentos_anvisa", "situacao_registro", type_=sa.String(30))
