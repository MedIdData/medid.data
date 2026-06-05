"""
Motor de Análise de Risco - Score Único de Risco de Glosa

Score de 0-100:
- Quanto MAIOR o score, MAIOR o risco de glosa
- Quanto MENOR o score, MENOR o risco de glosa

Faixas:
  0-20  = MUITO BAIXO
 21-40  = BAIXO
 41-60  = MÉDIO
 61-80  = ALTO
 81-100 = CRÍTICO
"""
from sqlalchemy.orm import Session
from typing import List

from app.repositories import analise_repo
from app.schemas.analise import AnaliseEntrada, AnaliseResultado, Situacao


def _normalizar(texto: str) -> str:
    """Normaliza texto para comparação (lowercase, sem acentos)."""
    import unicodedata
    if not texto:
        return ""
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ascii', 'ignore').decode('ascii')
    return texto.lower().strip()


def _classificar_score(score: int) -> str:
    """Retorna classificação textual do score."""
    if score <= 20:
        return "MUITO BAIXO"
    elif score <= 40:
        return "BAIXO"
    elif score <= 60:
        return "MÉDIO"
    elif score <= 80:
        return "ALTO"
    else:
        return "CRÍTICO"


def analisar(db: Session, entrada: AnaliseEntrada) -> AnaliseResultado:
    """
    Analisa risco de glosa e retorna score único de 0-100.

    Lógica:
    - Começa com score 0 (sem risco)
    - Cada problema ADICIONA pontos ao score
    - Score máximo: 100
    """

    motivos: List[str] = []
    score_total = 0

    # ──────────────────────────────────────────────────────────────
    # DIMENSÃO 1: MEDICAMENTO (+40 pts se não encontrado)
    # ──────────────────────────────────────────────────────────────

    med_row = analise_repo.buscar_medicamento_para_analise(
        db, entrada.medicamento
    )

    if not med_row:
        score_total += 40
        motivos.append(f"⚠️ Medicamento '{entrada.medicamento}' não encontrado na base ANVISA")
    elif med_row.get('situacao_registro', '').upper() != 'ATIVO':
        score_total += 35
        motivos.append(f"⚠️ Medicamento com registro INATIVO na ANVISA")

    # ──────────────────────────────────────────────────────────────
    # DIMENSÃO 2: PREÇO (+25 pts se muito acima)
    # ──────────────────────────────────────────────────────────────

    if med_row:
        pf = float(med_row.get('pf')) if med_row.get('pf') else None
        pmc = float(med_row.get('pmc')) if med_row.get('pmc') else None
        pmvg = float(med_row.get('pmvg')) if med_row.get('pmvg') else None

        # Compara com PMC (preço máximo ao consumidor)
        if pmc and entrada.preco_informado > pmc:
            variacao_pct = ((entrada.preco_informado - pmc) / pmc) * 100

            if variacao_pct > 50:
                score_total += 25
                motivos.append(f"⚠️ Preço informado R$ {entrada.preco_informado:.2f} está {variacao_pct:.0f}% acima do PMC (R$ {pmc:.2f})")
            elif variacao_pct > 20:
                score_total += 15
                motivos.append(f"⚠️ Preço informado R$ {entrada.preco_informado:.2f} está {variacao_pct:.0f}% acima do PMC (R$ {pmc:.2f})")
            elif variacao_pct > 10:
                score_total += 8
                motivos.append(f"ℹ️ Preço informado R$ {entrada.preco_informado:.2f} está {variacao_pct:.0f}% acima do PMC (R$ {pmc:.2f})")

    # ──────────────────────────────────────────────────────────────
    # DIMENSÃO 3: CID-10 (+15 pts se ausente, +10 se inválido)
    # ──────────────────────────────────────────────────────────────

    if not entrada.cid or not entrada.cid.strip():
        score_total += 15
        motivos.append("⚠️ CID-10 não informado")
    else:
        cid_row = analise_repo.buscar_cid(db, entrada.cid)
        if not cid_row:
            score_total += 10
            motivos.append(f"⚠️ CID-10 '{entrada.cid}' não encontrado na base")

    # ──────────────────────────────────────────────────────────────
    # DIMENSÃO 4: PROCEDIMENTO SIGTAP (+10 pts se ausente)
    # ──────────────────────────────────────────────────────────────

    if not entrada.procedimento or not entrada.procedimento.strip():
        score_total += 10
        motivos.append("⚠️ Código SIGTAP não informado")
    else:
        proc_row = analise_repo.buscar_procedimento(db, entrada.procedimento)
        if not proc_row:
            score_total += 8
            motivos.append(f"⚠️ Procedimento SIGTAP '{entrada.procedimento}' não encontrado")

    # ──────────────────────────────────────────────────────────────
    # DIMENSÃO 5: QUANTIDADE (+10 pts se excessiva)
    # ──────────────────────────────────────────────────────────────

    if entrada.quantidade > 10:
        score_total += 10
        motivos.append(f"⚠️ Quantidade informada ({entrada.quantidade}) acima do padrão (máx 10)")
    elif entrada.quantidade > 5:
        score_total += 5
        motivos.append(f"ℹ️ Quantidade informada ({entrada.quantidade}) acima do comum (padrão: 1-5)")

    # ──────────────────────────────────────────────────────────────
    # SCORE FINAL
    # ──────────────────────────────────────────────────────────────

    # Limita a 100
    score_final = min(score_total, 100)

    # Se não há motivos, tudo OK
    if not motivos:
        motivos.append("✓ Nenhuma inconsistência detectada")

    # Classificação
    classificacao = _classificar_score(score_final)

    # Monta resposta no formato antigo (compatibilidade)
    return AnaliseResultado(
        aderente=(score_final <= 40),
        pontuacao_aderencia=100 - score_final,  # Inverte para compatibilidade
        pontuacao_risco=score_final,            # SCORE PRINCIPAL
        potencial_glosa=classificacao,
        classificacao_risco=classificacao,
        motivos=motivos,

        # Campos legacy (mantém para não quebrar schema)
        analise_tratamento={"situacao": Situacao.NAO_INFORMADO, "motivo": ""},
        analise_cid={"situacao": Situacao.NAO_INFORMADO, "motivo": ""},
        analise_procedimento={"situacao": Situacao.NAO_INFORMADO, "motivo": ""},
        analise_cid_procedimento={"situacao": Situacao.NAO_INFORMADO, "motivo": ""},
        analise_preco={"situacao": Situacao.NAO_INFORMADO, "preco_informado": entrada.preco_informado, "motivo": ""},
        analise_quantidade={"situacao": Situacao.NAO_INFORMADO, "quantidade_informada": entrada.quantidade, "motivo": ""},

        medicamento_encontrado=med_row.get('nome_produto') if med_row else None,
        numero_registro=med_row.get('numero_registro') if med_row else None,
        situacao_anvisa=med_row.get('situacao_registro') if med_row else None,
    )
