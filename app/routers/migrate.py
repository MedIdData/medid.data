"""
Endpoint temporário para aplicar migrations em produção.
REMOVER APÓS USO!
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/migrate", tags=["migrate"])


@router.post("/apply-010")
async def apply_migration_010(db: Session = Depends(get_db)):
    """
    Aplica migration 010: remove sistema de planos, torna limites obrigatórios.
    ATENÇÃO: Este endpoint deve ser removido após uso!
    """
    try:
        resultado = {"steps": []}

        # Passo 1: Definir limites para usuários não-admin
        resultado["steps"].append("Definindo limites para usuários não-admin...")
        result = db.execute(text("""
            UPDATE usuarios
            SET limite_diario = COALESCE(limite_diario, 20),
                limite_mensal = COALESCE(limite_mensal, 100)
            WHERE perfil NOT IN ('ADMINISTRADOR', 'ADMIN')
        """))
        resultado["step_1_usuarios_atualizados"] = result.rowcount

        # Passo 2: Definir limites ilimitados para admins
        resultado["steps"].append("Definindo limites ilimitados para admins...")
        result = db.execute(text("""
            UPDATE usuarios
            SET limite_diario = 0, limite_mensal = 0
            WHERE perfil IN ('ADMINISTRADOR', 'ADMIN')
        """))
        resultado["step_2_admins_atualizados"] = result.rowcount

        # Passo 3: Desativar todos os planos
        resultado["steps"].append("Desativando todos os planos...")
        result = db.execute(text("UPDATE planos SET ativo = false"))
        resultado["step_3_planos_desativados"] = result.rowcount

        # Passo 4: Tornar limites obrigatórios
        resultado["steps"].append("Tornando limites obrigatórios (NOT NULL)...")
        try:
            db.execute(text("""
                ALTER TABLE usuarios
                ALTER COLUMN limite_diario SET NOT NULL,
                ALTER COLUMN limite_diario SET DEFAULT 20
            """))
            resultado["step_4a_limite_diario"] = "NOT NULL aplicado"
        except Exception as e:
            resultado["step_4a_limite_diario"] = f"Erro ou já aplicado: {str(e)}"

        try:
            db.execute(text("""
                ALTER TABLE usuarios
                ALTER COLUMN limite_mensal SET NOT NULL,
                ALTER COLUMN limite_mensal SET DEFAULT 100
            """))
            resultado["step_4b_limite_mensal"] = "NOT NULL aplicado"
        except Exception as e:
            resultado["step_4b_limite_mensal"] = f"Erro ou já aplicado: {str(e)}"

        db.commit()
        resultado["status"] = "SUCCESS"
        resultado["message"] = "Migration 010 aplicada com sucesso!"

        # Verificar estado final
        usuarios = db.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN limite_diario = 0 AND limite_mensal = 0 THEN 1 END) as ilimitados,
                   COUNT(CASE WHEN limite_diario > 0 AND limite_mensal > 0 THEN 1 END) as com_limites
            FROM usuarios
        """)).fetchone()

        resultado["usuarios_total"] = usuarios[0]
        resultado["usuarios_ilimitados"] = usuarios[1]
        resultado["usuarios_com_limites"] = usuarios[2]

        return JSONResponse(content=resultado, status_code=200)

    except Exception as e:
        db.rollback()
        import traceback
        error_info = {
            "status": "ERROR",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
        }
        return JSONResponse(content=error_info, status_code=500)
