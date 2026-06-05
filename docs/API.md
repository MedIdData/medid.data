# API Endpoints - MedID Data

## Base URL
**Produção**: `https://mediddata.up.railway.app`  
**Local**: `http://localhost:8000`

---

## 🔐 Autenticação

### POST `/auth/cadastro`
Cria nova conta de usuário

**Body**:
```json
{
  "nome": "João Silva",
  "email": "joao@empresa.com",
  "senha": "senha123"
}
```

**Response 201**:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "tipo": "bearer",
  "expira_em": 1800
}
```

---

### POST `/auth/login`
Autentica usuário existente

**Body**:
```json
{
  "email": "joao@empresa.com",
  "senha": "senha123"
}
```

**Response 200**: Mesma estrutura do cadastro

---

### POST `/auth/refresh`
Renova access_token usando refresh_token

**Headers**: `Authorization: Bearer <refresh_token>`

**Response 200**:
```json
{
  "access_token": "eyJ...",
  "tipo": "bearer",
  "expira_em": 1800
}
```

---

### POST `/auth/logout`
Revoga refresh_token

**Headers**: `Authorization: Bearer <access_token>`

**Response 204**: No content

---

### GET `/auth/me`
Retorna dados do usuário autenticado

**Headers**: `Authorization: Bearer <access_token>`

**Response 200**:
```json
{
  "id": 1,
  "nome": "João Silva",
  "email": "joao@empresa.com",
  "perfil": "CLIENTE",
  "ativo": true
}
```

---

## 💊 Medicamentos

### GET `/medicamentos/buscar`
Busca medicamentos por nome ou princípio ativo

**Query Params**:
- `q` (string, required): Termo de busca (mín. 2 caracteres)
- `apenas_ativos` (boolean, default: true): Filtrar apenas registros ativos
- `pagina` (int, default: 1): Número da página
- `limite` (int, default: 20, max: 100): Resultados por página

**Headers**: `Authorization: Bearer <access_token|api_key>`

**Response 200**:
```json
{
  "total": 42,
  "pagina": 1,
  "limite": 20,
  "resultados": [
    {
      "id": 123,
      "medicamento": "DIPIRONA SÓDICA 500MG",
      "principio_ativo": "DIPIRONA SÓDICA",
      "numero_registro": "1.0000.0000",
      "classe_terapeutica": "ANALGÉSICO",
      "apresentacao": "COMPRIMIDO",
      "empresa": "LABORATÓRIO XYZ",
      "tarja": "SEM TARJA",
      "situacao_registro": "ATIVO",
      "pf": 5.50,
      "pmc": 12.80,
      "pmvg": 10.20
    }
  ],
  "sugestao": null
}
```

---

### GET `/medicamentos/{id}`
Detalhes de um medicamento específico

**Path**: `id` (int)

**Headers**: `Authorization: Bearer <access_token|api_key>`

**Response 200**: Objeto medicamento completo

---

## 🎯 Análise de Risco

### POST `/analise/risco`
Analisa risco clínico e financeiro de uma prescrição

**Headers**: `Authorization: Bearer <access_token|api_key>`

**Body**:
```json
{
  "medicamento": "DIPIRONA",
  "preco_informado": 15.50,
  "tratamento": "Dor pós-operatória",
  "cid": "R52.9",
  "procedimento": "03.01.01.007-2",
  "quantidade": 1
}
```

**Validações**:
- `medicamento`: string 2-300 chars, deve conter texto
- `preco_informado`: float 0-999999.99
- `tratamento`: string 0-500 chars (opcional)
- `cid`: regex `[A-Z]\d{2}(\.\d{1,2})?` (opcional)
- `procedimento`: regex `\d{2}\.\d{2}\.\d{2}\.\d{3}-\d` (opcional)
- `quantidade`: int 1-9999

**Response 200**:
```json
{
  "aderente": false,
  "pontuacao_aderencia": 67,
  "pontuacao_risco": 33,
  "potencial_glosa": "MEDIO",
  "classificacao_risco": "MEDIO",
  "motivos": [
    "Preço informado 21% acima do PMC",
    "CID não compatível com procedimento SIGTAP"
  ],
  "analise_tratamento": {
    "situacao": "ADERENTE",
    "classe_terapeutica": "ANALGÉSICO",
    "motivo": ""
  },
  "analise_cid": {
    "situacao": "ADERENTE",
    "cid": "R52.9",
    "descricao": "Dor não especificada",
    "motivo": ""
  },
  "analise_procedimento": {
    "situacao": "ADERENTE",
    "procedimento": "03.01.01.007-2",
    "descricao": "Tratamento de dor",
    "motivo": ""
  },
  "analise_cid_procedimento": {
    "situacao": "NAO_ADERENTE",
    "motivo": "CID R52.9 não está na lista de CIDs compatíveis com procedimento 03.01.01.007-2"
  },
  "analise_preco": {
    "situacao": "ATENCAO",
    "preco_informado": 15.50,
    "pf": 5.50,
    "pmc": 12.80,
    "pmvg": 10.20,
    "variacao_pf_pct": 181.8,
    "variacao_pmc_pct": 21.1,
    "variacao_pmvg_pct": 51.9,
    "motivo": "Preço 21% acima do PMC"
  },
  "analise_quantidade": {
    "situacao": "ADERENTE",
    "quantidade_informada": 1,
    "quantidade_esperada": 1,
    "motivo": ""
  },
  "medicamento_encontrado": "DIPIRONA SÓDICA 500MG",
  "numero_registro": "1.0000.0000",
  "situacao_anvisa": "ATIVO"
}
```

---

## 👤 Usuário

### GET `/usuario/consumo`
Resumo de consumo (hoje + mês)

**Headers**: `Authorization: Bearer <access_token|api_key>`

**Response 200**:
```json
{
  "plano": "Gratuito",
  "limite_diario": 100,
  "limite_mensal": 2000,
  "consumo_hoje": 23,
  "consumo_mes": 456,
  "percentual_diario": 23.0,
  "percentual_mensal": 22.8,
  "por_modulo_hoje": [
    {"modulo": "MEDICAMENTOS", "total": 18},
    {"modulo": "ANALISE", "total": 5}
  ],
  "por_modulo_mes": [
    {"modulo": "MEDICAMENTOS", "total": 320},
    {"modulo": "ANALISE", "total": 136}
  ]
}
```

---

### GET `/usuario/chaves`
Lista chaves de API ativas

**Headers**: `Authorization: Bearer <access_token>`

**Response 200**:
```json
[
  {
    "id": 1,
    "nome": "Servidor de Produção",
    "prefixo": "med_abc12345",
    "ativa": true,
    "criado_em": "2026-06-01T10:00:00Z",
    "ultimo_uso_em": "2026-06-04T14:30:00Z"
  }
]
```

---

### POST `/usuario/chaves`
Cria nova chave de API

**Headers**: `Authorization: Bearer <access_token>`

**Body**:
```json
{
  "nome": "App Mobile"
}
```

**Response 201**:
```json
{
  "id": 2,
  "nome": "App Mobile",
  "prefixo": "med_xyz67890",
  "chave_completa": "med_xyz67890abcdefghijklmnopqrstuvwxyz123456",
  "ativa": true,
  "criado_em": "2026-06-04T15:00:00Z"
}
```

⚠️ **IMPORTANTE**: `chave_completa` só aparece na criação. Salve imediatamente.

---

### DELETE `/usuario/chaves/{id}`
Revoga chave de API

**Headers**: `Authorization: Bearer <access_token>`

**Response 204**: No content

---

### PUT `/usuario/perfil`
Atualiza nome do usuário

**Headers**: `Authorization: Bearer <access_token>`

**Body**:
```json
{
  "nome": "João Pedro Silva"
}
```

**Response 200**:
```json
{
  "mensagem": "Perfil atualizado com sucesso."
}
```

---

### PUT `/usuario/senha`
Altera senha

**Headers**: `Authorization: Bearer <access_token>`

**Body**:
```json
{
  "senha_atual": "senha123",
  "senha_nova": "novaSenha456"
}
```

**Response 200**:
```json
{
  "mensagem": "Senha alterada com sucesso. Faça login novamente."
}
```

**Obs**: Revoga todos os refresh tokens do usuário (força re-login)

---

## 🏥 Sistema

### GET `/saude`
Health check

**Response 200**:
```json
{
  "status": "operacional",
  "servico": "MedID Data",
  "versao": "1.0.0",
  "environment": "production"
}
```

---

### GET `/docs`
Swagger UI (documentação interativa)

---

### GET `/redoc`
ReDoc (documentação alternativa)

---

## 🔑 Métodos de Autenticação

### 1. JWT Bearer Token
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2. API Key (Header Authorization)
```
Authorization: Bearer med_abc12345678901234567890123456789012345678
```

### 3. API Key (Header X-API-Key)
```
X-API-Key: med_abc12345678901234567890123456789012345678
```

---

## 📊 Rate Limiting

**Plano Gratuito**:
- 100 requisições/dia
- 2.000 requisições/mês

**Plano Profissional**:
- 1.000 requisições/dia
- 20.000 requisições/mês

**Plano Enterprise**:
- Ilimitado

**Response 429** (Rate Limit):
```json
{
  "detail": "Limite diário excedido. Upgrade seu plano ou aguarde reset às 00:00."
}
```

---

**Última atualização**: 2026-06-04  
**Versão**: 1.0.0
