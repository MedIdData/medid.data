from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.medicamento import MedicamentoBuscaResposta, MedicamentoDetalhe
from app.services import busca_medicamento
from app.middleware.auth_middleware import requer_acesso

router = APIRouter()


@router.get(
    "/buscar",
    response_model=MedicamentoBuscaResposta,
    summary="Busca inteligente de medicamentos",
    description=(
        "Busca medicamentos por nome comercial ou princípio ativo usando similaridade textual "
        "com correção ortográfica. Retorna dados ANVISA e preços CMED (PF, PMC, PMVG).\n\n"
        "**Requer autenticação** — JWT Bearer ou chave de acesso."
    ),
)
def buscar_medicamentos(
    q: str = Query(..., min_length=2, description="Termo de busca"),
    apenas_ativos: bool = Query(True, description="Somente registros ativos ANVISA"),
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
    usuario: Usuario = Depends(requer_acesso("MEDICAMENTOS")),
    db: Session = Depends(get_db),
):
    return busca_medicamento.buscar(db, q, apenas_ativos, pagina, limite)


@router.get(
    "/{medicamento_id}",
    response_model=MedicamentoDetalhe,
    summary="Detalhes de um medicamento",
)
def obter_medicamento(
    medicamento_id: int,
    usuario: Usuario = Depends(requer_acesso("MEDICAMENTOS")),
    db: Session = Depends(get_db),
):
    resultado = busca_medicamento.obter_por_id(db, medicamento_id)
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicamento não encontrado.",
        )
    return resultado
