#!/usr/bin/env python3
"""
Script otimizado para sincronizar dados para Railway usando COPY.
100x mais rápido que INSERT linha por linha.
"""
import sys
import os
import csv
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from sqlalchemy import text
import pandas as pd


def importar_com_copy(db, tabela: str, arquivo_csv: str, colunas: list, sep='|', encoding='ISO-8859-1'):
    """
    Importa CSV usando COPY (muito mais rápido).
    """
    print(f"\n📦 Importando {tabela}...")
    inicio = datetime.now()

    # Ler CSV
    print(f"   Lendo {arquivo_csv}...")
    df = pd.read_csv(
        arquivo_csv,
        sep=sep,
        encoding=encoding,
        dtype=str,
        na_values=['', 'NA', 'NULL'],
        keep_default_na=False
    )

    total = len(df)
    print(f"   ✓ {total:,} registros encontrados")

    # Verificar se já tem dados
    count = db.execute(text(f"SELECT COUNT(*) FROM {tabela}")).scalar()
    if count > 0:
        print(f"   ⚠️  Tabela já tem {count:,} registros - pulando")
        return

    # Criar arquivo temporário para COPY
    print(f"   Preparando dados para COPY...")
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        # Selecionar apenas as colunas necessárias
        df_filtered = df[colunas] if colunas else df

        # Substituir NaN por NULL
        df_filtered = df_filtered.fillna('\\N')

        # Escrever CSV sem header
        df_filtered.to_csv(tmp, index=False, header=False, sep='\t', quoting=csv.QUOTE_NONE, escapechar='\\')
        tmp_path = tmp.name

    try:
        # Usar COPY para importar
        print(f"   Executando COPY...")

        # Ler arquivo temporário
        with open(tmp_path, 'r') as f:
            # Usar raw connection para COPY
            conn = db.connection()
            cursor = conn.connection.cursor()

            # COPY command
            copy_sql = f"COPY {tabela} ({','.join(colunas)}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', NULL '\\N')"
            cursor.copy_expert(copy_sql, f)
            conn.connection.commit()

        duracao = (datetime.now() - inicio).total_seconds()
        print(f"   ✅ {total:,} registros importados em {duracao:.1f}s ({total/duracao:.0f} reg/s)")

    finally:
        # Limpar arquivo temporário
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def importar_sigtap_procedimento_cid_otimizado(db):
    """
    Importa sigtap_procedimento_cid de forma otimizada (a mais lenta).
    """
    print(f"\n📦 Importando sigtap_procedimento_cid (163.728 registros)...")
    inicio = datetime.now()

    # Verificar progresso
    count = db.execute(text("SELECT COUNT(*) FROM sigtap_procedimento_cid")).scalar()
    if count > 0:
        print(f"   ⚠️  Já existem {count:,} registros - pulando")
        return

    arquivo = 'dados/sigtap_procedimento_cid.txt'

    print(f"   Lendo {arquivo}...")

    # Usar pandas com chunks para não estourar memória
    chunk_size = 50000
    total_importado = 0

    for i, chunk in enumerate(pd.read_csv(
        arquivo,
        sep='|',
        encoding='ISO-8859-1',
        dtype=str,
        chunksize=chunk_size,
        na_values=['', 'NA', 'NULL'],
        keep_default_na=False
    )):
        # Preparar dados
        chunk = chunk.fillna('\\N')

        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            chunk.to_csv(tmp, index=False, header=False, sep='\t', quoting=csv.QUOTE_NONE, escapechar='\\')
            tmp_path = tmp.name

        try:
            # COPY
            with open(tmp_path, 'r') as f:
                conn = db.connection()
                cursor = conn.connection.cursor()

                colunas = list(chunk.columns)
                copy_sql = f"COPY sigtap_procedimento_cid ({','.join(colunas)}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', NULL '\\N')"
                cursor.copy_expert(copy_sql, f)
                conn.connection.commit()

            total_importado += len(chunk)
            print(f"   ✓ Chunk {i+1}: {total_importado:,} registros ({total_importado/163728*100:.1f}%)")

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    duracao = (datetime.now() - inicio).total_seconds()
    print(f"   ✅ {total_importado:,} registros importados em {duracao:.1f}s")


def main():
    print("=" * 70)
    print("🚀 SYNC OTIMIZADO PARA RAILWAY (COPY)")
    print("=" * 70)

    db = SessionLocal()

    try:
        # 1. CID-10
        importar_com_copy(
            db,
            tabela='cid10',
            arquivo_csv='dados/CID-10-CATEGORIAS.CSV',
            colunas=['codigo', 'descricao'],
            sep=';'
        )

        # 2. SIGTAP Procedimentos
        importar_com_copy(
            db,
            tabela='sigtap_procedimento',
            arquivo_csv='dados/sigtap_procedimentos.txt',
            colunas=[
                'CO_PROCEDIMENTO', 'NO_PROCEDIMENTO', 'TP_COMPLEXIDADE',
                'TP_SEXO', 'QT_MAXIMA_EXECUCAO', 'VL_IDADE_MINIMA',
                'VL_IDADE_MAXIMA', 'VL_SH', 'VL_SA', 'VL_SP',
                'CO_FINANCIAMENTO', 'CO_RUBRICA', 'QT_TEMPO_PERMANENCIA',
                'DT_COMPETENCIA'
            ],
            sep='|'
        )

        # 3. SIGTAP Procedimento x CID (mais lento - usar método especial)
        importar_sigtap_procedimento_cid_otimizado(db)

        print("\n" + "=" * 70)
        print("✅ IMPORTAÇÃO CONCLUÍDA!")
        print("=" * 70)
        print("\nResumo:")

        # Contar registros
        cid = db.execute(text("SELECT COUNT(*) FROM cid10")).scalar()
        sigtap = db.execute(text("SELECT COUNT(*) FROM sigtap_procedimento")).scalar()
        sigtap_cid = db.execute(text("SELECT COUNT(*) FROM sigtap_procedimento_cid")).scalar()

        print(f"  • CID-10: {cid:,} registros")
        print(f"  • SIGTAP Procedimentos: {sigtap:,} registros")
        print(f"  • SIGTAP x CID: {sigtap_cid:,} registros")
        print("\n🎉 Todos os dados agora disponíveis em produção!")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
