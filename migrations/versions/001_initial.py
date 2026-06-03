"""Schema inicial completo do MedID Data

Revision ID: 001
Revises:
Create Date: 2026-06-03
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR, JSONB, INET, BIGINT

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensões ──────────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")

    # ── Dados de referência ────────────────────────────────────────────────────
    op.create_table(
        "medicamentos_anvisa",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("numero_registro", sa.String(50), unique=True),
        sa.Column("tipo_produto", sa.String(50)),
        sa.Column("nome_produto", sa.String(500)),
        sa.Column("data_finalizacao_processo", sa.String(30)),
        sa.Column("categoria_regulatoria", sa.String(100)),
        sa.Column("data_vencimento_registro", sa.String(30)),
        sa.Column("numero_processo", sa.String(100)),
        sa.Column("classe_terapeutica", sa.String(300)),
        sa.Column("empresa_detentora", sa.String(500)),
        sa.Column("situacao_registro", sa.String(30)),
        sa.Column("principio_ativo", sa.Text),
        sa.Column("indicacoes", sa.Text),
        sa.Column("sinonimos", sa.Text),
        sa.Column("codigo_atc", sa.String(30)),
        sa.Column("tarja", sa.String(50)),
        sa.Column("forma_fisica", sa.String(20)),
        sa.Column("situacao_apresentacao", sa.String(50)),
        sa.Column("substancias", sa.Text),
        sa.Column("search_vector", TSVECTOR),
        sa.Column("importado_em", sa.DateTime, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_medicamentos_anvisa_registro", "medicamentos_anvisa", ["numero_registro"])
    op.create_index("ix_medicamentos_anvisa_nome", "medicamentos_anvisa", ["nome_produto"])
    op.create_index("ix_medicamentos_anvisa_situacao", "medicamentos_anvisa", ["situacao_registro"])
    op.create_index(
        "ix_medicamentos_anvisa_search_gin", "medicamentos_anvisa", ["search_vector"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_medicamentos_anvisa_nome_trgm", "medicamentos_anvisa", ["nome_produto"],
        postgresql_using="gin",
        postgresql_ops={"nome_produto": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_medicamentos_anvisa_principio_trgm", "medicamentos_anvisa", ["principio_ativo"],
        postgresql_using="gin",
        postgresql_ops={"principio_ativo": "gin_trgm_ops"},
    )

    op.create_table(
        "medicamentos_cmed",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("codigo_ggrem", sa.String(20), unique=True),
        sa.Column("substancia", sa.Text),
        sa.Column("cnpj", sa.String(20)),
        sa.Column("laboratorio", sa.String(300)),
        sa.Column("registro", sa.String(50)),
        sa.Column("ean1", sa.String(20)),
        sa.Column("ean2", sa.String(20)),
        sa.Column("ean3", sa.String(20)),
        sa.Column("produto", sa.String(500)),
        sa.Column("apresentacao", sa.Text),
        sa.Column("classe_terapeutica", sa.String(300)),
        sa.Column("tipo_produto", sa.String(100)),
        sa.Column("regime_preco", sa.String(50)),
        sa.Column("pf_sem_impostos", sa.Numeric(12, 2)),
        sa.Column("pf_0", sa.Numeric(12, 2)),
        sa.Column("pf_12", sa.Numeric(12, 2)),
        sa.Column("pf_17", sa.Numeric(12, 2)),
        sa.Column("pf_17_5", sa.Numeric(12, 2)),
        sa.Column("pf_18", sa.Numeric(12, 2)),
        sa.Column("pf_20", sa.Numeric(12, 2)),
        sa.Column("pmc_sem_impostos", sa.Numeric(12, 2)),
        sa.Column("pmc_0", sa.Numeric(12, 2)),
        sa.Column("pmc_12", sa.Numeric(12, 2)),
        sa.Column("pmc_17", sa.Numeric(12, 2)),
        sa.Column("pmc_17_5", sa.Numeric(12, 2)),
        sa.Column("pmc_18", sa.Numeric(12, 2)),
        sa.Column("pmc_20", sa.Numeric(12, 2)),
        sa.Column("pmvg_sem_impostos", sa.Numeric(12, 2)),
        sa.Column("pmvg_0", sa.Numeric(12, 2)),
        sa.Column("pmvg_12", sa.Numeric(12, 2)),
        sa.Column("pmvg_17", sa.Numeric(12, 2)),
        sa.Column("pmvg_17_5", sa.Numeric(12, 2)),
        sa.Column("pmvg_18", sa.Numeric(12, 2)),
        sa.Column("pmvg_20", sa.Numeric(12, 2)),
        sa.Column("restricao_hospitalar", sa.Boolean),
        sa.Column("cap", sa.Boolean),
        sa.Column("confaz_87", sa.Boolean),
        sa.Column("icms_0", sa.Boolean),
        sa.Column("analise_recursal", sa.String(5)),
        sa.Column("comercializacao_2024", sa.String(5)),
        sa.Column("tarja", sa.String(50)),
        sa.Column("destinacao_comercial", sa.String(100)),
        sa.Column("importado_em", sa.DateTime, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_medicamentos_cmed_ggrem", "medicamentos_cmed", ["codigo_ggrem"])
    op.create_index("ix_medicamentos_cmed_registro", "medicamentos_cmed", ["registro"])

    op.create_table(
        "dcb",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("numero_dcb", sa.Integer, unique=True),
        sa.Column("denominacao", sa.String(300)),
        sa.Column("numero_cas", sa.String(50)),
        sa.Column("classificacao", sa.String(10)),
        sa.Column("historico", sa.Text),
        sa.Column("importado_em", sa.DateTime, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_dcb_denominacao", "dcb", ["denominacao"])
    op.create_index(
        "ix_dcb_denominacao_trgm", "dcb", ["denominacao"],
        postgresql_using="gin",
        postgresql_ops={"denominacao": "gin_trgm_ops"},
    )

    op.create_table(
        "cid10_categorias",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("codigo", sa.String(5), unique=True, nullable=False),
        sa.Column("classif", sa.String(10)),
        sa.Column("descricao", sa.String(300)),
        sa.Column("descricao_abrev", sa.String(200)),
        sa.Column("refer", sa.String(100)),
        sa.Column("excluidos", sa.Text),
    )
    op.create_index("ix_cid10_categorias_codigo", "cid10_categorias", ["codigo"])

    op.create_table(
        "cid10_subcategorias",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("categoria_id", sa.Integer, sa.ForeignKey("cid10_categorias.id")),
        sa.Column("codigo", sa.String(5), unique=True, nullable=False),
        sa.Column("classif", sa.String(10)),
        sa.Column("restricao_sexo", sa.String(5)),
        sa.Column("causa_obito", sa.Boolean),
        sa.Column("descricao", sa.String(300)),
        sa.Column("descricao_abrev", sa.String(200)),
        sa.Column("refer", sa.String(100)),
        sa.Column("excluidos", sa.Text),
    )
    op.create_index("ix_cid10_subcategorias_codigo", "cid10_subcategorias", ["codigo"])
    op.create_index(
        "ix_cid10_subcategorias_descricao_trgm", "cid10_subcategorias", ["descricao"],
        postgresql_using="gin",
        postgresql_ops={"descricao": "gin_trgm_ops"},
    )

    op.create_table(
        "sigtap_grupos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("codigo", sa.String(2), unique=True, nullable=False),
        sa.Column("descricao", sa.String(200)),
        sa.Column("competencia", sa.String(6)),
    )

    op.create_table(
        "sigtap_procedimentos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("grupo_id", sa.Integer, sa.ForeignKey("sigtap_grupos.id")),
        sa.Column("codigo", sa.String(10), unique=True, nullable=False),
        sa.Column("descricao", sa.String(300)),
        sa.Column("complexidade", sa.String(1)),
        sa.Column("sexo", sa.String(1)),
        sa.Column("qt_maxima_execucao", sa.Integer),
        sa.Column("qt_dias_permanencia", sa.Integer),
        sa.Column("qt_pontos", sa.Integer),
        sa.Column("vl_idade_minima", sa.Integer),
        sa.Column("vl_idade_maxima", sa.Integer),
        sa.Column("vl_sh", sa.Numeric(12, 2)),
        sa.Column("vl_sa", sa.Numeric(12, 2)),
        sa.Column("vl_sp", sa.Numeric(12, 2)),
        sa.Column("codigo_financiamento", sa.String(2)),
        sa.Column("codigo_rubrica", sa.String(6)),
        sa.Column("qt_tempo_permanencia", sa.Integer),
        sa.Column("competencia", sa.String(6)),
        sa.Column("search_vector", TSVECTOR),
    )
    op.create_index("ix_sigtap_procedimentos_codigo", "sigtap_procedimentos", ["codigo"])
    op.create_index(
        "ix_sigtap_procedimentos_search_gin", "sigtap_procedimentos", ["search_vector"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_sigtap_procedimentos_descricao_trgm", "sigtap_procedimentos", ["descricao"],
        postgresql_using="gin",
        postgresql_ops={"descricao": "gin_trgm_ops"},
    )

    op.create_table(
        "sigtap_procedimento_cid",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("procedimento_id", sa.Integer, sa.ForeignKey("sigtap_procedimentos.id")),
        sa.Column("cid_id", sa.Integer, sa.ForeignKey("cid10_subcategorias.id")),
        sa.Column("codigo_procedimento", sa.String(10)),
        sa.Column("codigo_cid", sa.String(5)),
        sa.Column("principal", sa.Boolean),
        sa.Column("competencia", sa.String(6)),
    )
    op.create_index("ix_sigtap_proc_cid_proc", "sigtap_procedimento_cid", ["codigo_procedimento"])
    op.create_index("ix_sigtap_proc_cid_cid", "sigtap_procedimento_cid", ["codigo_cid"])
    op.create_index("ix_sigtap_proc_cid_ids", "sigtap_procedimento_cid", ["procedimento_id", "cid_id"])

    # ── Planos e Empresas ──────────────────────────────────────────────────────
    op.create_table(
        "planos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String(100), unique=True, nullable=False),
        sa.Column("descricao", sa.Text),
        sa.Column("limite_diario", sa.Integer, nullable=False, server_default="100"),
        sa.Column("limite_mensal", sa.Integer, nullable=False, server_default="2000"),
        sa.Column("valor_mensal_centavos", sa.Integer, server_default="0"),
        sa.Column("ativo", sa.Boolean, server_default="true"),
        sa.Column("criado_em", sa.DateTime, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "empresas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("plano_id", sa.Integer, sa.ForeignKey("planos.id")),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("cnpj", sa.String(20), unique=True),
        sa.Column("email_contato", sa.String(200)),
        sa.Column("ativa", sa.Boolean, server_default="true"),
        sa.Column("criado_em", sa.DateTime, server_default=sa.text("NOW()")),
        sa.Column("atualizado_em", sa.DateTime, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_empresas_cnpj", "empresas", ["cnpj"])

    # ── Usuários ───────────────────────────────────────────────────────────────
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("empresa_id", sa.Integer, sa.ForeignKey("empresas.id")),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("email", sa.String(200), unique=True, nullable=False),
        sa.Column("senha_hash", sa.String(200), nullable=False),
        sa.Column("perfil", sa.String(20), nullable=False, server_default="CLIENTE"),
        sa.Column("ativo", sa.Boolean, server_default="true"),
        sa.Column("criado_em", sa.DateTime, server_default=sa.text("NOW()")),
        sa.Column("atualizado_em", sa.DateTime, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expira_em", sa.DateTime, nullable=False),
        sa.Column("revogado", sa.Boolean, server_default="false"),
        sa.Column("criado_em", sa.DateTime, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_refresh_tokens_hash", "refresh_tokens", ["token_hash"])

    op.create_table(
        "chaves_acesso",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("prefixo", sa.String(16), nullable=False),
        sa.Column("chave_hash", sa.String(64), nullable=False),
        sa.Column("ativa", sa.Boolean, server_default="true"),
        sa.Column("limite_diario_override", sa.Integer),
        sa.Column("limite_mensal_override", sa.Integer),
        sa.Column("ultimo_uso_em", sa.DateTime),
        sa.Column("criado_em", sa.DateTime, server_default=sa.text("NOW()")),
        sa.Column("revogada_em", sa.DateTime),
    )
    op.create_index("ix_chaves_acesso_hash", "chaves_acesso", ["chave_hash"])
    op.create_index("ix_chaves_acesso_usuario", "chaves_acesso", ["usuario_id"])

    # ── Auditoria e Consumo ────────────────────────────────────────────────────
    op.create_table(
        "auditoria_requisicoes",
        sa.Column("id", BIGINT, primary_key=True, autoincrement=True),
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuarios.id")),
        sa.Column("chave_acesso_id", sa.Integer, sa.ForeignKey("chaves_acesso.id")),
        sa.Column("canal", sa.String(5), nullable=False),
        sa.Column("modulo", sa.String(20), nullable=False),
        sa.Column("endpoint", sa.String(200)),
        sa.Column("metodo", sa.String(10)),
        sa.Column("parametros_json", JSONB),
        sa.Column("resposta_resumo_json", JSONB),
        sa.Column("status_http", sa.Integer),
        sa.Column("tempo_resposta_ms", sa.Integer),
        sa.Column("ip_origem", INET),
        sa.Column("criado_em", sa.DateTime, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_auditoria_usuario_criado", "auditoria_requisicoes", ["usuario_id", "criado_em"])
    op.create_index("ix_auditoria_modulo_criado", "auditoria_requisicoes", ["modulo", "criado_em"])
    op.create_index("ix_auditoria_criado", "auditoria_requisicoes", ["criado_em"])

    op.create_table(
        "consumo_diario",
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("data_referencia", sa.Date, primary_key=True),
        sa.Column("modulo", sa.String(20), primary_key=True),
        sa.Column("total_consultas", sa.Integer, server_default="0"),
    )

    # ── Plano padrão (dados de bootstrap) ────────────────────────────────────
    op.execute("""
        INSERT INTO planos (nome, descricao, limite_diario, limite_mensal, valor_mensal_centavos)
        VALUES
            ('Gratuito', 'Plano gratuito para avaliação', 20, 100, 0),
            ('Básico', 'Até 200 consultas/dia e 4.000/mês', 200, 4000, 9900),
            ('Profissional', 'Até 1.000 consultas/dia e 20.000/mês', 1000, 20000, 29900),
            ('Empresarial', 'Consultas ilimitadas', 99999, 9999999, 99900)
    """)


def downgrade() -> None:
    op.drop_table("consumo_diario")
    op.drop_table("auditoria_requisicoes")
    op.drop_table("chaves_acesso")
    op.drop_table("refresh_tokens")
    op.drop_table("usuarios")
    op.drop_table("empresas")
    op.drop_table("planos")
    op.drop_table("sigtap_procedimento_cid")
    op.drop_table("sigtap_procedimentos")
    op.drop_table("sigtap_grupos")
    op.drop_table("cid10_subcategorias")
    op.drop_table("cid10_categorias")
    op.drop_table("dcb")
    op.drop_table("medicamentos_cmed")
    op.drop_table("medicamentos_anvisa")
