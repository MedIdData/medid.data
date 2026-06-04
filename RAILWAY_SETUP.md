# Setup Railway - MedID Data API

## 🚀 Deploy Inicial no Railway

### 1. Criar Projeto e Adicionar PostgreSQL

1. Acesse [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub repo**
3. Selecione `mediddata-api`
4. Clique em **+ New** → **Database** → **PostgreSQL**

Railway cria automaticamente a variável `DATABASE_URL`.

### 2. Configurar Variáveis de Ambiente

No painel do serviço da API, vá em **Variables** e adicione:

```env
# Obrigatório - gerar com: openssl rand -hex 32
SECRET_KEY=<sua-chave-secreta-aqui>

# Ambiente
ENVIRONMENT=production

# CORS (substituir pelo domínio real)
ALLOWED_ORIGINS=https://seuapp.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=5000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**Gerar SECRET_KEY segura:**

```bash
openssl rand -hex 32
```

### 3. Deploy Automático

Railway faz deploy automaticamente após a configuração.

Monitor o deploy em **Deployments**.

---

## 🗄️ Setup do Banco de Dados

Após o primeiro deploy bem-sucedido, você precisa criar as tabelas e dados iniciais.

### Método 1: Via Railway CLI (Recomendado)

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link ao projeto
railway link

# Executar setup
railway run python setup_prod.py
```

### Método 2: Via Railway Dashboard

1. Vá no painel do serviço da API
2. Clique em **⋯** (três pontos) → **Shell**
3. Execute:

```bash
python setup_prod.py
```

### Output Esperado

```
======================================================================
MedID Data - Setup de Produção
======================================================================
Ambiente: production
Database: <railway-database-url>

[1/4] Testando conexão com o banco de dados...
✓ Conectado ao PostgreSQL: PostgreSQL 16.x

[2/4] Criando tabelas...
✓ Tabelas criadas com sucesso
  Total de tabelas: 15
    - auditoria_requisicoes
    - chaves_acesso
    - cid10_categorias
    - cid10_subcategorias
    - consumo_diario
    - dcb_lista
    - empresas
    - medicamentos_anvisa
    - medicamentos_cmed
    - planos
    - refresh_tokens
    - sigtap_grupos
    - sigtap_procedimento_cid
    - sigtap_procedimentos
    - usuarios

[3/4] Criando plano Gratuito...
✓ Plano Gratuito criado
    ID: 1
    Limite diário: 100 requisições
    Limite mensal: 2000 requisições

[4/4] Criando usuário administrador...
✓ Usuário administrador criado
    ID: 1
    E-mail: admin@mediddata.com
    Senha: medid@2026
    Perfil: ADMINISTRADOR

======================================================================
RESUMO DO SETUP
======================================================================
Planos: 1
Usuários: 1
Medicamentos ANVISA: 0
Medicamentos CMED: 0
CID-10 Categorias: 0
CID-10 Subcategorias: 0
SIGTAP Procedimentos: 0

======================================================================
✓ SETUP CONCLUÍDO COM SUCESSO!
======================================================================

Credenciais de acesso:
  E-mail: admin@mediddata.com
  Senha: medid@2026

⚠️  IMPORTANTE: Altere a senha padrão após o primeiro login!
======================================================================
```

---

## 📦 Importar Dados (Opcional)

Se você tiver os arquivos de dados:

### Via Railway Shell

```bash
# Acessar shell do container
railway shell

# Fazer upload dos arquivos para dados/
# (usar railway volumes ou outro método)

# Executar importações
python -m app.scripts.importar_anvisa
python -m app.scripts.importar_cmed
python -m app.scripts.importar_cid10
python -m app.scripts.importar_sigtap
python -m app.scripts.importar_dcb
```

---

## ✅ Verificar Deploy

### 1. Health Check

```bash
curl https://sua-app.up.railway.app/saude
```

**Resposta esperada:**

```json
{
  "status": "operacional",
  "servico": "MedID Data",
  "versao": "1.0.0",
  "environment": "production"
}
```

### 2. Swagger UI

Acesse: `https://sua-app.up.railway.app/docs`

### 3. Fazer Login

```bash
curl -X POST https://sua-app.up.railway.app/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@mediddata.com",
    "senha": "medid@2026"
  }'
```

**Resposta esperada:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tipo": "bearer",
  "expira_em": 1800
}
```

✅ **Se recebeu o token, o deploy está funcionando corretamente!**

---

## 🔧 Troubleshooting

### Erro: "Internal Server Error" no login

**Causa**: Tabelas não foram criadas.

**Solução**: Execute `python setup_prod.py` via Railway shell.

### Erro: "Database connection failed"

**Causa**: Variável `DATABASE_URL` não configurada.

**Solução**: Railway deve injetar automaticamente. Verifique em **Variables**.

### Erro: "Secret key not configured"

**Causa**: Variável `SECRET_KEY` não configurada.

**Solução**: Adicione em **Variables**:

```bash
SECRET_KEY=$(openssl rand -hex 32)
```

---

## 🔒 Segurança Pós-Deploy

### Checklist

- [ ] SECRET_KEY gerada com `openssl rand -hex 32`
- [ ] ENVIRONMENT=production
- [ ] ALLOWED_ORIGINS restrito (não `*`)
- [ ] Senha padrão alterada (`admin@mediddata.com`)
- [ ] Domínio customizado configurado
- [ ] HTTPS ativo (Railway automático)
- [ ] Backup automático ativo (Railway)

### Alterar Senha Padrão

```bash
# Via API
curl -X PUT https://sua-app.up.railway.app/usuario/senha \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "senha_atual": "medid@2026",
    "senha_nova": "NovaSenhaSegura123!"
  }'
```

Ou via interface web: `https://sua-app.up.railway.app/painel`

---

## 📞 Suporte

Problemas com o deploy? 

- **Logs**: Railway Dashboard → Deployments → View Logs
- **Shell**: Railway Dashboard → Service → ⋯ → Shell
- **Email**: deploy@mediddata.com

---

**Deploy Railway completo! 🚀**
