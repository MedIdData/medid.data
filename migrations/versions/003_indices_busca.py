"""Índices adicionais para otimizar busca de medicamentos

Revision ID: 003
Revises: 002
Create Date: 2026-06-03
"""
from typing import Sequence, Union
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Índice funcional no CMED para o join com ANVISA por substância
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_medicamentos_cmed_substancia_upper
        ON medicamentos_cmed (upper(trim(substancia)))
    """)
    # Índice trgm para busca fuzzy em substância CMED
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_medicamentos_cmed_substancia_trgm
        ON medicamentos_cmed USING gin (substancia gin_trgm_ops)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_medicamentos_cmed_substancia_upper")
    op.execute("DROP INDEX IF EXISTS ix_medicamentos_cmed_substancia_trgm")
