#!/bin/bash
# ============================================
# MONITORAMENTO DE TRÁFEGO
# Sandbox Ravena
# ============================================

echo "============================================"
echo "  MONITORAMENTO DE TRÁFEGO"
echo "============================================"

echo ""

# 1. Verificar interfaces de rede
echo "1. Interfaces de rede:"
if command -v ifconfig &> /dev/null; then
    ifconfig 2>/dev/null | grep -E "^[a-z]|inet " | head -20
elif command -v ip &> /dev/null; then
    ip addr 2>/dev/null | grep -E "^[0-9]|inet " | head -20
else
    echo "   Comandos de rede não disponíveis"
fi

echo ""

# 2. Verificar conexões ativas
echo "2. Conexões ativas:"
if command -v netstat &> /dev/null; then
    netstat -an 2>/dev/null | grep ESTABLISHED | head -10
elif command -v ss &> /dev/null; then
    ss -an 2>/dev/null | grep ESTAB | head -10
else
    echo "   Comandos de rede não disponíveis"
fi

echo ""

# 3. Verificar portas abertas
echo "3. Portas abertas:"
if command -v netstat &> /dev/null; then
    netstat -tlnp 2>/dev/null | head -10
elif command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | head -10
else
    echo "   Comandos de rede não disponíveis"
fi

echo ""

# 4. Verificar tráfego de rede
echo "4. Tráfego de rede:"
if command -v ifconfig &> /dev/null; then
    ifconfig eth0 2>/dev/null | grep -E "RX|TX" || echo "   Interface eth0 não encontrada"
elif command -v ip &> /dev/null; then
    ip -s link 2>/dev/null | head -20
else
    echo "   Comandos de rede não disponíveis"
fi

echo ""

# 5. Verificar containers Docker
echo "5. Containers Docker:"
if command -v docker &> /dev/null; then
    docker ps 2>/dev/null || echo "   Docker não está rodando"
else
    echo "   Docker não instalado"
fi

echo ""

# 6. Verificar logs de rede
echo "6. Últimos logs de rede:"
if [ -f /var/log/syslog ]; then
    tail -10 /var/log/syslog 2>/dev/null | grep -i "net\|eth\|docker" || echo "   Nenhum log relevante"
elif [ -f /var/log/messages ]; then
    tail -10 /var/log/messages 2>/dev/null | grep -i "net\|eth\|docker" || echo "   Nenhum log relevante"
else
    echo "   Logs de sistema não encontrados"
fi

echo ""
echo "============================================"
echo "  MONITORAMENTO CONCLUÍDO"
echo "============================================"
