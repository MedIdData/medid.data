"""
Importação da lista DCB (Denominações Comuns Brasileiras):
  - dcb_lista.xlsx — sheet "Lista DCB Consolidada", header linha 2

Classificações importadas: IFA, INF, HOM, BIO, PM, RAD
EXA (Exames) é excluído por ser não-medicamento.
"""
import os
import time
import argparse
import logging
from collections import Counter

import openpyxl
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("importar_dcb")

CLASSIFICACOES_MEDICAMENTO = {"IFA", "INF", "HOM", "BIO", "PM", "RAD"}


def limpar(val) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def parse_dcb(filepath: str) -> list[dict]:
    log.info(f"Lendo {filepath}...")
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb["Lista DCB Consolidada"]

    registros = []
    total_lidos = 0
    ignorados = 0

    for i, row in enumerate(ws.iter_rows(min_row=3, values_only=True), start=3):
        if row[0] is None:
            continue
        try:
            numero = int(row[0])
        except (TypeError, ValueError):
            continue

        classificacao = limpar(row[3]) or ""
        total_lidos += 1

        # Inclui todos — a filtragem por classificação fica disponível via query
        registros.append({
            "numero_dcb": numero,
            "denominacao": limpar(row[1]),
            "numero_cas": limpar(row[2]),
            "classificacao": classificacao,
            "historico": limpar(row[4]),
        })

    wb.close()
    log.info(f"  Total lido: {total_lidos:,} | Preparados: {len(registros):,}")
    return registros


def inserir(registros: list[dict], conn) -> int:
    sql = """
        INSERT INTO dcb (numero_dcb, denominacao, numero_cas, classificacao, historico)
        VALUES %s
        ON CONFLICT (numero_dcb) DO UPDATE SET
            denominacao = EXCLUDED.denominacao,
            classificacao = EXCLUDED.classificacao,
            historico = EXCLUDED.historico,
            importado_em = NOW()
    """
    LOTE = 2000
    total = 0
    cursor = conn.cursor()
    for i in range(0, len(registros), LOTE):
        lote = registros[i:i + LOTE]
        vals = [(r["numero_dcb"], r["denominacao"], r["numero_cas"], r["classificacao"], r["historico"]) for r in lote]
        execute_values(cursor, sql, vals)
        conn.commit()
        total += len(lote)
        log.info(f"  Inserido/atualizado: {total:,}/{len(registros):,}")
    cursor.close()
    return total


def relatorio(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT classificacao, COUNT(*) FROM dcb
        GROUP BY classificacao ORDER BY COUNT(*) DESC
    """)
    rows = cursor.fetchall()
    total_cursor = conn.cursor()
    total_cursor.execute("SELECT COUNT(*) FROM dcb")
    total = total_cursor.fetchone()[0]
    cursor.close()
    total_cursor.close()
    print()
    print("=" * 50)
    print("RELATÓRIO — dcb")
    print("=" * 50)
    print(f"  Total inserido: {total:,}")
    print("  Por classificação:")
    for classif, count in rows:
        print(f"    {classif or '(sem)':8s}  {count:>6,}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Importa lista DCB")
    parser.add_argument("--dados-dir", default=os.getenv("DADOS_DIR", "./dados"))
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL", "postgresql://mediddata:mediddata@localhost:5432/mediddata"))
    args = parser.parse_args()

    inicio = time.time()
    log.info("=== IMPORTAÇÃO DCB ===")

    registros = parse_dcb(os.path.join(args.dados_dir, "dcb_lista.xlsx"))

    conn = psycopg2.connect(args.db_url)
    try:
        inserir(registros, conn)
        relatorio(conn)
    finally:
        conn.close()

    log.info(f"Concluído em {time.time() - inicio:.1f}s")


if __name__ == "__main__":
    main()
