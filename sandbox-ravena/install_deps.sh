#!/bin/bash
# ============================================
# INSTALAÇÃO RÁPIDA DE DEPENDÊNCIAS
# Sandbox Ravena
# ============================================

echo "============================================"
echo "  INSTALAÇÃO RÁPIDA DE DEPENDÊNCIAS"
echo "============================================"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "1. Verificando Python..."
if command -v python3 &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Python3 encontrado"
    
    echo "2. Instalando dependências Python..."
    pip3 install flask psycopg2-binary redis pyjwt
    echo -e "  ${GREEN}✓${NC} Dependências instaladas"
else
    echo -e "  ${RED}✗${NC} Python3 não encontrado"
    echo "  Instale Python3 primeiro"
    exit 1
fi

echo ""
echo "3. Verificando instalação..."
if python3 -c "import flask; import psycopg2; import redis; import jwt; print('Todas as dependências OK')" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Todas as dependências instaladas"
else
    echo -e "  ${RED}✗${NC} Algumas dependências falharam"
fi

echo ""
echo "============================================"
echo "  INSTALAÇÃO CONCLUÍDA"
echo "============================================"
echo ""
echo "PRÓXIMOS PASSOS:"
echo "1. Execute: ./install_all.sh"
echo "2. Ou inicie manualmente: python3 app.py"
echo ""
