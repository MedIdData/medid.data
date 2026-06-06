# MedID Data - Documentação Técnica Completa

> Documento técnico para referência e troubleshooting do projeto MedID Data.
> Atualizado em: 06 de junho de 2026

---

## 1. VISÃO GERAL DO PROJETO

**MedID Data** é uma plataforma SaaS B2B de validação de prescrições médicas para prevenção de glosas em operadoras de saúde.

### 1.1 Proposta de Valor
- **Problema**: Glosas médicas causam prejuízos de milhões para operadoras e hospitais
- **Solução**: Motor de análise de risco com 9 dimensões que detecta inconsistências antes da auditoria
- **Diferenciais**:
  - Dados oficiais (ANVISA, CMED, CID-10, SIGTAP)
  - Busca fuzzy com similaridade fonética
  - API RESTful para integração
  - Interface web para uso rápido

### 1.2 Módulos Principais
1. **Base de Medicamentos** - Busca inteligente com 32.496 medicamentos
2. **Análise de Risco** - Motor de 9 dimensões com pontuação de glosa
3. **Gestão de Chaves** - Autenticação via JWT ou API Key
4. **Histórico de Consumo** - Analytics e métricas de uso

---

## 2. ARQUITETURA TÉCNICA

### 2.1 Stack Tecnológica

**Backend**:
- **Python 3.11+** - Linguagem base
- **FastAPI 0.115.6** - Framework web ASGI
- **SQLAlchemy 2.0.36** - ORM
- **Pydantic 2.10.3** - Validação de dados
- **Uvicorn** - Servidor ASGI com workers

**Banco de Dados**:
- **PostgreSQL 15+** - Banco principal
- **Extensões**:
  - `pg_trgm` - Busca fuzzy com trigram similarity
  - `unaccent` - Normalização de caracteres acentuados

**Frontend**:
- **Jinja2 3.1.4** - Templates HTML server-side
- **CSS puro** - Design system customizado (sem frameworks)
- **JavaScript vanilla** - Interatividade mínima

**Infraestrutura**:
- **Railway** - PaaS para deploy e banco PostgreSQL
- **Cloudflare** - DNS e proxy (domínio mediddata.com)
- **Git/GitHub** - Versionamento e CI/CD

### 2.2 Estrutura de Diretórios

```
mediddata/
├── app/
│   ├── main.py                  # Entrypoint FastAPI
│   ├── config.py                # Configurações (env vars)
│   ├── database.py              # Conexão SQLAlchemy
│   ├── models/                  # Modelos SQLAlchemy
│   │   ├── usuario.py
│   │   ├── empresa.py
│   │   ├── medicamento.py
│   │   └── auditoria.py
│   ├── schemas/                 # Pydantic schemas (validação)
│   │   ├── auth.py
│   │   ├── analise.py
│   │   └── usuario.py
│   ├── routers/                 # Rotas (controllers)
│   │   ├── web.py              # Interface web
│   │   ├── auth.py             # Login/JWT
│   │   ├── medicamentos.py     # API medicamentos
│   │   ├── analise.py          # API análise de risco
│   │   └── usuario.py          # Gestão de usuário
│   ├── services/                # Lógica de negócio
│   │   ├── auth_service.py
│   │   ├── busca_medicamento.py
│   │   └── analise_risco.py
│   ├── repositories/            # Queries SQL (data layer)
│   │   ├── usuario_repo.py
│   │   └── medicamento_repo.py
│   ├── middleware/              # Middlewares customizados
│   │   ├── auth_middleware.py  # Autenticação JWT/API Key
│   │   └── rate_limit.py       # Controle de limites
│   ├── templates/               # Jinja2 HTML
│   │   ├── base.html           # Layout base
│   │   ├── painel.html
│   │   ├── buscar.html
│   │   └── analise.html
│   └── static/                  # CSS, imagens
├── scripts/                     # Scripts de importação
│   ├── import_anvisa.py
│   ├── import_cmed.py
│   ├── import_cid10.py
│   └── import_sigtap.py
├── dados/                       # Arquivos CSV/XLSX (não versionados)
│   ├── anvisa_medicamentos.csv
│   ├── cmed_pmc.xlsx
│   ├── CID-10-CATEGORIAS.CSV
│   └── sigtap_procedimentos.txt
├── migrations/                  # Alembic (migrations SQL)
│   └── versions/
├── docs/                        # Documentação
├── .env                         # Variáveis de ambiente (local)
├── requirements.txt             # Dependências Python
└── railway.toml                 # Config Railway deploy
```

### 2.3 Fluxo de Dados

**Importação de Dados (offline)**:
```
dados/ (CSV/XLSX)
  ↓ scripts/import_*.py
  ↓ SQLAlchemy bulk insert (COPY)
PostgreSQL (tabelas normalizadas)
```

**Requisição API**:
```
Cliente (cURL/Postman/integração)
  ↓ HTTPS (Cloudflare)
  ↓ Railway (Uvicorn)
  ↓ FastAPI router
  ↓ Middleware (auth + rate limit)
  ↓ Service (lógica)
  ↓ Repository (SQL)
  ↓ PostgreSQL
  ↓ Pydantic schema (response)
JSON Response
```

**Requisição Web**:
```
Navegador
  ↓ HTTPS (Cloudflare)
  ↓ Railway (Uvicorn)
  ↓ FastAPI router (web.py)
  ↓ Service + Repository
  ↓ Jinja2 template
HTML Response
```

---

## 3. BANCO DE DADOS

### 3.1 PostgreSQL - Configuração

**Desenvolvimento (local)**:
```bash
# Instalar PostgreSQL
brew install postgresql@15  # macOS
# ou via Docker
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=mediddata \
  -e POSTGRES_PASSWORD=mediddata \
  -e POSTGRES_DB=mediddata \
  postgres:15

# Conectar
psql -U mediddata -d mediddata -h localhost
```

**Produção (Railway)**:
- Provisionado automaticamente ao criar projeto
- URL de conexão em variável `DATABASE_URL`
- Backups automáticos diários
- Extensões habilitadas: `pg_trgm`, `unaccent`

### 3.2 Extensões PostgreSQL

```sql
-- Necessário executar como superuser (Railway já tem)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
```

**pg_trgm** (Trigram Similarity):
- Busca fuzzy por similaridade
- Função: `similarity(texto1, texto2)` retorna 0.0 a 1.0
- Usado em: busca de medicamentos (tolerância a typos)

**unaccent**:
- Remove acentos: "José" → "Jose"
- Melhora busca independente de acentuação

### 3.3 Tabelas Principais

**Tabela: `medicamento`** (32.496 registros)
```sql
CREATE TABLE medicamento (
    id SERIAL PRIMARY KEY,
    registro_ms VARCHAR(15) UNIQUE,           -- ex: 1.0068.0924
    nome_produto TEXT NOT NULL,               -- ex: Dipirona Sódica 500mg
    principio_ativo TEXT,                     -- ex: DIPIRONA SÓDICA
    apresentacao TEXT,                        -- ex: 500 MG COM CT BL AL PLAS OPC X 10
    empresa_fabricante TEXT,
    cnpj_empresa VARCHAR(18),
    ativo BOOLEAN DEFAULT true,
    data_vencimento DATE,
    categoria VARCHAR(50),                    -- MEDICAMENTO, GENERICO, SIMILAR
    classe_terapeutica TEXT,
    tarja VARCHAR(20),                        -- VERMELHA, PRETA, SEM_TARJA
    registro_ativo BOOLEAN,
    num_processo_anvisa TEXT,
    -- Timestamps
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_medicamento_nome_trgm ON medicamento USING gin (nome_produto gin_trgm_ops);
CREATE INDEX idx_medicamento_principio ON medicamento USING gin (principio_ativo gin_trgm_ops);
CREATE INDEX idx_medicamento_ativo ON medicamento (ativo);
```

**Tabela: `preco_medicamento`** (CMED - preços regulados)
```sql
CREATE TABLE preco_medicamento (
    id SERIAL PRIMARY KEY,
    medicamento_id INTEGER REFERENCES medicamento(id),
    ean VARCHAR(14),                          -- Código de barras
    pmc_0 DECIMAL(10,2),                      -- Preço Máximo Consumidor 0%
    pmc_12 DECIMAL(10,2),                     -- PMC com 12% ICMS
    pmc_17 DECIMAL(10,2),                     -- PMC com 17% ICMS
    pmc_18 DECIMAL(10,2),                     -- PMC com 18% ICMS
    pmc_19 DECIMAL(10,2),                     -- PMC com 19% ICMS
    pmc_20 DECIMAL(10,2),                     -- PMC com 20% ICMS
    pmvg_sem_icms DECIMAL(10,2),             -- Preço Máximo Venda Gov
    pmvg_com_icms DECIMAL(10,2),
    pf_0 DECIMAL(10,2),                       -- Preço Fábrica
    pf_12 DECIMAL(10,2),
    pf_17 DECIMAL(10,2),
    pf_18 DECIMAL(10,2),
    pf_19 DECIMAL(10,2),
    pf_20 DECIMAL(10,2),
    restricao_hospitalar BOOLEAN,
    cap BOOLEAN,                              -- Coeficiente Adequação de Preço
    lista_concessao_credito_tributario BOOLEAN,
    lista_neutra BOOLEAN,
    comercializacao_2022 BOOLEAN,
    tarja VARCHAR(20)
);
```

**Tabela: `cid10_categoria`** (classificação de doenças)
```sql
CREATE TABLE cid10_categoria (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(5) UNIQUE NOT NULL,        -- ex: A00-B99
    descricao TEXT NOT NULL                   -- ex: Doenças infecciosas
);
```

**Tabela: `cid10_subcategoria`**
```sql
CREATE TABLE cid10_subcategoria (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(5) UNIQUE NOT NULL,        -- ex: A00.0
    descricao TEXT NOT NULL,                  -- ex: Cólera devida a Vibrio
    categoria_codigo VARCHAR(5) REFERENCES cid10_categoria(codigo)
);

CREATE INDEX idx_cid10_sub_codigo ON cid10_subcategoria(codigo);
CREATE INDEX idx_cid10_sub_desc ON cid10_subcategoria USING gin (descricao gin_trgm_ops);
```

**Tabela: `sigtap_procedimento`** (procedimentos SUS)
```sql
CREATE TABLE sigtap_procedimento (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(15) UNIQUE NOT NULL,       -- ex: 0301060029
    nome TEXT NOT NULL,                       -- ex: Consulta médica
    descricao TEXT,
    grupo_codigo VARCHAR(10),
    complexidade VARCHAR(50),
    ativo BOOLEAN DEFAULT true
);

CREATE INDEX idx_sigtap_codigo ON sigtap_procedimento(codigo);
CREATE INDEX idx_sigtap_nome ON sigtap_procedimento USING gin (nome gin_trgm_ops);
```

**Tabela: `usuario`**
```sql
CREATE TABLE usuario (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    perfil VARCHAR(20) NOT NULL DEFAULT 'USUARIO',  -- USUARIO | ADMINISTRADOR
    ativo BOOLEAN DEFAULT true,
    limite_diario INTEGER NOT NULL DEFAULT 20,
    limite_mensal INTEGER NOT NULL DEFAULT 100,
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_usuario_email ON usuario(email);
```

**Tabela: `consumo_diario`** (tracking de uso)
```sql
CREATE TABLE consumo_diario (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuario(id) ON DELETE CASCADE,
    data_referencia DATE NOT NULL,
    modulo VARCHAR(20) NOT NULL,              -- MEDICAMENTOS | ANALISE
    total_consultas INTEGER DEFAULT 0,
    UNIQUE(usuario_id, data_referencia, modulo)
);

CREATE INDEX idx_consumo_usuario_data ON consumo_diario(usuario_id, data_referencia);
CREATE INDEX idx_consumo_mes ON consumo_diario(usuario_id, EXTRACT(year FROM data_referencia), EXTRACT(month FROM data_referencia));
```

**Tabela: `auditoria_requisicao`** (log detalhado)
```sql
CREATE TABLE auditoria_requisicao (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuario(id),
    chave_acesso_id INTEGER,
    canal VARCHAR(10),                        -- WEB | API
    modulo VARCHAR(20),                       -- MEDICAMENTOS | ANALISE
    endpoint VARCHAR(255),
    metodo VARCHAR(10),
    parametros JSONB,
    ip VARCHAR(45),
    user_agent TEXT,
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_auditoria_usuario ON auditoria_requisicao(usuario_id);
CREATE INDEX idx_auditoria_data ON auditoria_requisicao(criado_em);
```

### 3.4 Volumetria de Dados

| Tabela | Registros | Tamanho aprox. | Fonte |
|--------|-----------|----------------|-------|
| medicamento | 32.496 | ~50 MB | ANVISA |
| preco_medicamento | 25.000+ | ~30 MB | CMED |
| cid10_categoria | 22 | < 1 MB | CID-10 |
| cid10_subcategoria | 14.000+ | ~5 MB | CID-10 |
| sigtap_procedimento | 4.500+ | ~3 MB | SIGTAP |
| usuario | variável | < 1 MB | - |
| consumo_diario | crescente | variável | - |
| auditoria_requisicao | crescente | variável | - |

**Total BD (apenas dados estáticos)**: ~90 MB

---

## 4. AUTENTICAÇÃO E SEGURANÇA

### 4.1 Métodos de Autenticação

**1. JWT Bearer Token** (sessões web):
```python
# Login
POST /auth/login
{
  "email": "usuario@example.com",
  "senha": "senha123"
}

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}

# Uso
GET /medicamentos/buscar?termo=dipirona
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**2. API Key** (integrações):
```bash
# Criar chave
POST /usuario/chaves
{
  "nome": "Integração ERP",
  "descricao": "Chave para sistema interno"
}

# Response
{
  "chave": "med_abc123def456...",  # Mostrado apenas na criação!
  "id": 1,
  "nome": "Integração ERP"
}

# Uso (duas formas)
GET /medicamentos/buscar?termo=dipirona
Authorization: Bearer med_abc123def456...

# OU
X-API-Key: med_abc123def456...
```

### 4.2 Hash de Senhas

**Algoritmo**: bcrypt com salt automático
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Criar hash
senha_hash = pwd_context.hash("senha123")
# $2b$12$Abc123...

# Verificar
pwd_context.verify("senha123", senha_hash)  # True
```

### 4.3 Rate Limiting

**Níveis de controle**:

1. **Por IP (SlowAPI)**:
   - Desenvolvimento: desabilitado
   - Produção: 60 req/min, 1000 req/hora

2. **Por Usuário (custom)**:
   - Limites diários: configurável por usuário
   - Limites mensais: configurável por usuário
   - Administradores: 0/0 = ilimitado

**Implementação**:
```python
# app/middleware/rate_limit.py
def verificar_limite_usuario(db: Session, usuario: Usuario):
    if usuario.limite_diario == 0:  # Admin = ilimitado
        return
    
    consumo_hoje = obter_consumo_total_dia(db, usuario.id, date.today())
    if consumo_hoje >= usuario.limite_diario:
        raise LimiteExcedidoException("Limite diário atingido")
```

### 4.4 CORS

**Configuração**:
```python
# Desenvolvimento
ALLOWED_ORIGINS=*

# Produção
ALLOWED_ORIGINS=https://mediddata.com,https://app.mediddata.com
```

---

## 5. API REST

### 5.1 Base URL

- **Produção**: `https://mediddata.com`
- **Desenvolvimento**: `http://localhost:8000`

### 5.2 Endpoints Principais

#### **Autenticação**

```bash
# Login (obter JWT)
POST /auth/login
Content-Type: application/json
{
  "email": "usuario@example.com",
  "senha": "senha123"
}

# Refresh token
POST /auth/refresh
Authorization: Bearer <refresh_token>

# Logout (revoga tokens)
POST /auth/logout
Authorization: Bearer <access_token>
```

#### **Medicamentos**

```bash
# Buscar medicamentos
GET /medicamentos/buscar?termo=dipirona&apenas_ativos=true&pagina=1&limite=50
Authorization: Bearer <token>

# Response
{
  "resultados": [
    {
      "id": 123,
      "registro_ms": "1.0068.0924",
      "nome_produto": "Dipirona Sódica 500mg",
      "principio_ativo": "DIPIRONA SÓDICA",
      "empresa_fabricante": "EMS",
      "ativo": true,
      "similaridade": 0.95
    }
  ],
  "total": 150,
  "pagina": 1,
  "total_paginas": 3
}

# Detalhe de medicamento
GET /medicamentos/{id}
Authorization: Bearer <token>

# Response (inclui preços CMED)
{
  "id": 123,
  "registro_ms": "1.0068.0924",
  "nome_produto": "Dipirona Sódica 500mg",
  "precos": {
    "pmc_18": 15.50,
    "pf_18": 8.30
  }
}
```

#### **Análise de Risco**

```bash
# Analisar risco de glosa
POST /analise/risco
Authorization: Bearer <token>
Content-Type: application/json
{
  "medicamento": "Dipirona Sódica 500mg",
  "preco_informado": 25.00,
  "tratamento": "Dor pós-operatória",
  "cid": "R52.9",
  "procedimento": "0301060029",
  "quantidade": 2
}

# Response (9 dimensões)
{
  "score_geral": 72,
  "potencial_glosa": "MÉDIO",
  "dimensoes": {
    "medicamento_encontrado": {
      "pontuacao": 10,
      "peso": 10,
      "descricao": "Medicamento identificado na base ANVISA",
      "detalhes": "Dipirona Sódica 500mg (registro 1.0068.0924)"
    },
    "preco_tabela": {
      "pontuacao": 5,
      "peso": 10,
      "descricao": "Preço 61% acima da tabela CMED",
      "detalhes": "Informado: R$ 25,00 | Tabela PMC: R$ 15,50"
    },
    "aderencia_cid": {
      "pontuacao": 8,
      "peso": 10,
      "descricao": "CID compatível com tratamento",
      "detalhes": "R52.9 - Dor não especificada"
    }
  },
  "recomendacoes": [
    "Revisar preço informado (61% acima da tabela)",
    "Verificar se quantidade (2) está dentro do protocolo"
  ]
}
```

#### **Usuário**

```bash
# Obter perfil
GET /usuario/me
Authorization: Bearer <token>

# Atualizar perfil
PUT /usuario/me
Authorization: Bearer <token>
{
  "nome": "Novo Nome"
}

# Criar chave de API
POST /usuario/chaves
Authorization: Bearer <token>
{
  "nome": "Integração ERP",
  "descricao": "Chave para sistema interno"
}

# Listar chaves
GET /usuario/chaves
Authorization: Bearer <token>

# Revogar chave
DELETE /usuario/chaves/{chave_id}
Authorization: Bearer <token>
```

#### **Histórico de Consumo**

```bash
# Obter consumo atual
GET /usuario/consumo
Authorization: Bearer <token>

# Response
{
  "consumo_hoje": 15,
  "limite_diario": 20,
  "consumo_mes": 280,
  "limite_mensal": 500,
  "por_modulo": [
    {"modulo": "MEDICAMENTOS", "total": 200},
    {"modulo": "ANALISE", "total": 80}
  ]
}
```

### 5.3 Códigos de Status

| Status | Significado | Exemplo |
|--------|-------------|---------|
| 200 | OK | Busca bem-sucedida |
| 201 | Created | Chave API criada |
| 400 | Bad Request | JSON inválido |
| 401 | Unauthorized | Token ausente/inválido |
| 403 | Forbidden | Sem permissão (não é admin) |
| 404 | Not Found | Medicamento não encontrado |
| 429 | Too Many Requests | Limite excedido |
| 500 | Internal Server Error | Erro no servidor |

---

## 6. DEPLOY E INFRAESTRUTURA

### 6.1 Railway (PaaS)

**Setup inicial**:
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link projeto local ao Railway
railway link

# Deploy manual
railway up

# Ver logs
railway logs
```

**Variáveis de ambiente (Railway)**:
```bash
# Database (Railway provisiona automaticamente)
DATABASE_URL=postgresql://postgres:***@postgres.railway.internal:5432/railway

# App
ENVIRONMENT=production
SECRET_KEY=<chave-secreta-gerada>
ALLOWED_ORIGINS=https://mediddata.com
WORKERS=2

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**Auto-deploy**:
- Push para `main` → Railway faz deploy automático
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`

**Health check**:
```bash
# Railway usa /saude para monitoramento
curl https://mediddata.com/saude

# Response
{
  "status": "operacional",
  "servico": "MedID Data",
  "versao": "1.0.0",
  "environment": "production"
}
```

### 6.2 Cloudflare (DNS + Proxy)

**Configuração DNS**:
```
Tipo: CNAME
Nome: @
Valor: <railway-url>.railway.app
Proxy: Ativado (laranja)
TTL: Auto
```

**Benefícios**:
- SSL/TLS automático
- DDoS protection
- CDN global
- Cache de assets estáticos

### 6.3 Domínio

**Registrar**: mediddata.com
**DNS**: Cloudflare nameservers
**SSL**: Full (strict) - Cloudflare ↔ Railway criptografado

### 6.4 Banco de Dados (Railway PostgreSQL)

**Conexão local ao Railway DB**:
```bash
# Via Railway CLI
railway connect postgres

# Ou direto
psql "postgresql://postgres:***@postgres.railway.internal:5432/railway"
```

**Backup manual**:
```bash
# Exportar schema + dados
pg_dump -h <host> -U postgres -d railway -F c -b -v -f backup_$(date +%Y%m%d).dump

# Restaurar
pg_restore -h localhost -U mediddata -d mediddata -v backup_20260606.dump
```

**Sincronizar dados locais → Railway**:
```bash
# Script customizado (scripts/sync_dados_para_railway.sh)
#!/bin/bash
# 1. Dump tabelas de dados do local
pg_dump -U mediddata -d mediddata -t medicamento -t preco_medicamento -t cid10_categoria -t cid10_subcategoria -t sigtap_procedimento -F c -b -v -f dados_local.dump

# 2. Restaurar no Railway
railway run pg_restore -d $DATABASE_URL -v dados_local.dump
```

---

## 7. AMBIENTE DE DESENVOLVIMENTO

### 7.1 Setup Local

```bash
# 1. Clonar repositório
git clone https://github.com/MedIdData/medid.data.git
cd mediddata

# 2. Criar virtualenv
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar .env
cp .env.example .env
# Editar .env com suas configurações

# 5. PostgreSQL local
brew install postgresql@15  # Mac
brew services start postgresql@15
createdb mediddata
psql mediddata -c "CREATE EXTENSION pg_trgm; CREATE EXTENSION unaccent;"

# 6. Rodar migrations
alembic upgrade head

# 7. Importar dados
python3 scripts/import_anvisa.py
python3 scripts/import_cmed.py
python3 scripts/import_cid10.py
python3 scripts/import_sigtap.py

# 8. Rodar servidor
uvicorn app.main:app --reload --port 8000
```

### 7.2 Arquivo .env (desenvolvimento)

```bash
# Database
DATABASE_URL=postgresql://mediddata:mediddata@localhost:5432/mediddata
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=development
DADOS_DIR=./dados
WORKERS=1

# CORS
ALLOWED_ORIGINS=*

# Rate Limiting
RATE_LIMIT_ENABLED=false
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=text
```

### 7.3 Comandos Úteis

```bash
# Rodar testes
pytest

# Criar nova migration
alembic revision -m "descrição da mudança"

# Aplicar migrations
alembic upgrade head

# Reverter migration
alembic downgrade -1

# Ver logs estruturados
uvicorn app.main:app --log-config logging.yaml

# Acessar shell Python com context
python3
>>> from app.database import SessionLocal
>>> from app.models.medicamento import Medicamento
>>> db = SessionLocal()
>>> db.query(Medicamento).count()
32496
```

---

## 8. DADOS E IMPORTAÇÃO

### 8.1 Fontes de Dados

**ANVISA** (medicamentos):
- URL: https://consultas.anvisa.gov.br/#/medicamentos/
- Formato: CSV
- Atualização: mensal
- Volumetria: ~18 MB, 32.496 registros

**CMED** (preços):
- URL: https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed
- Formato: XLSX
- Atualização: quinzenal
- Volumetria: ~22 MB (PMC + PMVG)

**CID-10** (doenças):
- URL: http://www.datasus.gov.br/cid10/
- Formato: CSV
- Atualização: anual
- Volumetria: ~1.5 MB, 14.000+ códigos

**SIGTAP** (procedimentos SUS):
- URL: http://sigtap.datasus.gov.br/
- Formato: TXT (pipe-separated)
- Atualização: mensal
- Volumetria: ~3.5 MB, 4.500+ procedimentos

### 8.2 Scripts de Importação

**Importar ANVISA**:
```bash
python3 scripts/import_anvisa.py
# Lê: dados/anvisa_medicamentos.csv
# Insere: tabela medicamento
# Estratégia: COPY (bulk insert) para performance
# Tempo: ~30 segundos
```

**Importar CMED**:
```bash
python3 scripts/import_cmed.py
# Lê: dados/cmed_pmc.xlsx, dados/cmed_pmvg.xlsx
# Insere: tabela preco_medicamento
# Match: por EAN ou nome do produto
# Tempo: ~2 minutos
```

**Importar CID-10**:
```bash
python3 scripts/import_cid10.py
# Lê: dados/CID-10-CATEGORIAS.CSV, dados/CID-10-SUBCATEGORIAS.CSV
# Insere: cid10_categoria, cid10_subcategoria
# Tempo: ~10 segundos
```

**Importar SIGTAP**:
```bash
python3 scripts/import_sigtap.py
# Lê: dados/sigtap_procedimentos.txt
# Insere: sigtap_procedimento
# Tempo: ~5 segundos
```

### 8.3 Estratégias de Performance

**COPY vs INSERT**:
```python
# Ruim (lento para grandes volumes)
for row in df.iterrows():
    db.add(Medicamento(**row))
db.commit()

# Bom (100x mais rápido)
from io import StringIO
csv_buffer = StringIO()
df.to_csv(csv_buffer, index=False, header=False)
csv_buffer.seek(0)

with db.connection() as conn:
    cursor = conn.connection.cursor()
    cursor.copy_from(csv_buffer, 'medicamento', sep=',', columns=df.columns)
```

**Batch commits**:
```python
# Processar em lotes de 1000
for i in range(0, len(data), 1000):
    batch = data[i:i+1000]
    db.bulk_insert_mappings(Medicamento, batch)
    db.commit()
```

---

## 9. MOTOR DE ANÁLISE DE RISCO

### 9.1 Dimensões de Análise

**9 dimensões avaliadas** (peso 10 cada = 100 total):

1. **Medicamento Encontrado** (peso 10):
   - 10 pontos: medicamento existe na base ANVISA
   - 0 pontos: não encontrado (similaridade < 0.7)

2. **Preço vs Tabela CMED** (peso 10):
   - 10 pontos: preço ≤ tabela
   - 8 pontos: até 10% acima
   - 5 pontos: 10-30% acima
   - 2 pontos: 30-50% acima
   - 0 pontos: > 50% acima

3. **Aderência CID x Tratamento** (peso 10):
   - Similaridade textual entre descrição CID e tratamento informado
   - 10 pontos: similaridade > 0.7
   - 5 pontos: similaridade 0.4-0.7
   - 0 pontos: similaridade < 0.4

4. **Compatibilidade CID x Procedimento** (peso 10):
   - Verifica se CID está na lista de CIDs compatíveis do procedimento SIGTAP
   - 10 pontos: CID na lista
   - 0 pontos: CID não autorizado

5. **Registro ANVISA Ativo** (peso 10):
   - 10 pontos: registro ativo
   - 0 pontos: vencido/suspenso

6. **Quantidade vs Protocolo** (peso 10):
   - Valida se quantidade está dentro do esperado
   - 10 pontos: 1-5 unidades
   - 5 pontos: 6-20 unidades
   - 2 pontos: > 20 unidades

7. **Tarja vs Prescrição** (peso 10):
   - Verifica restrições (tarja preta, vermelha)
   - 10 pontos: sem tarja ou procedimento compatível
   - 5 pontos: tarja vermelha com procedimento hospitalar
   - 0 pontos: tarja preta sem justificativa

8. **Princípio Ativo vs Nome Comercial** (peso 10):
   - Valida coerência entre nome informado e princípio ativo
   - 10 pontos: match exato
   - 5 pontos: similaridade > 0.5
   - 0 pontos: incompatível

9. **Completude de Dados** (peso 10):
   - Penaliza campos vazios importantes
   - 10 pontos: todos campos preenchidos
   - -2 pontos por campo vazio

### 9.2 Cálculo de Score

```python
score_geral = sum(dim.pontuacao for dim in dimensoes.values())
# score_geral: 0 a 100

# Classificação de risco
if score_geral >= 80:
    potencial_glosa = "BAIXO"
elif score_geral >= 60:
    potencial_glosa = "MÉDIO"
else:
    potencial_glosa = "ALTO"
```

### 9.3 Lógica de Busca Fuzzy

**Threshold de similaridade**:
```python
# Busca geral (listagem)
SIMILARIDADE_MIN_BUSCA = 0.3

# Análise de risco (validação)
SIMILARIDADE_MIN_ANALISE = 0.7

# Query SQL
SELECT *, similarity(nome_produto, %s) as sim
FROM medicamento
WHERE similarity(nome_produto, %s) > 0.3
ORDER BY sim DESC
LIMIT 50;
```

**Normalização**:
- Remove acentos: `unaccent(texto)`
- Lowercase: `LOWER(texto)`
- Trigram: `pg_trgm` compara "dipirona" vs "dipirone" (0.8 similaridade)

---

## 10. TROUBLESHOOTING

### 10.1 Problemas Comuns

**Erro: "relation does not exist"**
```bash
# Causa: migrations não aplicadas
# Solução:
alembic upgrade head
```

**Erro: "extension pg_trgm does not exist"**
```bash
# Causa: extensão não instalada
# Solução:
psql -U mediddata -d mediddata
CREATE EXTENSION pg_trgm;
CREATE EXTENSION unaccent;
```

**Erro: "Limite diário atingido"**
```bash
# Causa: consumo excedeu limite do usuário
# Solução temporária (admin):
curl https://mediddata.com/migrate/limpar-consumo-usuario?email=usuario@example.com

# Solução definitiva: aumentar limite
UPDATE usuario SET limite_diario = 100 WHERE email = 'usuario@example.com';
```

**Erro: "Medicamento não encontrado (similaridade < 0.7)"**
```bash
# Causa: nome informado muito diferente da base
# Solução: testar busca primeiro
GET /medicamentos/buscar?termo=dipirona

# Ajustar threshold (apenas em dev)
SIMILARIDADE_MIN_ANALISE = 0.5
```

### 10.2 Logs e Monitoramento

**Ver logs Railway**:
```bash
railway logs --tail 100
```

**Formato de log (produção - JSON)**:
```json
{
  "asctime": "2026-06-06T10:30:45",
  "levelname": "INFO",
  "name": "app.main",
  "message": "request_completed",
  "method": "POST",
  "path": "/analise/risco",
  "status_code": 200,
  "duration_ms": 145.3,
  "client_ip": "203.0.113.42"
}
```

**Métricas importantes**:
- Tempo de resposta (X-Tempo-Resposta header)
- Taxa de erro 5xx
- Consumo de memória (Railway dashboard)
- Conexões PostgreSQL ativas

### 10.3 Backup e Recovery

**Backup automático (Railway)**:
- Diário às 03:00 UTC
- Retenção: 7 dias

**Backup manual**:
```bash
# Exportar
railway run pg_dump $DATABASE_URL -F c -b -v -f backup.dump

# Importar
railway run pg_restore -d $DATABASE_URL -v backup.dump
```

---

## 11. SEGURANÇA E COMPLIANCE

### 11.1 LGPD

**Dados pessoais coletados**:
- Nome completo
- Email (login)
- Senha (hash bcrypt)
- IP (auditoria)

**Retenção**:
- Usuários ativos: indefinido
- Usuários inativos: 2 anos
- Logs de auditoria: 1 ano

**Direitos do titular**:
- Acesso: GET /usuario/me
- Correção: PUT /usuario/me
- Exclusão: DELETE /usuario/me (soft delete)

### 11.2 Boas Práticas

- ✅ Senhas nunca em plaintext (bcrypt)
- ✅ JWT com expiração curta (30 min)
- ✅ HTTPS obrigatório (Cloudflare)
- ✅ Rate limiting por IP e usuário
- ✅ Logs estruturados (auditoria)
- ✅ Validação de input (Pydantic)
- ✅ SQL parameterizado (SQLAlchemy - previne injection)

---

## 12. CONTATO E SUPORTE

**Fundador**: Fabbio Monteiro
**Email**: fabbiomonteiro@yahoo.com.br
**Domínio**: https://mediddata.com
**Repositório**: GitHub (privado)

**Serviços externos usados**:
- **Railway**: Hosting + PostgreSQL
- **Cloudflare**: DNS + Proxy + SSL
- **GitHub**: Versionamento + CI/CD

---

**Última atualização**: 06/06/2026
**Versão do documento**: 1.0
