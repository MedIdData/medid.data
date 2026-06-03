"""
Rotas da interface web (HTML/Jinja2).
Auth será integrado no DIA 5 — por ora as páginas são acessíveis sem login.
"""
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import busca_medicamento

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


@router.get("/buscar", response_class=HTMLResponse)
async def pagina_buscar(
    request: Request,
    q: str = Query("", alias="q"),
    apenas_ativos: bool = Query(True),
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    resultados = []
    total = 0
    sugestao = None

    if q and len(q.strip()) >= 2:
        resposta = busca_medicamento.buscar(db, q.strip(), apenas_ativos, pagina, limite)
        resultados = resposta.resultados
        total = resposta.total
        sugestao = resposta.sugestao

    return templates.TemplateResponse(
        request,
        "buscar.html",
        {
            "pagina_ativa": "buscar",
            "usuario": None,      # DIA 5: substituir pelo usuário autenticado
            "q": q.strip(),
            "apenas_ativos": apenas_ativos,
            "pagina": pagina,
            "limite": limite,
            "resultados": resultados,
            "total": total,
            "sugestao": sugestao,
        },
    )


@router.get("/", response_class=HTMLResponse)
async def pagina_raiz(request: Request):
    return templates.TemplateResponse(
        request,
        "buscar.html",
        {
            "pagina_ativa": "buscar",
            "usuario": None,
            "q": "",
            "apenas_ativos": True,
            "pagina": 1,
            "limite": 20,
            "resultados": [],
            "total": 0,
            "sugestao": None,
        },
    )
