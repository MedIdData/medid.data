# Documentação - MedID Data

## 📚 Índice de Documentação

Esta pasta contém toda a documentação técnica e de negócio do MedID Data.

**IMPORTANTE**: Futuras sessões do Claude Code devem ler APENAS estes documentos antes de qualquer implementação, evitando releitura completa da base de código.

---

## 🎯 Visão Geral

### [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)
**Leia PRIMEIRO em toda nova sessão**
- Visão geral do produto
- Proposta de valor
- Módulos principais
- Stack tecnológica
- Roadmap

### [ARCHITECTURE.md](ARCHITECTURE.md)
**Leia para entender a estrutura**
- Arquitetura em camadas
- Estrutura de diretórios
- Fluxo de requisições
- Deploy Railway

### [FILE_MAP.md](FILE_MAP.md)
**Leia para saber onde estão os arquivos**
- Mapa completo de arquivos
- Finalidade de cada arquivo
- Dependências entre arquivos
- Módulos impactados

---

## 🗄️ Dados e Regras

### [DATABASE.md](DATABASE.md)
**Leia para entender o modelo de dados**
- Diagrama ER
- Todas as tabelas
- Relacionamentos
- Índices e constraints

### [BUSINESS_RULES.md](BUSINESS_RULES.md)
**Leia para entender as regras de negócio**
- Autenticação e autorização
- Planos e limites
- Busca de medicamentos
- Análise de risco
- Perfis de usuário

### [GLOSA_RULES.md](GLOSA_RULES.md)
**Leia para entender as regras de glosa**
- Fórmula de cálculo
- 9 dimensões de análise
- Scoring e pesos
- Exemplos práticos
- ⚠️ Problemas identificados

---

## 🔌 Integrações

### [API.md](API.md)
**Leia para conhecer os endpoints**
- Todos os endpoints REST
- Autenticação (JWT + API Keys)
- Request/Response examples
- Rate limiting

### [AUTH.md](AUTH.md)
**Leia para entender autenticação**
- Fluxo JWT completo
- Fluxo API Keys
- Refresh tokens
- Cookies e segurança

---

## 🎨 Interface

### [UI_COMPONENTS.md](UI_COMPONENTS.md)
**Leia para reutilizar componentes**
- Design System (cores, tipografia)
- Componentes reutilizáveis (.card, .btn, .badge, etc)
- Grid responsivo
- Gauge circular

---

## 📋 Planejamento

### [BACKLOG.md](BACKLOG.md)
**Leia para saber o que fazer**
- Módulos pendentes (M1-M14)
- Prioridades (CRÍTICO, ALTO, MÉDIO, BAIXO)
- Status de cada item
- Arquivos impactados

### [CHANGELOG.md](CHANGELOG.md)
**Leia para saber o que já foi feito**
- Histórico de versões
- Features implementadas
- Bugs corrigidos
- Problemas identificados

### [TECH_DEBT.md](TECH_DEBT.md)
**Leia para conhecer débitos técnicos**
- Dívidas técnicas priorizadas
- Esforço estimado
- Recomendação de sprints

### [ROADMAP.md](ROADMAP.md)
**Leia para visão de longo prazo**
- MVP (concluído)
- V1 (em andamento)
- V2 (planejado)
- V3 (futuro)
- Indicadores de sucesso

---

## 🔄 Fluxo de Trabalho

### Para Novas Sessões

1. **Ler contexto** (5min):
   ```
   1. PROJECT_CONTEXT.md
   2. FILE_MAP.md
   3. BACKLOG.md
   4. CHANGELOG.md
   ```

2. **Identificar módulo** (1min):
   - Qual módulo será implementado?
   - Quais arquivos serão impactados?

3. **Ler documentação específica** (5min):
   - Se API: API.md, AUTH.md
   - Se UI: UI_COMPONENTS.md
   - Se Regras: BUSINESS_RULES.md, GLOSA_RULES.md
   - Se DB: DATABASE.md

4. **Ler apenas arquivos impactados** (10min):
   - Não reler toda a base
   - Usar FILE_MAP.md para identificar dependências

5. **Implementar** (N horas)

6. **Atualizar documentação** (10min):
   - Marcar item no BACKLOG.md como concluído
   - Registrar no CHANGELOG.md
   - Atualizar FILE_MAP.md se criar novos arquivos
   - Atualizar TECH_DEBT.md se resolver débito

---

## 📝 Convenções

### Status nos Arquivos

- ✅ CONCLUÍDO
- 🔄 EM ANDAMENTO
- 🔴 PENDENTE
- ⚠️ BLOQUEADO
- 🔵 PLANEJADO

### Prioridades

- 🔴 CRÍTICO: Bloqueador, impede uso
- 🟡 ALTO: Impacta UX significativamente
- 🟢 MÉDIO: Melhoria importante
- 🔵 BAIXO: Nice to have

---

## 🚫 O Que NÃO Fazer

❌ **Não** reler toda a base de código a cada sessão  
❌ **Não** realizar descoberta arquitetural novamente  
❌ **Não** buscar informações já documentadas aqui  
❌ **Não** esquecer de atualizar BACKLOG.md e CHANGELOG.md  
❌ **Não** implementar sem ler a documentação primeiro  
❌ **Não** criar arquivos sem atualizar FILE_MAP.md  

---

## ✅ O Que Fazer

✅ **Sempre** ler PROJECT_CONTEXT.md em novas sessões  
✅ **Sempre** consultar FILE_MAP.md antes de modificar arquivos  
✅ **Sempre** atualizar BACKLOG.md após completar módulo  
✅ **Sempre** registrar mudanças no CHANGELOG.md  
✅ **Sempre** usar estes docs como fonte primária de contexto  

---

## 📞 Contato

**Fundador**: Fabbio Monteiro  
**Email**: fabbiomonteiro@yahoo.com.br  
**Projeto**: MedID Data B2B SaaS  

---

**Última atualização**: 2026-06-04  
**Versão da Documentação**: 1.0.0
