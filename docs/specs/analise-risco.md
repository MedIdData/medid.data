# Spec: Análise de Risco de Glosa (M2)

**Módulo:** M2  
**Status:** ✅ Produção  
**Última atualização:** 2026-06-05

---

## Objetivo
Calcular score único de 0-100 indicando risco de glosa com base em 5 dimensões de validação.

**Lógica:** Quanto MAIOR o score, MAIOR o risco de glosa.

---

## Score e Classificação

### Faixas
- **0-20:** MUITO BAIXO (verde)
- **21-40:** BAIXO (verde claro)
- **41-60:** MÉDIO (amarelo)
- **61-80:** ALTO (laranja)
- **81-100:** CRÍTICO (vermelho)

### Cálculo
- Inicia em **0** (sem risco)
- Cada problema **ADICIONA** pontos
- Máximo: **100 pontos**

---

## Dimensões de Validação

### D1 - Medicamento (ANVISA)
**Objetivo:** Verificar se medicamento existe e está ativo

**Regras:**
- Busca por nome usando fuzzy matching
- Similaridade mínima: **0.7 (70%)**
- Valida apenas registros `situacao_registro = 'ATIVO'`

**Pontuações:**
- Medicamento não encontrado: **+80 pontos** (CRÍTICO)
- Medicamento inativo: **+70 pontos** (CRÍTICO)

**Motivo:** Sem medicamento válido, não há como confirmar prescrição.

---

### D2 - Preço (PMC = Preço Máximo ao Consumidor)
**Objetivo:** Validar se preço está dentro dos limites regulados (CMED)

**Regras:**
- Compara `preco_informado` com `pmc_0` (PMC sem impostos)
- Calcula variação percentual: `((informado - pmc) / pmc) * 100`

**Pontuações Progressivas:**
- **+200%:** +50 pontos (CRÍTICO)
- **+100%:** +40 pontos (ALTO)
- **+50%:** +30 pontos (ALTO)
- **+20%:** +20 pontos (MÉDIO)
- **+10%:** +10 pontos (BAIXO)

**Motivo:** Preços muito acima do PMC indicam superfaturamento.

---

### D3 - CID-10 (Classificação Internacional de Doenças)
**Objetivo:** Validar código de diagnóstico

**Regras:**
- Normaliza formato: remove `.` e `-` (ex: "J18.9" → "J189")
- Busca em `cid10_categorias` e `cid10_subcategorias`

**Pontuações:**
- CID não informado: **+70 pontos** (CRÍTICO)
- CID não existe na base: **+75 pontos** (CRÍTICO)

**Motivo:** Sem diagnóstico, não é possível validar indicação clínica.

---

### D4 - SIGTAP (Sistema de Gerenciamento da Tabela de Procedimentos)
**Objetivo:** Validar código de procedimento SUS

**Regras:**
- Busca código em `sigtap_procedimentos`
- Formato esperado: `XX.XX.XX.XXX-X`

**Pontuações:**
- SIGTAP não informado: **+70 pontos** (CRÍTICO)
- SIGTAP não existe na base: **+75 pontos** (CRÍTICO)

**Motivo:** Sem procedimento válido, não é possível validar cobrança.

---

### D5 - Quantidade
**Objetivo:** Detectar quantidades fora do padrão usual

**Regras:**
- Analisa se quantidade está muito acima do comum

**Pontuações Progressivas:**
- **100+ unidades:** +50 pontos (CRÍTICO - +200% do padrão)
- **50+ unidades:** +40 pontos (ALTO - +100% do padrão)
- **20+ unidades:** +30 pontos (ALTO - +50% do padrão)
- **10+ unidades:** +20 pontos (MÉDIO - +20% do usual)
- **5+ unidades:** +10 pontos (BAIXO - +10% do usual)

**Motivo:** Quantidades excessivas podem indicar prescrição irregular.

---

## Interface

### Elementos Exibidos
1. **Gauge circular** - visualização score 0-100
2. **Número grande** - score numérico
3. **Badge classificação** - texto (MUITO BAIXO, BAIXO, MÉDIO, ALTO, CRÍTICO)
4. **Lista de motivos** - bullets explicando problemas detectados
5. **Card medicamento** - nome e status ANVISA (se encontrado)

### Cards Removidos (Simplificação)
- ❌ Dimensões individuais (tratamento, CID, procedimento, preço breakdown)
- ❌ Gauge duplicado de aderência
- ❌ Detalhamento excessivo de pontuações

### Glossário de Siglas
Exibido na sidebar:
- **PMC** - Preço Máximo ao Consumidor
- **PF** - Preço Fábrica
- **PMVG** - Preço Máximo Venda ao Governo
- **CID** - Classificação Internacional de Doenças
- **SIGTAP** - Sistema de Gerenciamento da Tabela de Procedimentos (SUS)

### Descrição de Dimensões
Exibido na sidebar (sem mencionar pontuações):
- **D1 - Medicamento (ANVISA):** Verifica se medicamento existe e se registro está ativo. Similaridade mínima de 70% para aceitar.
- **D2 - Preço (PMC/CMED):** Compara preço informado com Preço Máximo ao Consumidor. Avalia desvios progressivos.
- **D3 - CID-10:** Valida se código de diagnóstico existe na base oficial. Sem CID não é possível confirmar indicação clínica.
- **D4 - SIGTAP:** Valida se código de procedimento SUS existe. Necessário para confirmar cobrança de procedimento.
- **D5 - Quantidade:** Analisa se quantidade está dentro do padrão usual.

---

## Fluxo de Processamento

```
1. Recebe AnaliseEntrada (medicamento, preco, cid, procedimento, quantidade)
2. Inicializa score = 0, motivos = []
3. Executa D1 → adiciona pontos + motivos
4. Executa D2 → adiciona pontos + motivos
5. Executa D3 → adiciona pontos + motivos
6. Executa D4 → adiciona pontos + motivos
7. Executa D5 → adiciona pontos + motivos
8. Limita score a 100
9. Classifica score → texto (MUITO BAIXO ... CRÍTICO)
10. Retorna AnaliseResultado
```

---

## Schemas Pydantic

### Input
```python
class AnaliseEntrada(BaseModel):
    medicamento: str  # min 2 chars
    preco_informado: float  # >= 0
    tratamento: str = ""  # opcional
    cid: str = ""  # opcional, formato A00 ou A00.0
    procedimento: str = ""  # opcional, formato 00.00.00.000-0
    quantidade: int = 1  # >= 1
```

### Output
```python
class AnaliseResultado(BaseModel):
    pontuacao_risco: int  # 0-100 (SCORE PRINCIPAL)
    classificacao_risco: str  # MUITO BAIXO | BAIXO | MÉDIO | ALTO | CRÍTICO
    motivos: List[str]  # bullets explicativos
    medicamento_encontrado: Optional[str]
    situacao_anvisa: Optional[str]
    # ... campos legacy para compatibilidade
```

---

## Testes Validados

### Casos de Teste
- ✅ Medicamento não encontrado → 80 pts (CRÍTICO)
- ✅ Medicamento inativo → 70 pts (CRÍTICO)
- ✅ Preço +200% PMC → +50 pts
- ✅ CID não informado → 70 pts (CRÍTICO)
- ✅ CID inválido → 75 pts (CRÍTICO)
- ✅ SIGTAP não informado → 70 pts (CRÍTICO)
- ✅ SIGTAP inválido → 75 pts (CRÍTICO)
- ✅ Quantidade 100+ → +50 pts

### Exemplo Real
```
Entrada:
  medicamento: "Medicamento X"
  preco_informado: 150.00
  cid: ""
  procedimento: ""
  quantidade: 50

Score acumulado:
  D1: Não encontrado → +80
  D2: Sem PMC para comparar → +0
  D3: CID ausente → +70
  D4: SIGTAP ausente → +70
  D5: Quantidade 50 → +40
  
Total: 260 → limitado a 100 (CRÍTICO)
```

---

## Arquivos Relacionados
- `app/routers/web.py::pagina_analise()`
- `app/services/analise_risco.py::analisar()`
- `app/repositories/analise_repo.py`
- `app/templates/analise.html`
- `app/schemas/analise.py`

---

## Dependências de Dados
- `medicamentos_anvisa` - validação medicamento
- `medicamentos_cmed` - validação preço PMC
- `cid10_categorias`, `cid10_subcategorias` - validação CID
- `sigtap_procedimentos` - validação procedimento
- Módulo M1 (busca fuzzy de medicamento)

---

## Pendências Conhecidas
- (nenhuma no momento)
