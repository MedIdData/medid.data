#!/usr/bin/env python3
"""
Script para exportar dados do banco local para SQL
Gera arquivo backup_dados.sql que pode ser importado no Railway
"""
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def exportar_tabela(conn, nome_tabela, arquivo_sql):
    """Exporta dados de uma tabela para arquivo SQL"""
    logger.info(f"Exportando {nome_tabela}...")

    # Contar registros
    result = conn.execute(text(f"SELECT COUNT(*) FROM {nome_tabela}"))
    total = result.scalar()

    if total == 0:
        logger.warning(f"  ⚠️  Tabela {nome_tabela} está vazia, pulando...")
        return 0

    logger.info(f"  {total:,} registros encontrados")

    # Obter nomes das colunas
    result = conn.execute(text(f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = '{nome_tabela}'
        ORDER BY ordinal_position
    """))
    colunas = [row[0] for row in result]

    # Buscar dados em lotes
    offset = 0
    batch_size = 1000
    total_exportado = 0

    arquivo_sql.write(f"\n-- Tabela: {nome_tabela} ({total:,} registros)\n")
    arquivo_sql.write(f"SET session_replication_role = replica; -- Desabilita triggers temporariamente\n")

    while offset < total:
        result = conn.execute(text(f"SELECT * FROM {nome_tabela} LIMIT {batch_size} OFFSET {offset}"))
        rows = result.fetchall()

        if not rows:
            break

        for row in rows:
            # Converter valores para SQL
            valores = []
            for i, val in enumerate(row):
                if val is None:
                    valores.append('NULL')
                elif isinstance(val, str):
                    # Escapa aspas simples
                    val_escaped = val.replace("'", "''").replace("\\", "\\\\")
                    valores.append(f"'{val_escaped}'")
                elif isinstance(val, (int, float)):
                    valores.append(str(val))
                elif isinstance(val, bool):
                    valores.append('TRUE' if val else 'FALSE')
                else:
                    # Datetime, etc
                    val_str = str(val).replace("'", "''")
                    valores.append(f"'{val_str}'")

            cols_str = ', '.join(colunas)
            vals_str = ', '.join(valores)
            arquivo_sql.write(f"INSERT INTO {nome_tabela} ({cols_str}) VALUES ({vals_str});\n")
            total_exportado += 1

        offset += batch_size

        if offset % 5000 == 0:
            logger.info(f"  Progresso: {offset:,}/{total:,} ({offset/total*100:.1f}%)")

    arquivo_sql.write(f"SET session_replication_role = DEFAULT; -- Reabilita triggers\n\n")
    logger.info(f"✓ {total_exportado:,} registros exportados")
    return total_exportado


def main():
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

    arquivo_saida = 'backup_dados.sql'

    logger.info("=" * 70)
    logger.info("EXPORTAÇÃO DE DADOS PARA SQL")
    logger.info("=" * 70)

    try:
        with engine.connect() as conn:
            with open(arquivo_saida, 'w', encoding='utf-8') as f:
                f.write("-- Backup de dados MedID Data\n")
                f.write("-- Gerado automaticamente\n")
                f.write(f"-- Data: {__import__('datetime').datetime.now()}\n\n")
                f.write("BEGIN;\n\n")

                total_geral = 0
                for tabela in tabelas:
                    try:
                        count = exportar_tabela(conn, tabela, f)
                        total_geral += count
                    except Exception as e:
                        logger.error(f"✗ Erro ao exportar {tabela}: {e}")
                        continue

                f.write("\nCOMMIT;\n")

        # Tamanho do arquivo
        tamanho_mb = os.path.getsize(arquivo_saida) / (1024 * 1024)

        logger.info("\n" + "=" * 70)
        logger.info("✓ EXPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        logger.info("=" * 70)
        logger.info(f"Arquivo gerado: {arquivo_saida}")
        logger.info(f"Tamanho: {tamanho_mb:.2f} MB")
        logger.info(f"Total de registros: {total_geral:,}")
        logger.info("\nPara importar no Railway:")
        logger.info("  psql $DATABASE_URL < backup_dados.sql")
        logger.info("=" * 70)

        return 0

    except Exception as e:
        logger.error(f"\n✗ ERRO: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
