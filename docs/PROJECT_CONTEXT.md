# MedID Data - Contexto do Projeto

## 🎯 Visão Geral

**MedID Data** é uma plataforma B2B SaaS de inteligência em saúde que oferece análise de risco clínico e financeiro baseada em dados oficiais brasileiros (ANVISA, CMED, CID-10, SIGTAP, DCB).

**Fundador**: Fabbio Monteiro (fabbiomonteiro@yahoo.com.br)

**Proposta de Valor**:
- Reduzir glosas em operadoras de saúde
- Validar consistência clínica e financeira de prescrições
- Fornecer base de referência atualizada de medicamentos
- API REST para integração com sistemas hospitalares, ERPs, prontuários eletrônicos

---

## 📦 Módulos Principais

### Módulo 1: Base de Referência de Medicamentos
- **40.000+ medicamentos** com dados ANVISA + CMED
- Busca inteligente com fuzzy matching e correção ortográfica
- Preços regulados (PF, PMC, PMVG)
- Informações: registro, fabricante, classe terapêutica, tarja, situação

### Módulo 2: Motor de Análise de Risco
- **9 dimensões de análise**:
  1. Tratamento vs. Classe Terapêutica
  2. CID-10
  3. Procedimento SIGTAP
  4. CID + Procedimento (compatibilidade)
  5. Preço (comparação com tabela CMED)
  6. Quantidade prescrita
  7. Cobertura (se medicamento é coberto por planos)
  8. Situação ANVISA (registro ativo/inativo)
  9. Inconsistências (medicamento não encontrado, dados faltantes)
  
- **Pontuações**:
  - Aderência (0-100)
  - Risco (0-100)
  - Potencial de Glosa: BAIXO | MEDIO | ALTO
  - Motivos explicáveis em português

### Módulo 3: Gestão e Analytics
- Dashboard de consumo com gráficos
- Chaves de API para integrações
- Limites por plano (diário/mensal)
- Auditoria completa de requisições
- Planos: Gratuito, Profissional, Enterprise

---

## 🏗️ Stack Tecnológica

**Backend**:
- Python 3.11
- FastAPI 0.115
- SQLAlchemy 2.0
- PostgreSQL 16
- Pydantic 2.10

**Frontend**:
- Jinja2 Templates
- HTML5 + CSS3 (Design System customizado)
- JavaScript Vanilla
- Chart.js (gráficos)

**Autenticação**:
- JWT (access + refresh tokens)
- API Keys (formato `med_*`)
- bcrypt 4.1.3 (hash de senhas)
- Passlib 1.7.4

**Deploy**:
- Railway (PostgreSQL + App)
- Docker (multi-stage build)
- GitHub Actions (CI/CD)

**Observabilidade**:
- python-json-logger
- SlowAPI (rate limiting)
- Auditoria de requisições

---

## 📊 Dados Utilizados

| Base           | Fonte                  | Registros | Atualização |
|----------------|------------------------|-----------|-------------|
| ANVISA         | consultas.anvisa.gov.br| ~40.000   | Mensal      |
| CMED           | gov.br/anvisa/cmed     | ~18.000   | Mensal      |
| CID-10         | datasus.saude.gov.br   | 14.000+   | Anual       |
| SIGTAP         | sigtap.datasus.gov.br  | 4.000+    | Trimestral  |
| DCB            | anvisa.gov.br/dcb      | 3.000+    | Anual       |

---

## 🚀 Roadmap

### ✅ MVP (Concluído)
- [x] Infraestrutura base (FastAPI + PostgreSQL)
- [x] Modelos de dados completos
- [x] Scripts de importação de dados
- [x] Busca de medicamentos (fuzzy matching)
- [x] Motor de análise de risco (9 dimensões)
- [x] Autenticação JWT + API Keys
- [x] Interface Web (Jinja2)
- [x] Deploy Railway

### 🔄 V1 (Em Progresso)
- [ ] Correção de bugs críticos (gauge, busca, glosa)
- [ ] Menu dropdown de usuário
- [ ] Tela de perfil e alteração de senha
- [ ] Padronização visual completa
- [ ] Paridade Web/API (validações unificadas)
- [ ] Módulo administrativo (/admin)
- [ ] Testes automatizados (pytest)
- [ ] Auditoria expandida

### 📅 V2 (Planejado)
- [ ] Webhooks para eventos de consumo
- [ ] Cache Redis para consultas frequentes
- [ ] Exportação de relatórios (PDF/Excel)
- [ ] Machine Learning para predição de glosa
- [ ] Integração com sistemas de saúde (Tasy, MV)

### 🔮 Futuro
- [ ] API v2 com GraphQL
- [ ] App mobile nativo
- [ ] Marketplace de integrações
- [ ] BI embarcado (Metabase/Superset)

---

## 🎯 KPIs de Sucesso

**Técnicos**:
- Uptime: 99.9%
- Latência p95: < 500ms
- Taxa de erro: < 0.1%

**Negócio**:
- Redução de glosas: 30%+
- Tempo de validação: < 2s
- Satisfação NPS: 8+

---

## 📞 Contato

**Suporte**: fabbiomonteiro@yahoo.com.br  
**Documentação**: `/docs` (Swagger)  
**Status**: Railway Dashboard

---

**Última atualização**: 2026-06-04  
**Versão**: 1.0.0
