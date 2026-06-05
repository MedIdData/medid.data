from contextlib import asynccontextmanager
import sys
import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pythonjsonlogger import jsonlogger

from app.config import settings
from app.middleware.auth_middleware import RedirectParaLogin
from app.utils.timezone import formatar_data_br, formatar_data_hora_br


# ── Logging estruturado ────────────────────────────────────────────────────

def setup_logging():
    """Configura logging estruturado em JSON para produção."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Handler para stdout
    handler = logging.StreamHandler(sys.stdout)

    if settings.log_format == "json":
        # JSON estruturado para produção
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            timestamp=True
        )
    else:
        # Formato texto para desenvolvimento
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logging.getLogger(__name__)


logger = setup_logging()


# ── Rate Limiting ──────────────────────────────────────────────────────────

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        f"{settings.rate_limit_per_minute}/minute",
        f"{settings.rate_limit_per_hour}/hour"
    ],
    enabled=settings.rate_limit_enabled,
    storage_uri="memory://" if settings.environment == "development" else settings.redis_url,
    strategy="fixed-window"
)


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
    title="MedID Data API",
    description=(
        "**Plataforma de Inteligência em Saúde**\n\n"
        "API RESTful para análise de risco clínico e financeiro com dados oficiais:\n"
        "- ANVISA (medicamentos)\n"
        "- CMED (preços regulados)\n"
        "- CID-10 (classificação de doenças)\n"
        "- SIGTAP (procedimentos SUS)\n\n"
        "## Autenticação\n\n"
        "Dois métodos de autenticação suportados:\n\n"
        "1. **JWT Bearer Token** (sessões web e aplicações):\n"
        "   ```\n"
        "   Authorization: Bearer <access_token>\n"
        "   ```\n\n"
        "2. **Chave de Acesso API** (integrações):\n"
        "   ```\n"
        "   Authorization: Bearer med_...\n"
        "   X-API-Key: med_...\n"
        "   ```\n\n"
        "Obtenha tokens via `/auth/login` ou chaves via `/usuario/chaves`.\n\n"
        "## Rate Limiting\n\n"
        "- **Desenvolvimento**: sem limites\n"
        "- **Produção**: 60 req/min por IP, 1000 req/hora\n"
        "- **Por plano**: limites diários/mensais por usuário\n\n"
        "## Módulos\n\n"
        "- **Base de Medicamentos** — busca inteligente com fuzzy matching\n"
        "- **Análise de Risco** — motor de 9 dimensões com pontuação de glosa\n"
        "- **Gestão de Chaves** — criar e gerenciar chaves de integração\n"
        "- **Histórico de Consumo** — métricas e analytics de uso\n\n"
        "## Suporte\n\n"
        "- Documentação: https://mediddata.com/docs\n"
        "- Contato: contato@mediddata.com\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "MedID Data",
        "email": "contato@mediddata.com",
        "url": "https://mediddata.com"
    },
    license_info={
        "name": "Proprietário",
        "url": "https://mediddata.com/termos"
    },
    servers=[
        {"url": "https://mediddata.com", "description": "Produção"},
        {"url": "http://localhost:8000", "description": "Desenvolvimento"}
    ]
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configurável
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Tempo-Resposta", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next: Callable):
    """Middleware para logging estruturado e métricas de tempo de resposta."""
    inicio = time.time()

    # Log da requisição
    logger.info(
        "request_started",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        }
    )

    try:
        response = await call_next(request)
        duracao_ms = (time.time() - inicio) * 1000

        # Headers de resposta
        response.headers["X-Tempo-Resposta"] = f"{duracao_ms:.0f}ms"

        # Log da resposta
        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duracao_ms, 2),
                "client_ip": request.client.host if request.client else None
            }
        )

        return response

    except Exception as e:
        duracao_ms = (time.time() - inicio) * 1000
        logger.error(
            "request_failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duracao_ms, 2),
                "error": str(e),
                "client_ip": request.client.host if request.client else None
            },
            exc_info=True
        )
        raise


@app.exception_handler(RedirectParaLogin)
async def redirect_para_login(request: Request, exc: RedirectParaLogin):
    """Redireciona para /login quando rota web exige autenticação."""
    proxima = str(request.url.path)
    if request.url.query:
        proxima += f"?{request.url.query}"
    return RedirectResponse(url=f"/login?proxima={proxima}", status_code=302)


# ── Health check ───────────────────────────────────────────────────────────

@app.get(
    "/saude",
    tags=["Sistema"],
    summary="Health check",
    description="Verifica se a API está operacional. Usado por orquestradores (Railway, Kubernetes) para monitoramento.",
    response_description="Status operacional da API",
    responses={
        200: {
            "description": "API operacional",
            "content": {
                "application/json": {
                    "example": {
                        "status": "operacional",
                        "servico": "MedID Data",
                        "versao": "1.0.0",
                        "environment": "production"
                    }
                }
            }
        }
    }
)
@limiter.exempt
async def saude():
    """Health check endpoint para monitoramento de infraestrutura."""
    return {
        "status": "operacional",
        "servico": "MedID Data",
        "versao": "1.0.0",
        "environment": settings.environment
    }


# ── Routers ────────────────────────────────────────────────────────────────

from app.routers import medicamentos, analise, auth, usuario, admin, web

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
app.include_router(
    admin.router,
    prefix="/admin/api",
    tags=["Administração"],
)
app.include_router(web.router)

# Servir arquivos estáticos (para imagens OG, etc)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ── Jinja2 Filters ─────────────────────────────────────────────────────────

def registrar_filtros_jinja():
    """Registra filtros customizados do Jinja2."""
    from app.routers.web import templates

    templates.env.filters["data_br"] = formatar_data_br
    templates.env.filters["data_hora_br"] = formatar_data_hora_br

registrar_filtros_jinja()
