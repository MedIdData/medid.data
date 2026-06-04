from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import logging
import time

from app.config import settings
from app.middleware.auth_middleware import RedirectParaLogin


logger = logging.getLogger(__name__)


# ── Seed de plano e usuário padrão ────────────────────────────────────────

def _seed_plano_gratuito():
    """Cria o plano Gratuito se não existir."""
    from app.database import SessionLocal
    from app.models.empresa import Plano

    with SessionLocal() as db:
        try:
            if not db.query(Plano).filter(Plano.nome == "Gratuito").first():
                plano = Plano(
                    nome="Gratuito",
                    descricao="Plano gratuito com limites básicos para testes e pequenos volumes",
                    limite_diario=100,
                    limite_mensal=2000,
                    valor_mensal_centavos=0,
                    ativo=True,
                )
                db.add(plano)
                db.commit()
                logger.info("Plano Gratuito criado: 100 req/dia, 2000 req/mês")
        except Exception as e:
            logger.warning(f"Seed de plano ignorado: {e}")


def _seed_usuario_padrao():
    """Cria um administrador padrão se não existir nenhum usuário."""
    from app.database import SessionLocal
    from app.models.usuario import Usuario
    from app.services.auth_service import hash_senha
    from app.repositories.usuario_repo import buscar_por_email, criar_usuario

    with SessionLocal() as db:
        try:
            if db.query(Usuario).count() == 0:
                admin = criar_usuario(
                    db, "Administrador", "admin@mediddata.com", hash_senha("medid@2026")
                )
                admin.perfil = "ADMINISTRADOR"
                db.commit()
                logger.info("Usuário padrão criado: admin@mediddata.com / medid@2026")
        except Exception as e:
            logger.warning(f"Seed de usuário ignorado: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _seed_plano_gratuito()
    _seed_usuario_padrao()
    yield


# ── App ────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="MedID Data",
    description=(
        "**Plataforma de Inteligência em Saúde**\n\n"
        "API de análise de risco com dados ANVISA, CMED, CID-10 e SIGTAP.\n\n"
        "## Autenticação\n"
        "- **JWT Bearer**: `Authorization: Bearer <access_token>`\n"
        "- **Chave de Acesso**: `Authorization: Bearer med_<token>` ou `X-API-Key: med_<token>`\n\n"
        "## Módulos\n"
        "- **Base de Medicamentos** — busca fuzzy com correção ortográfica\n"
        "- **Análise de Risco** — motor de 9 dimensões com pontuação de glosa\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
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


@app.exception_handler(RedirectParaLogin)
async def redirect_para_login(request: Request, exc: RedirectParaLogin):
    """Redireciona para /login quando rota web exige autenticação."""
    proxima = str(request.url.path)
    if request.url.query:
        proxima += f"?{request.url.query}"
    return RedirectResponse(url=f"/login?proxima={proxima}", status_code=302)


# ── Health check ───────────────────────────────────────────────────────────

@app.get("/saude", tags=["Sistema"], summary="Verificação de saúde")
async def saude():
    return {"status": "operacional", "servico": "MedID Data", "versao": "1.0.0"}


# ── Routers ────────────────────────────────────────────────────────────────

from app.routers import medicamentos, analise, auth, usuario, web

app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
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
app.include_router(
    usuario.router,
    prefix="/usuario",
    tags=["Usuário"],
)
app.include_router(web.router)
