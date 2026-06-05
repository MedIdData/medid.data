# Migrações do Banco de Dados

## Como aplicar em produção (Railway)

### Opção 1: Via psql (Recomendado)

1. Acesse o Railway CLI ou dashboard
2. Obtenha a string de conexão do PostgreSQL
3. Execute:

```bash
psql $DATABASE_URL -f migrations/add_extensions.sql
```

### Opção 2: Via Railway Dashboard

1. Acesse Railway Dashboard → PostgreSQL → Query
2. Copie e cole o conteúdo de `add_extensions.sql`
3. Execute

### Opção 3: Via setup_prod.py

Se você ainda não rodou o setup, basta executar:

```bash
python setup_prod.py
```

O script agora cria as extensões automaticamente.

---

## Histórico de Migrações

### 2026-06-04 - add_extensions.sql
**Problema**: Busca de medicamentos não funciona em produção  
**Causa**: Extensões pg_trgm e unaccent não instaladas  
**Solução**: CREATE EXTENSION IF NOT EXISTS pg_trgm, unaccent  
**Impacto**: CRÍTICO - sem essas extensões, queries falham com "function does not exist"

**Funções afetadas**:
- `word_similarity()` - requer pg_trgm
- `unaccent()` - requer unaccent
- Índices GIN com `gin_trgm_ops` - requer pg_trgm
- `websearch_to_tsquery('portuguese')` - built-in, não precisa extensão

**Arquivos que dependem**:
- `app/repositories/medicamento_repo.py` (linhas 31-32, 52-53, 92)
- `app/models/medicamento.py` (índices GIN, linhas 42-44)

---

## Verificação

Para verificar se as extensões estão instaladas:

```sql
SELECT extname, extversion
FROM pg_extension
WHERE extname IN ('pg_trgm', 'unaccent')
ORDER BY extname;
```

Saída esperada:
```
 extname  | extversion
----------+------------
 pg_trgm  | 1.6
 unaccent | 1.1
```

Se retornar vazio, as extensões NÃO estão instaladas.

---

## Troubleshooting

### Erro: "must be owner of extension"
**Causa**: Usuário do Railway pode não ter permissão para criar extensões  
**Solução**: Railway PostgreSQL normalmente permite, mas se falhar, contate suporte Railway

### Erro: "could not open extension control file"
**Causa**: Extensão não está disponível no servidor PostgreSQL  
**Solução**: Railway usa PostgreSQL com contrib instalado, deve funcionar. Verifique versão do PG.

### Busca ainda não funciona após instalar extensões
**Causa**: Índices podem não ter sido criados corretamente  
**Solução**: Execute `python setup_prod.py` novamente para recriar tabelas e índices
