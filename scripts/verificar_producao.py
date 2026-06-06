#!/usr/bin/env python3
"""
Script para verificar estado da produção.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from sqlalchemy import text


def verificar():
    db = SessionLocal()

    try:
        print("=" * 70)
        print("🔍 VERIFICAÇÃO DE PRODUÇÃO")
        print("=" * 70)

        # 1. Verificar se tabela usuarios tem limites NOT NULL
        print("\n📊 Estrutura da tabela usuarios:")
        result = db.execute(text("""
            SELECT column_name, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'usuarios'
            AND column_name IN ('limite_diario', 'limite_mensal')
            ORDER BY column_name
        """)).fetchall()

        for r in result:
            nullable = "NULL" if r[1] == 'YES' else "NOT NULL"
            default = r[2] if r[2] else "sem default"
            print(f"  • {r[0]:<20} {nullable:<10} default: {default}")

        # 2. Verificar usuários
        print("\n👥 Usuários:")
        usuarios = db.execute(text("""
            SELECT email, perfil, limite_diario, limite_mensal, ativo
            FROM usuarios
            ORDER BY perfil DESC
        """)).fetchall()

        for u in usuarios:
            print(f"  • {u[0]:<40} [{u[1]:<15}] {u[2]}/{u[3]} ativo={u[4]}")

        # 3. Verificar planos
        print("\n💳 Planos:")
        planos = db.execute(text("""
            SELECT nome, limite_diario, limite_mensal, ativo
            FROM planos
            ORDER BY ativo DESC, nome
        """)).fetchall()

        for p in planos:
            status = "✓" if p[3] else "✗"
            print(f"  {status} {p[0]:<20} {p[1]}/{p[2]}")

        # 4. Verificar se migrations foram aplicadas
        print("\n📋 Últimas alterações:")

        # Verificar se limites são NOT NULL
        limites_obrigatorios = all(r[1] == 'NO' for r in result)
        print(f"  • Limites obrigatórios (NOT NULL): {'✅' if limites_obrigatorios else '❌'}")

        # Verificar se admin tem limites ilimitados
        admin = db.execute(text("""
            SELECT limite_diario, limite_mensal
            FROM usuarios
            WHERE perfil IN ('ADMINISTRADOR', 'ADMIN')
            LIMIT 1
        """)).fetchone()

        if admin:
            admin_ilimitado = admin[0] == 0 and admin[1] == 0
            print(f"  • Admin com limites ilimitados: {'✅' if admin_ilimitado else '❌'}")

        # Verificar se planos estão desativados
        planos_ativos = db.execute(text("SELECT COUNT(*) FROM planos WHERE ativo = true")).scalar()
        print(f"  • Planos desativados: {'✅' if planos_ativos == 0 else f'❌ ({planos_ativos} ativos)'}")

        print("\n" + "=" * 70)

        if limites_obrigatorios and (not admin or admin_ilimitado) and planos_ativos == 0:
            print("✅ Produção está correta!")
        else:
            print("⚠️  Produção precisa de ajustes!")
            print("\nExecute:")
            print("  python3 scripts/run_migration_010.py")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    verificar()
