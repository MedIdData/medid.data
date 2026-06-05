"""
Repositório de usuários, tokens, consumo e auditoria.
"""
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import text, func
from sqlalchemy.orm import Session

from app.models.usuario import Usuario, RefreshToken
from app.models.empresa import Plano
from app.models.chave_acesso import ChaveAcesso
from app.models.auditoria import ConsumoDiario, AuditoriaRequisicao


# ── Usuário ───────────────────────────────────────────────────────────────

def buscar_por_email(db: Session, email: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(
        Usuario.email == email.strip().lower()
    ).first()


def buscar_por_id(db: Session, usuario_id: int) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def criar_usuario(db: Session, nome: str, email: str, senha_hash: str) -> Usuario:
    usuario = Usuario(
        nome=nome.strip(),
        email=email.strip().lower(),
        senha_hash=senha_hash,
        perfil="CLIENTE",
        ativo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


# ── Refresh Tokens ─────────────────────────────────────────────────────────

def salvar_refresh_token(
    db: Session,
    usuario_id: int,
    token_hash: str,
    expira_em: datetime,
) -> None:
    token = RefreshToken(
        usuario_id=usuario_id,
        token_hash=token_hash,
        expira_em=expira_em,
        revogado=False,
    )
    db.add(token)
    db.commit()


def buscar_refresh_token(db: Session, token_hash: str) -> Optional[RefreshToken]:
    return db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revogado == False,
    ).first()


def revogar_refresh_tokens_usuario(db: Session, usuario_id: int) -> None:
    db.query(RefreshToken).filter(
        RefreshToken.usuario_id == usuario_id
    ).update({"revogado": True})
    db.commit()


# ── Plano / Limites ────────────────────────────────────────────────────────

def obter_plano_usuario(db: Session, usuario: Usuario) -> Optional[Plano]:
    if usuario.empresa_id:
        from app.models.empresa import Empresa
        empresa = db.query(Empresa).filter(Empresa.id == usuario.empresa_id).first()
        if empresa and empresa.plano_id:
            return db.query(Plano).filter(Plano.id == empresa.plano_id).first()
    return db.query(Plano).filter(Plano.nome == "Gratuito").first()


# ── Consumo ────────────────────────────────────────────────────────────────

def obter_consumo_diario(db: Session, usuario_id: int, data: date, modulo: str) -> int:
    row = db.query(ConsumoDiario).filter(
        ConsumoDiario.usuario_id == usuario_id,
        ConsumoDiario.data_referencia == data,
        ConsumoDiario.modulo == modulo,
    ).first()
    return row.total_consultas if row else 0


def obter_consumo_total_dia(db: Session, usuario_id: int, data: date) -> int:
    sql = text("""
        SELECT coalesce(sum(total_consultas), 0)
        FROM consumo_diario
        WHERE usuario_id = :uid AND data_referencia = :data
    """)
    return db.execute(sql, {"uid": usuario_id, "data": data}).scalar_one()


def obter_consumo_mensal(db: Session, usuario_id: int, ano: int, mes: int) -> int:
    sql = text("""
        SELECT coalesce(sum(total_consultas), 0)
        FROM consumo_diario
        WHERE usuario_id = :uid
          AND extract(year FROM data_referencia) = :ano
          AND extract(month FROM data_referencia) = :mes
    """)
    return db.execute(sql, {"uid": usuario_id, "ano": ano, "mes": mes}).scalar_one()


def obter_consumo_por_modulo(
    db: Session, usuario_id: int, data: date
) -> list[dict]:
    sql = text("""
        SELECT modulo, sum(total_consultas) AS total
        FROM consumo_diario
        WHERE usuario_id = :uid AND data_referencia = :data
        GROUP BY modulo
    """)
    rows = db.execute(sql, {"uid": usuario_id, "data": data}).mappings().fetchall()
    return [{"modulo": r["modulo"], "total": r["total"]} for r in rows]


def obter_consumo_por_modulo_mes(
    db: Session, usuario_id: int, ano: int, mes: int
) -> list[dict]:
    sql = text("""
        SELECT modulo, sum(total_consultas) AS total
        FROM consumo_diario
        WHERE usuario_id = :uid
          AND extract(year FROM data_referencia) = :ano
          AND extract(month FROM data_referencia) = :mes
        GROUP BY modulo
    """)
    rows = db.execute(sql, {"uid": usuario_id, "ano": ano, "mes": mes}).mappings().fetchall()
    return [{"modulo": r["modulo"], "total": r["total"]} for r in rows]


def incrementar_consumo(db: Session, usuario_id: int, data: date, modulo: str) -> None:
    sql = text("""
        INSERT INTO consumo_diario (usuario_id, data_referencia, modulo, total_consultas)
        VALUES (:uid, :data, :modulo, 1)
        ON CONFLICT (usuario_id, data_referencia, modulo)
        DO UPDATE SET total_consultas = consumo_diario.total_consultas + 1
    """)
    db.execute(sql, {"uid": usuario_id, "data": data, "modulo": modulo})
    db.commit()


# ── Auditoria ──────────────────────────────────────────────────────────────

def registrar_auditoria(
    db: Session,
    usuario_id: int,
    chave_acesso_id: Optional[int],
    canal: str,
    modulo: str,
    endpoint: str,
    metodo: str,
    parametros: Optional[dict],
    ip: Optional[str],
) -> None:
    registro = AuditoriaRequisicao(
        usuario_id=usuario_id,
        chave_acesso_id=chave_acesso_id,
        canal=canal,
        modulo=modulo,
        endpoint=endpoint,
        metodo=metodo,
        parametros_json=parametros,
        criado_em=datetime.now(timezone.utc),
    )
    db.add(registro)
    db.commit()


# ── Chave de Acesso ───────────────────────────────────────────────────────

def buscar_chave_ativa(db: Session, chave_hash: str) -> Optional[ChaveAcesso]:
    return db.query(ChaveAcesso).filter(
        ChaveAcesso.chave_hash == chave_hash,
        ChaveAcesso.ativa == True,
    ).first()


def listar_chaves_usuario(db: Session, usuario_id: int) -> list[ChaveAcesso]:
    return db.query(ChaveAcesso).filter(
        ChaveAcesso.usuario_id == usuario_id,
        ChaveAcesso.ativa == True,
    ).order_by(ChaveAcesso.criado_em.desc()).all()


def criar_chave_acesso(
    db: Session,
    usuario_id: int,
    nome: str,
    prefixo: str,
    chave_hash: str,
) -> ChaveAcesso:
    chave = ChaveAcesso(
        usuario_id=usuario_id,
        nome=nome,
        prefixo=prefixo,
        chave_hash=chave_hash,
        ativa=True,
    )
    db.add(chave)
    db.commit()
    db.refresh(chave)
    return chave


def revogar_chave_acesso(db: Session, chave_id: int, usuario_id: int) -> bool:
    chave = db.query(ChaveAcesso).filter(
        ChaveAcesso.id == chave_id,
        ChaveAcesso.usuario_id == usuario_id,
    ).first()
    if not chave:
        return False
    chave.ativa = False
    chave.revogada_em = datetime.now(timezone.utc)
    db.commit()
    return True


def buscar_chave_por_id(db: Session, chave_id: int, usuario_id: int) -> Optional[ChaveAcesso]:
    return db.query(ChaveAcesso).filter(
        ChaveAcesso.id == chave_id,
        ChaveAcesso.usuario_id == usuario_id,
    ).first()


# ── Atualização de Perfil ──────────────────────────────────────────────────

def atualizar_nome_usuario(db: Session, usuario_id: int, nome: str) -> None:
    db.query(Usuario).filter(Usuario.id == usuario_id).update({"nome": nome})
    db.commit()


def atualizar_senha_usuario(db: Session, usuario_id: int, senha_hash: str) -> None:
    db.query(Usuario).filter(Usuario.id == usuario_id).update({"senha_hash": senha_hash})
    db.commit()


# ── Funções Admin ──────────────────────────────────────────────────────────

def contar_usuarios(db: Session) -> int:
    """Conta total de usuários no sistema."""
    return db.query(Usuario).count()


def contar_usuarios_ativos(db: Session) -> int:
    """Conta usuários ativos."""
    return db.query(Usuario).filter(Usuario.ativo == True).count()


def contar_chaves_total(db: Session) -> int:
    """Conta total de chaves API ativas no sistema."""
    from datetime import datetime
    return db.query(ChaveAcesso).filter(
        ChaveAcesso.revogada_em.is_(None)
    ).count()


def obter_consumo_sistema_dia(db: Session, data: date) -> int:
    """Obtém consumo total do sistema em um dia."""
    result = db.query(func.sum(ConsumoDiario.total_consultas)).filter(
        ConsumoDiario.data_referencia == data
    ).scalar()
    return result or 0


def listar_todos_usuarios(db: Session) -> list[Usuario]:
    """Lista todos os usuários do sistema (admin)."""
    return db.query(Usuario).order_by(Usuario.criado_em.desc()).all()


def atualizar_usuario(
    db: Session,
    usuario_id: int,
    nome: str,
    email: str,
    perfil: str,
    ativo: bool
) -> None:
    """Atualiza dados de um usuário (admin)."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario:
        usuario.nome = nome
        usuario.email = email.strip().lower()
        usuario.perfil = perfil
        usuario.ativo = ativo
        db.commit()


def atualizar_perfil_usuario(db: Session, usuario_id: int, perfil: str) -> None:
    """Atualiza perfil do usuário."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario:
        usuario.perfil = perfil
        db.commit()


def atualizar_limites_usuario(
    db: Session,
    usuario_id: int,
    limite_diario: Optional[int],
    limite_mensal: Optional[int]
) -> None:
    """Atualiza limites diários e mensais do usuário. None = ilimitado."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario:
        usuario.limite_diario = limite_diario
        usuario.limite_mensal = limite_mensal
        db.commit()


def toggle_status_usuario(db: Session, usuario_id: int) -> None:
    """Ativa/desativa usuário."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario:
        usuario.ativo = not usuario.ativo
        db.commit()


# ── Detalhes Completos de Usuário (Admin) ─────────────────────────────────

def obter_estatisticas_usuario(db: Session, usuario_id: int) -> dict:
    """Obtém estatísticas completas de um usuário."""
    from datetime import date, timedelta
    
    hoje = date.today()
    semana_passada = hoje - timedelta(days=7)
    inicio_mes = date(hoje.year, hoje.month, 1)
    
    # Consumo hoje
    consumo_hoje = obter_consumo_total_dia(db, usuario_id, hoje)
    
    # Consumo semana
    sql_semana = text("""
        SELECT COALESCE(SUM(total_consultas), 0)
        FROM consumo_diario
        WHERE usuario_id = :uid AND data_referencia >= :inicio
    """)
    consumo_semana = db.execute(sql_semana, {"uid": usuario_id, "inicio": semana_passada}).scalar_one()
    
    # Consumo mês
    consumo_mes = obter_consumo_mensal(db, usuario_id, hoje.year, hoje.month)
    
    # Consumo total
    sql_total = text("""
        SELECT COALESCE(SUM(total_consultas), 0)
        FROM consumo_diario
        WHERE usuario_id = :uid
    """)
    consumo_total = db.execute(sql_total, {"uid": usuario_id}).scalar_one()
    
    # Consumo por módulo (mês atual)
    consumo_modulos = obter_consumo_por_modulo_mes(db, usuario_id, hoje.year, hoje.month)
    
    return {
        "consumo_hoje": consumo_hoje,
        "consumo_semana": consumo_semana,
        "consumo_mes": consumo_mes,
        "consumo_total": consumo_total,
        "consumo_por_modulo": consumo_modulos,
    }


def obter_historico_consumo_usuario(db: Session, usuario_id: int, limite: int = 50) -> list[dict]:
    """Obtém histórico detalhado de consumo."""
    sql = text("""
        SELECT 
            cd.data_referencia,
            cd.modulo,
            cd.total_consultas,
            'WEB' as origem
        FROM consumo_diario cd
        WHERE cd.usuario_id = :uid
        ORDER BY cd.data_referencia DESC, cd.modulo
        LIMIT :limite
    """)
    
    rows = db.execute(sql, {"uid": usuario_id, "limite": limite}).mappings().fetchall()
    return [dict(r) for r in rows]


def obter_auditoria_usuario(db: Session, usuario_id: int, limite: int = 50) -> list[dict]:
    """Obtém histórico de auditoria do usuário."""
    sql = text("""
        SELECT 
            ar.criado_em,
            ar.canal,
            ar.modulo,
            ar.endpoint,
            ar.metodo,
            ar.parametros_json
        FROM auditoria_requisicoes ar
        WHERE ar.usuario_id = :uid
        ORDER BY ar.criado_em DESC
        LIMIT :limite
    """)
    
    rows = db.execute(sql, {"uid": usuario_id, "limite": limite}).mappings().fetchall()
    return [dict(r) for r in rows]


def obter_ultimo_login(db: Session, usuario_id: int) -> Optional[datetime]:
    """Obtém data do último login do usuário."""
    sql = text("""
        SELECT MAX(criado_em) as ultimo_login
        FROM refresh_tokens
        WHERE usuario_id = :uid
    """)
    result = db.execute(sql, {"uid": usuario_id}).scalar_one()
    return result


def obter_ultimo_uso_api(db: Session, usuario_id: int) -> Optional[datetime]:
    """Obtém data do último uso via API."""
    sql = text("""
        SELECT MAX(ultimo_uso_em) as ultimo_uso
        FROM chaves_acesso
        WHERE usuario_id = :uid AND ultimo_uso_em IS NOT NULL
    """)
    result = db.execute(sql, {"uid": usuario_id}).scalar_one()
    return result


def obter_consumo_por_tipo(db: Session, usuario_id: int) -> dict:
    """
    Obtém consumo dividido por tipo (WEB vs API).

    NOTA: auditoria_requisicoes está incompleta. Usando consumo_diario como base.
    Por enquanto, mostra total sem divisão precisa.
    TODO: Implementar rastreamento real de origem (WEB vs API) no consumo_diario.
    """
    from datetime import date

    hoje = date.today()

    # Total do mês (fonte confiável)
    consumo_mes = obter_consumo_mensal(db, usuario_id, hoje.year, hoje.month)

    # Verificar se usuário tem chaves API
    chaves = listar_chaves_usuario(db, usuario_id)

    if not chaves or len(chaves) == 0:
        # Sem chaves API = 100% WEB
        return {"WEB": consumo_mes, "API": 0}

    # Com chaves API, verificar se foram usadas este mês
    chaves_usadas_mes = [
        c for c in chaves
        if c.ultimo_uso_em and
           c.ultimo_uso_em.year == hoje.year and
           c.ultimo_uso_em.month == hoje.month
    ]

    if chaves_usadas_mes:
        # Tem chave E usou este mês
        # Estimativa: 60% API, 40% WEB (conservador)
        api_consumo = int(consumo_mes * 0.6)
        web_consumo = consumo_mes - api_consumo
        return {"WEB": web_consumo, "API": api_consumo}
    else:
        # Tem chave mas não usou este mês = 100% WEB
        return {"WEB": consumo_mes, "API": 0}
