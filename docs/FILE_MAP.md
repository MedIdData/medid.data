# Mapa de Arquivos - MedID Data

## 📁 Estrutura Completa

### `/app` - Aplicação Principal

#### `main.py`
**Finalidade**: Entry point FastAPI  
**Dependências**: config, database, routers  
**Módulos**: Todos (inicialização)

#### `config.py`
**Finalidade**: Configurações via Pydantic Settings  
**Dependências**: pydantic-settings, dotenv  
**Variáveis**:
- DATABASE_URL
- SECRET_KEY
- ENVIRONMENT
- ACCESS_TOKEN_EXPIRE_MINUTES (30)
- REFRESH_TOKEN_EXPIRE_DAYS (7)

#### `database.py`
**Finalidade**: Engine SQLAlchemy + Session  
**Dependências**: sqlalchemy, config  
**Exports**: `Base`, `get_db()`

---

### `/app/models` - SQLAlchemy ORM

| Arquivo | Tabela | Dependências | Módulos Impactados |
|---------|--------|--------------|-------------------|
| `usuario.py` | usuarios, refresh_tokens | empresa | Auth, Usuário, Consumo |
| `empresa.py` | empresas | plano | Usuário, Admin |
| `chave_acesso.py` | chaves_acesso | usuario | Auth, Usuário |
| `medicamento.py` | medicamentos_anvisa, medicamentos_cmed | - | Busca, Análise |
| `referencia.py` | cid10_*, sigtap_*, dcb_lista | - | Análise |
| `auditoria.py` | auditoria_requisicoes | usuario | Admin |

---

### `/app/schemas` - Pydantic Validation

| Arquivo | Finalidade | Usado em |
|---------|-----------|----------|
| `auth.py` | LoginEntrada, CadastroEntrada, TokenResposta | POST /auth/login, /auth/cadastro |
| `usuario.py` | ConsumoResposta, ChaveAcessoEntrada, AtualizarSenhaEntrada | GET /usuario/*, PUT /usuario/* |
| `analise.py` | AnaliseEntrada, AnaliseResultado, Situacao | POST /analise/risco |
| `medicamento.py` | BuscaMedicamentoResposta | GET /medicamentos/buscar |

---

### `/app/routers` - FastAPI Endpoints

| Arquivo | Rotas | Autenticação | Módulos |
|---------|-------|--------------|---------|
| `auth.py` | /auth/login, /auth/cadastro, /auth/refresh, /auth/logout | Público (exceto /me) | Auth |
| `usuario.py` | /usuario/consumo, /usuario/chaves, /usuario/perfil, /usuario/senha | JWT ou API Key | Usuário |
| `medicamentos.py` | /medicamentos/buscar, /medicamentos/{id} | JWT ou API Key | Busca |
| `analise.py` | /analise/risco | JWT ou API Key | Análise Risco |
| `web.py` | /, /login, /painel, /buscar, /analise, /chaves, /consumo, /perfil, /alterar-senha | Cookies JWT | Web UI |

---

### `/app/services` - Lógica de Negócio

| Arquivo | Funções Principais | Usado em |
|---------|-------------------|----------|
| `auth_service.py` | criar_access_token, criar_refresh_token, hash_senha, verificar_senha, gerar_chave_acesso | routers/auth, routers/usuario |
| `busca_medicamento.py` | buscar(db, termo, apenas_ativos, pagina, limite) | routers/medicamentos, routers/web |
| `analise_risco.py` | analisar(db, entrada) → AnaliseResultado | routers/analise, routers/web |

---

### `/app/repositories` - Data Access

| Arquivo | Responsabilidade | Usado em |
|---------|------------------|----------|
| `usuario_repo.py` | CRUD usuário, consumo, chaves, planos | services, routers |
| `medicamento_repo.py` | Query medicamentos ANVISA/CMED | services/busca_medicamento |
| `cid_repo.py` | Query CID-10 | services/analise_risco |
| `sigtap_repo.py` | Query SIGTAP | services/analise_risco |

---

### `/app/middleware` - Middlewares

| Arquivo | Finalidade | Usado em |
|---------|-----------|----------|
| `auth_middleware.py` | get_usuario_atual, requer_usuario, requer_usuario_web, requer_acesso | Todos routers autenticados |

---

### `/app/templates` - Jinja2 HTML

| Arquivo | Rota | Autenticação |
|---------|------|--------------|
| `base.html` | - | Template base (sidebar, topbar, menu dropdown) |
| `login.html` | GET /login | Público |
| `cadastro.html` | GET /cadastro | Público |
| `painel.html` | GET /painel | Requer login |
| `buscar.html` | GET /buscar | Requer login |
| `analise.html` | GET /analise | Requer login |
| `chaves.html` | GET /chaves | Requer login |
| `consumo.html` | GET /consumo | Requer login |
| `perfil.html` | GET /perfil | Requer login |
| `alterar_senha.html` | GET /alterar-senha | Requer login |

---

### `/app/scripts` - Importação de Dados

| Arquivo | Finalidade | Tabela Destino |
|---------|-----------|----------------|
| `importar_anvisa.py` | Importa medicamentos_anvisa.xlsx | medicamentos_anvisa |
| `importar_cmed.py` | Importa precos_cmed.xlsx | medicamentos_cmed |
| `importar_cid10.py` | Importa cid10_*.csv | cid10_categorias, cid10_subcategorias |
| `importar_sigtap.py` | Importa sigtap_*.csv | sigtap_grupos, sigtap_procedimentos, sigtap_procedimento_cid |
| `importar_dcb.py` | Importa dcb_lista.xlsx | dcb_lista |

---

### Raiz `/`

| Arquivo | Finalidade |
|---------|-----------|
| `Dockerfile` | Build Docker multi-stage |
| `docker-compose.yml` | Orquestração local (app + postgres + redis) |
| `requirements.txt` | Dependências Python |
| `setup_prod.py` | Setup inicial (criar tabelas + plano + admin) |
| `start.sh` | Script de inicialização Railway (expande $PORT) |
| `railway.toml` | Config Railway (startCommand, healthcheckPath) |
| `.env.example` | Template variáveis de ambiente |
| `README.md` | Documentação principal |
| `RAILWAY_SETUP.md` | Guia de deploy Railway |

---

### `/dados` (não versionado)

Arquivos CSV/XLSX importados:
- medicamentos_anvisa.xlsx (~40.000 linhas)
- precos_cmed.xlsx (~18.000 linhas)
- cid10_categorias.csv (~2.000 linhas)
- cid10_subcategorias.csv (~12.000 linhas)
- sigtap_procedimentos.csv (~4.000 linhas)
- dcb_lista.xlsx (~3.000 linhas)

---

### `/docs` - Documentação

| Arquivo | Conteúdo |
|---------|----------|
| PROJECT_CONTEXT.md | Visão geral, roadmap, stack |
| ARCHITECTURE.md | Arquitetura, camadas, deploy |
| DATABASE.md | Modelo de dados, tabelas, relacionamentos |
| API.md | Endpoints REST |
| GLOSA_RULES.md | Regras de potencial de glosa |
| BUSINESS_RULES.md | Regras de negócio |
| AUTH.md | Fluxo de autenticação |
| UI_COMPONENTS.md | Componentes reutilizáveis |
| BACKLOG.md | Backlog consolidado |
| CHANGELOG.md | Histórico de alterações |
| FILE_MAP.md | Este arquivo |
| TECH_DEBT.md | Dívida técnica |
| ROADMAP.md | Separação MVP/V1/V2 |

---

### `/tests` (futuro)

Estrutura planejada:
```
tests/
├── test_auth.py          # Login, cadastro, JWT
├── test_medicamentos.py  # Busca, fuzzy matching
├── test_analise.py       # Motor de risco
├── test_consumo.py       # Limites, tracking
└── conftest.py           # Fixtures pytest
```

---

## 🔗 Dependências entre Arquivos

### Fluxo POST /analise/risco

```
routers/analise.py
    ↓ usa
services/analise_risco.py (analisar)
    ↓ usa
repositories/medicamento_repo.py (buscar_medicamento_anvisa)
repositories/cid_repo.py (buscar_cid)
repositories/sigtap_repo.py (buscar_procedimento)
    ↓ usa
models/medicamento.py
models/referencia.py
    ↓ usa
database.py (Session)
```

### Fluxo GET /buscar

```
routers/web.py (pagina_buscar)
    ↓ usa
services/busca_medicamento.py (buscar)
    ↓ usa
repositories/medicamento_repo.py (buscar_medicamento_anvisa)
    ↓ usa
models/medicamento.py
    ↓ renderiza
templates/buscar.html
```

### Fluxo POST /auth/login

```
routers/auth.py (login)
    ↓ usa
repositories/usuario_repo.py (buscar_por_email)
services/auth_service.py (verificar_senha, criar_access_token)
    ↓ usa
models/usuario.py (Usuario, RefreshToken)
    ↓ retorna
schemas/auth.py (TokenResposta)
```

---

**Última atualização**: 2026-06-04  
**Versão**: 1.0.0
