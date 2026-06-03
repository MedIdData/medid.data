"""
Serviço de busca de medicamentos.

Camada entre o router e o repositório. Formata os dados brutos do banco
no schema de saída e aplica regras de negócio (ex: tarja unificada ANVISA+CMED).
"""
from sqlalchemy.orm import Session
from typing import Optional

from app.repositories import medicamento_repo
from app.schemas.medicamento import (
    MedicamentoBuscaResposta,
    MedicamentoItem,
    MedicamentoDetalhe,
)


def _tarja_display(tarja_anvisa: str | None, cmed_tarja: str | None) -> str | None:
    """Usa tarja do CMED quando disponível (mais atualizada), cai para ANVISA."""
    t = cmed_tarja or tarja_anvisa
    if not t:
        return None
    t = str(t).strip().upper()
    if t in ("N", "NAO", "NÃO", "SEM TARJA"):
        return "Sem tarja"
    if "VERMELHA" in t or t == "V":
        return "Tarja Vermelha"
    if "PRETA" in t or t == "P":
        return "Tarja Preta"
    if "AMARELA" in t or t == "A":
        return "Tarja Amarela"
    return t.capitalize() if t else None


def _indicacoes_lista(indicacoes_raw: str | None) -> list[str]:
    if not indicacoes_raw:
        return []
    return [i.strip() for i in indicacoes_raw.replace(";", ",").split(",") if i.strip()][:10]


def _row_para_item(row: dict, score: float = 0.0) -> MedicamentoItem:
    tarja = _tarja_display(row.get("tarja"), row.get("cmed_tarja"))
    fabricante = row.get("laboratorio") or row.get("empresa_detentora")

    # Preço: prioriza CMED. Remove zeros (armazenados como 0.0 quando sem preço)
    def preco(val) -> float | None:
        if val and float(val) > 0:
            return round(float(val), 2)
        return None

    return MedicamentoItem(
        id=row["id"],
        numero_registro=row.get("numero_registro"),
        medicamento=row.get("nome_produto"),
        principio_ativo=row.get("principio_ativo"),
        fabricante=fabricante,
        apresentacao=row.get("apresentacao"),
        dosagem=None,
        situacao_anvisa=row.get("situacao_registro"),
        categoria_regulatoria=row.get("categoria_regulatoria"),
        classe_terapeutica=row.get("classe_terapeutica"),
        tarja=tarja,
        pf=preco(row.get("pf")),
        pmc=preco(row.get("pmc")),
        pmvg=preco(row.get("pmvg")),
        indicacoes=_indicacoes_lista(row.get("indicacoes")),
        score_relevancia=round(float(score or row.get("score", 0)), 4),
    )


def buscar(
    db: Session,
    q: str,
    apenas_ativos: bool = True,
    pagina: int = 1,
    limite: int = 20,
) -> MedicamentoBuscaResposta:
    rows, total, sugestao = medicamento_repo.buscar_medicamentos(
        db, q, apenas_ativos, pagina, limite
    )
    resultados = [_row_para_item(r) for r in rows]
    return MedicamentoBuscaResposta(
        total=total,
        pagina=pagina,
        limite=limite,
        termo=q,
        resultados=resultados,
        sugestao=sugestao,
    )


def obter_por_id(db: Session, medicamento_id: int) -> MedicamentoDetalhe | None:
    row = medicamento_repo.obter_por_id(db, medicamento_id)
    if not row:
        return None

    def preco(val) -> float | None:
        if val and float(val) > 0:
            return round(float(val), 2)
        return None

    return MedicamentoDetalhe(
        id=row["id"],
        numero_registro=row.get("numero_registro"),
        medicamento=row.get("nome_produto"),
        principio_ativo=row.get("principio_ativo"),
        fabricante=row.get("laboratorio") or row.get("empresa_detentora"),
        apresentacao=row.get("apresentacao"),
        categoria_regulatoria=row.get("categoria_regulatoria"),
        classe_terapeutica=row.get("classe_terapeutica"),
        situacao_anvisa=row.get("situacao_registro"),
        tarja=_tarja_display(row.get("tarja"), None),
        forma_fisica=row.get("forma_fisica"),
        sinonimos=row.get("sinonimos"),
        substancias=row.get("substancias"),
        codigo_atc=row.get("codigo_atc"),
        indicacoes=row.get("indicacoes"),
        pf=preco(row.get("pf")),
        pmc=preco(row.get("pmc")),
        pmvg=preco(row.get("pmvg")),
        pf_12=preco(row.get("pf_12")),
        pmc_12=preco(row.get("pmc_12")),
        pmvg_12=preco(row.get("pmvg_12")),
        pf_17=preco(row.get("pf_17")),
        pmc_17=preco(row.get("pmc_17")),
        pmvg_17=preco(row.get("pmvg_17")),
        pf_18=preco(row.get("pf_18")),
        pmc_18=preco(row.get("pmc_18")),
        pmvg_18=preco(row.get("pmvg_18")),
    )
