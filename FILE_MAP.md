# Mapa de Arquivos - MedID Data

## Módulos Principais

### 🔍 M1 - Busca de Medicamentos
**Responsabilidade:** Busca fuzzy na base ANVISA com paginação

**Arquivos:**
- `app/routers/web.py::pagina_buscar()` - rota GET /buscar
- `app/repositories/medicamento_repo.py::buscar_medicamentos()` - query com pg_trgm
- `app/services/busca_medicamento.py` - lógica de negócio
- `app/templates/buscar.html` - interface web
- `app/schemas/medicamento.py` - modelos Pydantic

**Dependências:**
- PostgreSQL extensões: pg_trgm, unaccent
- Tabelas: medicamentos_anvisa, medicamentos_cmed

**Specs:** `docs/specs/busca-medicamentos.md`

---

### ⚠️ M2 - Análise de Risco
**Responsabilidade:** Score 0-100 de risco de glosa

**Arquivos:**
- `app/routers/web.py::pagina_analise()` - rota GET /analise
- `app/services/analise_risco.py::analisar()` - motor de score
- `app/repositories/analise_repo.py` - queries validação
- `app/templates/analise.html` - interface web
- `app/schemas/analise.py` - AnaliseEntrada, AnaliseResultado

**Dependências:**
- Tabelas: medicamentos_anvisa, medicamentos_cmed, cid10_*, sigtap_*
- M1 (busca medicamento similar)

**Specs:** `docs/specs/analise-risco.md`

---

### 🔐 M3 - Autenticação
**Responsabilidade:** Login, cadastro, JWT

**Arquivos:**
- `app/routers/web.py::pagina_login()`, `processar_login()`, `pagina_cadastro()`, `processar_cadastro()`
- `app/routers/auth.py` - endpoints API /auth/*
- `app/services/auth_service.py` - hash senha, JWT tokens
- `app/middleware/auth_middleware.py` - proteção rotas
- `app/repositories/usuario_repo.py` - CRUD usuários
- `app/templates/login.html`, `cadastro.html`

**Dependências:**
- Tabelas: usuarios
- Lib: passlib, PyJWT

**Specs:** `docs/specs/autenticacao.md`

---

### 👤 M4 - Usuários e Planos
**Responsabilidade:** Perfis, planos, consumo

**Arquivos:**
- `app/routers/web.py::pagina_painel()` - dashboard
- `app/repositories/usuario_repo.py` - planos, consumo
- `app/templates/painel.html`
- `app/models/usuario.py` - SQLAlchemy models

**Dependências:**
- Tabelas: usuarios, planos, consumos
- M3 (autenticação)

**Specs:** `docs/specs/usuarios.md`

---

### 🔑 M5 - Chaves de Acesso (API)
**Responsabilidade:** API keys para integração

**Arquivos:**
- `app/routers/web.py::pagina_chaves()` - gestão chaves
- `app/routers/chave_acesso.py` - CRUD API
- `app/repositories/chave_repo.py`
- `app/templates/chaves.html`

**Dependências:**
- Tabelas: chaves_acesso
- M4 (usuários)

**Specs:** `docs/specs/chaves-acesso.md`

---

### 📊 M6 - API REST
**Responsabilidade:** Endpoints JSON para integração

**Arquivos:**
- `app/routers/medicamentos.py` - GET /api/medicamentos
- `app/routers/analise.py` - POST /api/analise
- `app/middleware/api_auth.py` - validação API key

**Dependências:**
- M1, M2, M5

**Specs:** `docs/specs/api.md`

---

## Scripts

### Importação de Dados
- `scripts/importar_anvisa.py` - CSV ANVISA → PostgreSQL
- `scripts/importar_cmed.py` - XLSX CMED → PostgreSQL
- `scripts/importar_cid10.py` - CSV CID-10 → PostgreSQL
- `scripts/importar_sigtap.py` - TXT SIGTAP → PostgreSQL

### Sincronização
- `scripts/sync_para_railway.py` - Local → Railway (produção)

---

## Configuração
- `app/config.py` - settings from env vars
- `app/database.py` - SQLAlchemy engine
- `.env` - variáveis locais (não commitado)

---

## Templates Base
- `app/templates/base.html` - layout comum
- `app/templates/base_auth.html` - layout páginas públicas

---

## Modelos de Dados
- `app/models/usuario.py` - Usuario, Plano, Consumo, ChaveAcesso
- `app/models/medicamento.py` - MedicamentoAnvisa, MedicamentoCmed
- `app/models/cid.py` - CID10Categoria, CID10Subcategoria
- `app/models/sigtap.py` - SigtapGrupo, SigtapProcedimento
