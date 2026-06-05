# Regras de Negócio - MedID Data

## 🔐 Autenticação e Autorização

### Cadastro
- Email único (case-insensitive, normalizado com .strip().lower())
- Senha mínima: 6 caracteres
- Hash: bcrypt cost 12
- Perfil padrão: CLIENTE
- Status padrão: ativo=true

### Login
- Gera access_token (exp 30min)
- Gera refresh_token (exp 7 dias)
- Cookies HttpOnly + SameSite=Lax
- Falha: 401 "E-mail ou senha incorretos"
- Conta inativa: 403 "Conta desativada"

### API Keys
- Formato: `med_` + 36 chars (secrets.token_urlsafe)
- Armazenamento: SHA256 hash
- Prefixo: primeiros 12 chars (para identificação)
- Revogação: soft delete (ativa=false)

---

## 💰 Planos e Limites

### Plano Gratuito (Padrão)
- Limite diário: 100 requisições
- Limite mensal: 2.000 requisições
- Acesso: todos os módulos
- Preço: R$ 0,00

### Plano Profissional
- Limite diário: 1.000 requisições
- Limite mensal: 20.000 requisições
- Preço: R$ 299,00/mês

### Plano Enterprise
- Ilimitado
- SLA 99,9%
- Suporte dedicado
- Preço: sob consulta

### Contabilização de Consumo
- Incrementado a cada request bem-sucedido (200, 201)
- Não incrementa em erros 4xx/5xx
- Módulos: "MEDICAMENTOS" | "ANALISE"
- Reset diário: 00:00 UTC
- Reset mensal: dia 1 do mês

### Bloqueio por Limite
- HTTP 429: "Limite diário excedido"
- HTTP 429: "Limite mensal excedido"
- Mensagem: sugere upgrade de plano

---

## 🔍 Busca de Medicamentos

### Fuzzy Matching
- Termo mínimo: 2 caracteres
- Query: `ILIKE %termo%` em medicamento e principio_ativo
- Paginação: default 20, max 100
- Filtro: apenas_ativos=true (padrão)

### Sugestão Ortográfica
- Algoritmo básico: distância de edição
- Ativa quando total=0

### Response
- Integração ANVISA + CMED (JOIN por número registro ou nome)
- Retorna: medicamento, principio_ativo, classe, tarja, situação, pf, pmc, pmvg

---

## 🎯 Análise de Risco

### Entrada
- **Obrigatório**: medicamento, preco_informado, quantidade
- **Opcional**: tratamento, cid, procedimento

### Validações
- medicamento: 2-300 chars, deve conter texto
- preco_informado: 0-999999.99
- quantidade: 1-9999
- cid: regex `[A-Z]\d{2}(\.\d{1,2})?`
- procedimento: regex `\d{2}\.\d{2}\.\d{2}\.\d{3}-\d`

### 9 Dimensões
1. Tratamento vs Classe Terapêutica
2. CID-10
3. Procedimento SIGTAP
4. CID + Procedimento (compatibilidade)
5. Preço (comparação com PF/PMC/PMVG)
6. Quantidade
7. Cobertura
8. Situação ANVISA
9. Inconsistências

### Scoring
- Pesos: ADERENTE=0, ATENCAO=1, NAO_ADERENTE=3, NAO_INFORMADO=0
- Risco = (soma_pesos / 27) * 100
- Aderência = 100 - risco

### Potencial de Glosa
- Risco <30%: BAIXO
- Risco 30-60%: MEDIO
- Risco >60%: ALTO

### Regra Crítica
⚠️ **Ausência de dados confiáveis deve AUMENTAR risco**:
- Medicamento não encontrado: NAO_ADERENTE (3 pontos)
- Medicamento sem preço CMED: NAO_ADERENTE (3 pontos)
- CID inválido: NAO_ADERENTE (3 pontos)
- Procedimento inválido: NAO_ADERENTE (3 pontos)

---

## 👤 Perfis de Usuário

### CLIENTE
- Acesso: busca, análise, consumo, chaves
- Menu: Perfil, Alterar Senha, Chaves, Consumo, Sair
- Sem acesso a /admin

### ADMINISTRADOR
- Acesso: tudo do CLIENTE + /admin
- Menu: +item "Administração"
- Permissões: gerenciar usuários, planos, chaves globais

---

## 🔒 Segurança

### Senhas
- Mínimo: 6 caracteres
- Hash: bcrypt cost 12
- Sem validação de complexidade (por enquanto)
- Alterar senha: revoga todos refresh tokens (force re-login)

### Tokens
- Access Token: exp 30min, payload {user_id, email, perfil}
- Refresh Token: exp 7 dias, armazenado no DB (hash SHA256)
- Revogação: soft delete (revogado=true)

### Rate Limiting
- SlowAPI: 100 req/min por IP (opcional, desabilitado em dev)
- Limite por plano: hard limit no banco de dados

---

## 📊 Auditoria (Futuro)

### Eventos
- Login/logout
- Criação usuário
- Alteração senha
- Criação/revogação chave API
- Alteração plano
- Requisições às APIs

### Campos
- usuario_id
- acao (string)
- endpoint (string)
- ip (string)
- timestamp
- dados_json (JSONB)

---

**Última atualização**: 2026-06-04  
**Versão**: 1.0.0
