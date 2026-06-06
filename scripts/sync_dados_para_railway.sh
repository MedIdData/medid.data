#!/bin/bash

echo "========================================="
echo "🚀 SINCRONIZAÇÃO DE DADOS PARA RAILWAY"
echo "========================================="

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Obter credenciais do Railway
echo -e "\n${YELLOW}📋 Obtendo credenciais do Railway...${NC}"

# Verificar se railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI não encontrado!${NC}"
    echo "Instale com: npm i -g @railway/cli"
    echo "Ou: brew install railway"
    exit 1
fi

# Obter DATABASE_URL do Railway
echo -e "${YELLOW}🔑 Conectando ao Railway...${NC}"

# Tentar obter de diferentes formas
export RAILWAY_DB_URL=$(railway variables 2>/dev/null | grep DATABASE_URL | cut -d'=' -f2- | tr -d ' ')

if [ -z "$RAILWAY_DB_URL" ]; then
    # Tentar método alternativo
    export RAILWAY_DB_URL=$(railway run printenv DATABASE_URL 2>/dev/null)
fi

if [ -z "$RAILWAY_DB_URL" ]; then
    echo -e "${RED}❌ Não foi possível obter DATABASE_URL do Railway${NC}"
    echo ""
    echo "Execute manualmente:"
    echo "  railway run printenv DATABASE_URL"
    echo ""
    echo "E cole o resultado aqui quando perguntado:"
    read -p "DATABASE_URL do Railway: " RAILWAY_DB_URL

    if [ -z "$RAILWAY_DB_URL" ]; then
        echo -e "${RED}❌ DATABASE_URL não fornecido${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Conectado ao Railway${NC}"

# 2. Obter credenciais locais do .env
echo -e "\n${YELLOW}📋 Obtendo credenciais locais...${NC}"

if [ ! -f .env ]; then
    echo -e "${RED}❌ Arquivo .env não encontrado!${NC}"
    exit 1
fi

# Carregar .env
export $(grep -v '^#' .env | xargs)

echo -e "${GREEN}✓ Credenciais locais carregadas${NC}"

# 3. Fazer dump apenas dos DADOS (sem estrutura)
echo -e "\n${YELLOW}📦 Exportando dados do banco local...${NC}"

DUMP_FILE="/tmp/mediddata_dados_$(date +%Y%m%d_%H%M%S).sql"

# Tabelas para exportar (apenas dados, não estrutura)
TABELAS=(
    "medicamentos_anvisa"
    "medicamentos_cmed"
    "dcb"
    "cid10_categorias"
    "cid10_subcategorias"
    "sigtap_grupos"
    "sigtap_procedimentos"
    "sigtap_procedimento_cid"
)

# Truncar tabelas no Railway primeiro
echo -e "\n${YELLOW}🗑️  Limpando tabelas antigas no Railway...${NC}"
for tabela in "${TABELAS[@]}"; do
    echo "  Truncando $tabela..."
    psql "$RAILWAY_DB_URL" -c "TRUNCATE TABLE $tabela CASCADE;" 2>/dev/null
done

echo -e "${GREEN}✓ Tabelas limpas${NC}"

# Fazer dump de cada tabela
echo -e "\n${YELLOW}📤 Exportando tabelas...${NC}"

for tabela in "${TABELAS[@]}"; do
    echo "  Exportando $tabela..."

    # Contar registros locais
    COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM $tabela;" | tr -d ' ')
    echo "    Local: $COUNT registros"

    # Exportar apenas dados (--data-only) da tabela
    pg_dump "$DATABASE_URL" \
        --data-only \
        --table="$tabela" \
        --no-owner \
        --no-privileges \
        >> "$DUMP_FILE" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo -e "    ${GREEN}✓ Exportado${NC}"
    else
        echo -e "    ${RED}✗ Erro ao exportar${NC}"
    fi
done

# Verificar se o dump foi criado
if [ ! -f "$DUMP_FILE" ]; then
    echo -e "${RED}❌ Erro ao criar dump!${NC}"
    exit 1
fi

DUMP_SIZE=$(du -h "$DUMP_FILE" | cut -f1)
echo -e "${GREEN}✓ Dump criado: $DUMP_FILE ($DUMP_SIZE)${NC}"

# 4. Importar para Railway
echo -e "\n${YELLOW}📥 Importando dados para Railway...${NC}"
echo -e "${YELLOW}⏳ Isso pode levar alguns minutos...${NC}\n"

# Garantir que estamos usando a URL do Railway
unset DATABASE_URL
export PGPASSWORD=""

psql "$RAILWAY_DB_URL" -f "$DUMP_FILE"

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ IMPORTAÇÃO CONCLUÍDA COM SUCESSO!${NC}"
else
    echo -e "\n${RED}❌ Erro durante importação${NC}"
    echo "Dump salvo em: $DUMP_FILE"
    exit 1
fi

# 5. Verificar contagem no Railway
echo -e "\n${YELLOW}📊 Verificando dados no Railway...${NC}\n"

for tabela in "${TABELAS[@]}"; do
    COUNT=$(psql "$RAILWAY_DB_URL" -t -c "SELECT COUNT(*) FROM $tabela;" 2>/dev/null | tr -d ' ')
    echo "  $tabela: $COUNT registros"
done

# Limpar arquivo temporário
rm -f "$DUMP_FILE"

echo -e "\n========================================="
echo -e "${GREEN}🎉 SINCRONIZAÇÃO COMPLETA!${NC}"
echo "========================================="
echo ""
echo "Acesse https://mediddata.com/debug/check-data-counts para confirmar"
echo ""
