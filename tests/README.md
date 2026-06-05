# Testes Automatizados - MedID Data

## Estrutura

```
tests/
├── conftest.py              # Fixtures compartilhadas
├── test_auth.py             # Testes de autenticação
├── test_medicamentos.py     # Testes de busca de medicamentos
├── test_analise.py          # Testes de análise de risco
├── test_usuario.py          # Testes de gestão de usuário
└── test_admin.py            # Testes administrativos
```

## Executar Testes

### Todos os testes
```bash
pytest
```

### Arquivo específico
```bash
pytest tests/test_auth.py
```

### Teste específico
```bash
pytest tests/test_auth.py::test_login_sucesso
```

### Com cobertura
```bash
pytest --cov=app --cov-report=html
```

### Apenas testes rápidos (excluir lentos)
```bash
pytest -m "not slow"
```

## Cobertura

Os testes cobrem:
- ✅ Autenticação (login, refresh, logout)
- ✅ Busca de medicamentos (com/sem auth, validações)
- ✅ Análise de risco (casos válidos e inválidos)
- ✅ Gestão de usuário (perfil, senha, chaves, consumo)
- ✅ Administração (CRUD usuários, estatísticas, permissões)

## Fixtures Disponíveis

- `db` - Banco de dados em memória para cada teste
- `client` - Cliente HTTP de teste (TestClient)
- `usuario_teste` - Usuário comum pré-criado
- `admin_teste` - Administrador pré-criado
- `token_usuario` - Token JWT de usuário comum
- `token_admin` - Token JWT de administrador
- `headers_usuario` - Headers com autenticação de usuário
- `headers_admin` - Headers com autenticação de admin

## Adicionar Novos Testes

1. Criar arquivo `test_*.py` em `tests/`
2. Importar fixtures necessárias de `conftest.py`
3. Nomear funções com prefixo `test_`
4. Usar assertions padrão do pytest

Exemplo:
```python
def test_minha_feature(client, headers_usuario):
    response = client.get("/endpoint", headers=headers_usuario)
    assert response.status_code == 200
```
