from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import (
    ConsumoResposta,
    ConsumoItem,
    ChaveAcessoEntrada,
    ChaveAcessoResposta,
    AtualizarPerfilEntrada,
    AtualizarSenhaEntrada,
)
from app.repositories import usuario_repo
from app.services import auth_service
from app.middleware.auth_middleware import requer_usuario

router = APIRouter()


# ── Consumo ───────────────────────────────────────────────────────────────

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


# ── Chaves de Acesso ───────────────────────────────────────────────────────

@router.get(
    "/chaves",
    response_model=list[ChaveAcessoResposta],
    summary="Listar chaves de acesso ativas",
)
def listar_chaves(
    usuario: Usuario = Depends(requer_usuario),
    db: Session = Depends(get_db),
):
    chaves = usuario_repo.listar_chaves_usuario(db, usuario.id)
    return [ChaveAcessoResposta.model_validate(c) for c in chaves]


@router.post(
    "/chaves",
    response_model=ChaveAcessoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova chave de acesso",
    description=(
        "Cria uma nova chave API no formato `med_...`. "
        "**A chave completa só é retornada na criação** — salve-a imediatamente, "
        "pois não será possível recuperá-la depois."
    ),
)
def criar_chave(
    entrada: ChaveAcessoEntrada,
    usuario: Usuario = Depends(requer_usuario),
    db: Session = Depends(get_db),
):
    token, prefixo, token_hash = auth_service.gerar_chave_acesso()
    chave = usuario_repo.criar_chave_acesso(
        db, usuario.id, entrada.nome, prefixo, token_hash
    )
    resposta = ChaveAcessoResposta.model_validate(chave)
    resposta.chave_completa = token
    return resposta


@router.delete(
    "/chaves/{chave_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revogar chave de acesso",
)
def revogar_chave(
    chave_id: int,
    usuario: Usuario = Depends(requer_usuario),
    db: Session = Depends(get_db),
):
    sucesso = usuario_repo.revogar_chave_acesso(db, chave_id, usuario.id)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chave não encontrada ou já revogada.",
        )
    return None


# ── Perfil ─────────────────────────────────────────────────────────────────

@router.put(
    "/perfil",
    response_model=dict,
    summary="Atualizar nome do perfil",
)
def atualizar_perfil(
    entrada: AtualizarPerfilEntrada,
    usuario: Usuario = Depends(requer_usuario),
    db: Session = Depends(get_db),
):
    usuario_repo.atualizar_nome_usuario(db, usuario.id, entrada.nome)
    return {"mensagem": "Perfil atualizado com sucesso."}


@router.put(
    "/senha",
    response_model=dict,
    summary="Alterar senha",
)
def alterar_senha(
    entrada: AtualizarSenhaEntrada,
    usuario: Usuario = Depends(requer_usuario),
    db: Session = Depends(get_db),
):
    if not auth_service.verificar_senha(entrada.senha_atual, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta.",
        )
    nova_senha_hash = auth_service.hash_senha(entrada.senha_nova)
    usuario_repo.atualizar_senha_usuario(db, usuario.id, nova_senha_hash)
    usuario_repo.revogar_refresh_tokens_usuario(db, usuario.id)
    return {"mensagem": "Senha alterada com sucesso. Faça login novamente."}
