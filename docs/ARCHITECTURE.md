# Arquitetura - MedID Data

## 📐 Visão Geral

MedID Data segue arquitetura em camadas com separação clara de responsabilidades:

```
┌─────────────────────────────────────────────────────────┐
│                    INTERFACE WEB                         │
│              (Jinja2 Templates + HTML/CSS/JS)            │
└─────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│                     API REST                             │
│                  (FastAPI Routers)                       │
└─────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│                  CAMADA DE SERVIÇOS                      │
│         (Business Logic + Motor de Análise)              │
└─────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│               CAMADA DE REPOSITÓRIOS                     │
│              (Data Access Layer - SQLAlchemy)            │
└─────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│                  BANCO DE DADOS                          │
│                 (PostgreSQL 16)                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🗂️ Estrutura de Diretórios

```
mediddata/
├── app/
│   ├── main.py                    # Entry point FastAPI
│   ├── config.py                  # Configurações (Settings)
│   ├── database.py                # Engine SQLAlchemy + Session
│   │
│   ├── models/                    # SQLAlchemy Models (ORM)
│   │   ├── usuario.py
│   │   ├── plano.py
│   │   ├── chave_acesso.py
│   │   ├── consumo_diario.py
│   │   ├── medicamento_anvisa.py
│   │   ├── medicamento_cmed.py
│   │   ├── cid10.py
│   │   ├── sigtap.py
│   │   └── dcb.py
│   │
│   ├── schemas/                   # Pydantic Schemas (Validation)
│   │   ├── auth.py
│   │   ├── usuario.py
│   │   ├── analise.py
│   │   └── medicamento.py
│   │
│   ├── routers/                   # FastAPI Routers (Endpoints)
│   │   ├── auth.py                # POST /auth/login, /auth/cadastro
│   │   ├── usuario.py             # GET /usuario/consumo, /usuario/chaves
│   │   ├── medicamentos.py        # GET /medicamentos/buscar
│   │   ├── analise.py             # POST /analise/risco
│   │   └── web.py                 # Rotas HTML (Jinja2)
│   │
│   ├── services/                  # Lógica de Negócio
│   │   ├── auth_service.py        # JWT, hash senha, chaves API
│   │   ├── busca_medicamento.py   # Fuzzy search, sugestões
│   │   └── analise_risco.py       # Motor de análise 9 dimensões
│   │
│   ├── repositories/              # Data Access Layer
│   │   ├── usuario_repo.py        # CRUD usuário, consumo, chaves
│   │   ├── medicamento_repo.py    # Query medicamentos ANVISA/CMED
│   │   ├── cid_repo.py            # Query CID-10
│   │   └── sigtap_repo.py         # Query SIGTAP
│   │
│   ├── middleware/                # Middlewares FastAPI
│   │   ├── auth_middleware.py     # Validação JWT/API Key
│   │   └── rate_limit.py          # SlowAPI (opcional)
│   │
│   ├── templates/                 # Jinja2 Templates
│   │   ├── base.html              # Template base (sidebar, topbar)
│   │   ├── login.html
│   │   ├── cadastro.html
│   │   ├── painel.html
│   │   ├── buscar.html
│   │   ├── analise.html
│   │   ├── chaves.html
│   │   ├── consumo.html
│   │   ├── perfil.html
│   │   └── alterar_senha.html
│   │
│   └── scripts/                   # Scripts de importação de dados
│       ├── importar_anvisa.py
│       ├── importar_cmed.py
│       ├── importar_cid10.py
│       ├── importar_sigtap.py
│       └── importar_dcb.py
│
├── dados/                         # Arquivos CSV/XLSX (não versionados)
│   ├── medicamentos_anvisa.xlsx
│   ├── precos_cmed.xlsx
│   ├── cid10_categorias.csv
│   ├── cid10_subcategorias.csv
│   ├── sigtap_procedimentos.csv
│   └── dcb_lista.xlsx
│
├── docs/                          # Documentação (esta pasta)
├── tests/                         # Testes automatizados
├── Dockerfile                     # Build Docker
├── docker-compose.yml             # Orquestração local
├── requirements.txt               # Dependências Python
├── setup_prod.py                  # Setup inicial PostgreSQL
├── start.sh                       # Script de inicialização Railway
└── railway.toml                   # Config Railway

```

---

## 🔐 Camada de Autenticação

### Fluxo JWT (Web)

1. **Login**: POST `/auth/login` → retorna `access_token` + `refresh_token` em cookies HttpOnly
2. **Middleware**: `auth_middleware.py` lê cookie `access_token` e valida JWT
3. **Refresh**: POST `/auth/refresh` → renova access_token usando refresh_token
4. **Logout**: POST `/sair` → deleta cookies

### Fluxo API Key (Integrações)

1. **Criação**: POST `/usuario/chaves` → gera chave `med_*` (48 chars)
2. **Autenticação**: Header `Authorization: Bearer med_*` ou `X-API-Key: med_*`
3. **Middleware**: `auth_middleware.py` valida hash da chave no banco
4. **Revogação**: DELETE `/usuario/chaves/{id}` → marca como inativa

---

## 🧠 Camada de Serviços

### `auth_service.py`
- `criar_access_token()`: Gera JWT com exp 30min
- `criar_refresh_token()`: Gera JWT com exp 7 dias
- `verificar_senha()`: bcrypt.checkpw
- `hash_senha()`: bcrypt.hashpw
- `gerar_chave_acesso()`: secrets.token_urlsafe(36) → `med_*`

### `busca_medicamento.py`
- `buscar()`: Fuzzy matching com `ILIKE %termo%`
- `sugerir()`: Correção ortográfica básica
- Filtros: `apenas_ativos`, paginação

### `analise_risco.py`
- `analisar()`: Motor principal (9 dimensões)
- `_d1_tratamento_classe()`: Valida classe terapêutica vs tratamento
- `_d2_cid()`: Valida CID-10 existe
- `_d3_procedimento()`: Valida SIGTAP existe
- `_d4_cid_procedimento()`: Compatibilidade CID + SIGTAP
- `_d5_preco()`: Comparação com PF/PMC/PMVG
- `_d6_quantidade()`: Quantidade esperada vs informada
- `_d7_cobertura()`: Medicamento coberto por planos
- `_d8_situacao_anvisa()`: Registro ativo/inativo
- `_d9_inconsistencias()`: Medicamento não encontrado, dados faltantes

**Scoring**:
- Cada dimensão retorna: `(Situacao, motivos[])`
- Situacao: `ADERENTE | ATENCAO | NAO_ADERENTE | NAO_INFORMADO`
- Pesos: `ADERENTE=0`, `ATENCAO=1`, `NAO_ADERENTE=3`, `NAO_INFORMADO=0`
- Pontuação final: `100 - (soma_pesos / 27 * 100)`
- Potencial glosa: `BAIXO (<30%)`, `MEDIO (30-60%)`, `ALTO (>60%)`

---

## 🗄️ Camada de Repositórios

### `usuario_repo.py`
- `criar_usuario()`
- `buscar_por_email()`
- `obter_plano_usuario()`
- `incrementar_consumo()`
- `obter_consumo_total_dia()`
- `obter_consumo_mensal()`
- `criar_chave_acesso()`
- `validar_chave_acesso()`
- `revogar_chave_acesso()`

### `medicamento_repo.py`
- `buscar_medicamento_anvisa()`
- `buscar_medicamento_cmed()`
- `obter_medicamento_por_id()`

### `cid_repo.py`
- `buscar_cid()`
- `obter_categoria()`
- `obter_subcategoria()`

### `sigtap_repo.py`
- `buscar_procedimento()`
- `obter_procedimentos_por_cid()`

---

## 🎨 Camada de Interface

### Design System

**Cores**:
- Azul: `#0F4C81` (primário)
- Teal: `#14B8A6` (destaque)
- Âmbar: `#F59E0B` (atenção)
- Vermelho: `#EF4444` (erro/alto risco)

**Tipografia**:
- Títulos: `Syne` (700/800)
- Corpo: `DM Sans` (300/400/500)

**Componentes Reutilizáveis**:
- `.card`: Container padrão
- `.btn`: Botões (primário, secundário, perigo)
- `.badge`: Etiquetas (info, success, warning, danger)
- `.alerta`: Mensagens (sucesso, erro, info)
- `.tabela`: Tabelas responsivas
- `.modal`: Modais overlay

### Templates

**Base** (`base.html`):
- Sidebar fixa com navegação
- Topbar com título e menu usuário
- Área de conteúdo responsiva

**Páginas**:
- `login.html`: Formulário login
- `painel.html`: Dashboard resumo
- `buscar.html`: Busca medicamentos
- `analise.html`: Formulário + resultado análise
- `chaves.html`: Gerenciar API keys
- `consumo.html`: Gráficos consumo
- `perfil.html`: Dados do usuário
- `alterar_senha.html`: Trocar senha

---

## 🚀 Deploy

### Railway

**Serviços**:
1. PostgreSQL 16 (managed)
2. App FastAPI (Docker)

**Variáveis de Ambiente**:
```env
DATABASE_URL=postgresql://...
SECRET_KEY=<openssl rand -hex 32>
ENVIRONMENT=production
ALLOWED_ORIGINS=https://seuapp.com
RATE_LIMIT_ENABLED=true
LOG_FORMAT=json
```

**Build**:
- Dockerfile multi-stage (build + runtime)
- `start.sh`: Expande `$PORT` para Railway
- Health check: `/saude`

### GitHub Actions (Futuro)
- Testes automáticos em PRs
- Deploy automático após merge na main

---

## 📊 Observabilidade

### Logs
- JSON structured (python-json-logger)
- Níveis: DEBUG (dev), INFO (prod)

### Rate Limiting
- SlowAPI: 100 req/min por IP (opcional)
- Limites por plano no banco de dados

### Auditoria
- Tabela `auditoria_requisicoes` (futuro)
- Campos: usuario_id, endpoint, timestamp, ip, status_code

---

## 🔒 Segurança

### Autenticação
- JWT com exp 30min (access) + 7 dias (refresh)
- Senha hash bcrypt (cost 12)
- API Keys SHA256 hash

### HTTP
- HTTPS obrigatório em produção (Railway automático)
- Cookies HttpOnly + SameSite=Lax
- CORS configurável (ALLOWED_ORIGINS)

### Banco de Dados
- Prepared statements (SQLAlchemy ORM)
- Nenhuma query raw sem sanitização
- Índices em campos sensíveis (email, chave_hash)

---

**Última atualização**: 2026-06-04  
**Versão**: 1.0.0
