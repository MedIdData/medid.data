# Changelog - MedID Data

## [1.0.1] - 2026-06-04

### 🐛 Correções (Fase 1 e 2 + M1)

#### ✅ Completado
- **Lógica de risco invertida**: Medicamento não encontrado agora retorna NAO_ADERENTE (risco alto)
- **Validações unificadas**: Pydantic validators + HTML5 validation (medicamento, preço, CID, SIGTAP)
- **Debug removido**: Prints de debug retirados do fluxo de login (web.py)
- **Menu dropdown**: Implementado menu de usuário (Perfil, Alterar Senha, Chaves, Consumo, Admin, Sair)
- **Rotas de perfil**: Criadas rotas /perfil e /alterar-senha com validações
- **M1 - Busca travada**: Lista inicial, cursor, letra A (commit 1bac73d + hotfix c679f66)
- **M2.1 - Gauge invertido**: Removida rotação CSS, fórmula alinhada (commits eafae63 + 3 hotfixes)
- **M2.3 - Regras de glosa**: Ausência de dados = risco ALTO (commit f8eb672)

#### 🎉 Marcos Alcançados
- ✅ **100% dos módulos CRÍTICOS resolvidos**
- ✅ **67% dos módulos ALTO resolvidos** (M3, M2.2)
- ✅ Sistema funcionalmente correto nas funcionalidades principais
- ✅ Zero erros 500 por validação de campos

#### ✅ Completado (Módulo 2 - Análise de Risco)
- **M2.2 - Validação de campos**: Tratamento robusto de erros numéricos (commit f491f73)
  - Query params como string com conversão validada
  - Mensagens de erro amigáveis (tradução de ValidationError)
  - JavaScript: validação em tempo real, auto-limpeza, vírgula→ponto
  - Validators Pydantic expandidos (preço, quantidade, tratamento)

---

## [1.0.0] - 2026-06-02

### 🚀 MVP Inicial

#### Infraestrutura
- FastAPI 0.115 + SQLAlchemy 2.0 + PostgreSQL 16
- Deploy Railway com Dockerfile multi-stage
- Script setup_prod.py para inicialização do banco

#### Módulo 1: Base de Medicamentos
- Busca fuzzy matching em ~40k medicamentos ANVISA
- Integração com preços CMED (PF, PMC, PMVG)
- Sugestão ortográfica básica

#### Módulo 2: Motor de Análise de Risco
- 9 dimensões de análise implementadas
- Scoring: aderência 0-100, risco 0-100
- Potencial de glosa: BAIXO | MEDIO | ALTO
- Motivos explicáveis em português

#### Módulo 3: Gestão e Analytics
- Dashboard de consumo (hoje + mês)
- Chaves de API (formato med_*)
- Limites por plano (100/dia, 2000/mês no Gratuito)

#### Autenticação
- JWT (access 30min + refresh 7 dias)
- API Keys SHA256
- bcrypt 4.1.3 para senhas

#### Interface Web
- Design System customizado (Syne + DM Sans)
- Templates: login, cadastro, painel, buscar, analise, chaves, consumo
- Sidebar fixa + topbar responsivo

---

## [0.2.0] - 2026-05-30

### ⚙️ Correções de Deploy

- **bcrypt compatibility**: Downgrade bcrypt 5.0→4.1.3 (fix passlib)
- **Railway PORT**: Criado start.sh para expandir variável $PORT
- **Email normalization**: Unificado .strip().lower() em login/cadastro
- **Database setup**: Criado script setup_prod.py idempotente

---

## [0.1.0] - 2026-05-28

### 📦 Importação de Dados

- Script importar_anvisa.py (~40k registros)
- Script importar_cmed.py (~18k registros)
- Script importar_cid10.py (~14k registros)
- Script importar_sigtap.py (~4k registros)
- Script importar_dcb.py (~3k registros)

---

**Convenções**:
- 🚀 Features
- 🐛 Bug Fixes
- ⚡ Performance
- 📝 Docs
- 🔒 Security

**Última atualização**: 2026-06-04
