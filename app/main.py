from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from app.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MedID Data",
    description="Plataforma de Inteligência em Saúde — API de Análise de Risco",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else ["https://mediddata.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def registrar_tempo_resposta(request: Request, call_next):
    inicio = time.time()
    response = await call_next(request)
    response.headers["X-Tempo-Resposta"] = f"{(time.time() - inicio) * 1000:.0f}ms"
    return response


@app.get(
    "/saude",
    tags=["Sistema"],
    summary="Verificação de saúde da API",
    response_description="Status dos serviços",
)
async def saude():
    return {
        "status": "operacional",
        "servico": "MedID Data",
        "versao": "1.0.0",
        "ambiente": settings.environment,
    }


# Os roteadores serão registrados progressivamente nos DIAs 3-7:
# from app.routers import medicamentos, analise, auth, usuario, web
# app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
# app.include_router(medicamentos.router, prefix="/medicamentos", tags=["Medicamentos"])
# app.include_router(analise.router, prefix="/analise", tags=["Análise de Risco"])
# app.include_router(usuario.router, prefix="/usuario", tags=["Usuário"])
# app.include_router(web.router, tags=["Interface Web"])
