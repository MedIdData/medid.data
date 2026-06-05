"""
Testes de endpoints administrativos.
"""


def test_admin_acesso_negado_usuario_comum(client, headers_usuario):
    """Testa que usuário comum não acessa endpoints admin."""
    response = client.get("/admin/api/estatisticas", headers=headers_usuario)
    assert response.status_code == 403


def test_admin_estatisticas(client, headers_admin):
    """Testa endpoint de estatísticas do sistema."""
    response = client.get("/admin/api/estatisticas", headers=headers_admin)
    assert response.status_code == 200
    data = response.json()
    assert "total_usuarios" in data
    assert "usuarios_ativos" in data
    assert "total_chaves" in data
    assert "requisicoes_hoje" in data


def test_admin_listar_usuarios(client, headers_admin):
    """Testa listagem de todos os usuários."""
    response = client.get("/admin/api/usuarios", headers=headers_admin)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_admin_criar_usuario(client, headers_admin):
    """Testa criação de usuário pelo admin."""
    payload = {
        "nome": "Novo Usuário",
        "email": "novo@mediddata.com",
        "senha": "senha123",
        "perfil": "USUARIO",
        "limite_diario": 100,
        "limite_mensal": 2000
    }
    response = client.post("/admin/api/usuarios", json=payload, headers=headers_admin)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "novo@mediddata.com"
    assert data["perfil"] == "USUARIO"


def test_admin_criar_usuario_email_duplicado(client, headers_admin, usuario_teste):
    """Testa que não permite criar usuário com email duplicado."""
    payload = {
        "nome": "Outro Usuário",
        "email": "teste@mediddata.com",  # Email já existe
        "senha": "senha123",
        "perfil": "USUARIO",
        "limite_diario": 100,
        "limite_mensal": 2000
    }
    response = client.post("/admin/api/usuarios", json=payload, headers=headers_admin)
    assert response.status_code == 400


def test_admin_atualizar_usuario(client, headers_admin, usuario_teste):
    """Testa atualização de dados de usuário."""
    payload = {
        "nome": "Nome Atualizado",
        "email": "atualizado@mediddata.com",
        "perfil": "USUARIO",
        "ativo": True,
        "limite_diario": 200,
        "limite_mensal": 4000
    }
    response = client.put(
        f"/admin/api/usuarios/{usuario_teste.id}",
        json=payload,
        headers=headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Nome Atualizado"


def test_admin_resetar_senha(client, headers_admin, usuario_teste):
    """Testa reset de senha de usuário."""
    payload = {"senha": "novasenha123"}
    response = client.post(
        f"/admin/api/usuarios/{usuario_teste.id}/resetar-senha",
        json=payload,
        headers=headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert "mensagem" in data


def test_admin_toggle_status(client, headers_admin, usuario_teste):
    """Testa ativar/desativar usuário."""
    response = client.post(
        f"/admin/api/usuarios/{usuario_teste.id}/toggle-status",
        headers=headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ativo"] == False  # Deve ter invertido


def test_admin_nao_pode_desativar_si_mesmo(client, headers_admin, admin_teste):
    """Testa que admin não pode desativar a si mesmo."""
    response = client.post(
        f"/admin/api/usuarios/{admin_teste.id}/toggle-status",
        headers=headers_admin
    )
    assert response.status_code == 400
