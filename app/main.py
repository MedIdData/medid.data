from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

from app.config import settings
from app.routers import medicamentos, analise, web

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MedID Data",
    description=(
        "**Plataforma de Inteligência em Saúde**\n\n"
        "API de análise de risco com dados ANVISA, CMED, CID-10 e SIGTAP.\n\n"
        "Módulos disponíveis:\n"
        "- **Base de Medicamentos** — busca fuzzy com correção ortográfica\n"
        "- **Análise de Risco** — motor de 9 dimensões com pontuação de glosa\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={"name": "MedID Data", "url": "https://mediddata.com"},
    license_info={"name": "Proprietário"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else ["https://mediddata.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def registrar_tempo(request: Request, call_next):
    inicio = time.time()
    response = await call_next(request)
    response.headers["X-Tempo-Resposta"] = f"{(time.time() - inicio) * 1000:.0f}ms"
    return response


@app.get("/saude", tags=["Sistema"], summary="Verificação de saúde")
async def saude():
    return {"status": "operacional", "servico": "MedID Data", "versao": "1.0.0"}


# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(
    medicamentos.router,
    prefix="/medicamentos",
    tags=["Medicamentos"],
)
app.include_router(
    analise.router,
    prefix="/analise",
    tags=["Análise de Risco"],
)
app.include_router(web.router)

# DIA 5: auth, chaves, usuario
