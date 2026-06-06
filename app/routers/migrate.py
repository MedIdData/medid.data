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


@router.post("/limpar-usuarios")
async def limpar_usuarios(db: Session = Depends(get_db)):
    """
    Remove todos os usuários exceto admin@mediddata.com.
    ATENÇÃO: Este endpoint deve ser removido após uso!
    """
    try:
        resultado = {"steps": []}

        # 1. Identificar admin principal
        admin = db.execute(text("""
            SELECT id, email FROM usuarios
            WHERE email = 'admin@mediddata.com'
            LIMIT 1
        """)).fetchone()

        if not admin:
            return JSONResponse(
                content={"status": "ERROR", "message": "Admin principal não encontrado!"},
                status_code=404
            )

        admin_id = admin[0]
        resultado["admin_email"] = admin[1]
        resultado["admin_id"] = admin_id

        # 2. Listar usuários que serão removidos
        usuarios_remover = db.execute(text("""
            SELECT id, email, perfil FROM usuarios
            WHERE id != :admin_id
            ORDER BY id
        """), {"admin_id": admin_id}).fetchall()

        resultado["usuarios_a_remover"] = [
            {"id": u[0], "email": u[1], "perfil": u[2]}
            for u in usuarios_remover
        ]
        resultado["total_usuarios_a_remover"] = len(usuarios_remover)

        # 3. Remover dados relacionados
        resultado["steps"].append("Removendo consumo diário...")
        result = db.execute(text("DELETE FROM consumo_diario WHERE usuario_id != :admin_id"), {"admin_id": admin_id})
        resultado["consumo_diario_removido"] = result.rowcount

        resultado["steps"].append("Removendo auditoria...")
        result = db.execute(text("DELETE FROM auditoria_requisicoes"))
        resultado["auditoria_removida"] = result.rowcount

        resultado["steps"].append("Removendo chaves API...")
        result = db.execute(text("DELETE FROM chaves_acesso"))
        resultado["chaves_removidas"] = result.rowcount

        resultado["steps"].append("Removendo refresh tokens...")
        result = db.execute(text("DELETE FROM refresh_tokens WHERE usuario_id != :admin_id"), {"admin_id": admin_id})
        resultado["tokens_removidos"] = result.rowcount

        resultado["steps"].append("Removendo convites...")
        result = db.execute(text("DELETE FROM convites_usuario"))
        resultado["convites_removidos"] = result.rowcount

        resultado["steps"].append("Removendo usuários...")
        result = db.execute(text("DELETE FROM usuarios WHERE id != :admin_id"), {"admin_id": admin_id})
        resultado["usuarios_removidos"] = result.rowcount

        db.commit()
        resultado["status"] = "SUCCESS"
        resultado["message"] = f"Limpeza concluída! Apenas {admin[1]} permanece."

        # Verificar estado final
        total = db.execute(text("SELECT COUNT(*) FROM usuarios")).scalar()
        resultado["usuarios_restantes"] = total

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


@router.post("/reimportar-medicamentos")
async def reimportar_medicamentos(db: Session = Depends(get_db)):
    """
    Reimporta todos os medicamentos ANVISA e CMED.
    ATENÇÃO: Pode levar alguns minutos!
    """
    try:
        from sqlalchemy import text
        import subprocess
        import os
        
        resultado = {"steps": []}
        
        # Verificar se arquivos existem
        arquivos_necessarios = [
            "dados/anvisa_medicamentos.csv",
            "dados/anvisa_consulta_medicamentos.csv",
            "dados/CMED_PF.csv",
            "dados/CMED_PMVG.csv"
        ]
        
        for arq in arquivos_necessarios:
            if not os.path.exists(arq):
                return JSONResponse(
                    content={
                        "status": "ERROR",
                        "message": f"Arquivo não encontrado: {arq}",
                        "sugestao": "Faça upload dos arquivos para a pasta dados/"
                    },
                    status_code=404
                )
        
        resultado["steps"].append("Arquivos verificados - OK")
        
        # Executar scripts de importação
        resultado["steps"].append("Executando importação ANVISA...")
        try:
            result = subprocess.run(
                ["python3", "scripts/importar_anvisa.py"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                resultado["anvisa_import"] = "SUCCESS"
            else:
                resultado["anvisa_import"] = f"ERROR: {result.stderr}"
        except Exception as e:
            resultado["anvisa_import"] = f"ERROR: {str(e)}"
        
        resultado["steps"].append("Executando importação CMED...")
        try:
            result = subprocess.run(
                ["python3", "scripts/importar_cmed.py"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                resultado["cmed_import"] = "SUCCESS"
            else:
                resultado["cmed_import"] = f"ERROR: {result.stderr}"
        except Exception as e:
            resultado["cmed_import"] = f"ERROR: {str(e)}"
        
        # Contar registros finais
        anvisa_total = db.execute(text("SELECT COUNT(*) FROM medicamentos_anvisa")).scalar()
        cmed_total = db.execute(text("SELECT COUNT(*) FROM medicamentos_cmed")).scalar()
        
        resultado["contagem_final"] = {
            "anvisa": anvisa_total,
            "cmed": cmed_total
        }
        
        resultado["status"] = "SUCCESS"
        resultado["message"] = "Reimportação concluída!"
        
        return JSONResponse(content=resultado, status_code=200)
        
    except Exception as e:
        import traceback
        error_info = {
            "status": "ERROR",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
        }
        return JSONResponse(content=error_info, status_code=500)
