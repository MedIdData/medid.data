from pathlib import Path
import re
import json

ROOT = Path("app")

resultado = {
    "routers": [],
    "schemas": [],
    "endpoints": []
}

# -------------------------------
# ROUTERS
# -------------------------------

for arquivo in ROOT.rglob("routers/*.py"):
    try:
        conteudo = arquivo.read_text(encoding="utf-8")

        resultado["routers"].append(str(arquivo))

        matches = re.findall(
            r'@router\.(get|post|put|delete|patch)\s*\(\s*"([^"]+)"',
            conteudo,
            re.MULTILINE
        )

        for metodo, rota in matches:
            resultado["endpoints"].append({
                "arquivo": str(arquivo),
                "metodo": metodo.upper(),
                "rota": rota
            })

    except Exception as e:
        print(f"Erro lendo {arquivo}: {e}")

# -------------------------------
# SCHEMAS
# -------------------------------

for arquivo in ROOT.rglob("schemas/*.py"):
    try:
        conteudo = arquivo.read_text(encoding="utf-8")

        classes = re.findall(
            r"class\s+(\w+)\(",
            conteudo
        )

        resultado["schemas"].append({
            "arquivo": str(arquivo),
            "classes": classes
        })

    except Exception as e:
        print(f"Erro lendo {arquivo}: {e}")

# -------------------------------
# MAIN.PY
# -------------------------------

for nome in ["main.py", "app/main.py"]:
    path = Path(nome)

    if path.exists():
        try:
            resultado["main_py"] = path.read_text(
                encoding="utf-8"
            )
        except:
            pass

# -------------------------------
# OUTPUT
# -------------------------------

saida = Path("api_discovery.json")

with open(saida, "w", encoding="utf-8") as f:
    json.dump(
        resultado,
        f,
        indent=2,
        ensure_ascii=False
    )

print()
print("=" * 80)
print("API DISCOVERY FINALIZADO")
print("=" * 80)
print(f"Routers: {len(resultado['routers'])}")
print(f"Endpoints: {len(resultado['endpoints'])}")
print(f"Schemas: {len(resultado['schemas'])}")
print()
print(f"Arquivo gerado: {saida}")