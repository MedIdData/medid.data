"""
Importação das tabelas CMED:
  - cmed_pmc.xlsx  (Preço Fábrica + Preço Máximo ao Consumidor) — header linha 42
  - cmed_pmvg.xlsx (Preço Fábrica + Preço Máximo de Venda ao Governo) — header linha 53

Estratégia:
  1. Importa PMC: insere todos os registros com colunas PF e PMC.
  2. Importa PMVG: atualiza os registros existentes com colunas PMVG.
     Registros novos no PMVG (improvável) são inseridos.
"""
import os
import sys
import time
import argparse
import logging
from pathlib import Path

import openpyxl
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("importar_cmed")


def parse_preco(val) -> float | None:
    if val is None:
        return None
    s = str(val).strip().replace("\xa0", "").replace(" ", "")
    if not s or s in ("-", "    -     ", "—"):
        return None
    # Formato brasileiro: 1.234,56 → 1234.56
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_bool_flag(val) -> bool | None:
    if val is None:
        return None
    s = str(val).strip().upper()
    if s in ("SIM", "S", "X", "TRUE", "1"):
        return True
    if s in ("NÃO", "NAO", "N", "", "FALSE", "0"):
        return False
    return None


def limpar(val) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s and s not in ("-", "    -     ") else None


def ler_xlsx(filepath: str, header_row: int) -> list[dict]:
    """Lê o xlsx retornando lista de dicts com as colunas relevantes."""
    log.info(f"Lendo {filepath}...")
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active

    cabecalho = []
    registros = []
    lidos = 0

    for i, row in enumerate(ws.iter_rows(min_row=header_row, values_only=True), start=header_row):
        if i == header_row:
            cabecalho = [str(c).strip() if c else f"col_{j}" for j, c in enumerate(row)]
            continue
        if row[0] is None:
            continue
        registros.append(dict(zip(cabecalho, row)))
        lidos += 1
        if lidos % 5000 == 0:
            log.info(f"  {lidos:,} linhas lidas...")

    wb.close()
    log.info(f"  Total: {lidos:,} registros")
    return registros


def construir_registro_pmc(r: dict) -> dict:
    return {
        "codigo_ggrem": limpar(r.get("CÓDIGO GGREM")),
        "substancia": limpar(r.get("SUBSTÂNCIA")),
        "cnpj": limpar(r.get("CNPJ")),
        "laboratorio": limpar(r.get("LABORATÓRIO")),
        "registro": limpar(r.get("REGISTRO")),
        "ean1": limpar(r.get("EAN 1")),
        "ean2": limpar(r.get("EAN 2")),
        "ean3": limpar(r.get("EAN 3")),
        "produto": limpar(r.get("PRODUTO")),
        "apresentacao": limpar(r.get("APRESENTAÇÃO")),
        "classe_terapeutica": limpar(r.get("CLASSE TERAPÊUTICA")),
        "tipo_produto": limpar(r.get("TIPO DE PRODUTO (STATUS DO PRODUTO)")),
        "regime_preco": limpar(r.get("REGIME DE PREÇO")),
        "pf_sem_impostos": parse_preco(r.get("PF Sem Impostos")),
        "pf_0": parse_preco(r.get("PF 0%")),
        "pf_12": parse_preco(r.get("PF 12 %")),
        "pf_17": parse_preco(r.get("PF 17 %")),
        "pf_17_5": parse_preco(r.get("PF 17,5 %")),
        "pf_18": parse_preco(r.get("PF 18 %")),
        "pf_20": parse_preco(r.get("PF 20 %")),
        "pmc_sem_impostos": parse_preco(r.get("PMC Sem Impostos")),
        "pmc_0": parse_preco(r.get("PMC 0 %")),
        "pmc_12": parse_preco(r.get("PMC 12 %")),
        "pmc_17": parse_preco(r.get("PMC 17 %")),
        "pmc_17_5": parse_preco(r.get("PMC 17,5 %")),
        "pmc_18": parse_preco(r.get("PMC 18 %")),
        "pmc_20": parse_preco(r.get("PMC 20 %")),
        "restricao_hospitalar": parse_bool_flag(r.get("RESTRIÇÃO HOSPITALAR")),
        "cap": parse_bool_flag(r.get("CAP")),
        "confaz_87": parse_bool_flag(r.get("CONFAZ 87")),
        "icms_0": parse_bool_flag(r.get("ICMS 0%")),
        "analise_recursal": limpar(r.get("ANÁLISE RECURSAL")),
        "comercializacao_2024": limpar(r.get("COMERCIALIZAÇÃO 2024")),
        "tarja": limpar(r.get("TARJA")),
        "destinacao_comercial": limpar(r.get("DESTINAÇÃO COMERCIAL ")) or limpar(r.get("DESTINAÇÃO COMERCIAL 9")),
    }


def construir_registro_pmvg(r: dict) -> dict:
    return {
        "codigo_ggrem": limpar(r.get("CÓDIGO GGREM")),
        "pmvg_sem_impostos": parse_preco(r.get("PMVG Sem Impostos")),
        "pmvg_0": parse_preco(r.get("PMVG 0 %")),
        "pmvg_12": parse_preco(r.get("PMVG 12 %")),
        "pmvg_17": parse_preco(r.get("PMVG 17 %")),
        "pmvg_17_5": parse_preco(r.get("PMVG 17,5 %")),
        "pmvg_18": parse_preco(r.get("PMVG 18 %")),
        "pmvg_20": parse_preco(r.get("PMVG 20 %")),
    }


def inserir_pmc(registros: list[dict], conn) -> int:
    sql = """
        INSERT INTO medicamentos_cmed (
            codigo_ggrem, substancia, cnpj, laboratorio, registro,
            ean1, ean2, ean3, produto, apresentacao, classe_terapeutica,
            tipo_produto, regime_preco,
            pf_sem_impostos, pf_0, pf_12, pf_17, pf_17_5, pf_18, pf_20,
            pmc_sem_impostos, pmc_0, pmc_12, pmc_17, pmc_17_5, pmc_18, pmc_20,
            restricao_hospitalar, cap, confaz_87, icms_0, analise_recursal,
            comercializacao_2024, tarja, destinacao_comercial
        ) VALUES %s
        ON CONFLICT (codigo_ggrem) DO UPDATE SET
            substancia = EXCLUDED.substancia,
            laboratorio = EXCLUDED.laboratorio,
            produto = EXCLUDED.produto,
            apresentacao = EXCLUDED.apresentacao,
            pf_sem_impostos = EXCLUDED.pf_sem_impostos,
            pf_0 = EXCLUDED.pf_0,
            pmc_sem_impostos = EXCLUDED.pmc_sem_impostos,
            pmc_0 = EXCLUDED.pmc_0,
            tarja = EXCLUDED.tarja,
            importado_em = NOW()
    """
    validos = [r for r in registros if r.get("codigo_ggrem")]
    LOTE = 2000
    total = 0
    cursor = conn.cursor()
    for i in range(0, len(validos), LOTE):
        lote = validos[i:i + LOTE]
        vals = [(
            r["codigo_ggrem"], r["substancia"], r["cnpj"], r["laboratorio"], r["registro"],
            r["ean1"], r["ean2"], r["ean3"], r["produto"], r["apresentacao"], r["classe_terapeutica"],
            r["tipo_produto"], r["regime_preco"],
            r["pf_sem_impostos"], r["pf_0"], r["pf_12"], r["pf_17"], r["pf_17_5"], r["pf_18"], r["pf_20"],
            r["pmc_sem_impostos"], r["pmc_0"], r["pmc_12"], r["pmc_17"], r["pmc_17_5"], r["pmc_18"], r["pmc_20"],
            r["restricao_hospitalar"], r["cap"], r["confaz_87"], r["icms_0"], r["analise_recursal"],
            r["comercializacao_2024"], r["tarja"], r["destinacao_comercial"],
        ) for r in lote]
        execute_values(cursor, sql, vals)
        conn.commit()
        total += len(lote)
        log.info(f"  PMC inserido/atualizado: {total:,}/{len(validos):,}")
    cursor.close()
    return total


def atualizar_pmvg(registros: list[dict], conn) -> int:
    sql = """
        UPDATE medicamentos_cmed SET
            pmvg_sem_impostos = %(pmvg_sem_impostos)s,
            pmvg_0 = %(pmvg_0)s,
            pmvg_12 = %(pmvg_12)s,
            pmvg_17 = %(pmvg_17)s,
            pmvg_17_5 = %(pmvg_17_5)s,
            pmvg_18 = %(pmvg_18)s,
            pmvg_20 = %(pmvg_20)s
        WHERE codigo_ggrem = %(codigo_ggrem)s
    """
    validos = [r for r in registros if r.get("codigo_ggrem")]
    LOTE = 2000
    total = 0
    cursor = conn.cursor()
    for i in range(0, len(validos), LOTE):
        lote = validos[i:i + LOTE]
        cursor.executemany(sql, lote)
        conn.commit()
        total += cursor.rowcount if cursor.rowcount >= 0 else len(lote)
        log.info(f"  PMVG atualizado: {total:,}/{len(validos):,}")
    cursor.close()
    return total


def relatorio(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE pmc_0 IS NOT NULL) AS com_pmc,
            COUNT(*) FILTER (WHERE pmvg_0 IS NOT NULL) AS com_pmvg,
            COUNT(*) FILTER (WHERE pf_sem_impostos IS NOT NULL) AS com_pf,
            COUNT(*) FILTER (WHERE restricao_hospitalar = TRUE) AS hospitalar,
            COUNT(DISTINCT substancia) AS substancias_unicas
        FROM medicamentos_cmed
    """)
    row = cursor.fetchone()
    cursor.close()
    print()
    print("=" * 50)
    print("RELATÓRIO — medicamentos_cmed")
    print("=" * 50)
    print(f"  Total inserido:        {row[0]:>8,}")
    print(f"  Com PMC 0%:            {row[1]:>8,}")
    print(f"  Com PMVG 0%:           {row[2]:>8,}")
    print(f"  Com PF s/ impostos:    {row[3]:>8,}")
    print(f"  Restrição hospitalar:  {row[4]:>8,}")
    print(f"  Substâncias únicas:    {row[5]:>8,}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Importa tabelas CMED (PMC e PMVG)")
    parser.add_argument("--dados-dir", default=os.getenv("DADOS_DIR", "./dados"))
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL", "postgresql://mediddata:mediddata@localhost:5432/mediddata"))
    args = parser.parse_args()

    inicio = time.time()
    log.info("=== IMPORTAÇÃO CMED ===")

    # PMC — header na linha 42 (0-indexed: 41, mas openpyxl é 1-indexed)
    recs_pmc = ler_xlsx(os.path.join(args.dados_dir, "cmed_pmc.xlsx"), header_row=42)
    pmc_dicts = [construir_registro_pmc(r) for r in recs_pmc]

    # PMVG — header na linha 53
    recs_pmvg = ler_xlsx(os.path.join(args.dados_dir, "cmed_pmvg.xlsx"), header_row=53)
    pmvg_dicts = [construir_registro_pmvg(r) for r in recs_pmvg]

    conn = psycopg2.connect(args.db_url)
    try:
        log.info("Inserindo PMC...")
        inserir_pmc(pmc_dicts, conn)
        log.info("Atualizando PMVG...")
        atualizar_pmvg(pmvg_dicts, conn)
        relatorio(conn)
    finally:
        conn.close()

    log.info(f"Concluído em {time.time() - inicio:.1f}s")


if __name__ == "__main__":
    main()
