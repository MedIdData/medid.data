# Backlog - MedID Data

## 🔴 CRÍTICO - Correções Urgentes

### M1 - Busca de Medicamentos
**Status**: ✅ CONCLUÍDO  
**Prioridade**: CRÍTICA  
**Problemas resolvidos**:
- [x] Lista não aparece ao abrir a tela → Query vazia agora lista primeiros medicamentos
- [x] Letra "A" aparece automaticamente → Removido auto-redirect
- [x] Cursor retorna para início do campo → Removido auto-submit via JavaScript
- [x] Impossível digitar normalmente → Form usa comportamento HTML padrão
- [x] JavaScript interferindo na experiência → JavaScript simplificado (apenas focus)

**Arquivos modificados**:
- `app/templates/buscar.html` (JavaScript simplificado)
- `app/routers/web.py` (lógica simplificada)
- `app/repositories/medicamento_repo.py` (suporte query vazia)

**Commit**: `1bac73d`

---

### M2 - Análise de Risco - Gauge e Regras de Glosa
**Status**: 🔴 PENDENTE  
**Prioridade**: CRÍTICA

#### M2.1 - Gauge Invertido
**Status**: ✅ CONCLUÍDO
- [x] Gauge visual mostra risco ao contrário → Corrigido stroke-dashoffset
- [x] Fórmula correta: `totalArco * (1 - valor / 100)`

**Arquivos modificados**:
- `app/templates/analise.html` (linha 451)

**Commit**: `eafae63`

#### M2.2 - Validação de Campos
- [ ] Erro 500 ao inserir valores numéricos específicos
- [ ] Revisar conversões frontend/backend
- [ ] Garantir mensagens amigáveis

**Arquivos**:
- `app/schemas/analise.py` (validators Pydantic)
- `app/templates/analise.html` (validações HTML5)
- `app/routers/web.py` (tratamento de erros)

#### M2.3 - Regras de Potencial de Glosa
**Problema crítico**: Ausência de dados confiáveis está gerando RISCO BAIXO quando deveria ser ALTO.

- [ ] Medicamento não encontrado deve gerar RISCO ALTO
- [ ] CID/Procedimento ausentes devem aumentar risco
- [ ] Preço sem referência deve aumentar risco
- [ ] Dados inconsistentes devem aumentar risco
- [ ] Revisar pesos das 9 dimensões

**Arquivos**:
- `app/services/analise_risco.py` (scoring e pesos)
- `docs/GLOSA_RULES.md` (documentação)

---

## 🟡 ALTO - Melhorias UX

### M3 - Menu Dropdown de Usuário
**Status**: ✅ CONCLUÍDO (Fase 2)  
**Implementado**:
- [x] Dropdown clicável em nome/avatar
- [x] Itens: Perfil, Alterar Senha, Chaves, Consumo, Sair
- [x] Item "Administração" apenas para ADMIN
- [x] Rotas /perfil e /alterar-senha criadas

**Arquivos**:
- `app/templates/base.html`
- `app/templates/perfil.html`
- `app/templates/alterar_senha.html`
- `app/routers/web.py`

---

### M4 - Padronização Visual
**Status**: 🟡 PARCIAL

#### M4.1 - Chaves de Acesso
**Status**: ✅ OK (já padronizada)

#### M4.2 - Histórico de Consumo
**Status**: ✅ OK (já padronizada)

---

### M5 - Autocomplete na Busca
**Status**: 🔴 PENDENTE (relacionado a M1)  
- [ ] Auto-carregar primeiros resultados
- [ ] Filtro incremental em tempo real
- [ ] Debounce 600ms
- [ ] Sem necessidade de clicar "Buscar"

---

## 🟢 MÉDIO - Robustez

### M6 - Paridade Web/API
**Status**: 🟡 PARCIAL  
**Concluído**:
- [x] Validações Pydantic unificadas
- [x] HTML5 validation nos formulários

**Pendente**:
- [ ] Matriz de validação Web vs API
- [ ] Testes automáticos de paridade
- [ ] Documentação de regras compartilhadas

**Arquivos**:
- `app/schemas/analise.py`
- `app/templates/analise.html`
- `docs/API.md`

---

### M7 - Módulo Administrativo
**Status**: 🔴 PENDENTE  
**Prioridade**: MÉDIA

**Funcionalidades**:
- [ ] GET /admin - Dashboard administrativo
- [ ] Gestão de usuários (CRUD, ativar/desativar, resetar senha)
- [ ] Gestão de planos (criar, editar limites)
- [ ] Gestão de API Keys (visualizar todas, revogar, auditar)
- [ ] Dashboard: total usuários, consumo por cliente, top consumidores

**Segurança**:
- [ ] Middleware validação perfil=ADMINISTRADOR
- [ ] Frontend: esconder menu para CLIENTE

**Arquivos novos**:
- `app/routers/admin.py`
- `app/templates/admin/*.html`
- `app/middleware/admin_middleware.py`

---

### M8 - Testes Automatizados
**Status**: 🔴 PENDENTE  
**Prioridade**: MÉDIA

**Testes necessários**:
- [ ] test_auth.py: login sucesso/falha, cadastro, JWT refresh
- [ ] test_medicamentos.py: busca válida/vazia, fuzzy matching
- [ ] test_analise.py: análise válida, medicamento inexistente, campos inválidos
- [ ] test_consumo.py: incremento, limites diário/mensal
- [ ] test_api_keys.py: criação, autenticação, revogação

**Ferramenta**: pytest + pytest-asyncio

**Arquivos**:
- `tests/conftest.py` (fixtures)
- `tests/test_*.py`

---

### M9 - Auditoria Expandida
**Status**: 🔴 PENDENTE  
**Prioridade**: BAIXA

**Eventos a auditar**:
- [ ] Login/logout
- [ ] Criação de usuário
- [ ] Alteração de usuário
- [ ] Criação de chave API
- [ ] Revogação de chave
- [ ] Alteração de senha
- [ ] Alteração de plano

**Tabela**: `auditoria_requisicoes`  
**Campos**: usuario_id, acao, endpoint, ip, timestamp, dados_json

---

## 🔵 BAIXO - Futuro

### M10 - Webhooks
**Status**: 🔵 PLANEJADO  
- [ ] POST /usuario/webhooks
- [ ] Eventos: consumo_limite_atingido, chave_revogada

---

### M11 - Cache Redis
**Status**: 🔵 PLANEJADO  
- [ ] Cache busca de medicamentos (TTL 1h)
- [ ] Cache análise de risco para mesma entrada (TTL 5min)

---

### M12 - Exportação de Relatórios
**Status**: 🔵 PLANEJADO  
- [ ] GET /usuario/relatorio/pdf
- [ ] GET /usuario/relatorio/xlsx
- [ ] Dados: consumo mensal, análises realizadas, economia gerada

---

### M13 - Machine Learning - Predição de Glosa
**Status**: 🔵 PLANEJADO  
- [ ] Treinar modelo com histórico de glosas reais
- [ ] Endpoint POST /analise/ml-predict
- [ ] Precisão >85%

---

### M14 - Integrações com Sistemas de Saúde
**Status**: 🔵 PLANEJADO  
- [ ] Integração Tasy (via API)
- [ ] Integração MV (via HL7)
- [ ] Integração PEP genérico (webhook)

---

## 📊 Resumo

| Prioridade | Total | Concluídos | Pendentes | % |
|------------|-------|------------|-----------|---|
| 🔴 CRÍTICO | 3     | 2          | 1         | 67% |
| 🟡 ALTO    | 3     | 1          | 2         | 33% |
| 🟢 MÉDIO   | 4     | 0          | 4         | 0% |
| 🔵 BAIXO   | 4     | 0          | 4         | 0% |
| **TOTAL**  | **14**| **3**      | **11**    | **21%** |

---

**Última atualização**: 2026-06-04  
**Versão**: 1.0.0
