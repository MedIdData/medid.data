#!/usr/bin/env python3
"""
Script para promover um usuário a ADMINISTRADOR.
Uso: python3 scripts/promover_admin.py <email>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.usuario import Usuario


def promover_admin(email: str):
    """Promove um usuário a ADMINISTRADOR pelo email."""
    db = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == email.lower()).first()

        if not usuario:
            print(f"❌ Usuário com email '{email}' não encontrado.")
            return False

        print(f"\n📋 Usuário encontrado:")
        print(f"   Nome: {usuario.nome}")
        print(f"   Email: {usuario.email}")
        print(f"   Perfil atual: {usuario.perfil}")
        print(f"   Ativo: {usuario.ativo}")

        if usuario.perfil == 'ADMINISTRADOR':
            print(f"\n✅ Usuário já é ADMINISTRADOR!")
            return True

        # Promover
        usuario.perfil = 'ADMINISTRADOR'

        # Garantir limites generosos
        if not usuario.limite_diario or usuario.limite_diario < 1000:
            usuario.limite_diario = 1000
        if not usuario.limite_mensal or usuario.limite_mensal < 20000:
            usuario.limite_mensal = 20000

        # Garantir que está ativo
        if not usuario.ativo:
            usuario.ativo = True
            print("\n⚠️  Conta estava inativa, foi reativada.")

        db.commit()

        print(f"\n✅ SUCESSO! Usuário promovido a ADMINISTRADOR")
        print(f"   Limites: {usuario.limite_diario} req/dia, {usuario.limite_mensal} req/mês")
        print(f"\n🔐 Agora você pode:")
        print(f"   1. Fazer login com: {usuario.email}")
        print(f"   2. Acessar o menu dropdown (canto superior direito)")
        print(f"   3. Clicar em 'Administração'")
        print(f"   4. Gerenciar todos os usuários do sistema")

        return True

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/promover_admin.py <email>")
        print("\nExemplo:")
        print("  python3 scripts/promover_admin.py teste@mediddata.com")
        sys.exit(1)

    email = sys.argv[1]
    sucesso = promover_admin(email)
    sys.exit(0 if sucesso else 1)
