#!/usr/bin/env python3
"""
Script para executar migration 008 no Railway.
Ajusta limites do plano Gratuito (20/100) e cria plano Admin.
"""
import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from sqlalchemy import text


def run_migration():
    db = SessionLocal()

    try:
        print("🚀 Executando Migration 008...")
        print("=" * 60)

        # SQL statements
        sqls = [
            (
                "Atualizando plano Gratuito para 20/dia, 100/mês",
                """UPDATE planos
                   SET limite_diario = 20,
                       limite_mensal = 100,
                       descricao = 'Plano gratuito com limites básicos para testes e pequenos volumes'
                   WHERE nome = 'Gratuito'"""
            ),
            (
                "Criando plano Admin (ilimitado)",
                """INSERT INTO planos (nome, descricao, limite_diario, limite_mensal, valor_mensal_centavos, ativo, criado_em)
                   SELECT 'Admin',
                          'Plano exclusivo para administradores do sistema (uso interno ilimitado)',
                          0, 0, 0, true, NOW()
                   WHERE NOT EXISTS (SELECT 1 FROM planos WHERE nome = 'Admin')"""
            ),
            (
                "Configurando administradores com limites ilimitados",
                """UPDATE usuarios
                   SET limite_diario = 0, limite_mensal = 0
                   WHERE perfil IN ('ADMINISTRADOR', 'ADMIN')"""
            ),
            (
                "Atualizando usuários para novos limites do Gratuito",
                """UPDATE usuarios
                   SET limite_diario = 20, limite_mensal = 100
                   WHERE perfil NOT IN ('ADMINISTRADOR', 'ADMIN')
                     AND (
                       (limite_diario = 50 AND limite_mensal = 1000) OR
                       (limite_diario = 100 AND limite_mensal = 2000) OR
                       (limite_diario IS NULL OR limite_mensal IS NULL) OR
                       NOT (
                         (limite_diario = 500 AND limite_mensal = 10000) OR
                         (limite_diario = 2000 AND limite_mensal = 50000) OR
                         (limite_diario = 0 AND limite_mensal = 0)
                       )
                     )"""
            )
        ]

        for descricao, sql in sqls:
            print(f"\n{descricao}...")
            result = db.execute(text(sql))
            print(f"  ✅ {result.rowcount} linha(s) afetada(s)")

        db.commit()
        print("\n" + "=" * 60)
        print("✅ Migration 008 concluída com sucesso!")
        print("\nResumo:")
        print("  • Plano Gratuito: 20 req/dia, 100 req/mês")
        print("  • Plano Admin: ILIMITADO")
        print("  • Administradores: limites ilimitados")
        print("  • Demais usuários: migrados para Gratuito")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Erro ao executar migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
