"""
Repositório de medicamentos: consultas ao banco via pg_trgm + tsvector.

Estratégia de busca:
  1. Full-text (tsvector) com dicionário portuguese para palavras conhecidas.
  2. Trigram word_similarity para correção ortográfica e busca parcial.
  3. LATERAL join com medicamentos_cmed para obter preços por princípio ativo.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional


LIMIAR_SIMILARIDADE = 0.25


def _params(q: str, apenas_ativos: bool, limite: int, offset: int) -> dict:
    return {
        "q": q,
        "apenas_ativos": apenas_ativos,
        "limiar": LIMIAR_SIMILARIDADE,
        "limite": limite,
        "offset": offset,
    }


_SQL_WHERE = """
    (:apenas_ativos = FALSE OR upper(a.situacao_registro) = 'ATIVO')
    AND (
        a.search_vector @@ websearch_to_tsquery('portuguese', :q)
        OR word_similarity(unaccent(lower(:q)), unaccent(lower(coalesce(a.nome_produto, '')))) > :limiar
        OR word_similarity(unaccent(lower(:q)), unaccent(lower(coalesce(a.principio_ativo, '')))) > :limiar
    )
"""

_SQL_BUSCA = text(f"""
    SELECT
        a.id,
        a.numero_registro,
        a.nome_produto,
        a.principio_ativo,
        a.empresa_detentora,
        a.situacao_registro,
        a.categoria_regulatoria,
        a.classe_terapeutica,
        a.tarja,
        a.forma_fisica,
        a.indicacoes,
        a.sinonimos,
        a.codigo_atc,
        GREATEST(
            word_similarity(unaccent(lower(:q)), unaccent(lower(coalesce(a.nome_produto, '')))),
            word_similarity(unaccent(lower(:q)), unaccent(lower(coalesce(a.principio_ativo, ''))))
        ) AS score,
        c.pf_sem_impostos AS pf,
        c.pmc_0 AS pmc,
        c.pmvg_0 AS pmvg,
        c.tarja AS cmed_tarja,
        c.apresentacao,
        c.laboratorio
    FROM medicamentos_anvisa a
    LEFT JOIN LATERAL (
        SELECT
            mc.pf_sem_impostos,
            mc.pmc_0,
            mc.pmvg_0,
            mc.tarja,
            mc.apresentacao,
            mc.laboratorio
        FROM medicamentos_cmed mc
        WHERE
            upper(trim(mc.substancia)) = upper(trim(split_part(coalesce(a.principio_ativo, ''), ',', 1)))
            OR mc.substancia ILIKE '%' || trim(split_part(coalesce(a.principio_ativo, ''), ',', 1)) || '%'
        ORDER BY mc.pmc_0 ASC NULLS LAST
        LIMIT 1
    ) c ON TRUE
    WHERE {_SQL_WHERE}
    ORDER BY score DESC, a.nome_produto ASC
    LIMIT :limite OFFSET :offset
""")

_SQL_TOTAL = text(f"""
    SELECT COUNT(*)
    FROM medicamentos_anvisa a
    WHERE {_SQL_WHERE}
""")

_SQL_SUGESTAO = text("""
    SELECT nome_produto
    FROM medicamentos_anvisa
    WHERE upper(situacao_registro) = 'ATIVO'
    ORDER BY word_similarity(unaccent(lower(:q)), unaccent(lower(coalesce(nome_produto, '')))) DESC
    LIMIT 1
""")

_SQL_DETALHE = text("""
    SELECT
        a.id, a.numero_registro, a.nome_produto, a.principio_ativo,
        a.empresa_detentora, a.situacao_registro, a.categoria_regulatoria,
        a.classe_terapeutica, a.tarja, a.forma_fisica,
        a.sinonimos, a.substancias, a.codigo_atc, a.indicacoes,
        c.pf_sem_impostos  AS pf,
        c.pmc_0            AS pmc,
        c.pmvg_0           AS pmvg,
        c.pf_12, c.pmc_12, c.pmvg_12,
        c.pf_17, c.pmc_17, c.pmvg_17,
        c.pf_18, c.pmc_18, c.pmvg_18,
        c.apresentacao, c.laboratorio
    FROM medicamentos_anvisa a
    LEFT JOIN LATERAL (
        SELECT
            mc.pf_sem_impostos, mc.pmc_0, mc.pmvg_0,
            mc.pf_12, mc.pmc_12, mc.pmvg_12,
            mc.pf_17, mc.pmc_17, mc.pmvg_17,
            mc.pf_18, mc.pmc_18, mc.pmvg_18,
            mc.apresentacao, mc.laboratorio
        FROM medicamentos_cmed mc
        WHERE
            upper(trim(mc.substancia)) = upper(trim(split_part(coalesce(a.principio_ativo, ''), ',', 1)))
            OR mc.substancia ILIKE '%' || trim(split_part(coalesce(a.principio_ativo, ''), ',', 1)) || '%'
        ORDER BY mc.pmc_0 ASC NULLS LAST
        LIMIT 1
    ) c ON TRUE
    WHERE a.id = :id
""")


def buscar_medicamentos(
    db: Session,
    q: str,
    apenas_ativos: bool = True,
    pagina: int = 1,
    limite: int = 20,
) -> tuple[list[dict], int, str | None]:
    """
    Retorna (resultados, total, sugestao_ortografica).
    sugestao é None quando há resultados, ou o nome mais próximo quando zero.
    """
    q = q.strip()

    # Se query vazia, listar primeiros medicamentos (ordem alfabética)
    if len(q) < 2:
        limite = min(limite, 100)
        offset = (pagina - 1) * limite

        sql_listar = text("""
            SELECT
                a.id,
                a.nome_produto as medicamento,
                a.principio_ativo,
                a.numero_registro,
                a.classe_terapeutica,
                a.apresentacao,
                a.empresa_detentora as empresa,
                a.tarja,
                a.situacao_registro,
                a.venda_generico,
                c.pf,
                c.pmc,
                c.pmvg
            FROM medicamentos_anvisa a
            LEFT JOIN medicamentos_cmed c ON a.numero_registro = c.numero_registro
            WHERE (:apenas_ativos = FALSE OR upper(a.situacao_registro) = 'ATIVO')
            ORDER BY a.nome_produto ASC
            LIMIT :limite OFFSET :offset
        """)

        sql_total = text("""
            SELECT COUNT(*)
            FROM medicamentos_anvisa a
            WHERE (:apenas_ativos = FALSE OR upper(a.situacao_registro) = 'ATIVO')
        """)

        params_listar = {"apenas_ativos": apenas_ativos, "limite": limite, "offset": offset}
        total = db.execute(sql_total, {"apenas_ativos": apenas_ativos}).scalar_one()
        rows = db.execute(sql_listar, params_listar).mappings().fetchall()

        return [dict(r) for r in rows], total, None

    # Query com termo >= 2 caracteres: busca com fuzzy matching
    limite = min(limite, 100)
    offset = (pagina - 1) * limite
    params = _params(q, apenas_ativos, limite, offset)

    total: int = db.execute(_SQL_TOTAL, params).scalar_one()

    if total == 0:
        row = db.execute(_SQL_SUGESTAO, {"q": q}).fetchone()
        sugestao = row[0] if row else None
        return [], 0, sugestao

    rows = db.execute(_SQL_BUSCA, params).mappings().fetchall()
    return [dict(r) for r in rows], total, None


def obter_por_id(db: Session, medicamento_id: int) -> dict | None:
    row = db.execute(_SQL_DETALHE, {"id": medicamento_id}).mappings().fetchone()
    return dict(row) if row else None


def listar_fabricantes(db: Session, q: str = "") -> list[str]:
    """Lista fabricantes distintos para alimentar o filtro de busca."""
    if q:
        sql = text("""
            SELECT DISTINCT empresa_detentora
            FROM medicamentos_anvisa
            WHERE upper(situacao_registro) = 'ATIVO'
              AND empresa_detentora ILIKE :q
            ORDER BY empresa_detentora
            LIMIT 50
        """)
        rows = db.execute(sql, {"q": f"%{q}%"}).fetchall()
    else:
        sql = text("""
            SELECT DISTINCT empresa_detentora
            FROM medicamentos_anvisa
            WHERE upper(situacao_registro) = 'ATIVO'
              AND empresa_detentora IS NOT NULL
            ORDER BY empresa_detentora
            LIMIT 200
        """)
        rows = db.execute(sql).fetchall()
    return [r[0] for r in rows if r[0]]
