"""
Queries do banco necessárias para o motor de análise de risco.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional


def buscar_medicamento_para_analise(db: Session, nome: str) -> Optional[dict]:
    """Encontra o medicamento mais relevante pelo nome."""
    sql = text("""
        SELECT
            a.id, a.numero_registro, a.nome_produto, a.principio_ativo,
            a.classe_terapeutica, a.situacao_registro, a.categoria_regulatoria,
            a.tarja, a.indicacoes,
            c.pf_sem_impostos AS pf,
            c.pmc_0 AS pmc,
            c.pmvg_0 AS pmvg,
            c.apresentacao,
            GREATEST(
                word_similarity(unaccent(lower(:q)), unaccent(lower(coalesce(a.nome_produto, '')))),
                word_similarity(unaccent(lower(:q)), unaccent(lower(coalesce(a.principio_ativo, ''))))
            ) AS score
        FROM medicamentos_anvisa a
        LEFT JOIN LATERAL (
            SELECT pf_sem_impostos, pmc_0, pmvg_0, apresentacao
            FROM medicamentos_cmed mc
            WHERE
                upper(trim(mc.substancia)) = upper(trim(split_part(coalesce(a.principio_ativo, ''), ',', 1)))
                OR mc.substancia ILIKE '%' || trim(split_part(coalesce(a.principio_ativo, ''), ',', 1)) || '%'
            ORDER BY mc.pmc_0 ASC NULLS LAST
            LIMIT 1
        ) c ON TRUE
        WHERE
            upper(a.situacao_registro) = 'ATIVO'
            AND (
                a.search_vector @@ websearch_to_tsquery('portuguese', :q)
                OR word_similarity(unaccent(lower(:q)), unaccent(lower(coalesce(a.nome_produto, '')))) > 0.25
                OR word_similarity(unaccent(lower(:q)), unaccent(lower(coalesce(a.principio_ativo, '')))) > 0.25
            )
        ORDER BY score DESC
        LIMIT 1
    """)
    row = db.execute(sql, {"q": nome.strip()}).mappings().fetchone()
    return dict(row) if row else None


def buscar_cid(db: Session, codigo: str) -> Optional[dict]:
    """Busca um CID-10 por código, normalizando formatos como 'J18.9' → 'J189'."""
    codigo_norm = codigo.upper().replace(".", "").replace("-", "").strip()
    # Tenta subcategoria exata ou com variações de formato
    sql = text("""
        SELECT s.id, s.codigo, s.descricao, c.codigo AS codigo_categoria, c.descricao AS descricao_categoria
        FROM cid10_subcategorias s
        JOIN cid10_categorias c ON s.categoria_id = c.id
        WHERE replace(replace(upper(s.codigo), '.', ''), '-', '') = :codigo
        LIMIT 1
    """)
    row = db.execute(sql, {"codigo": codigo_norm}).mappings().fetchone()
    if not row and len(codigo_norm) >= 3:
        # Tenta pela categoria se código completo não foi encontrado
        sql_cat = text("""
            SELECT id, codigo, descricao, codigo AS codigo_categoria, descricao AS descricao_categoria
            FROM cid10_categorias
            WHERE upper(codigo) = :codigo
            LIMIT 1
        """)
        row = db.execute(sql_cat, {"codigo": codigo_norm[:3]}).mappings().fetchone()
    return dict(row) if row else None


def buscar_procedimento(db: Session, codigo: str) -> Optional[dict]:
    """Busca um procedimento SIGTAP por código, normalizando formatos."""
    # Remove pontos, espaços e hífens: "03.01.01.007-2" → "0301010072"
    codigo_norm = "".join(c for c in codigo if c.isdigit())[:10].ljust(10, "0")
    sql = text("""
        SELECT p.id, p.codigo, p.descricao, p.complexidade, p.vl_sh, p.vl_sa, p.vl_sp,
               g.codigo AS grupo_codigo, g.descricao AS grupo_descricao
        FROM sigtap_procedimentos p
        LEFT JOIN sigtap_grupos g ON p.grupo_id = g.id
        WHERE p.codigo = :codigo
        LIMIT 1
    """)
    row = db.execute(sql, {"codigo": codigo_norm}).mappings().fetchone()
    return dict(row) if row else None


def verificar_cid_procedimento(db: Session, codigo_proc: str, codigo_cid: str) -> bool:
    """Verifica se o CID está na lista de CIDs compatíveis com o procedimento."""
    codigo_cid_norm = codigo_cid.upper().replace(".", "").replace("-", "").strip()
    sql = text("""
        SELECT 1 FROM sigtap_procedimento_cid
        WHERE codigo_procedimento = :proc
          AND replace(replace(upper(codigo_cid), ' ', ''), '.', '') LIKE :cid || '%'
        LIMIT 1
    """)
    result = db.execute(sql, {"proc": codigo_proc, "cid": codigo_cid_norm[:3]}).fetchone()
    return result is not None


def contar_cids_procedimento(db: Session, codigo_proc: str) -> int:
    """Conta quantos CIDs estão associados ao procedimento (para avaliar especificidade)."""
    sql = text("""
        SELECT COUNT(*) FROM sigtap_procedimento_cid WHERE codigo_procedimento = :proc
    """)
    return db.execute(sql, {"proc": codigo_proc}).scalar_one()
