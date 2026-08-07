#!/bin/bash
# ============================================
# TESTE DE XSS
# Sandbox Ravena
# ============================================

echo "============================================"
echo "  TESTE DE XSS"
echo "============================================"

TARGET="http://localhost:8080"

echo "Alvo: $TARGET/api/auth/login"
echo ""

# Payloads de XSS
PAYLOADS=(
    "<script>alert('XSS')</script>"
    "javascript:alert(1)"
    "<img src=x onerror=alert(1)>"
    "<svg onload=alert(1)>"
)

echo "Testando payloads..."
echo ""

for payload in "${PAYLOADS[@]}"; do
    echo "Payload: $payload"
    curl -s -X POST "$TARGET/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"$payload\", \"password\": \"test\"}" \
        | python3 -m json.tool 2>/dev/null || echo "Resposta não é JSON"
    echo "---"
done

echo ""
echo "Teste concluído!"
