#!/bin/bash
# ============================================
# AUDITORIA DIÁRIA
# Sandbox Ravena
# ============================================

echo "============================================"
echo "  AUDITORIA DIÁRIA"
echo "============================================"

DATE=$(date +%Y%m%d)
REPORT_DIR="audit/daily"
REPORT_FILE="$REPORT_DIR/daily_$DATE.md"

mkdir -p "$REPORT_DIR"

echo "Data: $(date)"
echo ""

# 1. Verificar logs de ataque
echo "1. Verificando logs de ataque..."
if [ -f "/var/log/attack.log" ]; then
    echo "   Total de ataques hoje:"
    grep "$(date +%Y-%m-%d)" /var/log/attack.log 2>/dev/null | wc -l
else
    echo "   Arquivo de log não encontrado"
fi

echo ""

# 2. Verificar tentativas de login
echo "2. Verificando tentativas de login..."
if [ -f "/var/log/auth.log" ]; then
    echo "   Tentativas de login falhas:"
    grep "$(date +%Y-%m-%d)" /var/log/auth.log 2>/dev/null | grep -i "failed\|invalid" | wc -l
else
    echo "   Arquivo de log não encontrado"
fi

echo ""

# 3. Verificar status dos serviços
echo "3. Verificando status dos serviços..."
services=("ravena-app" "ravena-db" "ravena-redis" "nginx")
for service in "${services[@]}"; do
    if command -v docker &> /dev/null; then
        if docker ps | grep -q "$service"; then
            echo "   [OK] $service está rodando"
        else
            echo "   [FALHA] $service não está rodando"
        fi
    else
        echo "   Docker não instalado"
        break
    fi
done

echo ""

# 4. Verificar uso de recursos
echo "4. Verificando uso de recursos..."
if command -v docker &> /dev/null; then
    docker stats --no-stream 2>/dev/null | head -5 || echo "   Não foi possível obter estatísticas"
else
    echo "   Docker não instalado"
fi

echo ""

# 5. Verificar espaço em disco
echo "5. Verificando espaço em disco..."
df -h 2>/dev/null | grep -E "^/|^Filesystem" | head -5

echo ""

# 6. Gerar relatório
echo "6. Gerando relatório..."
cat > "$REPORT_FILE" << EOF
# RELATÓRIO DE AUDITORIA DIÁRIA
**Data:** $(date)
**Responsável:** Sistema Automatizado

## Resumo
- Total de ataques: $(grep "$(date +%Y-%m-%d)" /var/log/attack.log 2>/dev/null | wc -l)
- Tentativas de login falhas: $(grep "$(date +%Y-%m-%d)" /var/log/auth.log 2>/dev/null | grep -i "failed\|invalid" | wc -l)
- Status dos serviços: Verificado

## Detalhes
[Verificar logs para mais detalhes]

## Recomendações
[Nenhuma no momento]

## Conclusão
Status geral: VERIFICAR

---
Relatório gerado automaticamente em $(date)
EOF

echo "   Relatório gerado: $REPORT_FILE"

echo ""
echo "============================================"
echo "  AUDITORIA DIÁRIA CONCLUÍDA"
echo "============================================"
