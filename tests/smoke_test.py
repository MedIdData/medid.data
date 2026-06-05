import requests
import json
import time
from datetime import datetime

BASE_URL = "https://mediddata.com"

EMAIL = f"smoketest_{int(time.time())}@mediddata.com"
SENHA = "Teste@123"

resultados = []


def registrar(nome, sucesso, detalhe=""):
    resultados.append({
        "teste": nome,
        "sucesso": sucesso,
        "detalhe": detalhe
    })

    status = "PASS" if sucesso else "FAIL"
    print(f"[{status}] {nome}")


print("=" * 80)
print("MEDID DATA - SMOKE TEST")
print("=" * 80)

# ------------------------------------------------------------------
# HEALTH
# ------------------------------------------------------------------

try:
    r = requests.get(f"{BASE_URL}/saude", timeout=30)
    registrar("Health Check", r.status_code == 200, str(r.status_code))
except Exception as e:
    registrar("Health Check", False, str(e))

# ------------------------------------------------------------------
# CADASTRO
# ------------------------------------------------------------------

try:
    payload = {
        "nome": "Smoke Test",
        "email": EMAIL,
        "senha": SENHA
    }

    r = requests.post(
        f"{BASE_URL}/auth/cadastro",
        json=payload,
        timeout=30
    )

    registrar(
        "Cadastro",
        r.status_code in [200, 201],
        f"status={r.status_code}"
    )

except Exception as e:
    registrar("Cadastro", False, str(e))

# ------------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------------

token = None

try:
    payload = {
        "email": EMAIL,
        "senha": SENHA
    }

    r = requests.post(
        f"{BASE_URL}/auth/login",
        json=payload,
        timeout=30
    )

    if r.status_code == 200:
        body = r.json()
        token = body.get("access_token")

    registrar(
        "Login",
        r.status_code == 200 and token is not None,
        f"status={r.status_code}"
    )

except Exception as e:
    registrar("Login", False, str(e))

if not token:
    print("\nSem token. Encerrando.")
    exit(1)

headers = {
    "Authorization": f"Bearer {token}"
}

# ------------------------------------------------------------------
# PERFIL
# ------------------------------------------------------------------

try:
    r = requests.get(
        f"{BASE_URL}/usuario/perfil",
        headers=headers,
        timeout=30
    )

    registrar(
        "Perfil",
        r.status_code == 200,
        f"status={r.status_code}"
    )

except Exception as e:
    registrar("Perfil", False, str(e))

# ------------------------------------------------------------------
# BUSCA MEDICAMENTO
# ------------------------------------------------------------------

try:
    r = requests.get(
        f"{BASE_URL}/medicamentos/buscar?termo=dipirona",
        headers=headers,
        timeout=30
    )

    registrar(
        "Busca Dipirona",
        r.status_code == 200,
        f"status={r.status_code}"
    )

except Exception as e:
    registrar("Busca Dipirona", False, str(e))

# ------------------------------------------------------------------
# BUSCA INEXISTENTE
# ------------------------------------------------------------------

try:
    r = requests.get(
        f"{BASE_URL}/medicamentos/buscar?termo=MEDICAMENTO_QUE_NAO_EXISTE_99999",
        headers=headers,
        timeout=30
    )

    registrar(
        "Busca Inexistente",
        r.status_code in [200, 404],
        f"status={r.status_code}"
    )

except Exception as e:
    registrar("Busca Inexistente", False, str(e))

# ------------------------------------------------------------------
# ANALISE
# ------------------------------------------------------------------

try:
    payload = {
        "medicamentos": [
            {
                "principio_ativo": "DIPIRONA SÓDICA",
                "concentracao": "500MG",
                "forma_farmaceutica": "COMPRIMIDO",
                "quantidade_prescrita": 20,
                "posologia": "1 comprimido de 6/6h"
            }
        ],
        "diagnostico_cid": "R51",
        "paciente_idade": 35,
        "paciente_peso": 70
    }

    r = requests.post(
        f"{BASE_URL}/analise/analisar",
        headers=headers,
        json=payload,
        timeout=60
    )

    registrar(
        "Analise",
        r.status_code == 200,
        f"status={r.status_code}"
    )

except Exception as e:
    registrar("Analise", False, str(e))

# ------------------------------------------------------------------
# CONSUMO
# ------------------------------------------------------------------

try:
    r = requests.get(
        f"{BASE_URL}/usuario/consumo/hoje",
        headers=headers,
        timeout=30
    )

    registrar(
        "Consumo Hoje",
        r.status_code == 200,
        f"status={r.status_code}"
    )

except Exception as e:
    registrar("Consumo Hoje", False, str(e))

# ------------------------------------------------------------------
# RESUMO
# ------------------------------------------------------------------

total = len(resultados)
ok = sum(1 for x in resultados if x["sucesso"])
falha = total - ok

print("\n" + "=" * 80)
print("RELATORIO FINAL")
print("=" * 80)

print(f"TOTAL  : {total}")
print(f"PASSOU : {ok}")
print(f"FALHOU : {falha}")

arquivo = {
    "data_execucao": datetime.now().isoformat(),
    "total": total,
    "passou": ok,
    "falhou": falha,
    "detalhes": resultados
}

with open("smoke_test_report.json", "w", encoding="utf-8") as f:
    json.dump(arquivo, f, indent=2, ensure_ascii=False)

print("\nRelatório salvo em smoke_test_report.json")

if falha > 0:
    exit(1)

exit(0)