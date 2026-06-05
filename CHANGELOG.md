# Changelog - MedID Data

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/)

---

## [Unreleased]

### Em Progresso
- Sincronização completa dados Local → Railway (32.496 medicamentos)

---

## [2026-06-05] - Sistema de Busca e Análise Rigorosos

### Added
- Busca server-side na base completa (não mais limitada a 500 itens)
- Paginação com 50 itens por página
- Auto-submit com debounce de 500ms
- Glossário de siglas (PMC, PF, PMVG, CID, SIGTAP)
- Descrição de dimensões validadas na análise

### Changed
- **BREAKING:** Similaridade análise de risco: 0.25 → 0.7 (70% mínimo)
- **BREAKING:** Similaridade busca geral: 0.25 → 0.3 (30% mínimo)
- Pontuação medicamento não encontrado: 40 → 80 pontos (CRÍTICO)
- Pontuação medicamento inativo: 35 → 70 pontos (CRÍTICO)
- Pontuação CID ausente/inválido: 10-15 → 70-75 pontos (CRÍTICO)
- Pontuação SIGTAP ausente/inválido: 8-10 → 70-75 pontos (CRÍTICO)
- Ranges de preço mais agressivos: +10%, +20%, +50%, +100%, +200%
- Ranges de quantidade mais agressivos: 5+, 10+, 20+, 50+, 100+

### Fixed
- Busca agora encontra medicamentos conhecidos (Resfenol: 102 resultados, Gardenal: 9 resultados)
- Filtro "apenas ativos" funciona em toda a base, não apenas nos primeiros 500

### Performance
- Busca mantida em <1s com paginação
- JOIN LATERAL removido de listing (apenas em detail view)

---

## [2026-06-04] - Refatoração Completa Análise de Risco

### Changed
- **BREAKING:** Sistema de 9 dimensões → Score único 0-100
- Quanto MAIOR o score, MAIOR o risco (inverteu lógica anterior)
- Classificações: MUITO BAIXO, BAIXO, MÉDIO, ALTO, CRÍTICO

### Removed
- Cards individuais de dimensões (tratamento, CID, procedimento, etc)
- Gauge duplicado de aderência
- Detalhamento excessivo de pontuações

### Added
- Interface simplificada: gauge + score + classificação + motivos
- Lógica aditiva: começa em 0, soma pontos por problemas

---

## [2026-06-03] - Performance e UX Busca

### Fixed
- Performance listagem: 33s → <1s (removido JOIN LATERAL)
- Tooltip cortado no lado direito (nth-child right-align)
- Texto transbordando cards (word-break, line-clamp)
- Filtro "apenas ativos" client-side

### Changed
- Limite padrão: 20 → 500 medicamentos (para filtro client-side)
- Busca instantânea sem reload (JavaScript)

---

## [2026-06-02] - Motor de Análise de Risco

### Added
- Validação 9 dimensões de risco de glosa
- Fuzzy matching medicamento (ANVISA ↔ CMED por substância)
- Validação CID-10 e SIGTAP
- Score de aderência e risco

### Fixed
- CRÍTICO: JOIN ANVISA-CMED usando similarity em substância
- Extensões PostgreSQL em produção (pg_trgm, unaccent)

---

## [2026-06-01] - Base de Medicamentos

### Added
- Busca fuzzy com pg_trgm + tsvector
- Importação ANVISA (32.496 medicamentos)
- Importação CMED PMC/PMVG
- Filtro por status ativo/inativo
- Autocomplete em tempo real

---

## [2026-05-31] - Infraestrutura Base

### Added
- Setup FastAPI + SQLAlchemy + PostgreSQL
- Autenticação JWT (access + refresh tokens)
- Middleware de autenticação
- Templates Jinja2 base
- Deploy Railway
- Scripts de importação de dados

---

## Commits no Branch

Total: 22 commits aguardando produção
- 4962069 feat: busca server-side na base completa com paginação
- ff3b0aa feat: sistema de análise de risco mais rigoroso e completo
- 08247c6 fix: Converte Decimal para float na comparação de preços
- ... (19 commits anteriores)
