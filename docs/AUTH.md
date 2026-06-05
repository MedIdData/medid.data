# Fluxo de Autenticação - MedID Data

## 🔐 Visão Geral

MedID Data suporta **2 métodos de autenticação**:

1. **JWT Bearer Token** (sessões web, apps mobile)
2. **API Keys** (integrações servidor-a-servidor)

---

## 🌐 JWT Bearer Token

### 1. Cadastro

**Endpoint**: `POST /auth/cadastro`

**Fluxo**:
```
1. Usuário preenche: nome, email, senha
2. Backend valida:
   - Email único (case-insensitive)
   - Senha >= 6 chars
3. Backend cria:
   - Usuario (senha_hash = bcrypt.hashpw)
   - Perfil = CLIENTE
   - Ativo = true
4. Backend gera:
   - access_token (exp 30min)
   - refresh_token (exp 7 dias)
5. Backend salva:
   - RefreshToken (token_hash = SHA256, expira_em)
6. Backend retorna:
   - JSON: {access_token, refresh_token, tipo, expira_em}
   - Web: cookies HttpOnly
```

---

### 2. Login

**Endpoint**: `POST /auth/login`

**Fluxo**:
```
1. Usuário envia: email, senha
2. Backend normaliza: email = email.strip().lower()
3. Backend busca: Usuario WHERE email = ...
4. Backend valida:
   - bcrypt.checkpw(senha, usuario.senha_hash)
   - usuario.ativo == true
5. Backend gera:
   - access_token (exp 30min)
   - refresh_token (exp 7 dias)
6. Backend salva:
   - RefreshToken (token_hash, expira_em)
7. Backend retorna:
   - JSON: {access_token, refresh_token, tipo, expira_em}
   - Web: cookies HttpOnly + redirect /painel
```

**Cookies (Web)**:
```http
Set-Cookie: access_token=eyJ...; HttpOnly; SameSite=Lax; Secure; Max-Age=1800
Set-Cookie: refresh_token=eyJ...; HttpOnly; SameSite=Lax; Secure; Max-Age=604800; Path=/auth/refresh
```

---

### 3. Autenticação de Requisições

**Middleware**: `auth_middleware.py`

**Fluxo**:
```
1. Request chega em endpoint protegido
2. Middleware extrai token:
   - Header: Authorization: Bearer <token>
   - Cookie: access_token
3. Middleware decodifica JWT:
   - jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
   - Valida exp (30min)
4. Middleware extrai payload:
   - {user_id, email, perfil}
5. Middleware busca Usuario no DB:
   - Usuario.get(id=user_id)
   - Valida usuario.ativo == true
6. Middleware injeta:
   - usuario: Usuario no Depends(requer_usuario)
7. Request prossegue normalmente
```

**Erro 401**:
```json
{
  "detail": "Token inválido ou expirado. Faça login novamente."
}
```

**Erro 403**:
```json
{
  "detail": "Conta desativada. Entre em contato com o suporte."
}
```

---

### 4. Refresh Token

**Endpoint**: `POST /auth/refresh`

**Fluxo**:
```
1. Cliente envia: refresh_token (header ou cookie)
2. Backend decodifica JWT:
   - jwt.decode(refresh_token, SECRET_KEY)
3. Backend valida:
   - RefreshToken.token_hash = SHA256(refresh_token)
   - RefreshToken.expira_em > now()
   - RefreshToken.revogado == false
4. Backend gera:
   - Novo access_token (exp 30min)
5. Backend retorna:
   - {access_token, tipo, expira_em}
```

**Por que não renovar o refresh_token?**:
- Refresh token é válido por 7 dias
- Renovar access_token 14x (7 dias / 30min) sem forçar re-login

---

### 5. Logout

**Endpoint**: `POST /auth/logout`

**Fluxo**:
```
1. Backend decodifica refresh_token do cookie
2. Backend marca:
   - RefreshToken.revogado = true
3. Backend deleta cookies:
   - access_token
   - refresh_token
4. Frontend redireciona para /login
```

---

## 🔑 API Keys

### 1. Criação

**Endpoint**: `POST /usuario/chaves`

**Fluxo**:
```
1. Usuário autenticado (JWT) envia: {nome}
2. Backend gera:
   - token = "med_" + secrets.token_urlsafe(36)  # 48 chars total
   - prefixo = token[:12]  # "med_abc12345"
   - token_hash = hashlib.sha256(token.encode()).hexdigest()
3. Backend cria:
   - ChaveAcesso(usuario_id, nome, prefixo, token_hash, ativa=true)
4. Backend retorna:
   - {id, nome, prefixo, chave_completa, ativa, criado_em}
```

⚠️ **IMPORTANTE**: `chave_completa` só é exibida UMA VEZ na criação.

---

### 2. Autenticação com API Key

**Middleware**: `auth_middleware.py`

**Fluxo**:
```
1. Request chega com API Key:
   - Header: Authorization: Bearer med_...
   - Header: X-API-Key: med_...
2. Middleware detecta prefixo "med_"
3. Middleware calcula:
   - chave_hash = SHA256(token)
4. Middleware busca:
   - ChaveAcesso WHERE chave_hash = ... AND ativa = true
5. Middleware busca:
   - Usuario WHERE id = chave_acesso.usuario_id AND ativo = true
6. Middleware atualiza:
   - ChaveAcesso.ultimo_uso_em = now()
7. Middleware injeta:
   - usuario: Usuario no Depends()
8. Request prossegue normalmente
```

**Erro 401**:
```json
{
  "detail": "Chave de acesso inválida ou revogada."
}
```

---

### 3. Revogação

**Endpoint**: `DELETE /usuario/chaves/{id}`

**Fluxo**:
```
1. Backend valida:
   - ChaveAcesso.usuario_id == current_user.id
2. Backend atualiza:
   - ChaveAcesso.ativa = false
3. Backend retorna:
   - 204 No Content
```

**Soft delete**: Chave permanece no banco, mas `ativa=false` bloqueia autenticação.

---

## 🔒 Segurança

### JWT

**Payload**:
```json
{
  "user_id": 1,
  "email": "joao@empresa.com",
  "perfil": "CLIENTE",
  "exp": 1717523456  // timestamp
}
```

**Assinatura**: HS256 (HMAC-SHA256) com SECRET_KEY

**Validação**:
- Assinatura válida?
- exp > now()?
- Usuario.ativo == true?

---

### Refresh Token

**Armazenamento**: Banco de dados (não apenas JWT)

**Vantagens**:
- Revogação imediata (logout)
- Auditoria (criado_em, revogado)
- Segurança: força re-login se comprometido

**Hash**: SHA256 antes de salvar no banco

---

### API Keys

**Armazenamento**: SHA256 hash (não plaintext)

**Prefixo**: Apenas primeiros 12 chars visíveis (identificação)

**Exemplo**:
```
Token completo: med_abc123def456ghi789jkl012mno345pqr678stu901
Prefixo visível: med_abc123de...
Hash no banco: 5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8
```

---

### Cookies (Web)

**Flags de segurança**:
- `HttpOnly`: JavaScript não pode acessar (anti-XSS)
- `SameSite=Lax`: Proteção contra CSRF
- `Secure`: HTTPS only (produção)
- `Path=/auth/refresh`: refresh_token só enviado nesse endpoint

---

## 🚨 Cenários de Erro

### 1. Senha Errada (3x)
**Atual**: Sem bloqueio  
**Futuro**: Bloquear por 15min após 5 tentativas

### 2. Token Expirado
**Response**: 401  
**Ação**: Frontend solicita refresh_token  
**Se refresh também expirou**: Redireciona para /login

### 3. Conta Desativada
**Response**: 403  
**Mensagem**: "Conta desativada. Entre em contato com o suporte."

### 4. Chave Revogada
**Response**: 401  
**Mensagem**: "Chave de acesso inválida ou revogada."

---

**Última atualização**: 2026-06-04  
**Versão**: 1.0.0
