"""
Testes de autenticação (login, cadastro, refresh, logout).
"""


def test_login_sucesso(client, usuario_teste):
    """Testa login com credenciais válidas."""
    response = client.post(
        "/auth/login",
        json={"email": "teste@mediddata.com", "password": "senha123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_senha_incorreta(client, usuario_teste):
    """Testa login com senha errada."""
    response = client.post(
        "/auth/login",
        json={"email": "teste@mediddata.com", "password": "senhaerrada"}
    )
    assert response.status_code == 401


def test_login_usuario_inexistente(client):
    """Testa login com usuário que não existe."""
    response = client.post(
        "/auth/login",
        json={"email": "naoexiste@mediddata.com", "password": "senha123"}
    )
    assert response.status_code == 401


def test_refresh_token(client, usuario_teste):
    """Testa renovação de token."""
    # Login
    login_response = client.post(
        "/auth/login",
        json={"email": "teste@mediddata.com", "password": "senha123"}
    )
    refresh_token = login_response.json()["refresh_token"]

    # Refresh
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_rota_protegida_sem_token(client):
    """Testa acesso a rota protegida sem autenticação."""
    response = client.get("/usuario/consumo")
    assert response.status_code == 401


def test_rota_protegida_com_token(client, headers_usuario):
    """Testa acesso a rota protegida com token válido."""
    response = client.get("/usuario/consumo", headers=headers_usuario)
    assert response.status_code == 200
