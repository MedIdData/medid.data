# MedID Data API

**Plataforma de Inteligência em Saúde** — API RESTful para análise de risco clínico e financeiro com dados oficiais brasileiros.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-Proprietário-red)](https://mediddata.com/termos)

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Dados Utilizados](#dados-utilizados)
- [Instalação Local](#instalação-local)
- [Uso da API](#uso-da-api)
- [Autenticação](#autenticação)
- [Endpoints](#endpoints)
- [Exemplos de Integração](#exemplos-de-integração)
- [Deploy](#deploy)
- [Contribuição](#contribuição)

---

## 🎯 Visão Geral

MedID Data é uma plataforma B2B SaaS que oferece:

### Módulo 1: Base de Referência de Medicamentos
- Busca inteligente com **fuzzy matching** e correção ortográfica
- Dados consolidados ANVISA + CMED (preços regulados)
- 40.000+ medicamentos com preços atualizados
- Informações de registro, fabricante, classe terapêutica, tarja

### Módulo 2: Motor de Análise de Risco
- **9 dimensões de análise** clínica e financeira
- Pontuação de aderência e risco de glosa
- Validação de CID-10, SIGTAP, preços CMED
- Motivos explicáveis em português

### Módulo 3: Gestão e Analytics
- Chaves de API para integrações
- Dashboard de consumo com gráficos
- Limites por plano (diário/mensal)
- Auditoria completa de requisições

---

## 📊 Dados Utilizados

| Base de Dados | Fonte | Registros | Atualização |
|---------------|-------|-----------|-------------|
| **Medicamentos ANVISA** | [Consulta de Medicamentos](https://consultas.anvisa.gov.br) | ~40.000 | Mensal |
| **Preços CMED** | [CMED PMC/PMVG](https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed) | ~18.000 | Mensal |
| **CID-10** | [Datasus](https://datasus.saude.gov.br) | 14.000+ | Anual |
| **SIGTAP** | [SIGTAP SUS](http://sigtap.datasus.gov.br) | 4.000+ | Trimestral |
| **DCB (Denominação Comum)** | [ANVISA DCB](https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/dcb) | 3.000+ | Anual |

---

## 🚀 Instalação Local

### Pré-requisitos

- Python 3.11+
- PostgreSQL 14+
- Redis 7+ (opcional, para rate limiting)
- Git

### 1. Clonar repositório

```bash
git clone https://github.com/mediddata/mediddata-api.git
cd mediddata-api
```

### 2. Criar ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar banco de dados

```bash
# Criar banco PostgreSQL
createdb mediddata

# Exportar URL do banco
export DATABASE_URL="postgresql://usuario:senha@localhost:5432/mediddata"
```

### 5. Setup inicial (criar tabelas e dados básicos)

```bash
# Criar todas as tabelas + plano Gratuito + usuário admin
python setup_prod.py
```

**Credenciais padrão criadas:**
- E-mail: `admin@mediddata.com`
- Senha: `medid@2026`

⚠️ **IMPORTANTE**: Altere a senha após o primeiro login!

### 6. Importar dados (opcional)

```bash
# Baixar arquivos de dados em dados/
# Executar scripts de importação

python -m app.scripts.importar_anvisa
python -m app.scripts.importar_cmed
python -m app.scripts.importar_cid10
python -m app.scripts.importar_sigtap
python -m app.scripts.importar_dcb
```

### 7. Iniciar servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Acesse:
- **API Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Interface Web**: http://localhost:8000

---

## 🔐 Autenticação

A API suporta **dois métodos** de autenticação:

### 1. JWT Bearer Token (Sessões Web)

**Criar conta:**
```bash
curl -X POST http://localhost:8000/auth/cadastro \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "email": "joao@empresa.com",
    "senha": "senha123"
  }'
```

**Fazer login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao@empresa.com",
    "senha": "senha123"
  }'
```

**Resposta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tipo": "bearer",
  "expira_em": 1800
}
```

**Usar token:**
```bash
curl http://localhost:8000/medicamentos/buscar?q=dipirona \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 2. Chave de API (Integrações)

**Criar chave:**
```bash
curl -X POST http://localhost:8000/usuario/chaves \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Servidor de Produção"
  }'
```

**Resposta:**
```json
{
  "id": 1,
  "nome": "Servidor de Produção",
  "prefixo": "med_abc12345...",
  "chave_completa": "med_abc12345678901234567890123456789012345678",
  "ativa": true,
  "criado_em": "2026-06-04T10:00:00Z"
}
```

⚠️ **IMPORTANTE**: Salve a `chave_completa` imediatamente. Ela só é exibida uma vez.

**Usar chave:**
```bash
# Método 1: Authorization Bearer
curl http://localhost:8000/medicamentos/buscar?q=dipirona \
  -H "Authorization: Bearer med_abc12345678901234567890123456789012345678"

# Método 2: X-API-Key
curl http://localhost:8000/medicamentos/buscar?q=dipirona \
  -H "X-API-Key: med_abc12345678901234567890123456789012345678"
```

---

## 📡 Endpoints

### Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/auth/cadastro` | Criar nova conta |
| `POST` | `/auth/login` | Autenticar usuário |
| `POST` | `/auth/refresh` | Renovar access token |
| `POST` | `/auth/logout` | Encerrar sessão |
| `GET` | `/auth/me` | Perfil do usuário autenticado |

### Medicamentos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/medicamentos/buscar` | Busca inteligente de medicamentos |
| `GET` | `/medicamentos/{id}` | Detalhes de um medicamento |

### Análise de Risco

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/analise/risco` | Análise de risco clínico e financeiro |

### Gestão de Usuário

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/usuario/consumo` | Resumo de consumo (hoje/mês) |
| `GET` | `/usuario/chaves` | Listar chaves de API |
| `POST` | `/usuario/chaves` | Criar nova chave de API |
| `DELETE` | `/usuario/chaves/{id}` | Revogar chave de API |
| `PUT` | `/usuario/perfil` | Atualizar nome |
| `PUT` | `/usuario/senha` | Alterar senha |

### Sistema

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/saude` | Health check |
| `GET` | `/docs` | Documentação Swagger |
| `GET` | `/redoc` | Documentação ReDoc |

---

## 💻 Exemplos de Integração

### Python

```python
import requests

# Configuração
BASE_URL = "https://mediddata.com"
API_KEY = "med_abc12345678901234567890123456789012345678"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Buscar medicamento
response = requests.get(
    f"{BASE_URL}/medicamentos/buscar",
    params={"q": "dipirona", "limite": 10},
    headers=headers
)

medicamentos = response.json()
print(f"Encontrados: {medicamentos['total']} medicamentos")

for med in medicamentos['resultados']:
    print(f"- {med['medicamento']} ({med['principio_ativo']}) - R$ {med['pmc']}")

# Análise de risco
payload = {
    "medicamento": "DIPIRONA",
    "preco_informado": 15.50,
    "tratamento": "Dor pós-operatória",
    "cid": "R52.9",
    "procedimento": "03.01.01.007-2",
    "quantidade": 1
}

response = requests.post(
    f"{BASE_URL}/analise/risco",
    json=payload,
    headers=headers
)

analise = response.json()
print(f"Risco: {analise['classificacao_risco']}")
print(f"Potencial de glosa: {analise['potencial_glosa']}")
print(f"Motivos: {analise['motivos']}")
```

### Node.js

```javascript
const axios = require('axios');

const BASE_URL = 'https://mediddata.com';
const API_KEY = 'med_abc12345678901234567890123456789012345678';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  }
});

// Buscar medicamento
async function buscarMedicamento(termo) {
  const response = await api.get('/medicamentos/buscar', {
    params: { q: termo, limite: 10 }
  });
  return response.data;
}

// Análise de risco
async function analisarRisco(dados) {
  const response = await api.post('/analise/risco', dados);
  return response.data;
}

// Uso
(async () => {
  const medicamentos = await buscarMedicamento('dipirona');
  console.log(`Encontrados: ${medicamentos.total} medicamentos`);

  const analise = await analisarRisco({
    medicamento: 'DIPIRONA',
    preco_informado: 15.50,
    tratamento: 'Dor pós-operatória',
    cid: 'R52.9',
    procedimento: '03.01.01.007-2',
    quantidade: 1
  });
  console.log(`Risco: ${analise.classificacao_risco}`);
})();
```

### cURL

```bash
# Buscar medicamento
curl "https://mediddata.com/medicamentos/buscar?q=dipirona&limite=10" \
  -H "X-API-Key: med_abc12345678901234567890123456789012345678"

# Análise de risco
curl -X POST https://mediddata.com/analise/risco \
  -H "X-API-Key: med_abc12345678901234567890123456789012345678" \
  -H "Content-Type: application/json" \
  -d '{
    "medicamento": "DIPIRONA",
    "preco_informado": 15.50,
    "tratamento": "Dor pós-operatória",
    "cid": "R52.9",
    "procedimento": "03.01.01.007-2",
    "quantidade": 1
  }'
```

---

## 🎛️ Limites e Planos

### Plano Gratuito (Padrão)
- **100 requisições/dia**
- **2.000 requisições/mês**
- Acesso a todos os módulos
- Suporte por e-mail

### Plano Profissional
- **1.000 requisições/dia**
- **20.000 requisições/mês**
- Acesso a todos os módulos
- Suporte prioritário
- Webhooks

### Plano Enterprise
- **Ilimitado**
- SLA 99,9%
- Suporte dedicado
- Infraestrutura isolada
- Customizações

**Contato para upgrade**: comercial@mediddata.com

---

## 🐳 Deploy

### Railway (Recomendado)

1. Fork este repositório
2. Criar conta em [Railway](https://railway.app)
3. New Project → Deploy from GitHub
4. Selecionar repositório `mediddata-api`
5. Configurar variáveis de ambiente:

```env
DATABASE_URL=postgresql://...
SECRET_KEY=<gerar-chave-segura>
ENVIRONMENT=production
ALLOWED_ORIGINS=https://seuapp.com
RATE_LIMIT_ENABLED=true
LOG_FORMAT=json
```

6. **⚠️ IMPORTANTE**: Instalar extensões PostgreSQL (OBRIGATÓRIO)

   **Opção A - Via Railway Dashboard**:
   - Acesse PostgreSQL → Query
   - Cole e execute:
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   CREATE EXTENSION IF NOT EXISTS unaccent;
   ```

   **Opção B - Via psql**:
   ```bash
   # Copie DATABASE_URL do Railway
   psql $DATABASE_URL -f migrations/add_extensions.sql
   ```

7. Executar setup inicial:

```bash
# Via Railway CLI ou shell do container
python setup_prod.py
```

8. Deploy automático ✅

**🔍 Verificar**: Acesse `/buscar` e confirme que medicamentos aparecem. Se retornar vazio, extensões não estão instaladas.

**Troubleshooting**: Veja `migrations/README.md` para detalhes.

### Docker

```bash
# Build
docker build -t mediddata-api .

# Run
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e SECRET_KEY="..." \
  -e ENVIRONMENT="production" \
  mediddata-api

# Setup inicial (executar UMA VEZ)
docker exec -it <container_id> python setup_prod.py
```

**⚠️ PostgreSQL externo**: Se usar banco externo, instale extensões primeiro:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
```

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/mediddata
      - SECRET_KEY=chave-super-secreta
      - ENVIRONMENT=production
    depends_on:
      - db

  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=mediddata
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations/add_extensions.sql:/docker-entrypoint-initdb.d/01_extensions.sql

volumes:
  postgres_data:
```

---

## 🔒 Segurança

### Credenciais Padrão

Após instalação local, é criado automaticamente:

- **E-mail**: `admin@mediddata.com`
- **Senha**: `medid@2026`
- **Perfil**: `ADMINISTRADOR`

⚠️ **IMPORTANTE**: Altere a senha padrão imediatamente em produção.

### Boas Práticas

- **Nunca** compartilhe chaves de API
- Use HTTPS em produção
- Rotacione chaves periodicamente
- Revogue chaves comprometidas imediatamente
- Use variáveis de ambiente para secrets
- Monitore logs de auditoria

---

## 📝 Licença

Copyright © 2026 MedID Data. Todos os direitos reservados.

Este software é proprietário. O uso não autorizado é proibido.

Para licenciamento comercial: comercial@mediddata.com

---

## 🤝 Suporte

- **Documentação**: https://mediddata.com/docs
- **E-mail**: suporte@mediddata.com
- **Status**: https://status.mediddata.com

---

## 📈 Roadmap

- [ ] Webhook para eventos de consumo
- [ ] Cache Redis para consultas frequentes
- [ ] Exportação de relatórios (PDF/Excel)
- [ ] API v2 com GraphQL
- [ ] Integração com sistemas de saúde (Tasy, MV)
- [ ] Machine Learning para predição de glosa
- [ ] App mobile nativo

---

Desenvolvido com ❤️ pela equipe MedID Data
