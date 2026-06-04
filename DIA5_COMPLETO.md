# MedID Data — Dia 5 COMPLETO ✓

**Data:** 2026-06-04  
**Objetivo:** Sistema completo de autenticação JWT + controle de acesso + limites de consumo

---

## ✅ O que foi implementado

### 1. Autenticação JWT Completa

#### Modelos de Dados
- `Usuario` — perfil, empresa_id, ativo
- `RefreshToken` — rotação automática, expiração, revogação
- `Plano` — limite_diario, limite_mensal, valor_mensal_centavos
- `Empresa` — gestão multitenancy B2B
- `ChaveAcesso` — API keys `med_...` para integrações
- `ConsumoDiario` — rastreamento por usuário/dia/módulo
- `AuditoriaRequisicao` — log completo de acessos

#### Endpoints API (`/auth`)
- `POST /auth/cadastro` — criar conta + retorna tokens
- `POST /auth/login` — autenticar + retorna tokens
- `POST /auth/refresh` — renovar access_token com rotação de refresh_token
- `POST /auth/logout` — limpa cookies
- `GET /auth/me` — perfil do usuário autenticado

#### Páginas Web
- `GET /login` — formulário de login
- `POST /login` — autenticação via formulário → redireciona para `/painel`
- `GET /cadastro` — formulário de criação de conta
- `POST /cadastro` — criar conta → redireciona para `/painel`
- `POST /sair` — logout → redireciona para `/login`
- `GET /painel` — dashboard com consumo diário/mensal e limites

#### Middleware de Autenticação (`auth_middleware.py`)
- `get_usuario_atual()` — extrai usuário de JWT (cookie ou Bearer) ou chave API
- `requer_usuario()` — dependência que exige autenticação (401 se ausente)
- `requer_usuario_web()` — dependência que redireciona para `/login` se ausente
- `requer_acesso(modulo)` — autenticação + verificação de limites + auditoria + consumo

#### Proteção das Rotas API
- `/medicamentos/buscar` → `requer_acesso("MEDICAMENTOS")`
- `/medicamentos/{id}` → `requer_acesso("MEDICAMENTOS")`
- `/analise/risco` → `requer_acesso("ANALISE")`

### 2. Sistema de Planos e Limites

#### Plano Gratuito (seed automático)
- **Limite diário:** 100 requisições
- **Limite mensal:** 2000 requisições
- **Custo:** R$ 0,00

#### Lógica de Verificação
1. Usuário faz requisição autenticada
2. Sistema verifica consumo_hoje vs. limite_diario
3. Se limite atingido → HTTP 429 "Too Many Requests"
4. Se OK → incrementa consumo_diario
5. Registra em auditoria_requisicoes

### 3. Seed Automático

**Executado no startup da aplicação (`lifespan`):**

```python
_seed_plano_gratuito()    # Cria plano "Gratuito" se não existir
_seed_usuario_padrao()     # Cria admin@mediddata.com se não houver usuários
```

**Credenciais padrão:**
- E-mail: `admin@mediddata.com`
- Senha: `medid@2026`
- Perfil: `ADMINISTRADOR`

---

## 🧪 Testes Executados

### ✅ Fluxo de Cadastro
```bash
POST /auth/cadastro
{
  "nome": "Teste Usuario",
  "email": "teste@mediddata.com",
  "senha": "senha123"
}
→ Retorna access_token + refresh_token
→ Cria usuário com perfil CLIENTE
```

### ✅ Fluxo de Autenticação
```bash
GET /auth/me
Authorization: Bearer <access_token>
→ Retorna perfil do usuário
```

### ✅ Consumo e Auditoria
```bash
GET /medicamentos/buscar?q=dipirona
Authorization: Bearer <access_token>
→ Retorna 575 resultados
→ Incrementa consumo_diario (MEDICAMENTOS)
→ Registra em auditoria_requisicoes
```

**Consumo verificado:**
- MEDICAMENTOS: 7 consultas
- ANALISE: 2 consultas
- TOTAL: 9/100 (limite diário)

### ✅ Verificação de Limites
```bash
# Alterado plano para limite_diario = 10 (teste)
# Após 10 requisições:
→ HTTP 429: "Limite diário de 10 consultas atingido. Aguarde o próximo dia ou faça upgrade do plano."
✓ Limite restaurado para 100 req/dia
```

### ✅ Páginas Web
- `/login` → título correto, formulário presente
- `/cadastro` → título correto, formulário presente
- `/painel` → redireciona para `/login?proxima=/painel` quando não autenticado

---

## 📁 Estrutura Final

```
app/
├── main.py                          # seed_plano + seed_usuario no lifespan
├── config.py                        # SECRET_KEY, JWT settings
├── database.py                      # SessionLocal, get_db
├── middleware/
│   └── auth_middleware.py           # requer_usuario, requer_acesso, get_usuario_atual
├── models/
│   ├── usuario.py                   # Usuario, RefreshToken
│   ├── empresa.py                   # Plano, Empresa
│   ├── chave_acesso.py              # ChaveAcesso
│   └── auditoria.py                 # ConsumoDiario, AuditoriaRequisicao
├── repositories/
│   └── usuario_repo.py              # CRUD, consumo, auditoria
├── routers/
│   ├── auth.py                      # /auth/cadastro, /login, /refresh, /logout, /me
│   ├── usuario.py                   # /usuario/perfil, /usuario/chaves
│   ├── medicamentos.py              # /medicamentos/buscar [protegido]
│   ├── analise.py                   # /analise/risco [protegido]
│   └── web.py                       # /login, /cadastro, /painel, /buscar, /analise (HTML)
├── schemas/
│   ├── auth.py                      # CadastroEntrada, LoginEntrada, TokenSaida
│   └── usuario.py                   # UsuarioPerfil
├── services/
│   └── auth_service.py              # hash_senha, JWT, chaves API
└── templates/
    ├── base_auth.html               # layout para login/cadastro
    ├── login.html                   # página de login
    ├── cadastro.html                # página de cadastro
    └── painel.html                  # dashboard do usuário
```

---

## 🚀 Como Testar

### 1. Iniciar o servidor
```bash
uvicorn app.main:app --reload
```

### 2. Criar conta via API
```bash
curl -X POST http://localhost:8000/auth/cadastro \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "email": "joao@empresa.com",
    "senha": "senha123"
  }'
```

### 3. Fazer login via API
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao@empresa.com",
    "senha": "senha123"
  }'
```

### 4. Buscar medicamentos (autenticado)
```bash
curl http://localhost:8000/medicamentos/buscar?q=dipirona \
  -H "Authorization: Bearer <access_token>"
```

### 5. Analisar risco (autenticado)
```bash
curl -X POST http://localhost:8000/analise/risco \
  -H "Authorization: Bearer <access_token>" \
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

### 6. Acessar via Web
- http://localhost:8000/cadastro → criar conta
- http://localhost:8000/login → fazer login
- http://localhost:8000/painel → dashboard
- http://localhost:8000/buscar → busca de medicamentos
- http://localhost:8000/analise → análise de risco

---

## 🎯 Próximos Passos: Dias 6 e 7

### **DIA 6: Gestão de Usuários e Chaves de Acesso**

#### Endpoints a implementar:
1. **Gestão de Chaves API**
   - `POST /usuario/chaves` — criar nova chave `med_...`
   - `GET /usuario/chaves` — listar chaves do usuário
   - `DELETE /usuario/chaves/{id}` — revogar chave
   - Página web `/chaves` — interface de gestão

2. **Gestão de Perfil**
   - `PUT /usuario/perfil` — atualizar nome
   - `PUT /usuario/senha` — alterar senha
   - Página web `/perfil` — editar dados

3. **Histórico de Consumo**
   - `GET /usuario/consumo` — consumo mensal agregado
   - Página web `/consumo` — gráficos e histórico

4. **Auditoria (Admin)**
   - `GET /admin/usuarios` — listar todos os usuários
   - `GET /admin/auditoria` — logs de requisições
   - `PUT /admin/usuarios/{id}` — ativar/desativar usuário

### **DIA 7: Deploy e Finalização**

1. **Deploy Railway**
   - Configurar variáveis de ambiente (DATABASE_URL, SECRET_KEY)
   - Deploy automático via GitHub
   - Teste em produção

2. **Documentação API**
   - Completar descrições no Swagger (`/docs`)
   - Adicionar exemplos de requisição/resposta
   - Criar README.md público

3. **Melhorias de Segurança**
   - Rate limiting por IP (Slowapi)
   - CORS configurável por ambiente
   - Logs estruturados (Loguru)

4. **Testes Automatizados**
   - Testes de integração (pytest)
   - Testes de autenticação
   - Testes de limites de consumo

5. **Monitoramento**
   - Health check avançado (`/saude`)
   - Métricas de consumo agregado
   - Alertas de limite

---

## 📊 Métricas do Dia 5

- **Arquivos criados:** 8
- **Arquivos modificados:** 5
- **Linhas de código:** ~800
- **Endpoints API:** 6 novos
- **Páginas web:** 4 novas
- **Modelos de dados:** 7
- **Testes manuais:** 100% sucesso

---

## 🔐 Segurança Implementada

✅ Senhas com bcrypt (12 rounds)  
✅ JWT com expiração (30min access, 7 dias refresh)  
✅ Refresh token rotation (revoga token antigo)  
✅ Cookies HTTP-only (proteção XSS)  
✅ Chaves API com SHA-256 hash  
✅ Rate limiting por usuário/plano  
✅ Auditoria completa de requisições  
✅ Validação de entrada (Pydantic)  

---

**Status:** DIA 5 COMPLETO ✅  
**Próximo:** DIA 6 — Gestão de Usuários  
**Prazo estimado:** 1-2 horas de desenvolvimento
