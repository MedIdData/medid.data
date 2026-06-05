# MedID Data - Instruções para Claude

## Visão Geral
MedID Data é um SaaS B2B de validação de prescrições médicas para prevenir glosas.
Stack: FastAPI + PostgreSQL + Jinja2 + Railway

## Arquitetura
- `/app` - código principal
- `/app/routers` - rotas web e API
- `/app/services` - lógica de negócio
- `/app/repositories` - queries SQL
- `/app/schemas` - Pydantic models
- `/app/templates` - Jinja2 HTML
- `/scripts` - importação de dados

## Bases de Dados
- ANVISA: 32.496 medicamentos (10.298 ativos)
- CMED: preços PMC/PF/PMVG
- CID-10: diagnósticos
- SIGTAP: procedimentos SUS

## Performance Critical
- Busca usa pg_trgm + tsvector (similaridade fuzzy)
- LATERAL JOIN só em detail view (não em listing)
- Paginação: 50 itens/página
- Similaridade: 0.3 (busca geral) / 0.7 (análise risco)

## Regras de Desenvolvimento
1. **SEMPRE ler STATUS.md antes de iniciar**
2. **NUNCA** reler projeto inteiro
3. **Carregar apenas módulo impactado**
4. **Consultar docs antes de código**
5. **Atualizar STATUS.md ao finalizar**

## Deploy
- Platform: Railway
- Auto-deploy: git push origin main
- Database: PostgreSQL com extensões pg_trgm, unaccent
- Sync dados: `python3 scripts/sync_para_railway.py`

## Contato
Fundador: fabbiomonteiro@yahoo.com.br
