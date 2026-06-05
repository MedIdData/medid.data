import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"

EMAIL_ADMIN = "admin@mediddata.com"
SENHA_ADMIN = "medid@2026"


def print_result(nome, response):
    print("\n" + "=" * 80)
    print(nome)
    print("=" * 80)
    print("Status:", response.status_code)

    try:
        pprint(response.json())
    except:
        print(response.text)


session = requests.Session()

# --------------------------------------------------
# 1. HEALTH CHECK
# --------------------------------------------------

r = session.get(f"{BASE_URL}/saude")
print_result("HEALTH CHECK", r)

# --------------------------------------------------
# 2. LOGIN
# --------------------------------------------------

login_payload = {
    "email": EMAIL_ADMIN,
    "senha": SENHA_ADMIN
}

r = session.post(
    f"{BASE_URL}/auth/login",
    json=login_payload
)

print_result("LOGIN", r)

if r.status_code != 200:
    print("\nERRO: login falhou")
    exit()

token = r.json()["access_token"]

headers = {
    "Authorization": f"Bearer {token}"
}

# --------------------------------------------------
# 3. PERFIL
# --------------------------------------------------

r = session.get(
    f"{BASE_URL}/auth/me",
    headers=headers
)

print_result("AUTH ME", r)

# --------------------------------------------------
# 4. CONSUMO
# --------------------------------------------------

r = session.get(
    f"{BASE_URL}/usuario/consumo",
    headers=headers
)

print_result("CONSUMO", r)

# --------------------------------------------------
# 5. CHAVES
# --------------------------------------------------

r = session.get(
    f"{BASE_URL}/usuario/chaves",
    headers=headers
)

print_result("LISTAR CHAVES", r)

# --------------------------------------------------
# 6. CRIAR CHAVE
# --------------------------------------------------

payload = {
    "nome": "Teste Automatizado"
}

r = session.post(
    f"{BASE_URL}/usuario/chaves",
    headers=headers,
    json=payload
)

print_result("CRIAR CHAVE", r)

api_key = None

if r.status_code in [200, 201]:
    api_key = r.json().get("chave_completa")

# --------------------------------------------------
# 7. BUSCA MEDICAMENTO VÁLIDA
# --------------------------------------------------

r = session.get(
    f"{BASE_URL}/medicamentos/buscar",
    headers=headers,
    params={
        "q": "dipirona"
    }
)

print_result("BUSCA DIPIRONA", r)

# --------------------------------------------------
# 8. BUSCA MEDICAMENTO INVÁLIDA
# --------------------------------------------------

r = session.get(
    f"{BASE_URL}/medicamentos/buscar",
    headers=headers,
    params={
        "q": "xxxxxxxxxxxx"
    }
)

print_result("BUSCA INEXISTENTE", r)

# --------------------------------------------------
# 9. ANALISE DE RISCO
# --------------------------------------------------

payload = {
    "medicamento": "Dipirona",
    "preco_informado": 15.50,
    "tratamento": "Dor aguda",
    "cid": "R52",
    "procedimento": "03.01.01.007-2",
    "quantidade": 1
}

r = session.post(
    f"{BASE_URL}/analise/risco",
    headers=headers,
    json=payload
)

print_result("ANALISE DE RISCO", r)

# --------------------------------------------------
# 10. ESTATISTICAS ADMIN
# --------------------------------------------------

r = session.get(
    f"{BASE_URL}/admin/api/estatisticas",
    headers=headers
)

print_result("ESTATISTICAS ADMIN", r)

# --------------------------------------------------
# 11. OPENAPI
# --------------------------------------------------

r = session.get(
    f"{BASE_URL}/openapi.json"
)

print_result("OPENAPI", r)

# --------------------------------------------------
# 12. TESTE API KEY
# --------------------------------------------------

if api_key:

    api_headers = {
        "Authorization": f"Bearer {api_key}"
    }

    r = session.get(
        f"{BASE_URL}/medicamentos/buscar",
        headers=api_headers,
        params={
            "q": "dipirona"
        }
    )

    print_result("TESTE API KEY", r)

# --------------------------------------------------
# RESUMO
# --------------------------------------------------

print("\n")
print("=" * 80)
print("TESTE FINALIZADO")
print("=" * 80)
print("API:", BASE_URL)
print("Usuário:", EMAIL_ADMIN)
print("Endpoints testados:")
print(" - /saude")
print(" - /auth/login")
print(" - /auth/me")
print(" - /usuario/consumo")
print(" - /usuario/chaves")
print(" - /medicamentos/buscar")
print(" - /analise/risco")
print(" - /admin/api/estatisticas")
print(" - /openapi.json")
print("=" * 80)