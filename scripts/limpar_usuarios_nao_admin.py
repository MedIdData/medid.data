#!/usr/bin/env python3
"""
Script para limpar usuários não-administrativos e revogar chaves API.
Mantém apenas admin@mediddata.com
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from sqlalchemy import text


def limpar_usuarios():
    db = SessionLocal()

    try:
        print("=" * 70)
        print("🧹 LIMPEZA DE USUÁRIOS E CHAVES API")
        print("=" * 70)

        # 1. Listar usuários atuais
        usuarios = db.execute(text("""
            SELECT id, nome, email, perfil
            FROM usuarios
            ORDER BY perfil DESC, email
        """)).fetchall()

        print("\n📋 Usuários atuais:")
        for u in usuarios:
            print(f"  • [{u[3]:<15}] {u[2]:<40} ({u[1]})")

        # 2. Identificar admin principal
        admin_principal = db.execute(text("""
            SELECT id, email FROM usuarios
            WHERE email = 'admin@mediddata.com'
            LIMIT 1
        """)).fetchone()

        if not admin_principal:
            print("\n⚠️  Administrador principal (admin@mediddata.com) não encontrado!")
            print("   Criando agora...")

            db.execute(text("""
                INSERT INTO usuarios (nome, email, perfil, senha_hash, ativo, verificado, limite_diario, limite_mensal, criado_em)
                VALUES ('Administrador', 'admin@mediddata.com', 'ADMINISTRADOR',
                        '$2b$12$dummy_hash_will_need_reset', true, true, 0, 0, NOW())
            """))
            db.commit()

            admin_principal = db.execute(text("""
                SELECT id, email FROM usuarios
                WHERE email = 'admin@mediddata.com'
                LIMIT 1
            """)).fetchone()

            print(f"   ✓ Admin criado: {admin_principal[1]}")

        admin_id = admin_principal[0]

        # 3. Contar registros a serem removidos
        outros_usuarios = db.execute(text("""
            SELECT COUNT(*) FROM usuarios WHERE id != :admin_id
        """), {"admin_id": admin_id}).scalar()

        chaves = db.execute(text("SELECT COUNT(*) FROM chaves_acesso")).scalar()
        convites = db.execute(text("SELECT COUNT(*) FROM convites_usuario")).scalar()

        print(f"\n📊 Dados a serem removidos:")
        print(f"  • Usuários (exceto admin): {outros_usuarios}")
        print(f"  • Chaves API: {chaves}")
        print(f"  • Convites pendentes: {convites}")

        # 4. Remover dados relacionados primeiro
        print(f"\n🗑️  Removendo dados...")

        # Consumo diário
        result = db.execute(text("DELETE FROM consumo_diario WHERE usuario_id != :admin_id"), {"admin_id": admin_id})
        print(f"  ✓ Consumo diário: {result.rowcount} registros removidos")

        # Auditoria (TODAS - antes de remover chaves)
        result = db.execute(text("DELETE FROM auditoria_requisicoes"))
        print(f"  ✓ Auditoria: {result.rowcount} registros removidos")

        # Chaves de acesso
        result = db.execute(text("DELETE FROM chaves_acesso"))
        print(f"  ✓ Chaves API: {result.rowcount} chaves revogadas")

        # Refresh tokens
        result = db.execute(text("DELETE FROM refresh_tokens WHERE usuario_id != :admin_id"), {"admin_id": admin_id})
        print(f"  ✓ Refresh tokens: {result.rowcount} tokens removidos")

        # Convites
        result = db.execute(text("DELETE FROM convites_usuario"))
        print(f"  ✓ Convites: {result.rowcount} convites removidos")

        # Usuários
        result = db.execute(text("DELETE FROM usuarios WHERE id != :admin_id"), {"admin_id": admin_id})
        print(f"  ✓ Usuários: {result.rowcount} usuários removidos")

        db.commit()

        print("\n" + "=" * 70)
        print("✅ LIMPEZA CONCLUÍDA!")
        print("=" * 70)

        # Verificar estado final
        total_usuarios = db.execute(text("SELECT COUNT(*) FROM usuarios")).scalar()
        total_chaves = db.execute(text("SELECT COUNT(*) FROM chaves_acesso")).scalar()

        print(f"\n📊 Estado final:")
        print(f"  • Usuários: {total_usuarios}")
        print(f"  • Chaves API: {total_chaves}")

        print(f"\n✅ Apenas {admin_principal[1]} permanece no sistema.")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    limpar_usuarios()
