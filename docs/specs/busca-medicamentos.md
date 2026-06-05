# Spec: Busca de Medicamentos (M1)

**Módulo:** M1  
**Status:** ✅ Produção (aguardando sync dados)  
**Última atualização:** 2026-06-05

---

## Objetivo
Permitir busca fuzzy na base completa ANVISA (~32k medicamentos) com paginação eficiente.

---

## Regras de Negócio

### RN-M1-001: Busca Fuzzy
- Utiliza PostgreSQL pg_trgm (trigram) + tsvector (full-text)
- Busca em `nome_produto` e `principio_ativo`
- Similaridade mínima: **0.3 (30%)**
- Sem query (vazio): retorna listagem alfabética
- Com query (>=2 chars): busca fuzzy na base completa

### RN-M1-002: Paginação
- **50 medicamentos por página**
- Parâmetros: `?q=termo&apenas_ativos=true&pagina=1`
- Navegação: botões "Anterior" e "Próxima"
- Indicador: "Página X de Y"

### RN-M1-003: Filtro Ativos
- Checkbox "Somente registros ativos"
- Default: `true` (apenas ativos)
- SQL: `upper(situacao_registro) = 'ATIVO'`
- Recarrega página ao mudar (auto-submit)

### RN-M1-004: Performance
- **Listagem inicial:** SEM JOIN LATERAL (rápido, <0.5s)
- **Busca com termo:** COM JOIN LATERAL (necessário para preços)
- Timeout máximo: 2s
- Preços na listagem: NULL (carrega apenas em detail view)

### RN-M1-005: Auto-Submit
- Debounce: **500ms** após parar de digitar
- Enter: submit imediato
- Evita requisições desnecessárias

---

## SQL Queries

### Query Listagem (sem termo)
```sql
SELECT id, numero_registro, nome_produto, principio_ativo,
       situacao_registro, categoria_regulatoria, tarja,
       NULL as pf, NULL as pmc, NULL as pmvg
FROM medicamentos_anvisa
WHERE (:apenas_ativos = FALSE OR upper(situacao_registro) = 'ATIVO')
ORDER BY nome_produto ASC
LIMIT 50 OFFSET :offset
```

### Query Busca (com termo)
```sql
SELECT a.*, c.pf_sem_impostos AS pf, c.pmc_0 AS pmc, c.pmvg_0 AS pmvg,
       GREATEST(
         word_similarity(:q, lower(a.nome_produto)),
         word_similarity(:q, lower(a.principio_ativo))
       ) AS score
FROM medicamentos_anvisa a
LEFT JOIN LATERAL (
  SELECT pf_sem_impostos, pmc_0, pmvg_0
  FROM medicamentos_cmed mc
  WHERE upper(mc.substancia) = upper(split_part(a.principio_ativo, ',', 1))
  LIMIT 1
) c ON TRUE
WHERE (
  a.search_vector @@ websearch_to_tsquery('portuguese', :q)
  OR word_similarity(:q, lower(a.nome_produto)) > 0.3
  OR word_similarity(:q, lower(a.principio_ativo)) > 0.3
)
ORDER BY score DESC, a.nome_produto ASC
LIMIT 50 OFFSET :offset
```

---

## Interface

### Elementos
1. **Campo de busca:** Placeholder "Buscar medicamento (ex: Resfenol, Gardenal, Dipirona)..."
2. **Filtro lateral:** Checkbox "Somente registros ativos"
3. **Grid de cards:** 3 colunas (responsivo 1 coluna mobile)
4. **Tooltip hover:** Detalhes do medicamento
5. **Paginação:** Botões + indicador página

### Feedback Visual
- **Encontrados X medicamentos para "termo"** (quando há busca)
- **Mostrando X de Y medicamentos** (listagem geral)
- **Busca na base completa ANVISA com fuzzy matching**

---

## Testes Validados

### Casos de Teste
- ✅ Busca vazia: retorna 10.298 ativos paginados
- ✅ Busca "resfenol": 102 resultados
- ✅ Busca "gardenal": 9 resultados
- ✅ Busca "dipirona": múltiplos resultados
- ✅ Filtro apenas ativos: ON (10.298) / OFF (32.496)
- ✅ Paginação: navegação entre páginas mantém termo e filtros

---

## Dependências Técnicas

### PostgreSQL Extensions
- `pg_trgm` - trigram similarity
- `unaccent` - remove acentos para busca

### Índices
```sql
CREATE INDEX idx_anvisa_search ON medicamentos_anvisa USING gin(search_vector);
CREATE INDEX idx_anvisa_trgm_nome ON medicamentos_anvisa USING gin(nome_produto gin_trgm_ops);
CREATE INDEX idx_anvisa_trgm_principio ON medicamentos_anvisa USING gin(principio_ativo gin_trgm_ops);
```

---

## Arquivos Relacionados
- `app/routers/web.py::pagina_buscar()`
- `app/repositories/medicamento_repo.py::buscar_medicamentos()`
- `app/services/busca_medicamento.py`
- `app/templates/buscar.html`
- `app/schemas/medicamento.py`

---

## Pendências Conhecidas
- [ ] Validar sync completo em produção (2.196 → 10.298 ativos)
- [ ] Testar performance com base completa em Railway
