# Modelo de Dados - MedID Data

## 📊 Diagrama ER (Resumido)

```
usuarios ←→ empresas (opcional)
    ↓
    ├─→ refresh_tokens
    ├─→ chaves_acesso
    └─→ consumo_diario

medicamentos_anvisa
medicamentos_cmed
cid10_categorias ←→ cid10_subcategorias
sigtap_grupos ←→ sigtap_procedimentos ←→ sigtap_procedimento_cid
dcb_lista
```

---

## 🗃️ Tabelas Principais

### `usuarios`
| Coluna | Tipo | Chave | Descrição |
|--------|------|-------|-----------|
| id | INT | PK | ID único |
| empresa_id | INT | FK | Empresa (opcional) |
| nome | VARCHAR(200) | | Nome completo |
| email | VARCHAR(200) | UNIQUE, INDEX | E-mail (único) |
| senha_hash | VARCHAR(200) | | bcrypt hash |
| perfil | VARCHAR(20) | | ADMINISTRADOR \| CLIENTE |
| ativo | BOOLEAN | | true = ativo |
| criado_em | TIMESTAMP | | Data de criação |
| atualizado_em | TIMESTAMP | | Última atualização |

**Índices**: `email`

### `empresas`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INT PK | ID único |
| plano_id | INT FK | Plano contratado |
| nome | VARCHAR(200) | Razão social |
| cnpj | VARCHAR(18) | CNPJ (único) |
| ativo | BOOLEAN | Status |
| criado_em | TIMESTAMP | Data criação |

**Índices**: `cnpj`

### `planos`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INT PK | ID único |
| nome | VARCHAR(100) | Ex: Gratuito, Profissional |
| limite_diario | INT | Requisições/dia |
| limite_mensal | INT | Requisições/mês |
| preco_mensal | DECIMAL(10,2) | Valor R$ |
| ativo | BOOLEAN | Status |

**Valores padrão**:
- Plano Gratuito: 100/dia, 2000/mês, R$ 0,00

### `refresh_tokens`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INT PK | ID único |
| usuario_id | INT FK | Usuário |
| token_hash | VARCHAR(64) INDEX | SHA256 do token |
| expira_em | TIMESTAMP | Validade (7 dias) |
| revogado | BOOLEAN | Revogado? |
| criado_em | TIMESTAMP | Criação |

**Índices**: `token_hash`

### `chaves_acesso`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INT PK | ID único |
| usuario_id | INT FK | Proprietário |
| nome | VARCHAR(100) | Nome descritivo |
| prefixo | VARCHAR(16) | Primeiros 12 chars |
| chave_hash | VARCHAR(64) INDEX | SHA256 da chave completa |
| ativa | BOOLEAN | Ativa? |
| criado_em | TIMESTAMP | Criação |
| ultimo_uso_em | TIMESTAMP | Último uso |

**Índices**: `chave_hash`, `prefixo`

### `consumo_diario`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INT PK | ID único |
| usuario_id | INT FK | Usuário |
| data | DATE INDEX | Data (YYYY-MM-DD) |
| modulo | VARCHAR(50) INDEX | MEDICAMENTOS \| ANALISE |
| total | INT | Quantidade de requests |

**Índices**: `usuario_id + data`, `modulo`

---

## 📦 Tabelas de Referência (Dados Oficiais)

### `medicamentos_anvisa`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INT PK | ID único |
| medicamento | VARCHAR(300) INDEX | Nome comercial |
| principio_ativo | VARCHAR(300) INDEX | Substância ativa |
| numero_registro | VARCHAR(50) INDEX | Nº registro ANVISA |
| classe_terapeutica | VARCHAR(200) | Classe |
| apresentacao | VARCHAR(300) | Forma farmacêutica |
| empresa | VARCHAR(200) | Fabricante |
| tarja | VARCHAR(20) | Vermelha/Preta/Sem |
| situacao_registro | VARCHAR(50) INDEX | ATIVO \| INATIVO |
| venda_generico | BOOLEAN | É genérico? |

**Índices**: `medicamento`, `principio_ativo`, `numero_registro`, `situacao_registro`

### `medicamentos_cmed`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INT PK | ID único |
| ean | VARCHAR(20) INDEX | Código EAN |
| produto | VARCHAR(300) INDEX | Nome do produto |
| apresentacao | VARCHAR(300) | Apresentação |
| pf | DECIMAL(10,2) | Preço Fábrica |
| pmc | DECIMAL(10,2) | Preço Máx. Consumidor |
| pmvg | DECIMAL(10,2) | Preço Máx. Venda Gov |
| tarja | VARCHAR(20) | Tarja |
| tipo | VARCHAR(50) | Genérico/Similar/Ref |

**Índices**: `ean`, `produto`

### `cid10_categorias`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INT PK | ID único |
| codigo | VARCHAR(3) INDEX | Ex: A00 |
| nome | TEXT | Descrição |

**Índices**: `codigo`

### `cid10_subcategorias`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INT PK | ID único |
| categoria_id | INT FK | Categoria pai |
| codigo | VARCHAR(6) INDEX | Ex: A00.0 |
| nome | TEXT | Descrição |

**Índices**: `codigo`

### `sigtap_procedimentos`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INT PK | ID único |
| grupo_id | INT FK | Grupo SIGTAP |
| codigo | VARCHAR(20) INDEX | Ex: 03.01.01.007-2 |
| nome | TEXT | Nome procedimento |
| valor | DECIMAL(10,2) | Valor SUS |

**Índices**: `codigo`

### `sigtap_procedimento_cid`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INT PK | ID único |
| procedimento_id | INT FK | Procedimento |
| cid_codigo | VARCHAR(6) INDEX | CID-10 compatível |

**Índices**: `procedimento_id + cid_codigo`

### `dcb_lista`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INT PK | ID único |
| codigo | VARCHAR(10) INDEX | Código DCB |
| denominacao | VARCHAR(300) INDEX | Denominação Comum |
| sinonimos | TEXT | Sinônimos |

**Índices**: `codigo`, `denominacao`

---

## 🔐 Constraints e Relacionamentos

### Foreign Keys
```sql
usuarios.empresa_id → empresas.id (ON DELETE SET NULL)
empresas.plano_id → planos.id (ON DELETE RESTRICT)
refresh_tokens.usuario_id → usuarios.id (ON DELETE CASCADE)
chaves_acesso.usuario_id → usuarios.id (ON DELETE CASCADE)
consumo_diario.usuario_id → usuarios.id (ON DELETE CASCADE)
cid10_subcategorias.categoria_id → cid10_categorias.id
sigtap_procedimentos.grupo_id → sigtap_grupos.id
sigtap_procedimento_cid.procedimento_id → sigtap_procedimentos.id
```

### Unique Constraints
- `usuarios.email`
- `empresas.cnpj`
- `chaves_acesso.prefixo` (parcial - primeiros 12 chars da chave)

---

## 📈 Volumetria Esperada

| Tabela | Registros |
|--------|-----------|
| usuarios | ~1.000 |
| empresas | ~100 |
| planos | ~5 |
| refresh_tokens | ~10.000 (rotativo) |
| chaves_acesso | ~500 |
| consumo_diario | ~500.000/ano |
| medicamentos_anvisa | ~40.000 |
| medicamentos_cmed | ~18.000 |
| cid10_categorias | ~2.000 |
| cid10_subcategorias | ~12.000 |
| sigtap_procedimentos | ~4.000 |
| dcb_lista | ~3.000 |

---

**Última atualização**: 2026-06-04  
**Versão**: 1.0.0
