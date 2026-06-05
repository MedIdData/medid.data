# Dívida Técnica - MedID Data

## 🔴 CRÍTICO

### 1. ~~Gauge Invertido (analise.html)~~ ✅ RESOLVIDO
**Problema**: Correção aplicada inverteu ainda mais o visual do gauge  
**Localização**: `app/templates/analise.html` linha 451  
**Impacto**: Usuário vê risco baixo quando é alto e vice-versa  
**Solução**: Revertido para fórmula correta: `totalArco * (1 - valor / 100)`  
**Esforço**: 1h  
**Status**: ✅ Resolvido no commit `eafae63` (M2.1)

### 2. ~~Busca Travada (buscar.html)~~ ✅ RESOLVIDO
**Problema**: Letra "A" auto-carrega e reaparece, cursor volta ao início  
**Localização**: `app/templates/buscar.html` linhas 450-485 (JavaScript)  
**Impacto**: Impossível digitar normalmente  
**Solução**: Removido auto-redirect, auto-submit e event listener input  
**Esforço**: 2h  
**Status**: ✅ Resolvido no commit `1bac73d` (M1)

### 3. Potencial de Glosa Incorreto
**Problema**: Falta de dados confiáveis gera risco BAIXO (deveria ser ALTO)  
**Localização**: `app/services/analise_risco.py` (scoring e pesos)  
**Impacto**: Análise clínica incorreta, risco de glosas não detectadas  
**Solução**: Aumentar peso de NAO_ADERENTE quando medicamento não encontrado  
**Esforço**: 4h (incluindo testes)

---

## 🟡 ALTO

### 4. Validação de Campos (erro 500)
**Problema**: Valores numéricos específicos causam erro interno  
**Localização**: `app/schemas/analise.py`, `app/routers/web.py`  
**Impacto**: UX ruim, erro 500 ao invés de mensagem amigável  
**Solução**: Melhorar try/catch e parsing de erros Pydantic  
**Esforço**: 2h

### 5. Sem Testes Automatizados
**Problema**: Nenhum teste pytest implementado  
**Impacto**: Regressões não detectadas, difícil refatorar com segurança  
**Solução**: Criar suite básica (auth, busca, análise)  
**Esforço**: 8h

### 6. Sem Auditoria
**Problema**: Nenhum log de ações críticas (login, alteração senha, etc)  
**Impacto**: Impossível rastrear ações suspeitas  
**Solução**: Implementar tabela auditoria_requisicoes  
**Esforço**: 4h

---

## 🟢 MÉDIO

### 7. Fuzzy Matching Básico
**Problema**: Busca usa apenas `ILIKE %termo%`, sem ranking de relevância  
**Impacto**: Resultados menos precisos  
**Solução**: Implementar pg_trgm ou Elasticsearch  
**Esforço**: 6h

### 8. Sem Cache
**Problema**: Toda busca/análise bate no banco  
**Impacto**: Latência alta em picos de uso  
**Solução**: Redis para cache de busca (TTL 1h)  
**Esforço**: 4h

### 9. Sem Rate Limiting por Usuário
**Problema**: SlowAPI limita por IP, não por user_id  
**Impacto**: Bypass via múltiplos IPs  
**Solução**: Implementar rate limit baseado em user_id  
**Esforço**: 3h

### 10. Sem Bloqueio por Tentativas Falhas
**Problema**: Login permite tentativas ilimitadas  
**Impacto**: Vulnerável a brute force  
**Solução**: Bloquear por 15min após 5 falhas  
**Esforço**: 2h

---

## 🔵 BAIXO

### 11. Senhas Sem Validação de Complexidade
**Problema**: Aceita senhas fracas (ex: "123456")  
**Impacto**: Segurança reduzida  
**Solução**: Exigir mínimo 8 chars + letra + número  
**Esforço**: 1h

### 12. Sem Logs Estruturados
**Problema**: Logs em texto livre, difícil de parsear  
**Impacto**: Troubleshooting lento  
**Solução**: python-json-logger já instalado, apenas configurar  
**Esforço**: 1h

### 13. Sem Paginação em Consumo
**Problema**: GET /usuario/consumo retorna sempre 30 dias fixos  
**Impacto**: Performance ruim com histórico longo  
**Solução**: Adicionar ?data_inicio e ?data_fim  
**Esforço**: 2h

### 14. Sugestão Ortográfica Simples
**Problema**: Algoritmo básico de distância de edição  
**Impacto**: Sugestões imprecisas  
**Solução**: Implementar algoritmo mais robusto (ex: Levenshtein)  
**Esforço**: 3h

### 15. Sem Webhooks
**Problema**: Cliente precisa polling para eventos  
**Impacto**: Latência e desperdício de requests  
**Solução**: Implementar webhooks para limite_atingido, chave_revogada  
**Esforço**: 6h

### 16. Sem Exportação de Relatórios
**Problema**: Dados só disponíveis via API/interface  
**Impacto**: Cliente precisa integrar para gerar relatórios  
**Solução**: GET /usuario/relatorio/pdf e /xlsx  
**Esforço**: 8h

---

## 📊 Resumo por Esforço

| Prioridade | Item | Esforço | Impacto |
|------------|------|---------|---------|
| 🔴 CRÍTICO | Gauge invertido | 1h | Alto |
| 🔴 CRÍTICO | Busca travada | 2h | Alto |
| 🔴 CRÍTICO | Potencial glosa | 4h | Muito Alto |
| 🟡 ALTO | Validação campos | 2h | Médio |
| 🟡 ALTO | Testes automatizados | 8h | Muito Alto |
| 🟡 ALTO | Auditoria | 4h | Médio |
| 🟢 MÉDIO | Fuzzy matching | 6h | Médio |
| 🟢 MÉDIO | Cache Redis | 4h | Alto |
| 🟢 MÉDIO | Rate limit user | 3h | Médio |
| 🟢 MÉDIO | Bloqueio login | 2h | Baixo |
| 🔵 BAIXO | Senha complexa | 1h | Baixo |
| 🔵 BAIXO | Logs JSON | 1h | Baixo |
| 🔵 BAIXO | Paginação consumo | 2h | Baixo |
| 🔵 BAIXO | Sugestão ortográfica | 3h | Baixo |
| 🔵 BAIXO | Webhooks | 6h | Médio |
| 🔵 BAIXO | Relatórios | 8h | Médio |

**Total**: ~57h de esforço

---

## 🎯 Recomendação de Priorização

### Sprint 1 (7h)
1. ✅ Gauge invertido (1h)
2. ✅ Busca travada (2h)
3. ✅ Potencial glosa (4h)

### Sprint 2 (10h)
4. ✅ Validação campos (2h)
5. ✅ Testes automatizados (8h)

### Sprint 3 (13h)
6. ✅ Auditoria (4h)
7. ✅ Fuzzy matching (6h)
8. ✅ Rate limit user (3h)

### Sprint 4 (11h)
9. ✅ Cache Redis (4h)
10. ✅ Bloqueio login (2h)
11. ✅ Senha complexa (1h)
12. ✅ Logs JSON (1h)
13. ✅ Paginação consumo (2h)

### Futuro (17h)
14. Sugestão ortográfica (3h)
15. Webhooks (6h)
16. Relatórios (8h)

---

**Última atualização**: 2026-06-04  
**Versão**: 1.0.0
