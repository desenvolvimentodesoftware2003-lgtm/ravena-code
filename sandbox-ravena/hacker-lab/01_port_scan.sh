#!/bin/bash
# ============================================
# VARREDURA DE PORTAS
# Sandbox Ravena
# ============================================

echo "============================================"
echo "  VARREDURA DE PORTAS"
echo "============================================"

TARGET="localhost"

echo "Alvo: $TARGET"
echo ""

# Varredura rápida
echo "1. Varredura rápida de portas principais..."
echo ""

# Verificar se nmap está instalado
if command -v nmap &> /dev/null; then
    nmap -p 80,8080,5432,6379,3000,5601,9090,9200 $TARGET 2>/dev/null || echo "Falha na varredura"
else
    echo "Nmap não instalado. Usando netcat..."
    for port in 80 8080 5432 6379 3000 5601 9090 9200; do
        (echo > /dev/tcp/$TARGET/$port) 2>/dev/null && echo "Porta $port: ABERTA" || echo "Porta $port: FECHADA"
    done
fi

echo ""

# Varredura detalhada
echo "2. Verificando serviços nas portas..."
echo ""

# Verificar HTTP (porta 80)
echo "Porta 80 (HTTP):"
curl -s -I "http://localhost:80" 2>/dev/null | head -5 || echo "Não disponível"
echo ""

# Verificar App (porta 8080)
echo "Porta 8080 (App):"
curl -s -I "http://localhost:8080" 2>/dev/null | head -5 || echo "Não disponível"
echo ""

# Verificar PostgreSQL (porta 5432)
echo "Porta 5432 (PostgreSQL):"
nc -z -w1 localhost 5432 2>/dev/null && echo "PostgreSQL está rodando" || echo "PostgreSQL não está rodando"
echo ""

# Verificar Redis (porta 6379)
echo "Porta 6379 (Redis):"
nc -z -w1 localhost 6379 2>/dev/null && echo "Redis está rodando" || echo "Redis não está rodando"
echo ""

# Verificar Grafana (porta 3000)
echo "Porta 3000 (Grafana):"
curl -s -I "http://localhost:3000" 2>/dev/null | head -5 || echo "Não disponível"
echo ""

# Verificar Kibana (porta 5601)
echo "Porta 5601 (Kibana):"
curl -s -I "http://localhost:5601" 2>/dev/null | head -5 || echo "Não disponível"
echo ""

# Verificar Prometheus (porta 9090)
echo "Porta 9090 (Prometheus):"
curl -s -I "http://localhost:9090" 2>/dev/null | head -5 || echo "Não disponível"
echo ""

echo "============================================"
echo "  VARREDURA CONCLUÍDA"
echo "============================================"
