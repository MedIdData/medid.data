"""
Testes de análise de risco.
"""


def test_analise_risco_sem_auth(client):
    """Testa análise sem autenticação."""
    payload = {
        "medicamento": "Dipirona",
        "preco_informado": 10.5,
        "quantidade": 1
    }
    response = client.post("/analise/risco", json=payload)
    assert response.status_code == 401


def test_analise_risco_basica(client, headers_usuario):
    """Testa análise básica com dados mínimos."""
    payload = {
        "medicamento": "Dipirona",
        "preco_informado": 10.5,
        "quantidade": 1
    }
    response = client.post("/analise/risco", json=payload, headers=headers_usuario)
    assert response.status_code == 200
    data = response.json()
    assert "pontuacao_risco" in data
    assert "classificacao_risco" in data
    assert "motivos" in data
    assert 0 <= data["pontuacao_risco"] <= 100


def test_analise_risco_completa(client, headers_usuario):
    """Testa análise com todos os campos."""
    payload = {
        "medicamento": "Dipirona",
        "preco_informado": 10.5,
        "tratamento": "Dor de cabeça",
        "cid": "R51",
        "procedimento": "03.01.01.007-0",
        "quantidade": 2
    }
    response = client.post("/analise/risco", json=payload, headers=headers_usuario)
    assert response.status_code == 200
    data = response.json()
    assert "pontuacao_risco" in data


def test_analise_risco_preco_negativo(client, headers_usuario):
    """Testa validação de preço negativo."""
    payload = {
        "medicamento": "Dipirona",
        "preco_informado": -10.5,
        "quantidade": 1
    }
    response = client.post("/analise/risco", json=payload, headers=headers_usuario)
    assert response.status_code == 422  # Validação Pydantic


def test_analise_risco_quantidade_zero(client, headers_usuario):
    """Testa validação de quantidade zero."""
    payload = {
        "medicamento": "Dipirona",
        "preco_informado": 10.5,
        "quantidade": 0
    }
    response = client.post("/analise/risco", json=payload, headers=headers_usuario)
    assert response.status_code == 422  # Validação Pydantic


def test_analise_risco_medicamento_inexistente(client, headers_usuario):
    """Testa análise com medicamento que não existe."""
    payload = {
        "medicamento": "MedicamentoInexistente123XYZ",
        "preco_informado": 10.5,
        "quantidade": 1
    }
    response = client.post("/analise/risco", json=payload, headers=headers_usuario)
    assert response.status_code == 200
    data = response.json()
    # Deve retornar alto score de risco
    assert data["pontuacao_risco"] >= 70  # CRÍTICO
