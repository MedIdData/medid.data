from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import ConsumoResposta, ConsumoItem
from app.repositories import usuario_repo
from app.middleware.auth_middleware import requer_usuario

router = APIRouter()


@router.get(
    "/consumo",
    response_model=ConsumoResposta,
    summary="Resumo de consumo do plano",
    description="Retorna o consumo diário e mensal do usuário em relação aos limites do plano contratado.",
)
def obter_consumo(
    usuario: Usuario = Depends(requer_usuario),
    db: Session = Depends(get_db),
):
    hoje = date.today()
    plano = usuario_repo.obter_plano_usuario(db, usuario)
    limite_diario = plano.limite_diario if plano else 100
    limite_mensal = plano.limite_mensal if plano else 2000
    nome_plano = plano.nome if plano else "Gratuito"

    consumo_hoje = usuario_repo.obter_consumo_total_dia(db, usuario.id, hoje)
    consumo_mes = usuario_repo.obter_consumo_mensal(db, usuario.id, hoje.year, hoje.month)

    por_modulo_hoje = [
        ConsumoItem(**r)
        for r in usuario_repo.obter_consumo_por_modulo(db, usuario.id, hoje)
    ]
    por_modulo_mes = [
        ConsumoItem(**r)
        for r in usuario_repo.obter_consumo_por_modulo_mes(db, usuario.id, hoje.year, hoje.month)
    ]

    return ConsumoResposta(
        plano=nome_plano,
        limite_diario=limite_diario,
        limite_mensal=limite_mensal,
        consumo_hoje=consumo_hoje,
        consumo_mes=consumo_mes,
        percentual_diario=round(consumo_hoje / limite_diario * 100, 1) if limite_diario else 0,
        percentual_mensal=round(consumo_mes / limite_mensal * 100, 1) if limite_mensal else 0,
        por_modulo_hoje=por_modulo_hoje,
        por_modulo_mes=por_modulo_mes,
    )
