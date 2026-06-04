from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.analise import AnaliseEntrada, AnaliseResultado
from app.services import analise_risco
from app.middleware.auth_middleware import requer_acesso

router = APIRouter()


@router.post(
    "/risco",
    response_model=AnaliseResultado,
    summary="Análise de risco de consistência clínica e financeira",
    description=(
        "Avalia um conjunto medicamento + tratamento + CID + procedimento + quantidade + preço "
        "em 9 dimensões, gerando pontuações de aderência e risco, potencial de glosa e "
        "motivos explicáveis em português.\n\n"
        "**O potencial de glosa não representa uma glosa real nem uma decisão de operadora.** "
        "É um indicador preventivo baseado em inconsistências detectadas.\n\n"
        "**Requer autenticação** — JWT Bearer ou chave de acesso."
    ),
)
def analisar_risco(
    entrada: AnaliseEntrada,
    usuario: Usuario = Depends(requer_acesso("ANALISE")),
    db: Session = Depends(get_db),
):
    return analise_risco.analisar(db, entrada)
