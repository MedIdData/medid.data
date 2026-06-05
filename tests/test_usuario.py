"""
Testes de gestão de usuário (perfil, senha, chaves, consumo).
"""


def test_obter_consumo(client, headers_usuario):
    """Testa endpoint de consumo."""
    response = client.get("/usuario/consumo", headers=headers_usuario)
    assert response.status_code == 200
    data = response.json()
    assert "plano" in data
    assert "limite_diario" in data
    assert "limite_mensal" in data
    assert "consumo_hoje" in data
    assert "consumo_mes" in data


def test_listar_chaves_vazio(client, headers_usuario):
    """Testa listagem de chaves quando não há nenhuma."""
    response = client.get("/usuario/chaves", headers=headers_usuario)
    assert response.status_code == 200
    assert response.json() == []


def test_criar_chave(client, headers_usuario):
    """Testa criação de chave API."""
    payload = {"nome": "Chave de Teste"}
    response = client.post("/usuario/chaves", json=payload, headers=headers_usuario)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "prefixo" in data
    assert "chave_completa" in data
    assert data["chave_completa"].startswith("med_")


def test_revogar_chave(client, headers_usuario):
    """Testa revogação de chave."""
    # Criar chave
    criar_response = client.post(
        "/usuario/chaves",
        json={"nome": "Chave Teste"},
        headers=headers_usuario
    )
    chave_id = criar_response.json()["id"]

    # Revogar
    response = client.delete(f"/usuario/chaves/{chave_id}", headers=headers_usuario)
    assert response.status_code == 204


def test_alterar_perfil(client, headers_usuario):
    """Testa atualização de nome do perfil."""
    payload = {"nome": "Novo Nome"}
    response = client.put("/usuario/perfil", json=payload, headers=headers_usuario)
    assert response.status_code == 200
    data = response.json()
    assert "mensagem" in data


def test_alterar_senha_incorreta(client, headers_usuario):
    """Testa alteração de senha com senha atual errada."""
    payload = {
        "senha_atual": "senhaerrada",
        "senha_nova": "novasenha123"
    }
    response = client.put("/usuario/senha", json=payload, headers=headers_usuario)
    assert response.status_code == 400


def test_alterar_senha_sucesso(client, headers_usuario):
    """Testa alteração de senha com sucesso."""
    payload = {
        "senha_atual": "senha123",
        "senha_nova": "novasenha123"
    }
    response = client.put("/usuario/senha", json=payload, headers=headers_usuario)
    assert response.status_code == 200
