# Regras de Potencial de Glosa - MedID Data

## 🎯 Objetivo

Calcular o **potencial de glosa** de uma prescrição médica baseado em inconsistências clínicas e financeiras detectadas automaticamente.

⚠️ **IMPORTANTE**: O potencial de glosa **NÃO é uma glosa real** nem uma decisão de operadora. É um **indicador preventivo** baseado em regras de auditoria hospitalar.

---

## 📐 Fórmula de Cálculo

### Pontuação de Risco

Cada uma das 9 dimensões retorna:
- **Situacao**: `ADERENTE | ATENCAO | NAO_ADERENTE | NAO_INFORMADO`
- **Motivos**: Lista de problemas detectados

**Pesos**:
```
ADERENTE      = 0 pontos (sem problemas)
ATENCAO       = 1 ponto  (problema leve)
NAO_ADERENTE  = 3 pontos (problema grave)
NAO_INFORMADO = 0 pontos (dados não fornecidos - não penaliza)
```

**Pontuação Final**:
```
Soma dos pesos = (peso_d1 + peso_d2 + ... + peso_d9)
Pontuação de risco = (soma_pesos / 27) * 100
Pontuação de aderência = 100 - pontuação_risco

Máximo possível: 9 dimensões * 3 pontos = 27 pontos = 100% risco
```

### Classificação de Potencial de Glosa

```
Pontuação de risco < 30%  → BAIXO
Pontuação de risco 30-60% → MEDIO
Pontuação de risco > 60%  → ALTO
```

---

## 🔍 Dimensões de Análise

### D1 - Tratamento vs. Classe Terapêutica

**Objetivo**: Validar se a classe terapêutica do medicamento é compatível com o tratamento informado.

**Situações**:
- ✅ **ADERENTE**: Classe compatível com tratamento (ex: Analgésico para "dor pós-operatória")
- ⚠️ **ATENCAO**: Compatibilidade parcial
- ❌ **NAO_ADERENTE**: Classe incompatível (ex: Antibiótico para "hipertensão")
- ⚪ **NAO_INFORMADO**: Tratamento não informado

---

### D2 - CID-10

**Objetivo**: Validar se o código CID-10 existe e está formatado corretamente.

**Situações**:
- ✅ **ADERENTE**: CID existe na tabela CID-10
- ❌ **NAO_ADERENTE**: CID não encontrado ou formato inválido
- ⚪ **NAO_INFORMADO**: CID não fornecido

**Formato válido**: `[A-Z]\d{2}(\.\d{1,2})?` (ex: J18.9, A00, B20.1)

---

### D3 - Procedimento SIGTAP

**Objetivo**: Validar se o código de procedimento SIGTAP existe.

**Situações**:
- ✅ **ADERENTE**: Procedimento existe no SIGTAP
- ❌ **NAO_ADERENTE**: Procedimento não encontrado ou formato inválido
- ⚪ **NAO_INFORMADO**: Procedimento não fornecido

**Formato válido**: `\d{2}\.\d{2}\.\d{2}\.\d{3}-\d` (ex: 03.01.01.007-2)

---

### D4 - CID + Procedimento (Compatibilidade)

**Objetivo**: Validar se o CID informado é compatível com o procedimento SIGTAP.

**Fonte**: Tabela `sigtap_procedimento_cid` (relacionamento N:N)

**Situações**:
- ✅ **ADERENTE**: CID está na lista de CIDs compatíveis com o procedimento
- ⚠️ **ATENCAO**: Compatibilidade parcial (CID genérico)
- ❌ **NAO_ADERENTE**: CID não está na lista de compatibilidade
- ⚪ **NAO_INFORMADO**: CID ou procedimento não fornecidos

---

### D5 - Preço

**Objetivo**: Comparar preço informado com preços de referência CMED (PF, PMC, PMVG).

**Fórmulas**:
```
variacao_pf   = ((preco_informado - pf)   / pf)   * 100
variacao_pmc  = ((preco_informado - pmc)  / pmc)  * 100
variacao_pmvg = ((preco_informado - pmvg) / pmvg) * 100
```

**Situações**:
- ✅ **ADERENTE**: Preço dentro de ±10% do PMC
- ⚠️ **ATENCAO**: Preço entre 10-30% acima do PMC
- ❌ **NAO_ADERENTE**: Preço >30% acima do PMC ou medicamento sem preço de referência
- ⚪ **NAO_INFORMADO**: Preço não fornecido

**Motivos**:
```
"Preço X% acima do PMC"
"Preço X% abaixo do PF (suspeito)"
"Medicamento sem preço de tabela CMED (pode ser importado ou manipulado)"
```

---

### D6 - Quantidade

**Objetivo**: Validar se a quantidade prescrita é razoável.

**Regras atuais**:
- ✅ **ADERENTE**: Quantidade 1-10 unidades (padrão esperado)
- ⚠️ **ATENCAO**: Quantidade 11-30 unidades (atenção)
- ❌ **NAO_ADERENTE**: Quantidade >30 unidades (suspeito)

**Motivos**:
```
"Quantidade elevada (X unidades)"
"Quantidade incompatível com prescrição padrão"
```

---

### D7 - Cobertura

**Objetivo**: Validar se o medicamento tem cobertura por planos de saúde.

**Situações**:
- ✅ **ADERENTE**: Medicamento tem cobertura ANS
- ⚠️ **ATENCAO**: Cobertura condicional
- ❌ **NAO_ADERENTE**: Medicamento sem cobertura
- ⚪ **NAO_INFORMADO**: Informação de cobertura indisponível

---

### D8 - Situação ANVISA

**Objetivo**: Validar se o registro ANVISA está ativo.

**Situações**:
- ✅ **ADERENTE**: Registro ATIVO
- ❌ **NAO_ADERENTE**: Registro INATIVO, CANCELADO, VENCIDO
- ⚪ **NAO_INFORMADO**: Medicamento não encontrado na base ANVISA

**Motivos**:
```
"Registro ANVISA não está ativo"
"Registro ANVISA vencido"
```

---

### D9 - Inconsistências

**Objetivo**: Detectar ausência de dados críticos para validação.

**⚠️ REGRA CRÍTICA**: **Ausência de informação confiável deve AUMENTAR o risco, não reduzir.**

**Situações**:
- ✅ **ADERENTE**: Todos os dados essenciais presentes e válidos
- ⚠️ **ATENCAO**: 1 problema menor (ex: medicamento sem preço CMED)
- ❌ **NAO_ADERENTE**: Múltiplos problemas OU medicamento não encontrado

**Problemas detectados**:
```
"⚠️ RISCO ALTO: Medicamento não localizado na base ANVISA. Sem referência para validação de preço, classe terapêutica ou situação de registro."
"Registro ANVISA do medicamento não está ativo."
"Medicamento sem preço de tabela CMED - pode ser importado ou manipulado."
"CID 'X' não encontrado na tabela CID-10 - verifique o código."
"Procedimento 'X' não encontrado no SIGTAP - verifique o código."
```

**🚨 IMPORTANTE**: Se `medicamento não encontrado`, a dimensão retorna **NAO_ADERENTE** (3 pontos), pois:
- Não é possível validar preço
- Não é possível validar classe terapêutica
- Não é possível validar situação de registro
- Não é possível validar compatibilidade

---

## 📊 Exemplos Práticos

### Exemplo 1: Análise BAIXO Risco

**Entrada**:
```json
{
  "medicamento": "DIPIRONA SÓDICA 500MG",
  "preco_informado": 12.00,
  "tratamento": "Dor pós-operatória",
  "cid": "R52.9",
  "procedimento": "03.01.01.007-2",
  "quantidade": 1
}
```

**Resultado**:
```
D1 - Tratamento: ADERENTE (0)
D2 - CID: ADERENTE (0)
D3 - Procedimento: ADERENTE (0)
D4 - CID+Proc: ADERENTE (0)
D5 - Preço: ADERENTE (0) - dentro de ±10%
D6 - Quantidade: ADERENTE (0)
D7 - Cobertura: ADERENTE (0)
D8 - Situação: ADERENTE (0)
D9 - Inconsistências: ADERENTE (0)

Soma: 0 pontos
Risco: 0%
Potencial de glosa: BAIXO
```

---

### Exemplo 2: Análise MEDIO Risco

**Entrada**:
```json
{
  "medicamento": "DIPIRONA SÓDICA 500MG",
  "preco_informado": 18.00,
  "tratamento": "Dor pós-operatória",
  "cid": "R52.9",
  "procedimento": "03.01.01.999-9",
  "quantidade": 1
}
```

**Resultado**:
```
D1 - Tratamento: ADERENTE (0)
D2 - CID: ADERENTE (0)
D3 - Procedimento: NAO_ADERENTE (3) - não encontrado
D4 - CID+Proc: NAO_INFORMADO (0) - procedimento inválido
D5 - Preço: ATENCAO (1) - 40% acima do PMC
D6 - Quantidade: ADERENTE (0)
D7 - Cobertura: ADERENTE (0)
D8 - Situação: ADERENTE (0)
D9 - Inconsistências: ATENCAO (1) - procedimento inválido

Soma: 5 pontos
Risco: 18.5%
Potencial de glosa: BAIXO (próximo de MEDIO)
```

---

### Exemplo 3: Análise ALTO Risco

**Entrada**:
```json
{
  "medicamento": "MEDICAMENTO DESCONHECIDO XYZ",
  "preco_informado": 500.00,
  "tratamento": "",
  "cid": "",
  "procedimento": "",
  "quantidade": 50
}
```

**Resultado**:
```
D1 - Tratamento: NAO_INFORMADO (0)
D2 - CID: NAO_INFORMADO (0)
D3 - Procedimento: NAO_INFORMADO (0)
D4 - CID+Proc: NAO_INFORMADO (0)
D5 - Preço: NAO_ADERENTE (3) - sem referência CMED
D6 - Quantidade: NAO_ADERENTE (3) - quantidade suspeita
D7 - Cobertura: NAO_INFORMADO (0)
D8 - Situação: NAO_INFORMADO (0)
D9 - Inconsistências: NAO_ADERENTE (3) - medicamento não encontrado

Soma: 9 pontos
Risco: 33.3%
Potencial de glosa: MEDIO

⚠️ Se considerarmos falta de dados como penalização adicional:
Soma ajustada: 15 pontos
Risco: 55.5%
Potencial de glosa: MEDIO (próximo de ALTO)
```

---

## 🔧 Ajustes Pendentes

### Problemas Identificados

1. **Medicamento não encontrado**: Atualmente retorna NAO_ADERENTE (3 pontos), mas deveria penalizar mais fortemente.
   
2. **Falta de dados essenciais**: CID/Procedimento não informados não penalizam (NAO_INFORMADO = 0 pontos).

3. **Gauge invertido**: Visual do gauge está mostrando risco ao contrário (100% parece baixo risco).

4. **Validação de campos**: Alguns valores numéricos geram erro 500.

### Propostas de Correção

**Opção 1**: Aumentar peso de NAO_ADERENTE quando medicamento não encontrado:
```
Medicamento não encontrado = 6 pontos (peso dobrado)
```

**Opção 2**: Criar peso especial para "dados essenciais ausentes":
```
CRITICO = 5 pontos (para medicamento não encontrado)
```

**Opção 3**: Penalizar ausência de CID/Procedimento em cenários críticos:
```
Se medicamento não encontrado E CID ausente → +3 pontos
```

---

**Última atualização**: 2026-06-04  
**Versão**: 1.0.0  
**Status**: ⚠️ Regras em revisão
