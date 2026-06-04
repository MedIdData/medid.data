#!/usr/bin/env python3
"""
Script de setup para produção - MedID Data API

Cria:
1. Todas as tabelas do banco de dados
2. Plano Gratuito padrão
3. Usuário administrador padrão

Uso:
    python setup_prod.py

Variáveis de ambiente necessárias:
    DATABASE_URL - URL de conexão PostgreSQL
"""
import sys
import logging
from sqlalchemy import text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_database():
    """Cria todas as tabelas e dados iniciais."""

    logger.info("=" * 70)
    logger.info("MedID Data - Setup de Produção")
    logger.info("=" * 70)

    try:
        # Import aqui para garantir que env vars estão carregadas
        from app.database import engine, Base, SessionLocal
        from app.models import (
            Plano, Empresa, Usuario, RefreshToken, ChaveAcesso,
            MedicamentoAnvisa, MedicamentoCmed, Dcb,
            Cid10Categoria, Cid10Subcategoria,
            SigtapGrupo, SigtapProcedimento, SigtapProcedimentoCid,
            AuditoriaRequisicao, ConsumoDiario
        )
        from app.services.auth_service import hash_senha
        from app.config import settings

        logger.info(f"Ambiente: {settings.environment}")
        logger.info(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}")

        # 1. Testar conexão
        logger.info("\n[1/4] Testando conexão com o banco de dados...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✓ Conectado ao PostgreSQL: {version.split(',')[0]}")

        # 2. Criar todas as tabelas
        logger.info("\n[2/4] Criando tabelas...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Tabelas criadas com sucesso")

        # Listar tabelas criadas
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """))
            tables = [row[0] for row in result]
            logger.info(f"  Total de tabelas: {len(tables)}")
            for table in tables:
                logger.info(f"    - {table}")

        # 3. Criar plano Gratuito
        logger.info("\n[3/4] Criando plano Gratuito...")
        with SessionLocal() as db:
            plano_existente = db.query(Plano).filter(Plano.nome == "Gratuito").first()

            if plano_existente:
                logger.info("✓ Plano Gratuito já existe")
            else:
                plano = Plano(
                    nome="Gratuito",
                    descricao="Plano gratuito com limites básicos para testes e pequenos volumes",
                    limite_diario=100,
                    limite_mensal=2000,
                    valor_mensal_centavos=0,
                    ativo=True,
                )
                db.add(plano)
                db.commit()
                db.refresh(plano)
                logger.info("✓ Plano Gratuito criado")
                logger.info(f"    ID: {plano.id}")
                logger.info(f"    Limite diário: {plano.limite_diario} requisições")
                logger.info(f"    Limite mensal: {plano.limite_mensal} requisições")

        # 4. Criar usuário admin
        logger.info("\n[4/4] Criando usuário administrador...")
        with SessionLocal() as db:
            admin_email = "admin@mediddata.com"
            admin_existente = db.query(Usuario).filter(Usuario.email == admin_email).first()

            if admin_existente:
                logger.info(f"✓ Usuário admin já existe (ID: {admin_existente.id})")
            else:
                admin = Usuario(
                    nome="Administrador",
                    email=admin_email,
                    senha_hash=hash_senha("medid@2026"),
                    perfil="ADMINISTRADOR",
                    ativo=True,
                )
                db.add(admin)
                db.commit()
                db.refresh(admin)
                logger.info("✓ Usuário administrador criado")
                logger.info(f"    ID: {admin.id}")
                logger.info(f"    E-mail: {admin.email}")
                logger.info(f"    Senha: medid@2026")
                logger.info(f"    Perfil: {admin.perfil}")

        # 5. Verificar contagens
        logger.info("\n" + "=" * 70)
        logger.info("RESUMO DO SETUP")
        logger.info("=" * 70)

        with SessionLocal() as db:
            total_planos = db.query(Plano).count()
            total_usuarios = db.query(Usuario).count()
            total_medicamentos_anvisa = db.query(MedicamentoAnvisa).count()
            total_medicamentos_cmed = db.query(MedicamentoCmed).count()
            total_cid10_cat = db.query(Cid10Categoria).count()
            total_cid10_sub = db.query(Cid10Subcategoria).count()
            total_sigtap_proc = db.query(SigtapProcedimento).count()

            logger.info(f"Planos: {total_planos}")
            logger.info(f"Usuários: {total_usuarios}")
            logger.info(f"Medicamentos ANVISA: {total_medicamentos_anvisa}")
            logger.info(f"Medicamentos CMED: {total_medicamentos_cmed}")
            logger.info(f"CID-10 Categorias: {total_cid10_cat}")
            logger.info(f"CID-10 Subcategorias: {total_cid10_sub}")
            logger.info(f"SIGTAP Procedimentos: {total_sigtap_proc}")

        logger.info("\n" + "=" * 70)
        logger.info("✓ SETUP CONCLUÍDO COM SUCESSO!")
        logger.info("=" * 70)
        logger.info("\nCredenciais de acesso:")
        logger.info("  E-mail: admin@mediddata.com")
        logger.info("  Senha: medid@2026")
        logger.info("\n⚠️  IMPORTANTE: Altere a senha padrão após o primeiro login!")
        logger.info("=" * 70)

        return 0

    except Exception as e:
        logger.error("\n" + "=" * 70)
        logger.error("✗ ERRO NO SETUP")
        logger.error("=" * 70)
        logger.error(f"Erro: {str(e)}", exc_info=True)
        logger.error("\nVerifique:")
        logger.error("  1. DATABASE_URL está configurado corretamente")
        logger.error("  2. PostgreSQL está acessível")
        logger.error("  3. Credenciais estão corretas")
        logger.error("  4. Banco de dados existe")
        return 1


if __name__ == "__main__":
    sys.exit(setup_database())
