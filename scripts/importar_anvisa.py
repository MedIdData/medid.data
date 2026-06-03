"""
Importação das bases ANVISA:
  - anvisa_medicamentos.csv  (encoding: latin-1, atenção: espaço no final do nome)
  - anvisa_consulta_medicamentos.csv (encoding: latin-1)

Os dois arquivos têm os mesmos 43.140 registros em formatos diferentes.
São cruzados por número de registro via LEFT JOIN (seguro: sem risco de explosão cartesiana).
"""
import os
import time
import argparse
import logging

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("importar_anvisa")


def parse_anvisa(dados_dir: str) -> pd.DataFrame:
    # Arquivo 1: nome com espaço no final
    arq1 = os.path.join(dados_dir, "anvisa_medicamentos.csv ")
    if not os.path.exists(arq1):
        arq1 = os.path.join(dados_dir, "anvisa_medicamentos.csv")

    log.info(f"Lendo {arq1}...")
    df1 = pd.read_csv(arq1, sep=";", encoding="latin-1", dtype=str, keep_default_na=False)
    df1 = df1.replace("", pd.NA)
    df1["_key"] = df1["NUMERO_REGISTRO_PRODUTO"].str.strip()
    log.info(f"  {len(df1):,} registros")

    arq2 = os.path.join(dados_dir, "anvisa_consulta_medicamentos.csv")
    log.info(f"Lendo {arq2}...")
    df2 = pd.read_csv(arq2, sep=";", encoding="latin-1", dtype=str, keep_default_na=False)
    df2 = df2.replace("", pd.NA)
    df2["_key"] = df2["NU_REGISTRO_PRODUTO"].str.strip()
    log.info(f"  {len(df2):,} registros")

    # Seleciona apenas as colunas úteis de df2 para evitar merge pesado
    cols_uteis = ["_key", "NO_PRODUTO", "INDICACOES", "CO_ATC",
                  "CO_TARJA", "CO_FORMA_FISICA", "TP_SITUACAO_APRESENTACAO",
                  "SUBSTANCIAS_MEDICAMENTOS", "SINONIMOS"]
    df2_slim = df2[[c for c in cols_uteis if c in df2.columns]].drop_duplicates(subset=["_key"])

    # LEFT JOIN: garante exatamente len(df1) linhas, sem explosão cartesiana
    merged = pd.merge(df1, df2_slim, on="_key", how="left", suffixes=("", "_c"))
    log.info(f"Merge concluído: {len(merged):,} registros")
    return merged


def get(row, *keys):
    """Retorna o primeiro valor não-nulo entre as colunas fornecidas."""
    for k in keys:
        v = row.get(k)
        if pd.notna(v) and str(v).strip() not in ("", "-", "NULL"):
            return str(v).strip()
    return None


def construir_dataframe_saida(merged: pd.DataFrame) -> pd.DataFrame:
    """Constrói o DataFrame de saída de forma vetorizada (sem iterrows)."""

    def coalesce(*cols):
        result = pd.Series([pd.NA] * len(merged), dtype="object")
        for c in cols:
            if c in merged.columns:
                result = result.combine_first(merged[c].where(merged[c].notna()))
        return result.where(result.notna(), None)

    out = pd.DataFrame({
        "numero_registro": coalesce("NUMERO_REGISTRO_PRODUTO", "_key"),
        "tipo_produto": coalesce("TIPO_PRODUTO"),
        "nome_produto": coalesce("NOME_PRODUTO", "NO_PRODUTO"),
        "data_finalizacao_processo": coalesce("DATA_FINALIZACAO_PROCESSO"),
        "categoria_regulatoria": coalesce("CATEGORIA_REGULATORIA"),
        "data_vencimento_registro": coalesce("DATA_VENCIMENTO_REGISTRO"),
        "numero_processo": coalesce("NUMERO_PROCESSO"),
        "classe_terapeutica": coalesce("CLASSE_TERAPEUTICA"),
        "empresa_detentora": coalesce("EMPRESA_DETENTORA_REGISTRO"),
        "situacao_registro": coalesce("SITUACAO_REGISTRO"),
        "principio_ativo": coalesce("PRINCIPIO_ATIVO", "SUBSTANCIAS_MEDICAMENTOS"),
        "indicacoes": coalesce("INDICACOES"),
        "sinonimos": coalesce("SINONIMOS"),
        "codigo_atc": coalesce("CO_ATC"),
        "tarja": coalesce("CO_TARJA"),
        "forma_fisica": coalesce("CO_FORMA_FISICA"),
        "situacao_apresentacao": coalesce("TP_SITUACAO_APRESENTACAO"),
        "substancias": coalesce("SUBSTANCIAS_MEDICAMENTOS"),
    })

    # Remove linhas sem chave de registro válida
    out = out[out["numero_registro"].notna()].copy()
    log.info(f"Registros com chave válida: {len(out):,}")
    return out


def inserir(df: pd.DataFrame, conn) -> int:
    sql = """
        INSERT INTO medicamentos_anvisa (
            numero_registro, tipo_produto, nome_produto, data_finalizacao_processo,
            categoria_regulatoria, data_vencimento_registro, numero_processo,
            classe_terapeutica, empresa_detentora, situacao_registro, principio_ativo,
            indicacoes, sinonimos, codigo_atc, tarja, forma_fisica,
            situacao_apresentacao, substancias
        ) VALUES %s
        ON CONFLICT (numero_registro) DO UPDATE SET
            nome_produto = EXCLUDED.nome_produto,
            situacao_registro = EXCLUDED.situacao_registro,
            principio_ativo = EXCLUDED.principio_ativo,
            indicacoes = EXCLUDED.indicacoes,
            sinonimos = EXCLUDED.sinonimos,
            codigo_atc = EXCLUDED.codigo_atc,
            tarja = EXCLUDED.tarja,
            substancias = EXCLUDED.substancias,
            importado_em = NOW()
    """
    cols = [
        "numero_registro", "tipo_produto", "nome_produto", "data_finalizacao_processo",
        "categoria_regulatoria", "data_vencimento_registro", "numero_processo",
        "classe_terapeutica", "empresa_detentora", "situacao_registro", "principio_ativo",
        "indicacoes", "sinonimos", "codigo_atc", "tarja", "forma_fisica",
        "situacao_apresentacao", "substancias",
    ]

    LOTE = 2000
    total = 0
    cursor = conn.cursor()
    records = df[cols].where(df[cols].notna(), None).to_dict("records")

    for i in range(0, len(records), LOTE):
        lote = records[i:i + LOTE]
        vals = [tuple(r[c] for c in cols) for r in lote]
        execute_values(cursor, sql, vals)
        conn.commit()
        total += len(lote)
        log.info(f"  Inserido/atualizado: {total:,}/{len(records):,}")

    cursor.close()
    return total


def atualizar_search_vector(conn):
    log.info("Atualizando search_vector...")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE medicamentos_anvisa
        SET search_vector =
            setweight(to_tsvector('portuguese', coalesce(nome_produto, '')), 'A') ||
            setweight(to_tsvector('portuguese', coalesce(principio_ativo, '')), 'B') ||
            setweight(to_tsvector('portuguese', coalesce(classe_terapeutica, '')), 'C') ||
            setweight(to_tsvector('portuguese', coalesce(indicacoes, '')), 'D')
    """)
    conn.commit()
    cursor.close()
    log.info("  search_vector atualizado")


def relatorio(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE situacao_registro ILIKE '%tivo%') AS ativos,
            COUNT(*) FILTER (WHERE situacao_registro ILIKE '%nativo%') AS inativos,
            COUNT(*) FILTER (WHERE principio_ativo IS NOT NULL) AS com_principio,
            COUNT(*) FILTER (WHERE indicacoes IS NOT NULL) AS com_indicacoes,
            COUNT(*) FILTER (WHERE codigo_atc IS NOT NULL) AS com_atc
        FROM medicamentos_anvisa
    """)
    row = cursor.fetchone()
    cursor.close()
    print()
    print("=" * 50)
    print("RELATÓRIO — medicamentos_anvisa")
    print("=" * 50)
    print(f"  Total inserido:       {row[0]:>8,}")
    print(f"  Situação Ativo:       {row[1]:>8,}")
    print(f"  Situação Inativo:     {row[2]:>8,}")
    print(f"  Com princípio ativo:  {row[3]:>8,}")
    print(f"  Com indicações:       {row[4]:>8,}")
    print(f"  Com código ATC:       {row[5]:>8,}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Importa base ANVISA")
    parser.add_argument("--dados-dir", default=os.getenv("DADOS_DIR", "./dados"))
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL", "postgresql://mediddata:mediddata@localhost:5432/mediddata"))
    args = parser.parse_args()

    inicio = time.time()
    log.info("=== IMPORTAÇÃO ANVISA ===")

    merged = parse_anvisa(args.dados_dir)
    df_saida = construir_dataframe_saida(merged)

    conn = psycopg2.connect(args.db_url)
    try:
        inserir(df_saida, conn)
        atualizar_search_vector(conn)
        relatorio(conn)
    finally:
        conn.close()

    log.info(f"Concluído em {time.time() - inicio:.1f}s")


if __name__ == "__main__":
    main()
