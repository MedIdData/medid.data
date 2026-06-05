"""
Testes de busca de medicamentos.
"""


def test_buscar_medicamentos_sem_auth(client):
    """Testa busca sem autenticação."""
    response = client.get("/medicamentos/buscar?q=dipirona")
    assert response.status_code == 401


def test_buscar_medicamentos_com_auth(client, headers_usuario):
    """Testa busca com autenticação."""
    response = client.get("/medicamentos/buscar?q=dipirona", headers=headers_usuario)
    assert response.status_code == 200
    data = response.json()
    assert "resultados" in data
    assert "total" in data


def test_buscar_medicamentos_termo_curto(client, headers_usuario):
    """Testa busca com termo muito curto (< 2 caracteres)."""
    response = client.get("/medicamentos/buscar?q=a", headers=headers_usuario)
    assert response.status_code == 422  # Validação Pydantic


def test_buscar_medicamentos_apenas_ativos(client, headers_usuario):
    """Testa filtro apenas ativos."""
    response = client.get(
        "/medicamentos/buscar?q=dipirona&apenas_ativos=true",
        headers=headers_usuario
    )
    assert response.status_code == 200


def test_buscar_medicamentos_paginacao(client, headers_usuario):
    """Testa paginação."""
    response = client.get(
        "/medicamentos/buscar?q=dipirona&pagina=1&limite=10",
        headers=headers_usuario
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["resultados"]) <= 10
