"""
Importação SIGTAP (Tabela Unificada de Procedimentos SUS):
  - sigtap_grupos.txt          (fixed-width: código[2] + descrição[100] + competência[6])
  - sigtap_procedimentos.txt   (fixed-width 337 chars, layout em bkp/tb_procedimento_layout.txt)
  - sigtap_procedimento_cid.txt (fixed-width 21 chars: proc[10] + cid[4] + principal[1] + comp[6])

Os CIDs da relação procedimento×CID são resolvidos contra cid10_subcategorias já importadas.
"""
import os
import time
import argparse
import logging
from collections import defaultdict

import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("importar_sigtap")


def parse_int(s: str) -> int | None:
    s = s.strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def parse_decimal_sigtap(s: str) -> float | None:
    """Valores SIGTAP são inteiros representando centavos × 10 (sem separador decimal)."""
    s = s.strip()
    if not s:
        return None
    try:
        return round(int(s) / 100, 2)
    except ValueError:
        return None


# ── Grupos ────────────────────────────────────────────────────────────────────

def parse_grupos(filepath: str) -> list[dict]:
    log.info(f"Lendo {filepath}...")
    grupos = []
    with open(filepath, encoding="latin-1") as f:
        for line in f:
            line = line.rstrip("\n")
            if len(line) < 8:
                continue
            grupos.append({
                "codigo": line[0:2].strip(),
                "descricao": line[2:102].strip(),
                "competencia": line[102:108].strip() if len(line) >= 108 else None,
            })
    log.info(f"  {len(grupos)} grupos lidos")
    return grupos


def inserir_grupos(grupos: list[dict], conn) -> dict[str, int]:
    sql = """
        INSERT INTO sigtap_grupos (codigo, descricao, competencia)
        VALUES %s
        ON CONFLICT (codigo) DO UPDATE SET descricao = EXCLUDED.descricao
    """
    cursor = conn.cursor()
    vals = [(g["codigo"], g["descricao"], g["competencia"]) for g in grupos]
    execute_values(cursor, sql, vals, page_size=len(vals))
    conn.commit()
    cursor.execute("SELECT codigo, id FROM sigtap_grupos")
    mapa = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    log.info(f"  Grupos inseridos: {len(mapa)}")
    return mapa


# ── Procedimentos ─────────────────────────────────────────────────────────────

def parse_procedimentos(filepath: str, mapa_grupos: dict[str, int]) -> list[dict]:
    """
    Layout (tb_procedimento_layout.txt):
    CO_PROCEDIMENTO[10] NO_PROCEDIMENTO[250] TP_COMPLEXIDADE[1] TP_SEXO[1]
    QT_MAXIMA_EXECUCAO[4] QT_DIAS_PERMANENCIA[4] QT_PONTOS[4]
    VL_IDADE_MINIMA[4] VL_IDADE_MAXIMA[4]
    VL_SH[12] VL_SA[12] VL_SP[12]
    CO_FINANCIAMENTO[2] CO_RUBRICA[6] QT_TEMPO_PERMANENCIA[4] DT_COMPETENCIA[6]
    """
    log.info(f"Lendo {filepath}...")
    procs = []
    with open(filepath, encoding="latin-1") as f:
        for line in f:
            if len(line) < 336:
                continue
            codigo = line[0:10].strip()
            if not codigo:
                continue
            grupo_codigo = codigo[0:2]
            procs.append({
                "codigo": codigo,
                "grupo_id": mapa_grupos.get(grupo_codigo),
                "descricao": line[10:260].strip(),
                "complexidade": line[260:261].strip() or None,
                "sexo": line[261:262].strip() or None,
                "qt_maxima_execucao": parse_int(line[262:266]),
                "qt_dias_permanencia": parse_int(line[266:270]),
                "qt_pontos": parse_int(line[270:274]),
                "vl_idade_minima": parse_int(line[274:278]),
                "vl_idade_maxima": parse_int(line[278:282]),
                "vl_sh": parse_decimal_sigtap(line[282:294]),
                "vl_sa": parse_decimal_sigtap(line[294:306]),
                "vl_sp": parse_decimal_sigtap(line[306:318]),
                "codigo_financiamento": line[318:320].strip() or None,
                "codigo_rubrica": line[320:326].strip() or None,
                "qt_tempo_permanencia": parse_int(line[326:330]),
                "competencia": line[330:336].strip() or None,
            })
    log.info(f"  {len(procs):,} procedimentos lidos")
    return procs


def inserir_procedimentos(procs: list[dict], conn) -> dict[str, int]:
    sql = """
        INSERT INTO sigtap_procedimentos (
            codigo, grupo_id, descricao, complexidade, sexo,
            qt_maxima_execucao, qt_dias_permanencia, qt_pontos,
            vl_idade_minima, vl_idade_maxima,
            vl_sh, vl_sa, vl_sp,
            codigo_financiamento, codigo_rubrica, qt_tempo_permanencia, competencia
        ) VALUES %s
        ON CONFLICT (codigo) DO UPDATE SET
            descricao = EXCLUDED.descricao,
            competencia = EXCLUDED.competencia,
            vl_sh = EXCLUDED.vl_sh,
            vl_sa = EXCLUDED.vl_sa,
            vl_sp = EXCLUDED.vl_sp
    """
    LOTE = 1000
    total = 0
    cursor = conn.cursor()
    for i in range(0, len(procs), LOTE):
        lote = procs[i:i + LOTE]
        vals = [(
            p["codigo"], p["grupo_id"], p["descricao"], p["complexidade"], p["sexo"],
            p["qt_maxima_execucao"], p["qt_dias_permanencia"], p["qt_pontos"],
            p["vl_idade_minima"], p["vl_idade_maxima"],
            p["vl_sh"], p["vl_sa"], p["vl_sp"],
            p["codigo_financiamento"], p["codigo_rubrica"], p["qt_tempo_permanencia"], p["competencia"],
        ) for p in lote]
        execute_values(cursor, sql, vals)
        conn.commit()
        total += len(lote)
        log.info(f"  Procedimentos inseridos: {total:,}/{len(procs):,}")
    # Constrói o mapa via SELECT após todos os INSERTs
    cursor.execute("SELECT codigo, id FROM sigtap_procedimentos")
    mapa = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    return mapa


def atualizar_search_vector_procs(conn):
    log.info("Atualizando search_vector dos procedimentos...")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE sigtap_procedimentos
        SET search_vector = to_tsvector('portuguese', coalesce(descricao, ''))
    """)
    conn.commit()
    cursor.close()


# ── Procedimento × CID ────────────────────────────────────────────────────────

def parse_proc_cid(filepath: str) -> list[dict]:
    """
    Formato: CO_PROCEDIMENTO[10] CO_CID[4] ST_PRINCIPAL[1] DT_COMPETENCIA[6]
    """
    log.info(f"Lendo {filepath}...")
    relacoes = []
    with open(filepath, encoding="latin-1") as f:
        for line in f:
            line = line.rstrip("\n")
            if len(line) < 15:
                continue
            relacoes.append({
                "codigo_procedimento": line[0:10].strip(),
                "codigo_cid": line[10:14].strip(),
                "principal": line[14:15].strip() == "S",
                "competencia": line[15:21].strip() if len(line) >= 21 else None,
            })
    log.info(f"  {len(relacoes):,} relações lidas")
    return relacoes


def carregar_mapa_cids(conn) -> dict[str, int]:
    cursor = conn.cursor()
    cursor.execute("SELECT codigo, id FROM cid10_subcategorias")
    mapa = {row[0].strip(): row[1] for row in cursor.fetchall()}
    cursor.close()
    log.info(f"  Mapa de CIDs carregado: {len(mapa):,} subcategorias")
    return mapa


def inserir_proc_cid(relacoes: list[dict], mapa_procs: dict[str, int], mapa_cids: dict[str, int], conn) -> int:
    sql = """
        INSERT INTO sigtap_procedimento_cid
            (procedimento_id, cid_id, codigo_procedimento, codigo_cid, principal, competencia)
        VALUES %s
        ON CONFLICT DO NOTHING
    """
    LOTE = 5000
    total = 0
    sem_proc = 0
    sem_cid = 0
    cursor = conn.cursor()

    for i in range(0, len(relacoes), LOTE):
        lote = relacoes[i:i + LOTE]
        vals = []
        for r in lote:
            proc_id = mapa_procs.get(r["codigo_procedimento"])
            cid_codigo = r["codigo_cid"].strip()
            cid_id = mapa_cids.get(cid_codigo)
            if proc_id is None:
                sem_proc += 1
            if cid_id is None:
                sem_cid += 1
            vals.append((proc_id, cid_id, r["codigo_procedimento"], cid_codigo, r["principal"], r["competencia"]))

        execute_values(cursor, sql, vals)
        conn.commit()
        total += len(lote)
        log.info(f"  Relações inseridas: {total:,}/{len(relacoes):,}")

    cursor.close()
    if sem_proc:
        log.warning(f"  {sem_proc:,} relações sem procedimento correspondente (ignoradas FK)")
    if sem_cid:
        log.warning(f"  {sem_cid:,} relações com CID não encontrado na tabela (FK NULL)")
    return total


def relatorio(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sigtap_grupos")
    total_g = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sigtap_procedimentos")
    total_p = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT codigo_procedimento) FROM sigtap_procedimento_cid")
    total_rel, procs_com_cid = cursor.fetchone()
    cursor.close()
    print()
    print("=" * 50)
    print("RELATÓRIO — SIGTAP")
    print("=" * 50)
    print(f"  Grupos:                 {total_g:>6,}")
    print(f"  Procedimentos:          {total_p:>6,}")
    print(f"  Relações proc×CID:      {total_rel:>6,}")
    print(f"  Proc. com CID:          {procs_com_cid:>6,}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Importa tabelas SIGTAP")
    parser.add_argument("--dados-dir", default=os.getenv("DADOS_DIR", "./dados"))
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL", "postgresql://mediddata:mediddata@localhost:5432/mediddata"))
    args = parser.parse_args()

    inicio = time.time()
    log.info("=== IMPORTAÇÃO SIGTAP ===")

    dados = args.dados_dir
    grupos = parse_grupos(os.path.join(dados, "sigtap_grupos.txt"))
    procs = None  # carregado após grupos
    relacoes = parse_proc_cid(os.path.join(dados, "sigtap_procedimento_cid.txt"))

    conn = psycopg2.connect(args.db_url)
    try:
        mapa_grupos = inserir_grupos(grupos, conn)

        procs = parse_procedimentos(os.path.join(dados, "sigtap_procedimentos.txt"), mapa_grupos)
        mapa_procs = inserir_procedimentos(procs, conn)
        atualizar_search_vector_procs(conn)

        mapa_cids = carregar_mapa_cids(conn)
        inserir_proc_cid(relacoes, mapa_procs, mapa_cids, conn)

        relatorio(conn)
    finally:
        conn.close()

    log.info(f"Concluído em {time.time() - inicio:.1f}s")


if __name__ == "__main__":
    main()
