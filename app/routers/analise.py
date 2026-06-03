from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analise import AnaliseEntrada, AnaliseResultado
from app.services import analise_risco

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
        "É um indicador preventivo baseado em inconsistências detectadas entre os dados informados "
        "e as bases ANVISA, CMED, CID-10 e SIGTAP."
    ),
)
def analisar_risco(
    entrada: AnaliseEntrada,
    db: Session = Depends(get_db),
):
    return analise_risco.analisar(db, entrada)
