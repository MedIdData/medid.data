"""
Endpoints API para administração do sistema.
Requer perfil ADMINISTRADOR.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.admin import (
    UsuarioDetalhado,
    CriarUsuarioEntrada,
    AtualizarUsuarioEntrada,
    ResetarSenhaEntrada,
    EstatisticasResposta,
)
from app.repositories import usuario_repo
from app.services import auth_service
from app.middleware.auth_middleware import requer_usuario

router = APIRouter()


def requer_admin(usuario: Usuario = Depends(requer_usuario)):
    """Middleware que valida se usuário é administrador."""
    if usuario.perfil != 'ADMINISTRADOR':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores."
        )
    return usuario


# ── Estatísticas ───────────────────────────────────────────────────────────

@router.get(
    "/estatisticas",
    response_model=EstatisticasResposta,
    summary="Estatísticas do sistema",
    description="Retorna métricas gerais: usuários, chaves API, consumo.",
)
def obter_estatisticas(
    admin: Usuario = Depends(requer_admin),
    db: Session = Depends(get_db),
):
    return EstatisticasResposta(
        total_usuarios=usuario_repo.contar_usuarios(db),
        usuarios_ativos=usuario_repo.contar_usuarios_ativos(db),
        total_chaves=usuario_repo.contar_chaves_total(db),
        requisicoes_hoje=usuario_repo.obter_consumo_sistema_dia(db, date.today()),
    )


# ── Gestão de Usuários ─────────────────────────────────────────────────────

@router.get(
    "/usuarios",
    response_model=list[UsuarioDetalhado],
    summary="Listar todos os usuários",
)
def listar_usuarios(
    admin: Usuario = Depends(requer_admin),
    db: Session = Depends(get_db),
):
    usuarios = usuario_repo.listar_todos_usuarios(db)
    return [UsuarioDetalhado.model_validate(u) for u in usuarios]


@router.post(
    "/usuarios",
    response_model=UsuarioDetalhado,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo usuário",
)
def criar_usuario(
    entrada: CriarUsuarioEntrada,
    admin: Usuario = Depends(requer_admin),
    db: Session = Depends(get_db),
):
    # Validar email único
    email_normalizado = entrada.email.strip().lower()
    if usuario_repo.buscar_por_email(db, email_normalizado):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado.",
        )

    # Criar usuário
    senha_hash = auth_service.hash_senha(entrada.senha)
    usuario = usuario_repo.criar_usuario(db, entrada.nome, email_normalizado, senha_hash)

    # Atualizar perfil e limites
    usuario_repo.atualizar_perfil_usuario(db, usuario.id, entrada.perfil)
    usuario_repo.atualizar_limites_usuario(
        db, usuario.id, entrada.limite_diario, entrada.limite_mensal
    )

    # Recarregar para pegar valores atualizados
    db.refresh(usuario)
    return UsuarioDetalhado.model_validate(usuario)


@router.put(
    "/usuarios/{usuario_id}",
    response_model=UsuarioDetalhado,
    summary="Atualizar usuário",
)
def atualizar_usuario(
    usuario_id: int,
    entrada: AtualizarUsuarioEntrada,
    admin: Usuario = Depends(requer_admin),
    db: Session = Depends(get_db),
):
    # Verificar se usuário existe
    usuario = usuario_repo.buscar_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    # Atualizar dados
    usuario_repo.atualizar_usuario(
        db, usuario_id, entrada.nome, entrada.email, entrada.perfil, entrada.ativo
    )

    if entrada.limite_diario is not None and entrada.limite_mensal is not None:
        usuario_repo.atualizar_limites_usuario(
            db, usuario_id, entrada.limite_diario, entrada.limite_mensal
        )

    # Recarregar
    db.refresh(usuario)
    return UsuarioDetalhado.model_validate(usuario)


@router.post(
    "/usuarios/{usuario_id}/resetar-senha",
    response_model=dict,
    summary="Resetar senha de usuário",
)
def resetar_senha_usuario(
    usuario_id: int,
    entrada: ResetarSenhaEntrada,
    admin: Usuario = Depends(requer_admin),
    db: Session = Depends(get_db),
):
    # Verificar se usuário existe
    usuario = usuario_repo.buscar_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    # Resetar senha
    senha_hash = auth_service.hash_senha(entrada.senha)
    usuario_repo.atualizar_senha_usuario(db, usuario_id, senha_hash)
    usuario_repo.revogar_refresh_tokens_usuario(db, usuario_id)

    return {"mensagem": f"Senha resetada para o usuário {usuario.nome}."}


@router.post(
    "/usuarios/{usuario_id}/toggle-status",
    response_model=UsuarioDetalhado,
    summary="Ativar/desativar usuário",
)
def toggle_status_usuario(
    usuario_id: int,
    admin: Usuario = Depends(requer_admin),
    db: Session = Depends(get_db),
):
    # Verificar se usuário existe
    usuario = usuario_repo.buscar_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    # Impedir que admin desative a si mesmo
    if usuario_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode desativar sua própria conta.",
        )

    # Toggle status
    usuario_repo.toggle_status_usuario(db, usuario_id)

    # Recarregar
    db.refresh(usuario)
    return UsuarioDetalhado.model_validate(usuario)


@router.delete(
    "/usuarios/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir usuário (soft delete)",
)
def excluir_usuario(
    usuario_id: int,
    admin: Usuario = Depends(requer_admin),
    db: Session = Depends(get_db),
):
    # Verificar se usuário existe
    usuario = usuario_repo.buscar_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    # Impedir que admin exclua a si mesmo
    if usuario_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode excluir sua própria conta.",
        )

    # Desativar usuário (soft delete)
    usuario_repo.toggle_status_usuario(db, usuario_id)

    return None
