# test_release.py

import requests
import time
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8000"

ADMIN_EMAIL = "admin@mediddata.com"
ADMIN_PASSWORD = "medid@2026"


def check(nome, condicao):
    if condicao:
        print(f"[OK] {nome}")
    else:
        print(f"[ERRO] {nome}")


print("\n===== HEALTH =====")

r = requests.get(f"{BASE_URL}/saude")
check("Health Check", r.status_code == 200)

print("\n===== LOGIN =====")

r = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": ADMIN_EMAIL,
        "senha": ADMIN_PASSWORD
    }
)

check("Login", r.status_code == 200)

token = r.json()["access_token"]

headers = {
    "Authorization": f"Bearer {token}"
}

print("\n===== AUTH =====")

r = requests.get(
    f"{BASE_URL}/auth/me",
    headers=headers
)

check("Perfil", r.status_code == 200)

print("\n===== CONSUMO =====")

r = requests.get(
    f"{BASE_URL}/usuario/consumo",
    headers=headers
)

check("Consumo", r.status_code == 200)

print("\n===== CHAVES =====")

r = requests.post(
    f"{BASE_URL}/usuario/chaves",
    headers=headers,
    json={"nome": "teste-release"}
)

check("Criar chave", r.status_code in [200, 201])

api_key = None

if r.status_code in [200, 201]:
    api_key = r.json().get("chave_completa")

print("\n===== MEDICAMENTOS =====")

r = requests.get(
    f"{BASE_URL}/medicamentos/buscar",
    headers=headers,
    params={"q": "dipirona"}
)

check("Buscar medicamento", r.status_code == 200)

if r.status_code == 200 and r.json()["resultados"]:
    med_id = r.json()["resultados"][0]["id"]

    r2 = requests.get(
        f"{BASE_URL}/medicamentos/{med_id}",
        headers=headers
    )

    check("Detalhe medicamento", r2.status_code == 200)

print("\n===== ANALISE =====")

payload = {
    "medicamento": "dipirona",
    "preco_informado": 5.50,
    "tratamento": "dor e febre",
    "cid": "R50",
    "quantidade": 1
}

r = requests.post(
    f"{BASE_URL}/analise/risco",
    headers=headers,
    json=payload
)

check("Análise risco", r.status_code == 200)

print("\n===== OPENAPI =====")

r = requests.get(
    f"{BASE_URL}/openapi.json"
)

check("OpenAPI", r.status_code == 200)

print("\n===== SEGURANÇA =====")

r = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "' OR 1=1 --",
        "senha": "' OR 1=1 --"
    }
)

check(
    "SQL Injection Login",
    r.status_code in [400,401,422]
)

r = requests.get(
    f"{BASE_URL}/auth/me",
    headers={
        "Authorization": "Bearer token_falso"
    }
)

check(
    "JWT Inválido",
    r.status_code in [401,403]
)

print("\n===== PERFORMANCE =====")

inicio = time.time()

for _ in range(50):
    requests.get(
        f"{BASE_URL}/saude"
    )

fim = time.time()

tempo = fim - inicio

print(f"50 requests em {tempo:.2f}s")

check(
    "Performance",
    tempo < 10
)

print("\n===== CONCORRÊNCIA =====")


def worker():
    return requests.get(
        f"{BASE_URL}/saude"
    ).status_code


with ThreadPoolExecutor(max_workers=50) as pool:
    resultados = list(pool.map(
        lambda _: worker(),
        range(200)
    ))

check(
    "Concorrência",
    all(x == 200 for x in resultados)
)

print("\n===== API KEY =====")

if api_key:

    r = requests.get(
        f"{BASE_URL}/medicamentos/buscar",
        headers={
            "Authorization": f"Bearer {api_key}",
            "X-API-Key": api_key
        },
        params={"q": "dipirona"}
    )

    check(
        "API Key",
        r.status_code == 200
    )

print("\n===== FINAL =====")
print("HOMOLOGAÇÃO CONCLUÍDA")