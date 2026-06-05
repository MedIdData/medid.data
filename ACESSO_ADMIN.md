# 🔐 Como Acessar a Área Administrativa

## Opção 1: Usar conta admin padrão

O sistema cria automaticamente um usuário administrador:

```
Email: admin@mediddata.com
Senha: medid@2026
```

## Opção 2: Promover seu usuário atual

Se você já tem um usuário cadastrado e quer promovê-lo a administrador:

```bash
python3 scripts/promover_admin.py seu-email@exemplo.com
```

**Exemplo:**
```bash
python3 scripts/promover_admin.py teste@mediddata.com
```

O script irá:
- ✅ Encontrar seu usuário pelo email
- ✅ Promover para perfil ADMINISTRADOR
- ✅ Ajustar limites para 1000 req/dia e 20000 req/mês
- ✅ Reativar a conta se estiver inativa

---

## 🎯 Acessando o Painel Admin

### 1. Fazer Login
```
http://localhost:8000/login
```
Use as credenciais do usuário admin.

### 2. Acessar Administração

**Via Dropdown:**
- Clicar no seu nome (canto superior direito)
- Clicar em "Administração"

**Via URL direta:**
```
http://localhost:8000/admin
```

---

## 📋 O que você pode fazer na área admin:

### ✅ **Estatísticas do Sistema**
- Ver total de usuários
- Ver usuários ativos
- Ver total de chaves API
- Ver requisições do dia

### ✅ **Criar Novo Usuário**
- Clicar em "Novo Usuário"
- Preencher: nome, email, senha, perfil
- Definir limites diários e mensais
- Salvar

### ✅ **Editar Usuário Existente**
- Clicar no ícone de lápis (editar)
- Alterar: nome, email, perfil, status
- Ajustar limites de uso
- Salvar alterações

### ✅ **Resetar Senha**
- Clicar no ícone de cadeado
- Definir nova senha (mínimo 6 caracteres)
- Confirmar

### ✅ **Ativar/Desativar Usuário**
- Clicar no ícone de desativar (círculo cortado)
- Confirmar ação
- Status muda entre Ativo/Inativo

---

## ⚠️ Proteções de Segurança

- **Você não pode desativar sua própria conta** (proteção contra lockout)
- **Você não pode excluir sua própria conta**
- **Apenas perfil ADMINISTRADOR acessa esta área** (403 Forbidden para outros)
- **Todas as ações são auditáveis** (logs no sistema)

---

## 🐛 Problemas Comuns

### "Acesso negado. Apenas administradores."
- Verifique se você está logado como ADMINISTRADOR
- Execute: `python3 scripts/promover_admin.py seu-email@exemplo.com`
- Faça logout e login novamente

### "Não vejo o botão Administração"
- Apenas perfil ADMINISTRADOR vê este botão
- Promova seu usuário com o script acima

### "Internal Server Error ao acessar /admin"
- Verifique se o servidor está rodando
- Veja os logs no terminal: `uvicorn app.main:app --reload`

---

## 📞 Suporte

Se ainda tiver problemas, verifique:
1. Logs do servidor (terminal onde rodou uvicorn)
2. Perfil do seu usuário no banco
3. Se está logado corretamente
