# Roadmap - MedID Data

---

## 🔥 Prioridade CRÍTICA (Produção Atual)

### ⏳ Em Andamento
- [ ] **Sync dados completos Local → Railway**
  - Status: Rodando em terminal separado
  - Aguardando: Cópia de 32.496 medicamentos
  - Validação: Verificar 10.298 ativos em produção

### 🎯 Próximos Passos Imediatos
- [ ] **Validar sync completo**
  - Acessar Railway e verificar contagem
  - Testar busca: "Resfenol" deve retornar ~102 resultados
  - Testar busca: "Gardenal" deve retornar ~9 resultados

---

## 📋 Backlog Identificado pelo Usuário

> Aguardando usuário listar pendências identificadas durante testes

### Categoria: Busca de Medicamentos
- (aguardando feedback)

### Categoria: Análise de Risco
- (aguardando feedback)

### Categoria: UX/UI
- (aguardando feedback)

### Categoria: Performance
- (aguardando feedback)

### Categoria: API
- (aguardando feedback)

---

## 🚀 Funcionalidades Futuras (Não Solicitadas)

### M7 - Relatórios e Analytics
- Dashboard administrativo
- Métricas de uso por usuário
- Relatórios de glosas evitadas
- Export CSV/PDF

### M8 - Integrações
- Webhook notificações
- API GraphQL (opcional)
- SDK Python/JavaScript
- Zapier/Make integration

### M9 - Machine Learning
- Predição de glosa com ML
- Sugestões de medicamentos alternativos
- Detecção de padrões anômalos

### M10 - Compliance e Auditoria
- Log de todas as análises
- Auditoria de acessos
- LGPD compliance
- Assinatura digital

---

## 🔧 Melhorias Técnicas Futuras

### Performance
- Cache Redis para medicamentos frequentes
- CDN para assets estáticos
- Índices adicionais no PostgreSQL
- Query optimization

### DevOps
- CI/CD com GitHub Actions
- Testes automatizados (pytest)
- Monitoramento (Sentry, New Relic)
- Backup automático diário

### Qualidade de Código
- Type hints completos
- Testes unitários >80% coverage
- Testes E2E com Playwright
- Linting automático (ruff, black)

---

## 📊 Métricas de Sucesso

### Atuais (Baseline)
- Performance busca: <1s
- Performance análise: <2s
- Uptime: 99.9%
- Base dados: 10.298 medicamentos ativos

### Metas Q3 2026
- (a definir com cliente)

---

## 🗓️ Timeline

### Junho 2026
- ✅ Semana 1: Infraestrutura base + M1 + M2 + M3
- 🔄 Semana 2: Refinamentos UX +Sync produção
- ⏳ Semana 3-4: (aguardando feedback do usuário)

### Julho-Agosto 2026
- (a definir após conclusão das pendências de junho)
