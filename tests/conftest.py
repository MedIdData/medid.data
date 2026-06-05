"""
Configuração compartilhada para testes com pytest.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.usuario import Usuario
from app.models.empresa import Plano
from app.services import auth_service


# Database de teste em memória
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Cria banco em memória para cada teste."""
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        # Seed plano gratuito
        plano = Plano(
            nome="Gratuito",
            descricao="Plano teste",
            limite_diario=100,
            limite_mensal=2000,
            valor_mensal_centavos=0,
            ativo=True
        )
        db.add(plano)
        db.commit()

        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Cliente HTTP de teste."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def usuario_teste(db):
    """Cria usuário padrão para testes."""
    usuario = Usuario(
        nome="Usuário Teste",
        email="teste@mediddata.com",
        senha_hash=auth_service.hash_senha("senha123"),
        perfil="USUARIO",
        ativo=True,
        limite_diario=100,
        limite_mensal=2000
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@pytest.fixture
def admin_teste(db):
    """Cria administrador para testes."""
    admin = Usuario(
        nome="Admin Teste",
        email="admin@mediddata.com",
        senha_hash=auth_service.hash_senha("admin123"),
        perfil="ADMINISTRADOR",
        ativo=True,
        limite_diario=1000,
        limite_mensal=20000
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def token_usuario(usuario_teste):
    """Token JWT de usuário comum."""
    return auth_service.criar_access_token(
        usuario_teste.id,
        usuario_teste.email,
        usuario_teste.perfil
    )


@pytest.fixture
def token_admin(admin_teste):
    """Token JWT de administrador."""
    return auth_service.criar_access_token(
        admin_teste.id,
        admin_teste.email,
        admin_teste.perfil
    )


@pytest.fixture
def headers_usuario(token_usuario):
    """Headers com autenticação de usuário."""
    return {"Authorization": f"Bearer {token_usuario}"}


@pytest.fixture
def headers_admin(token_admin):
    """Headers com autenticação de admin."""
    return {"Authorization": f"Bearer {token_admin}"}
