"""
Router de debug temporário para diagnosticar erros em produção.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories import usuario_repo
from datetime import date
import traceback

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/test-admin-data")
async def test_admin_data(db: Session = Depends(get_db)):
    """Testa a lógica da página admin para identificar erro."""
    try:
        resultado = {}

        # Estatísticas
        resultado["step_1"] = "Buscando estatísticas..."
        total_usuarios = usuario_repo.contar_usuarios(db)
        resultado["total_usuarios"] = total_usuarios

        resultado["step_2"] = "Buscando usuários ativos..."
        usuarios_ativos = usuario_repo.contar_usuarios_ativos(db)
        resultado["usuarios_ativos"] = usuarios_ativos

        resultado["step_3"] = "Buscando total de chaves..."
        total_chaves = usuario_repo.contar_chaves_total(db)
        resultado["total_chaves"] = total_chaves

        resultado["step_4"] = "Buscando requisições hoje..."
        requisicoes_hoje = usuario_repo.obter_consumo_sistema_dia(db, date.today())
        resultado["requisicoes_hoje"] = requisicoes_hoje

        resultado["step_5"] = "Listando todos os usuários..."
        usuarios = usuario_repo.listar_todos_usuarios(db)
        resultado["usuarios_count"] = len(usuarios)
        resultado["usuarios"] = [
            {
                "id": u.id,
                "email": u.email,
                "perfil": u.perfil,
                "limite_diario": u.limite_diario,
                "limite_mensal": u.limite_mensal,
            }
            for u in usuarios
        ]

        resultado["step_6"] = "Mapeando chaves por usuário..."
        chaves_por_usuario = {}
        for u in usuarios:
            chaves = usuario_repo.listar_chaves_usuario(db, u.id)
            chaves_por_usuario[u.id] = len(chaves)
        resultado["chaves_por_usuario"] = chaves_por_usuario

        resultado["step_7"] = "Calculando consumo..."
        consumo_por_usuario = {}
        hoje = date.today()

        for u in usuarios:
            consumo_hoje = usuario_repo.obter_consumo_total_dia(db, u.id, hoje)

            if u.limite_diario and u.limite_diario > 0:
                percentual_dia = (consumo_hoje / u.limite_diario) * 100
            else:
                percentual_dia = 0

            consumo_mes = usuario_repo.obter_consumo_mensal(db, u.id, hoje.year, hoje.month)

            if u.limite_mensal and u.limite_mensal > 0:
                percentual_mes = (consumo_mes / u.limite_mensal) * 100
            else:
                percentual_mes = 0

            consumo_por_usuario[u.id] = {
                "consumo_hoje": consumo_hoje,
                "percentual_dia": min(percentual_dia, 100),
                "consumo_mes": consumo_mes,
                "percentual_mes": min(percentual_mes, 100),
            }

        resultado["consumo_por_usuario"] = consumo_por_usuario
        resultado["status"] = "SUCCESS"

        return JSONResponse(content=resultado, status_code=200)

    except Exception as e:
        error_info = {
            "status": "ERROR",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
        }
        return JSONResponse(content=error_info, status_code=500)


@router.get("/check-imports")
async def check_imports():
    """Verifica se todos os imports estão funcionando."""
    try:
        resultado = {"imports": {}}

        # Testar imports
        resultado["imports"]["usuario_repo"] = "OK"

        from app.repositories import usuario_repo as ur
        resultado["imports"]["usuario_repo_direct"] = "OK"

        # Verificar funções
        funcs = dir(ur)
        resultado["available_functions"] = [f for f in funcs if not f.startswith('_')]

        # Verificar funções específicas
        resultado["has_contar_usuarios"] = hasattr(ur, "contar_usuarios")
        resultado["has_contar_usuarios_ativos"] = hasattr(ur, "contar_usuarios_ativos")
        resultado["has_contar_chaves_total"] = hasattr(ur, "contar_chaves_total")
        resultado["has_obter_consumo_sistema_dia"] = hasattr(ur, "obter_consumo_sistema_dia")
        resultado["has_listar_todos_usuarios"] = hasattr(ur, "listar_todos_usuarios")

        resultado["status"] = "SUCCESS"
        return JSONResponse(content=resultado, status_code=200)

    except Exception as e:
        error_info = {
            "status": "ERROR",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
        }
        return JSONResponse(content=error_info, status_code=500)


@router.get("/check-data-counts")
async def check_data_counts(db: Session = Depends(get_db)):
    """Verifica a quantidade de dados em todas as tabelas."""
    from sqlalchemy import text
    try:
        resultado = {}

        # Medicamentos
        anvisa_total = db.execute(text("SELECT COUNT(*) FROM medicamentos_anvisa")).scalar()
        anvisa_ativos = db.execute(text("SELECT COUNT(*) FROM medicamentos_anvisa WHERE situacao_registro = 'Ativo'")).scalar()
        cmed_total = db.execute(text("SELECT COUNT(*) FROM medicamentos_cmed")).scalar()
        dcb_total = db.execute(text("SELECT COUNT(*) FROM dcb")).scalar()

        resultado["medicamentos"] = {
            "anvisa_total": anvisa_total,
            "anvisa_ativos": anvisa_ativos,
            "cmed_total": cmed_total,
            "dcb_total": dcb_total
        }

        # CID-10
        cid_cat = db.execute(text("SELECT COUNT(*) FROM cid10_categorias")).scalar()
        cid_sub = db.execute(text("SELECT COUNT(*) FROM cid10_subcategorias")).scalar()

        resultado["cid10"] = {
            "categorias": cid_cat,
            "subcategorias": cid_sub
        }

        # SIGTAP
        sigtap_proc = db.execute(text("SELECT COUNT(*) FROM sigtap_procedimentos")).scalar()
        sigtap_grupos = db.execute(text("SELECT COUNT(*) FROM sigtap_grupos")).scalar()
        sigtap_cid = db.execute(text("SELECT COUNT(*) FROM sigtap_procedimento_cid")).scalar()

        resultado["sigtap"] = {
            "procedimentos": sigtap_proc,
            "grupos": sigtap_grupos,
            "procedimento_cid": sigtap_cid
        }

        # Análise
        resultado["analise"] = {
            "anvisa_ok": anvisa_total >= 30000,
            "cmed_ok": cmed_total >= 20000,
            "cid_ok": cid_cat >= 2000 and cid_sub >= 12000,
            "sigtap_ok": sigtap_proc >= 4000 and sigtap_cid >= 160000
        }

        resultado["status"] = "SUCCESS"

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
