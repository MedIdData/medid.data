#!/usr/bin/env python3
"""
Aplica migration 010 diretamente em produção via script.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from sqlalchemy import text


def aplicar_migration():
    db = SessionLocal()

    try:
        print("=" * 70)
        print("🚀 APLICANDO MIGRATION 010 EM PRODUÇÃO")
        print("=" * 70)

        # 1. Mostrar estado atual
        print("\n📊 Estado ANTES:")
        usuarios = db.execute(text("""
            SELECT id, email, perfil, limite_diario, limite_mensal
            FROM usuarios
            ORDER BY id
        """)).fetchall()

        for u in usuarios:
            print(f"  [{u[0]}] {u[1]:<40} {u[2]:<15} {u[3]}/{u[4]}")

        # 2. Aplicar correções
        print("\n🔧 Aplicando correções...")

        # Passo 1: Garantir limites para usuários não-admin
        print("\n  1. Definindo limites para usuários não-admin...")
        result = db.execute(text("""
            UPDATE usuarios
            SET limite_diario = COALESCE(limite_diario, 20),
                limite_mensal = COALESCE(limite_mensal, 100)
            WHERE perfil NOT IN ('ADMINISTRADOR', 'ADMIN')
        """))
        print(f"     ✓ {result.rowcount} usuários atualizados")

        # Passo 2: Garantir limites ilimitados para admins
        print("\n  2. Definindo limites ilimitados para admins...")
        result = db.execute(text("""
            UPDATE usuarios
            SET limite_diario = 0, limite_mensal = 0
            WHERE perfil IN ('ADMINISTRADOR', 'ADMIN')
        """))
        print(f"     ✓ {result.rowcount} administradores atualizados")

        # Passo 3: Desativar todos os planos
        print("\n  3. Desativando todos os planos...")
        result = db.execute(text("UPDATE planos SET ativo = false"))
        print(f"     ✓ {result.rowcount} planos desativados")

        # Passo 4: Tornar limites obrigatórios (NOT NULL)
        print("\n  4. Tornando limites obrigatórios (NOT NULL)...")
        try:
            db.execute(text("""
                ALTER TABLE usuarios
                ALTER COLUMN limite_diario SET NOT NULL,
                ALTER COLUMN limite_diario SET DEFAULT 20
            """))
            print(f"     ✓ limite_diario agora é NOT NULL com default 20")
        except Exception as e:
            print(f"     ⚠️  limite_diario: {e}")

        try:
            db.execute(text("""
                ALTER TABLE usuarios
                ALTER COLUMN limite_mensal SET NOT NULL,
                ALTER COLUMN limite_mensal SET DEFAULT 100
            """))
            print(f"     ✓ limite_mensal agora é NOT NULL com default 100")
        except Exception as e:
            print(f"     ⚠️  limite_mensal: {e}")

        db.commit()
        print("\n✅ COMMIT realizado com sucesso!")

        # 3. Mostrar estado final
        print("\n📊 Estado DEPOIS:")
        usuarios = db.execute(text("""
            SELECT id, email, perfil, limite_diario, limite_mensal, ativo
            FROM usuarios
            ORDER BY id
        """)).fetchall()

        for u in usuarios:
            status = "✓" if u[5] else "✗"
            limites = f"{u[3]}/{u[4]}" if u[3] != 0 else "∞/∞"
            print(f"  {status} [{u[0]}] {u[1]:<40} {u[2]:<15} {limites}")

        print("\n" + "=" * 70)
        print("✅ MIGRATION 010 APLICADA COM SUCESSO!")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    aplicar_migration()
