"""
Importação CID-10:
  - CID-10-CATEGORIAS.CSV    (encoding Latin-1, separador ;)
  - CID-10-SUBCATEGORIAS.CSV (encoding Latin-1, separador ;)

As subcategorias são vinculadas às categorias pelos 3 primeiros caracteres do código.
"""
import os
import csv
import time
import argparse
import logging

import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("importar_cid10")


def limpar(val) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def parse_bool(val) -> bool | None:
    s = limpar(val)
    if not s:
        return None
    return s.upper() in ("1", "S", "SIM", "X")


def parse_categorias(filepath: str) -> list[dict]:
    log.info(f"Lendo {filepath}...")
    registros = []
    with open(filepath, encoding="latin-1") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            codigo = limpar(row.get("CAT"))
            if not codigo:
                continue
            registros.append({
                "codigo": codigo,
                "classif": limpar(row.get("CLASSIF")),
                "descricao": limpar(row.get("DESCRICAO")),
                "descricao_abrev": limpar(row.get("DESCRABREV")),
                "refer": limpar(row.get("REFER")),
                "excluidos": limpar(row.get("EXCLUIDOS")),
            })
    log.info(f"  {len(registros):,} categorias lidas")
    return registros


def parse_subcategorias(filepath: str, mapa_categorias: dict[str, int]) -> list[dict]:
    log.info(f"Lendo {filepath}...")
    registros = []
    sem_categoria = 0
    with open(filepath, encoding="latin-1") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            codigo = limpar(row.get("SUBCAT"))
            if not codigo:
                continue
            # Categoria = primeiros 3 chars do código da subcategoria (ex: A000 → A00)
            codigo_cat = codigo[:3]
            categoria_id = mapa_categorias.get(codigo_cat)
            if categoria_id is None:
                sem_categoria += 1

            registros.append({
                "codigo": codigo,
                "categoria_id": categoria_id,
                "classif": limpar(row.get("CLASSIF")),
                "restricao_sexo": limpar(row.get("RESTRSEXO")),
                "causa_obito": parse_bool(row.get("CAUSAOBITO")),
                "descricao": limpar(row.get("DESCRICAO")),
                "descricao_abrev": limpar(row.get("DESCRABREV")),
                "refer": limpar(row.get("REFER")),
                "excluidos": limpar(row.get("EXCLUIDOS")),
            })

    log.info(f"  {len(registros):,} subcategorias lidas | sem categoria: {sem_categoria:,}")
    return registros


def inserir_categorias(registros: list[dict], conn) -> dict[str, int]:
    sql = """
        INSERT INTO cid10_categorias (codigo, classif, descricao, descricao_abrev, refer, excluidos)
        VALUES %s
        ON CONFLICT (codigo) DO UPDATE SET
            descricao = EXCLUDED.descricao,
            descricao_abrev = EXCLUDED.descricao_abrev
    """
    cursor = conn.cursor()
    vals = [(r["codigo"], r["classif"], r["descricao"], r["descricao_abrev"], r["refer"], r["excluidos"])
            for r in registros]
    execute_values(cursor, sql, vals, page_size=len(vals))
    conn.commit()
    # Busca o mapa completo após o INSERT (não depende do RETURNING por lotes)
    cursor.execute("SELECT codigo, id FROM cid10_categorias")
    mapa = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    log.info(f"  Categorias inseridas/atualizadas: {len(mapa):,}")
    return mapa


def inserir_subcategorias(registros: list[dict], conn) -> int:
    sql = """
        INSERT INTO cid10_subcategorias
            (codigo, categoria_id, classif, restricao_sexo, causa_obito, descricao, descricao_abrev, refer, excluidos)
        VALUES %s
        ON CONFLICT (codigo) DO UPDATE SET
            descricao = EXCLUDED.descricao,
            descricao_abrev = EXCLUDED.descricao_abrev,
            categoria_id = EXCLUDED.categoria_id
    """
    LOTE = 2000
    total = 0
    cursor = conn.cursor()
    for i in range(0, len(registros), LOTE):
        lote = registros[i:i + LOTE]
        vals = [(
            r["codigo"], r["categoria_id"], r["classif"], r["restricao_sexo"],
            r["causa_obito"], r["descricao"], r["descricao_abrev"], r["refer"], r["excluidos"],
        ) for r in lote]
        execute_values(cursor, sql, vals)
        conn.commit()
        total += len(lote)
        log.info(f"  Subcategorias inseridas: {total:,}/{len(registros):,}")
    cursor.close()
    return total


def relatorio(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM cid10_categorias")
    total_cat = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE categoria_id IS NOT NULL) FROM cid10_subcategorias")
    total_sub, com_cat = cursor.fetchone()
    cursor.close()
    print()
    print("=" * 50)
    print("RELATÓRIO — CID-10")
    print("=" * 50)
    print(f"  Categorias:                  {total_cat:>6,}")
    print(f"  Subcategorias:               {total_sub:>6,}")
    print(f"  Subcategorias com categoria: {com_cat:>6,}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Importa CID-10 (categorias e subcategorias)")
    parser.add_argument("--dados-dir", default=os.getenv("DADOS_DIR", "./dados"))
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL", "postgresql://mediddata:mediddata@localhost:5432/mediddata"))
    args = parser.parse_args()

    inicio = time.time()
    log.info("=== IMPORTAÇÃO CID-10 ===")

    cats = parse_categorias(os.path.join(args.dados_dir, "CID-10-CATEGORIAS.CSV"))

    conn = psycopg2.connect(args.db_url)
    try:
        mapa_cats = inserir_categorias(cats, conn)
        subs = parse_subcategorias(os.path.join(args.dados_dir, "CID-10-SUBCATEGORIAS.CSV"), mapa_cats)
        inserir_subcategorias(subs, conn)
        relatorio(conn)
    finally:
        conn.close()

    log.info(f"Concluído em {time.time() - inicio:.1f}s")


if __name__ == "__main__":
    main()
