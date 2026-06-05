# Roadmap - MedID Data

## ✅ MVP (Concluído - Maio 2026)

### Infraestrutura
- [x] FastAPI + SQLAlchemy + PostgreSQL
- [x] Docker multi-stage build
- [x] Deploy Railway
- [x] Script setup_prod.py

### Autenticação
- [x] JWT (access + refresh tokens)
- [x] API Keys (formato med_*)
- [x] bcrypt para senhas

### Módulos Core
- [x] Busca de medicamentos (fuzzy matching)
- [x] Motor de análise de risco (9 dimensões)
- [x] Dashboard de consumo
- [x] Gestão de chaves API

### Interface
- [x] Design System customizado
- [x] Templates Jinja2 (login, painel, buscar, analise, chaves, consumo)
- [x] Layout responsivo

### Dados
- [x] Importação ANVISA (~40k medicamentos)
- [x] Importação CMED (~18k preços)
- [x] Importação CID-10 (~14k códigos)
- [x] Importação SIGTAP (~4k procedimentos)
- [x] Importação DCB (~3k denominações)

---

## 🔄 V1 (Em Andamento - Junho 2026)

### Correções Críticas
- [ ] **M1**: Busca de medicamentos (auto-load, filtro real-time, cursor travado)
- [ ] **M2.1**: Gauge invertido (correção do stroke-dashoffset)
- [ ] **M2.2**: Validação de campos (tratamento de erros Pydantic)
- [ ] **M2.3**: Regras de glosa (ausência de dados = risco alto)

### UX/Design
- [x] **M3**: Menu dropdown de usuário (Perfil, Senha, Chaves, Consumo, Admin, Sair)
- [x] Rotas /perfil e /alterar-senha
- [ ] **M5**: Autocomplete na busca (auto-load + debounce)

### Robustez
- [ ] **M6**: Paridade Web/API (matriz de validação)
- [ ] **M7**: Módulo administrativo (/admin)
  - [ ] Dashboard admin
  - [ ] Gestão de usuários
  - [ ] Gestão de planos
  - [ ] Gestão de API Keys global
- [ ] **M8**: Testes automatizados (pytest)
  - [ ] test_auth.py
  - [ ] test_medicamentos.py
  - [ ] test_analise.py
  - [ ] test_consumo.py
- [ ] **M9**: Auditoria expandida
  - [ ] Tabela auditoria_requisicoes
  - [ ] Logs de login/logout, alteração senha, CRUD

### Segurança
- [ ] Rate limiting por user_id (não apenas IP)
- [ ] Bloqueio após 5 tentativas de login
- [ ] Validação de complexidade de senha (8+ chars, letra + número)
- [ ] Logs estruturados (JSON)

**Meta de entrega**: Final de Junho 2026

---

## 📅 V2 (Julho-Agosto 2026)

### Performance
- [ ] Cache Redis para busca de medicamentos (TTL 1h)
- [ ] Cache Redis para análise de risco (TTL 5min)
- [ ] Índices adicionais no PostgreSQL
- [ ] Query optimization (EXPLAIN ANALYZE)

### UX Avançado
- [ ] Fuzzy matching com ranking de relevância (pg_trgm)
- [ ] Sugestão ortográfica avançada (Levenshtein)
- [ ] Autocomplete com highlight de termos
- [ ] Histórico de buscas recentes (localStorage)

### Analytics
- [ ] Exportação de relatórios (PDF + XLSX)
- [ ] Dashboard executivo (gráficos avançados)
- [ ] Paginação em histórico de consumo (?data_inicio, ?data_fim)
- [ ] Comparativo mensal (tendências)

### Integrações
- [ ] Webhooks para eventos
  - [ ] limite_diario_atingido
  - [ ] limite_mensal_atingido
  - [ ] chave_revogada
  - [ ] analise_alto_risco
- [ ] API v2 (GraphQL)
- [ ] SDK Python
- [ ] SDK Node.js

**Meta de entrega**: Final de Agosto 2026

---

## 🔮 V3 (Setembro-Dezembro 2026)

### Machine Learning
- [ ] Modelo de predição de glosa (precision >85%)
- [ ] Treinamento com histórico de glosas reais
- [ ] Endpoint POST /analise/ml-predict
- [ ] Explainability (SHAP values)

### Integrações Hospitalares
- [ ] Integração Tasy (via API REST)
- [ ] Integração MV (via HL7)
- [ ] Integração PEP genérico (webhook)
- [ ] SSO via SAML/OAuth2

### Mobile
- [ ] App iOS nativo (Swift)
- [ ] App Android nativo (Kotlin)
- [ ] Notificações push
- [ ] Análise offline (SQLite)

### BI Embarcado
- [ ] Metabase/Superset integrado
- [ ] Dashboards customizáveis
- [ ] Alertas automáticos
- [ ] Agendamento de relatórios

**Meta de entrega**: Final de 2026

---

## 🚀 Futuro (2027+)

### Marketplace
- [ ] Marketplace de integrações (plugins)
- [ ] API pública para desenvolvedores
- [ ] Certificação de parceiros

### AI Avançada
- [ ] Chatbot para auditoria clínica
- [ ] OCR para prescrições médicas
- [ ] Análise de imagens (exames)

### Expansão Internacional
- [ ] Base de dados FDA (USA)
- [ ] Base de dados EMA (Europa)
- [ ] Multi-idioma (EN, ES)

### Blockchain
- [ ] Auditoria imutável em blockchain
- [ ] Timestamping de análises
- [ ] Smart contracts para glosas

---

## 📊 Indicadores de Sucesso

### V1 (Junho 2026)
- ✅ 0 bugs críticos em produção
- ✅ Cobertura de testes >70%
- ✅ Latência p95 <500ms
- ✅ Uptime 99.5%+

### V2 (Agosto 2026)
- ✅ 100 clientes ativos
- ✅ 500k análises/mês
- ✅ NPS >8
- ✅ Latência p95 <300ms

### V3 (Dezembro 2026)
- ✅ 500 clientes ativos
- ✅ 2M análises/mês
- ✅ ML precision >85%
- ✅ 3 integrações hospitalares live

### 2027
- ✅ 1.000 clientes
- ✅ 10M análises/mês
- ✅ Expansão internacional (USA)
- ✅ Serie A funding

---

**Última atualização**: 2026-06-04  
**Versão**: 1.0.0  
**Responsável**: Fabbio Monteiro (fabbiomonteiro@yahoo.com.br)
