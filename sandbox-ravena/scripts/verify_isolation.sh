#!/bin/bash
# ============================================
# VERIFICAÇÃO DE ISOLAMENTO
# Sandbox Ravena
# ============================================

echo "============================================"
echo "  VERIFICAÇÃO DE ISOLAMENTO"
echo "============================================"

echo ""

# 1. Testar acesso à internet
echo "1. Testando acesso à internet..."
if ping -c 1 google.com &> /dev/null; then
    echo "   [FALHA] Acesso à internet detectado!"
else
    echo "   [OK] Sem acesso à internet"
fi

# 2. Testar DNS externo
echo "2. Testando DNS externo..."
if nslookup google.com &> /dev/null; then
    echo "   [FALHA] DNS externo acessível!"
else
    echo "   [OK] DNS externo bloqueado"
fi

# 3. Testar portas externas
echo "3. Testando portas externas..."
if nc -z -w1 8.8.8.8 53 &> /dev/null; then
    echo "   [FALHA] Porta externa acessível!"
else
    echo "   [OK] Portas externas bloqueadas"
fi

# 4. Verificar containers
echo "4. Verificando containers..."
if command -v docker &> /dev/null; then
    docker network inspect ravena-sandbox 2>/dev/null | grep "Internal" || echo "   Rede não encontrada"
else
    echo "   Docker não instalado"
fi

# 5. Verificar rotas
echo "5. Verificando rotas de rede..."
if command -v route &> /dev/null; then
    route -n 2>/dev/null | head -10 || echo "   Não foi possível listar rotas"
else
    echo "   Comando route não disponível"
fi

# 6. Verificar interfaces de rede
echo "6. Verificando interfaces de rede..."
if command -v ifconfig &> /dev/null; then
    ifconfig 2>/dev/null | grep -A1 "eth0\|docker0" || echo "   Interfaces não encontradas"
elif command -v ip &> /dev/null; then
    ip addr 2>/dev/null | grep -A1 "eth0\|docker0" || echo "   Interfaces não encontradas"
else
    echo "   Comandos de rede não disponíveis"
fi

echo ""
echo "============================================"
echo "  VERIFICAÇÃO CONCLUÍDA"
echo "============================================"
