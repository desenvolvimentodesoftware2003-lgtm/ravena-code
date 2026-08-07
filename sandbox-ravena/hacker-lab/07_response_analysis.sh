#!/bin/bash
# ============================================
# ANÁLISE DE RESPOSTA
# Sandbox Ravena
# ============================================

echo "============================================"
echo "  ANÁLISE DE RESPOSTA"
echo "============================================"

TARGET="http://localhost:8080"

echo "Analisando endpoints..."
echo ""

# Analisar headers de segurança
echo "1. Headers de segurança:"
curl -sI "$TARGET" | grep -i "x-frame-options\|x-content-type\|x-xss-protection\|content-security-policy" || echo "Nenhum header de segurança encontrado"
echo ""

# Analisar endpoint de health
echo "2. Health check:"
curl -s "$TARGET/health" | python3 -m json.tool 2>/dev/null || echo "Endpoint não disponível"
echo ""

# Analisar resposta de erro
echo "3. Resposta de erro (endpoint inexistente):"
curl -s "$TARGET/api/naoexiste" | python3 -m json.tool 2>/dev/null || echo "404 ou outro erro"
echo ""

# Analisar tempo de resposta
echo "4. Tempo de resposta:"
curl -s -o /dev/null -w "Tempo total: %{time_total}s\n" "$TARGET/health" 2>/dev/null || echo "Não foi possível medir"
echo ""

# Analisar endpoints da API
echo "5. Endpoints da API:"
for endpoint in /api/auth/login /api/slots/spin /api/withdrawals/request; do
    echo "  Testing: $endpoint"
    curl -s -I "$TARGET$endpoint" | head -1 || echo "    Não disponível"
done
echo ""

echo "Análise concluída!"
