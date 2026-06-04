"""
Motor de Análise de Risco  -  9 dimensões.

O potencial de glosa NÃO representa uma glosa real nem uma decisão de operadora.
É um indicador preventivo baseado em inconsistências entre os dados informados
e as bases ANVISA, CMED, CID-10 e SIGTAP.
"""
import re
import unicodedata
from typing import Optional
from sqlalchemy.orm import Session

from app.repositories import analise_repo
from app.schemas.analise import (
    AnaliseEntrada, AnaliseResultado,
    AnaliseTratamento, AnaliseCid, AnaliseProced, AnalisePreco, AnaliseQuantidade,
    Situacao,
)


# ── Mapeamentos clínicos ───────────────────────────────────────────────────

# Palavras-chave de tratamento esperadas para cada classe terapêutica
_CLASSE_TRATAMENTO: dict[str, list[str]] = {
    "ANALGESICO": ["dor", "cefaleia", "migranea", "febre", "enxaqueca", "algesia", "dores"],
    "ANESTESICO": ["cirurgia", "anestesia", "sedacao", "procedimento"],
    "ANTIBIOTICO": ["infeccao", "bacteriana", "pneumonia", "sinusite", "bronquite", "itu", "sepse", "abscesso"],
    "ANTIFUNGIC": ["candidose", "micose", "fungo", "funqica"],
    "ANTIVIRAL": ["viral", "herpes", "influenza", "gripe", "covid", "hiv", "aids"],
    "ANTIPARASITARIO": ["parasita", "lombriga", "verme", "giardia", "ameba", "helmintiase"],
    "ANTINEOPLASIC": ["cancer", "neoplasia", "tumor", "quimioterapia", "oncologia", "leucemia", "linfoma"],
    "ANTIHIPERTENSIVO": ["hipertensao", "pressao alta", "hipertensao arterial", "has"],
    "DIURETICO": ["edema", "retencao", "hipertensao", "insuficiencia cardiaca", "ascite"],
    "HIPOGLICEMIANTE": ["diabetes", "glicemia", "hiperglicemia", "dm", "insulina"],
    "HIPOLIPEMIANTE": ["dislipidemia", "colesterol", "triglicerides", "hiperlipidemia", "hipercolesterol"],
    "ANTICOAGULANTE": ["trombose", "embolia", "fibrilacao", "coagulacao", "tromboembolia", "tvp"],
    "BRONCODILATADOR": ["asma", "dpoc", "broncoespasmo", "bronquite", "dispneia", "falta de ar"],
    "ANTIDEPRESSIVO": ["depressao", "ansiedade", "humor", "transtorno afetivo", "tdm"],
    "ANTIPSICOTIC": ["psicose", "esquizofrenia", "mania", "delusao", "alucinacao"],
    "ANTICONVULSIVANTE": ["epilepsia", "convulsao", "crises convulsivas", "status epilepticus"],
    "ANTIULCEROSO": ["ulcera", "gastrite", "refluxo", "dispepsia", "gerd", "esofagite"],
    "CORTICOIDE": ["inflamacao", "alergica", "asma", "artrite", "autoimune", "inflamatoria"],
    "IMUNOSSUPRESSOR": ["transplante", "autoimune", "artrite reumatoide", "lupus", "rejeicao"],
    "CARDIOVASCULAR": ["insuficiencia cardiaca", "arritmia", "angina", "isquemia", "infarto"],
    "HORMONIO": ["hipotireoidismo", "hipertireoidismo", "reposicao hormonal", "endocrina"],
    "VITAMINA": ["deficiencia", "suplementacao", "carencia", "nutricional", "avitaminose"],
    # Subtipos de antibióticos (classes específicas ANVISA)
    "PENICILINA": ["infeccao", "bacteriana", "pneumonia", "itu", "sepse", "streptococ", "sinusite"],
    "CEFALOSPORINA": ["infeccao", "bacteriana", "pneumonia", "itu", "sepse"],
    "MACROLIDEO": ["infeccao", "pneumonia", "bronquite", "atipica"],
    "QUINOLONA": ["infeccao", "itu", "pneumonia", "bacteriana"],
    "AMINOGLICOSIDEO": ["infeccao", "sepse", "bacteriana"],
    # Classes cardiovasculares específicas ANVISA
    "INIBIDOR": ["hipertensao", "pressao alta", "insuficiencia cardiaca", "has"],
    "ANGIOTENSINA": ["hipertensao", "pressao alta", "has", "insuficiencia cardiaca"],
    "BLOQUEADOR": ["hipertensao", "pressao alta", "has", "angina", "arritmia"],
    "ESTATINA": ["dislipidemia", "colesterol", "triglicerides"],
    "FIBRATO": ["dislipidemia", "triglicerides", "colesterol"],
    # Antiinflamatórios
    "AINE": ["inflamacao", "dor", "artrite", "febre"],
    "ANTIINFLAMATORIO": ["inflamacao", "dor", "artrite", "febre", "edema"],
    # Antiulcerosos específicos
    "INIBIDOR DE BOMBA": ["gastrite", "ulcera", "refluxo", "dispepsia", "gerd"],
    "OMEPRAZOL": ["gastrite", "ulcera", "refluxo", "dispepsia"],
    "ANTIULCEROSO": ["gastrite", "ulcera", "refluxo", "dispepsia"],
    # Relaxantes musculares
    "RELAXANTE": ["contratura", "espasmo", "miorrelaxante", "dor muscular", "contratura"],
    "MIORRELAX": ["contratura", "espasmo", "miorrelaxante", "dor muscular"],
}

# Prefixo CID -> palavras-chave de classe terapêutica compatíveis
# Inclui tanto categorias genéricas quanto nomes específicos ANVISA
_CID_CLASSES: dict[str, list[str]] = {
    "A": ["ANTIBIOTICO", "ANTIVIRAL", "ANTIPARASITARIO", "ANTIFUNGIC",
          "PENICILINA", "CEFALOSPORINA", "MACROLIDEO", "QUINOLONA", "SULFONAMIDA",
          "AMINOGLICOSIDEO", "CARBAPENEM", "TETRACICLINA", "GLICOPEPTIDEO"],
    "B": ["ANTIBIOTICO", "ANTIVIRAL", "ANTIPARASITARIO", "ANTIFUNGIC",
          "PENICILINA", "CEFALOSPORINA", "QUINOLONA", "IMUNOSSUPRESSOR"],
    "C": ["ANTINEOPLASIC", "CORTICOIDE", "IMUNOSSUPRESSOR",
          "CITOSTATICO", "ANTICANCER", "QUIMIOTERAPIC"],
    "D": ["ANTINEOPLASIC", "VITAMINA", "CORTICOIDE", "IMUNOSSUPRESSOR",
          "HEMATOPOIET", "HEMATINICO"],
    "E": ["HIPOGLICEMIANTE", "HORMONIO", "VITAMINA", "HIPOLIPEMIANTE", "CORTICOIDE",
          "INSULINA", "ANTIDIABETICO", "TIREOID", "DIABETES"],
    "F": ["ANTIDEPRESSIVO", "ANTIPSICOTIC", "ANTICONVULSIVANTE", "ANSIOLITIC",
          "BENZODIAZEP", "LITIO", "TRANQUILIZ"],
    "G": ["ANTICONVULSIVANTE", "ANALGESICO", "CORTICOIDE", "ANTIPSICOTIC",
          "DOPAMINERGIC", "ANTIPARKINSON", "RELAXANTE MUSCULAR", "MIORRELAX"],
    "H": ["ANTIBIOTICO", "CORTICOIDE", "ANTIINFLAMATORIO", "ANTIVIRAL",
          "PENICILINA", "CEFALOSPORINA", "QUINOLONA", "OFTALMIC", "OTIC"],
    "I": ["ANTIHIPERTENSIVO", "DIURETICO", "ANTICOAGULANTE", "CARDIOVASCULAR", "HIPOLIPEMIANTE",
          "INIBIDOR", "ANGIOTENSINA", "BLOQUEADOR", "CALCIO", "BETA BLOQ", "ECA",
          "ESTATINA", "FIBRATO", "VASODILATADOR", "CARDIOTON", "ANTIARRITMICO",
          "ANTIAGREGANTE", "DIGOXINA"],
    "J": ["ANTIBIOTICO", "BRONCODILATADOR", "CORTICOIDE", "ANTIVIRAL", "MUCOLITIC",
          "PENICILINA", "CEFALOSPORINA", "MACROLIDEO", "QUINOLONA", "AMINOGLICOSIDEO",
          "AZITROMICINA", "AMOXICILINA", "EXPECTORANTE", "ANTITUSSIG"],
    "K": ["ANTIULCEROSO", "ANTIBIOTICO", "CORTICOIDE", "ANTIFUNGIC",
          "PENICILINA", "MACROLIDEO", "INIBIDOR DE BOMBA", "OMEPRAZOL", "ANTIEMETICO",
          "PROCINETIC", "ANTIESPASMODI"],
    "L": ["CORTICOIDE", "ANTIBIOTICO", "ANTIFUNGIC", "IMUNOSSUPRESSOR",
          "RETINOID", "DERMATOLOGIC", "ANTIPSORIASE"],
    "M": ["ANALGESICO", "ANTIINFLAMATORIO", "CORTICOIDE", "IMUNOSSUPRESSOR",
          "RELAXANTE MUSCULAR", "MIORRELAX", "AINE", "ANTI-REUMATI"],
    "N": ["ANTIBIOTICO", "ANTIFUNGIC", "HORMONIO",
          "PENICILINA", "CEFALOSPORINA", "QUINOLONA", "PROGESTOGENIO", "ESTROGEN"],
    "O": ["HORMONIO", "ANTIBIOTICO", "VITAMINA", "ANALGESICO",
          "TOCOLIT", "UTEROTONICO", "OCITOCINA"],
    "P": ["ANTIBIOTICO", "VITAMINA", "CORTICOIDE",
          "PENICILINA", "CEFALOSPORINA", "SURFACTANTE"],
    "Q": [],
    "R": ["ANALGESICO", "ANTIBIOTICO", "BRONCODILATADOR", "ANTITUSSIGENO",
          "PENICILINA", "CEFALOSPORINA", "DIPIRONA", "RELAXANTE MUSCULAR", "MIORRELAX",
          "ANTIINFLAMATORIO", "AINE"],
    "S": ["ANALGESICO", "ANTIBIOTICO", "ANTIINFLAMATORIO", "ANESTESICO",
          "PENICILINA", "CEFALOSPORINA", "QUINOLONA", "MIORRELAX"],
    "T": ["ANTIBIOTICO", "CORTICOIDE", "ANALGESICO",
          "PENICILINA", "CEFALOSPORINA", "ANTIDOTO"],
    "Z": [],
}


def _normalizar(texto: str) -> str:
    """Remove acentos e converte para minúsculas."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _classe_contem(classe: str, palavras: list[str]) -> bool:
    """Verifica se a classe terapêutica contém pelo menos uma das palavras."""
    c = _normalizar(classe)
    return any(p in c for p in palavras)


def _tratamento_contem(tratamento: str, palavras: list[str]) -> bool:
    t = _normalizar(tratamento)
    return any(p in t for p in palavras)


def _prefixo_cid(codigo_cid: str) -> str:
    """Extrai o prefixo de 1 letra do código CID ('J18' -> 'J')."""
    return re.sub(r"[^A-Z]", "", codigo_cid.upper())[:1]


def _classificar_risco(pontuacao: int) -> str:
    if pontuacao <= 30:
        return "BAIXO"
    if pontuacao <= 70:
        return "MEDIO"
    return "ALTO"


def _variacao_pct(informado: float, referencia: float) -> float | None:
    if not referencia or referencia <= 0:
        return None
    return round((informado - referencia) / referencia * 100, 1)


# ── Pesos das dimensões ────────────────────────────────────────────────────
# Cada dimensão tem custo (aderência, risco) por nível de problema.
_PESOS = {
    "tratamento":      {"ATENCAO": (5, 8),   "NAO_ADERENTE": (12, 18)},
    "cid":             {"ATENCAO": (5, 8),   "NAO_ADERENTE": (12, 18)},
    "med_proc":        {"ATENCAO": (4, 6),   "NAO_ADERENTE": (10, 14)},
    "cid_proc":        {"ATENCAO": (4, 6),   "NAO_ADERENTE": (10, 14)},
    "preco_pf":        {"ATENCAO": (3, 5),   "NAO_ADERENTE": (5,  8)},
    "preco_pmc":       {"ATENCAO": (4, 7),   "NAO_ADERENTE": (10, 16)},
    "preco_pmvg":      {"ATENCAO": (3, 5),   "NAO_ADERENTE": (7,  10)},
    "quantidade":      {"ATENCAO": (3, 5),   "NAO_ADERENTE": (8,  12)},
    "inconsistencias": {"ATENCAO": (2, 3),   "NAO_ADERENTE": (5,  8)},
}


def _aplicar_peso(dimensao: str, situacao: Situacao, aderencia: int, risco: int) -> tuple[int, int]:
    if situacao not in (Situacao.ATENCAO, Situacao.NAO_ADERENTE):
        return aderencia, risco
    nivel = situacao.value  # "ATENCAO" ou "NAO_ADERENTE"
    da, dr = _PESOS[dimensao][nivel]
    return max(0, aderencia - da), min(100, risco + dr)


# ── Dimensão 1: Medicamento × Tratamento ──────────────────────────────────

def _d1_tratamento(classe: str | None, tratamento: str) -> tuple[Situacao, str]:
    if not tratamento.strip():
        return Situacao.NAO_INFORMADO, "Tratamento não informado."
    if not classe:
        return Situacao.NAO_INFORMADO, "Classe terapêutica do medicamento não disponível."

    t_norm = _normalizar(tratamento)
    c_norm = _normalizar(classe)

    # Busca correspondência no mapa de classes (comparação case-insensitive)
    for chave, palavras in _CLASSE_TRATAMENTO.items():
        if chave.lower() in c_norm and palavras:
            if any(p in t_norm for p in palavras):
                return Situacao.ADERENTE, f"Medicamento da classe {classe} é compatível com o tratamento informado."
            # Classe reconhecida mas sem correspondência no tratamento
            return Situacao.NAO_ADERENTE, (
                f'Medicamento da classe {classe} nao corresponde ao tratamento descrito: "{tratamento}".'
            )

    # Classe não mapeada  -  atenção
    return Situacao.ATENCAO, (
        f"Classe terapêutica {classe} não pode ser avaliada automaticamente para o tratamento informado."
    )


# ── Dimensão 2: Medicamento × CID ─────────────────────────────────────────

def _d2_cid(classe: str | None, cid_row: dict | None, codigo_cid: str) -> tuple[Situacao, str]:
    if not codigo_cid.strip():
        return Situacao.NAO_INFORMADO, "CID não informado."
    if not cid_row:
        return Situacao.NAO_INFORMADO, f"CID {codigo_cid} não encontrado na base CID-10."
    if not classe:
        return Situacao.NAO_INFORMADO, "Classe terapêutica não disponível para verificação."

    prefixo = _prefixo_cid(cid_row["codigo"])
    classes_compat = _CID_CLASSES.get(prefixo, [])
    c_norm = _normalizar(classe)

    # Categoria sem restrição (Q, Z)
    if not classes_compat:
        return Situacao.ADERENTE, (
            f"CID {cid_row['codigo']} ({cid_row['descricao']}) não impõe restrição de classe terapêutica."
        )

    if any(chave.lower() in c_norm for chave in classes_compat):
        return Situacao.ADERENTE, (
            f"Classe {classe} é compatível com o CID {cid_row['codigo']} "
            f"({cid_row['descricao']})."
        )

    return Situacao.NAO_ADERENTE, (
        f"CID {cid_row['codigo']} ({cid_row['descricao']}) não consta nas indicações "
        f"esperadas para a classe {classe}."
    )


# ── Dimensão 3: Medicamento × Procedimento ────────────────────────────────

def _d3_med_procedimento(classe: str | None, proc_row: dict | None, codigo_proc: str) -> tuple[Situacao, str]:
    if not codigo_proc.strip():
        return Situacao.NAO_INFORMADO, "Procedimento não informado."
    if not proc_row:
        return Situacao.NAO_INFORMADO, f"Procedimento {codigo_proc} não encontrado no SIGTAP."
    if not classe:
        return Situacao.ATENCAO, "Classe terapêutica não disponível para verificar procedimento."

    grupo = proc_row.get("grupo_codigo", "")
    grupo_desc = proc_row.get("grupo_descricao", "")
    c_norm = _normalizar(classe)

    # Grupo 6 = Medicamentos -> sempre aderente (procedimento É o medicamento)
    if grupo == "06":
        return Situacao.ADERENTE, f"Procedimento {proc_row['codigo']} é classificado como Medicamento pelo SIGTAP."

    # Grupos clínicos/cirúrgicos  -  verificar coerência por classe
    if grupo in ("03", "04", "05"):  # Clínicos, Cirúrgicos, Transplantes
        if "ANESTESIC" in c_norm and grupo == "04":
            return Situacao.ADERENTE, "Anestésico compatível com procedimento cirúrgico."
        if "ANTIBIOTICO" in c_norm:
            return Situacao.ATENCAO, (
                "Antibiótico associado a procedimento clínico/cirúrgico  -  "
                "verifique se há indicação de profilaxia ou infecção associada."
            )
        if any(k in c_norm for k in ("ANALGESICO", "ANTIINFLAMATORIO", "CORTICOIDE")):
            return Situacao.ADERENTE, f"Classe {classe} é compatível com procedimento clínico/cirúrgico."
        return Situacao.ATENCAO, (
            f"Associação entre {classe} e procedimento do grupo {grupo_desc} "
            "requer confirmação clínica."
        )

    # Diagnóstico  -  qualquer medicamento é incomum
    if grupo == "02":
        return Situacao.ATENCAO, (
            f"Medicamento associado a procedimento diagnóstico ({proc_row['descricao'][:60]}...)  -  "
            "verifique se a associação é justificada."
        )

    return Situacao.ADERENTE, (
        f"Não foram identificadas incompatibilidades entre {classe} e o procedimento {proc_row['codigo']}."
    )


# ── Dimensão 4: CID × Procedimento ────────────────────────────────────────

def _d4_cid_procedimento(
    db: Session,
    cid_row: dict | None,
    proc_row: dict | None,
    codigo_cid: str,
    codigo_proc: str,
) -> tuple[Situacao, str]:
    if not codigo_cid.strip() or not codigo_proc.strip():
        return Situacao.NAO_INFORMADO, "CID ou procedimento não informado."
    if not cid_row:
        return Situacao.NAO_INFORMADO, f"CID {codigo_cid} não encontrado."
    if not proc_row:
        return Situacao.NAO_INFORMADO, f"Procedimento {codigo_proc} não encontrado no SIGTAP."

    compativel = analise_repo.verificar_cid_procedimento(db, proc_row["codigo"], cid_row["codigo"])
    total_cids = analise_repo.contar_cids_procedimento(db, proc_row["codigo"])

    if compativel:
        return Situacao.ADERENTE, (
            f"CID {cid_row['codigo']} ({cid_row['descricao']}) consta na lista de CIDs "
            f"compatíveis com o procedimento {proc_row['codigo']} no SIGTAP."
        )

    if total_cids > 0:
        return Situacao.NAO_ADERENTE, (
            f"CID {cid_row['codigo']} ({cid_row['descricao']}) não consta na lista de "
            f"{total_cids:,} CIDs relacionados ao procedimento {proc_row['codigo']} no SIGTAP."
        )

    return Situacao.ATENCAO, (
        f"Procedimento {proc_row['codigo']} não possui CIDs vinculados no SIGTAP para verificação."
    )


# ── Dimensões 5-7: Preço ───────────────────────────────────────────────────

def _d567_preco(
    preco_informado: float,
    pf: float | None,
    pmc: float | None,
    pmvg: float | None,
) -> tuple[Situacao, str, AnalisePreco]:
    """Avalia preço em relação a PF, PMC e PMVG. Retorna situação consolidada."""
    problemas = []
    situacao_final = Situacao.ADERENTE

    vpf = _variacao_pct(preco_informado, pf)
    vpmc = _variacao_pct(preco_informado, pmc)
    vpmvg = _variacao_pct(preco_informado, pmvg)

    # PMC (mais relevante para glosa)
    if vpmc is not None:
        if vpmc > 10:
            problemas.append(f"Preço {vpmc:+.1f}% acima do PMC vigente (R$ {pmc:.2f}).")
            situacao_final = Situacao.NAO_ADERENTE
        elif vpmc > 5:
            problemas.append(f"Preço {vpmc:+.1f}% acima do PMC vigente  -  dentro da margem de atenção.")
            if situacao_final == Situacao.ADERENTE:
                situacao_final = Situacao.ATENCAO

    # PF
    if vpf is not None:
        if vpf > 15:
            problemas.append(f"Preço {vpf:+.1f}% acima do PF (Preço Fábrica: R$ {pf:.2f}).")
            situacao_final = Situacao.NAO_ADERENTE
        elif vpf > 5:
            problemas.append(f"Preço {vpf:+.1f}% acima do PF  -  verificar justificativa.")
            if situacao_final == Situacao.ADERENTE:
                situacao_final = Situacao.ATENCAO

    # PMVG (apenas para aquisições governamentais)
    if vpmvg is not None and vpmvg > 15:
        problemas.append(f"Preço {vpmvg:+.1f}% acima do PMVG (teto governo: R$ {pmvg:.2f}).")
        if situacao_final == Situacao.ADERENTE:
            situacao_final = Situacao.ATENCAO

    if not problemas:
        if pmc is None and pf is None:
            motivo = "Preço de referência CMED não disponível para este medicamento."
            situacao_final = Situacao.NAO_INFORMADO
        else:
            motivo = "Preço informado está dentro dos limites de referência CMED."
    else:
        motivo = " ".join(problemas)

    analise = AnalisePreco(
        situacao=situacao_final,
        preco_informado=preco_informado,
        pf=pf,
        pmc=pmc,
        pmvg=pmvg,
        variacao_pf_pct=vpf,
        variacao_pmc_pct=vpmc,
        variacao_pmvg_pct=vpmvg,
        motivo=motivo,
    )
    return situacao_final, motivo, analise


# ── Dimensão 8: Quantidade ─────────────────────────────────────────────────

def _quantidade_esperada(classe: str | None, apresentacao: str | None) -> int:
    """Estima a quantidade esperada com base na forma farmacêutica e classe."""
    if apresentacao:
        ap = apresentacao.upper()
        # Injetáveis e frascos de uso único — verificar antes do padrão "X N"
        if any(k in ap for k in ("AMP", "FR INJ", "SOL INJ")):
            return 10
        # Soluções orais — até 3 frascos por ciclo é razoável
        if any(k in ap for k in ("FR GOT", "SOL OR", "XAROPE", "ELIXIR")):
            return 3
        # Extrai número de unidades da apresentação: "X 30" ou "X 20 COMP"
        m = re.search(r"X\s*(\d+)", ap)
        if m:
            return int(m.group(1))
    # Padrão: 30 comprimidos/cápsulas por ciclo mensal
    if classe:
        c = _normalizar(classe)
        if "antibiotico" in c:
            return 21  # ciclo típico 7 dias × 3/dia
        if "antineoplasic" in c:
            return 5   # oncológicos  -  quantidades menores por administração
    return 30


def _d8_quantidade(
    quantidade: int,
    classe: str | None,
    apresentacao: str | None,
) -> tuple[Situacao, str, int]:
    esperada = _quantidade_esperada(classe, apresentacao)
    razao = quantidade / esperada

    if razao <= 1.5:
        return Situacao.ADERENTE, (
            f"Quantidade {quantidade} está dentro do padrão esperado "
            f"({esperada} unidades por ciclo)."
        ), esperada
    if razao <= 2.5:
        return Situacao.ATENCAO, (
            f"Quantidade {quantidade} é {razao:.1f}× o padrão esperado "
            f"({esperada} unidades). Verifique se há justificativa clínica."
        ), esperada
    return Situacao.NAO_ADERENTE, (
        f"Quantidade {quantidade} excede em {razao:.1f}× o padrão esperado "
        f"({esperada} unidades)  -  risco de fracionamento irregular ou prescrição excessiva."
    ), esperada


# ── Dimensão 9: Inconsistências cruzadas ──────────────────────────────────

def _d9_inconsistencias(
    med_row: dict | None,
    cid_row: dict | None,
    proc_row: dict | None,
    codigo_cid: str,
    codigo_proc: str,
    preco_informado: float,
) -> tuple[Situacao, list[str]]:
    problemas = []

    # CORREÇÃO CRÍTICA: Medicamento não encontrado = RISCO ALTO
    # Sem base de referência, não é possível validar preço, classe, registro
    if med_row is None:
        problemas.append("⚠️ RISCO ALTO: Medicamento não localizado na base ANVISA. Sem referência para validação de preço, classe terapêutica ou situação de registro.")

    if med_row and med_row.get("situacao_registro", "").upper() not in ("ATIVO",):
        problemas.append("Registro ANVISA do medicamento não está ativo.")

    if med_row and not med_row.get("pmc"):
        problemas.append("Medicamento sem preço de tabela CMED  -  pode ser importado ou manipulado.")

    if codigo_cid.strip() and not cid_row:
        problemas.append(f'CID "{codigo_cid}" não encontrado na tabela CID-10  -  verifique o código.')

    if codigo_proc.strip() and not proc_row:
        problemas.append(f'Procedimento "{codigo_proc}" não encontrado no SIGTAP  -  verifique o código.')

    # CORREÇÃO: Medicamento não encontrado deve sempre ser NAO_ADERENTE (risco alto)
    if med_row is None:
        return Situacao.NAO_ADERENTE, problemas

    if not problemas:
        return Situacao.ADERENTE, []
    if len(problemas) == 1:
        return Situacao.ATENCAO, problemas
    return Situacao.NAO_ADERENTE, problemas


# ── Motor principal ────────────────────────────────────────────────────────

def analisar(db: Session, entrada: AnaliseEntrada) -> AnaliseResultado:
    # 1. Buscar dados base
    med = analise_repo.buscar_medicamento_para_analise(db, entrada.medicamento)
    cid = analise_repo.buscar_cid(db, entrada.cid) if entrada.cid.strip() else None
    codigo_proc_norm = "".join(c for c in entrada.procedimento if c.isdigit())[:10].ljust(10, "0") if entrada.procedimento.strip() else ""
    proc = analise_repo.buscar_procedimento(db, entrada.procedimento) if entrada.procedimento.strip() else None

    classe = med.get("classe_terapeutica") if med else None
    apresentacao = med.get("apresentacao") if med else None
    pf = float(med["pf"]) if med and med.get("pf") else None
    pmc = float(med["pmc"]) if med and med.get("pmc") else None
    pmvg = float(med["pmvg"]) if med and med.get("pmvg") else None

    # 2. Avaliar cada dimensão
    s1, m1 = _d1_tratamento(classe, entrada.tratamento)
    s2, m2 = _d2_cid(classe, cid, entrada.cid)
    s3, m3 = _d3_med_procedimento(classe, proc, entrada.procedimento)
    s4, m4 = _d4_cid_procedimento(db, cid, proc, entrada.cid, entrada.procedimento)

    spreco, mpreco, analise_preco = _d567_preco(entrada.preco_informado, pf, pmc, pmvg)

    s8, m8, qtd_esperada = _d8_quantidade(entrada.quantidade, classe, apresentacao)
    s9, lista_inc = _d9_inconsistencias(med, cid, proc, entrada.cid, entrada.procedimento, entrada.preco_informado)

    # 3. Calcular pontuações
    aderencia = 100
    risco = 0

    aderencia, risco = _aplicar_peso("tratamento", s1, aderencia, risco)
    aderencia, risco = _aplicar_peso("cid", s2, aderencia, risco)
    aderencia, risco = _aplicar_peso("med_proc", s3, aderencia, risco)
    aderencia, risco = _aplicar_peso("cid_proc", s4, aderencia, risco)
    aderencia, risco = _aplicar_peso("preco_pmc", spreco, aderencia, risco)
    aderencia, risco = _aplicar_peso("quantidade", s8, aderencia, risco)
    aderencia, risco = _aplicar_peso("inconsistencias", s9, aderencia, risco)

    # Penalidades adicionais por PF (dentro da dimensão preço)
    vpf = _variacao_pct(entrada.preco_informado, pf)
    if vpf and vpf > 15:
        aderencia, risco = _aplicar_peso("preco_pf", Situacao.NAO_ADERENTE, aderencia, risco)
    elif vpf and vpf > 5:
        aderencia, risco = _aplicar_peso("preco_pf", Situacao.ATENCAO, aderencia, risco)

    aderencia = max(0, aderencia)
    risco = min(100, risco)

    # 4. Classificações
    aderente = aderencia >= 90
    class_risco = _classificar_risco(risco)
    potencial_glosa = class_risco

    if aderencia >= 90:
        status_aderencia = "ADERENTE"
    elif aderencia >= 70:
        status_aderencia = "ATENÇÃO"
    else:
        status_aderencia = "NÃO ADERENTE"

    # 5. Motivos consolidados em português
    motivos = []
    for situacao, motivo in [
        (s1, m1), (s2, m2), (s3, m3), (s4, m4), (spreco, mpreco), (s8, m8)
    ]:
        if situacao != Situacao.NAO_INFORMADO and motivo:
            motivos.append(motivo)
    motivos.extend(lista_inc)

    return AnaliseResultado(
        aderente=aderente,
        pontuacao_aderencia=aderencia,
        pontuacao_risco=risco,
        potencial_glosa=potencial_glosa,
        classificacao_risco=class_risco,
        motivos=motivos,
        analise_tratamento=AnaliseTratamento(
            situacao=s1,
            classe_terapeutica=classe,
            motivo=m1,
        ),
        analise_cid=AnaliseCid(
            situacao=s2,
            cid=cid["codigo"] if cid else entrada.cid or None,
            descricao=cid["descricao"] if cid else None,
            motivo=m2,
        ),
        analise_procedimento=AnaliseProced(
            situacao=s3,
            procedimento=proc["codigo"] if proc else entrada.procedimento or None,
            descricao=proc["descricao"] if proc else None,
            motivo=m3,
        ),
        analise_cid_procedimento=AnaliseProced(
            situacao=s4,
            procedimento=proc["codigo"] if proc else None,
            descricao=cid["descricao"] if cid else None,
            motivo=m4,
        ),
        analise_preco=analise_preco,
        analise_quantidade=AnaliseQuantidade(
            situacao=s8,
            quantidade_informada=entrada.quantidade,
            quantidade_esperada=qtd_esperada,
            motivo=m8,
        ),
        medicamento_encontrado=med["nome_produto"] if med else None,
        numero_registro=med["numero_registro"] if med else None,
        situacao_anvisa=med["situacao_registro"] if med else None,
    )
