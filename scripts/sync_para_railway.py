#!/usr/bin/env python3
"""
Sincroniza dados do banco LOCAL para RAILWAY via Python
Não precisa de pg_dump/psql, funciona puro Python
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.database import engine as local_engine
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def copiar_tabela(conn_local, conn_railway, nome_tabela):
    """Copia dados de uma tabela do local para Railway"""
    logger.info(f"Copiando {nome_tabela}...")

    # Contar registros local
    result = conn_local.execute(text(f"SELECT COUNT(*) FROM {nome_tabela}"))
    total = result.scalar()

    if total == 0:
        logger.warning(f"  ⚠️  Tabela {nome_tabela} vazia no local, pulando...")
        return 0

    logger.info(f"  {total:,} registros no banco local")

    # Verificar se Railway já tem dados
    result = conn_railway.execute(text(f"SELECT COUNT(*) FROM {nome_tabela}"))
    total_railway = result.scalar()

    if total_railway > 0:
        logger.warning(f"  ⚠️  Railway já tem {total_railway:,} registros em {nome_tabela}")
        resp = input(f"  Limpar tabela {nome_tabela} no Railway? (s/N): ")
        if resp.lower() == 's':
            conn_railway.execute(text(f"TRUNCATE TABLE {nome_tabela} CASCADE"))
            conn_railway.commit()
            logger.info(f"  ✓ Tabela {nome_tabela} limpa")
        else:
            logger.info(f"  Pulando {nome_tabela}")
            return 0

    # Obter nomes das colunas
    result = conn_local.execute(text(f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = '{nome_tabela}'
        ORDER BY ordinal_position
    """))
    colunas = [row[0] for row in result]
    cols_str = ', '.join(colunas)

    # Copiar dados em lotes
    offset = 0
    batch_size = 1000
    total_copiado = 0

    # Desabilita triggers temporariamente
    conn_railway.execute(text("SET session_replication_role = replica"))

    while offset < total:
        # Buscar lote do local
        result = conn_local.execute(text(f"SELECT * FROM {nome_tabela} LIMIT {batch_size} OFFSET {offset}"))
        rows = result.fetchall()

        if not rows:
            break

        # Preparar INSERT com placeholders
        placeholders = ', '.join([f":{col}" for col in colunas])
        insert_sql = f"INSERT INTO {nome_tabela} ({cols_str}) VALUES ({placeholders})"

        # Inserir lote no Railway
        for row in rows:
            params = {col: row[i] for i, col in enumerate(colunas)}
            conn_railway.execute(text(insert_sql), params)
            total_copiado += 1

        conn_railway.commit()
        offset += batch_size

        if offset % 5000 == 0:
            logger.info(f"  Progresso: {offset:,}/{total:,} ({offset/total*100:.1f}%)")

    # Reabilita triggers
    conn_railway.execute(text("SET session_replication_role = DEFAULT"))
    conn_railway.commit()

    logger.info(f"✓ {total_copiado:,} registros copiados para Railway")
    return total_copiado


def main():
    # Pede URL do Railway
    railway_url = os.getenv('RAILWAY_DATABASE_URL')

    if not railway_url:
        print("\n" + "="*70)
        print("SINCRONIZAÇÃO LOCAL → RAILWAY")
        print("="*70)
        print("\n1. Acesse Railway Dashboard → PostgreSQL → Connect")
        print("2. Copie a DATABASE_URL PÚBLICA (com .proxy.rlwy.net)\n")
        railway_url = input("Cole a DATABASE_URL do Railway aqui: ").strip()

        if not railway_url:
            logger.error("URL do Railway não fornecida")
            return 1

    logger.info("\n" + "="*70)
    logger.info("INICIANDO SINCRONIZAÇÃO")
    logger.info("="*70)

    tabelas = [
        'medicamentos_anvisa',
        'medicamentos_cmed',
        'cid10_categorias',
        'cid10_subcategorias',
        'sigtap_grupos',
        'sigtap_procedimentos',
        'sigtap_procedimento_cid',
        'dcb',
    ]

    try:
        # Conectar no Railway
        logger.info(f"Conectando no Railway...")
        railway_engine = create_engine(railway_url)

        with local_engine.connect() as conn_local:
            with railway_engine.connect() as conn_railway:
                # Testar conexões
                result = conn_local.execute(text("SELECT version()"))
                logger.info(f"✓ Local: {result.scalar().split(',')[0]}")

                result = conn_railway.execute(text("SELECT version()"))
                logger.info(f"✓ Railway: {result.scalar().split(',')[0]}")

                logger.info("")
                total_geral = 0

                for tabela in tabelas:
                    try:
                        count = copiar_tabela(conn_local, conn_railway, tabela)
                        total_geral += count
                    except Exception as e:
                        logger.error(f"✗ Erro ao copiar {tabela}: {e}")
                        continue

        logger.info("\n" + "="*70)
        logger.info("✓ SINCRONIZAÇÃO CONCLUÍDA!")
        logger.info("="*70)
        logger.info(f"Total de registros copiados: {total_geral:,}")
        logger.info("\nAcesse o site Railway e teste a busca de medicamentos!")
        logger.info("="*70)

        return 0

    except Exception as e:
        logger.error(f"\n✗ ERRO: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
