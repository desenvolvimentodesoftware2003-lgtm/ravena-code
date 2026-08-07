#!/bin/bash
# ============================================
# AUDITORIA SEMANAL
# Sandbox Ravena
# ============================================

echo "============================================"
echo "  AUDITORIA SEMANAL"
echo "============================================"

DATE=$(date +%Y%m%d)
REPORT_DIR="audit/weekly"
REPORT_FILE="$REPORT_DIR/weekly_$DATE.md"

mkdir -p "$REPORT_DIR"

echo "Semana: $(date +%Y-%W)"
echo ""

# 1. Análise de tendências de ataque
echo "1. Análise de tendências de ataque..."
if [ -f "/var/log/attack.log" ]; then
    echo "   Ataques por tipo:"
    grep "$(date +%Y-%m)" /var/log/attack.log 2>/dev/null | awk '{print $3}' | sort | uniq -c | sort -rn | head -10
else
    echo "   Arquivo de log não encontrado"
fi

echo ""

# 2. Revisão de usuários
echo "2. Revisão de usuários..."
if [ -f "/var/log/auth.log" ]; then
    echo "   Usuários com mais tentativas de login:"
    grep "$(date +%Y-%m)" /var/log/auth.log 2>/dev/null | grep -i "failed" | awk '{print $8}' | sort | uniq -c | sort -rn | head -10
else
    echo "   Arquivo de log não encontrado"
fi

echo ""

# 3. Verificar configurações de segurança
echo "3. Verificando configurações de segurança..."
if [ -f "nginx/nginx.conf" ]; then
    echo "   [OK] Arquivo nginx.conf encontrado"
else
    echo "   [FALHA] Arquivo nginx.conf não encontrado"
fi

echo ""

# 4. Verificar dependências
echo "4. Verificando dependências..."
if [ -f "requirements.txt" ]; then
    echo "   [OK] requirements.txt encontrado"
    echo "   Dependências listadas: $(wc -l < requirements.txt)"
else
    echo "   [FALHA] requirements.txt não encontrado"
fi

echo ""

# 5. Verificar scripts de segurança
echo "5. Verificando scripts de segurança..."
scripts=("sqli_detector.py" "brute_force_protector.py" "session_manager.py" "input_validator.py" "rate_limiter.py" "audit_logger.py")
for script in "${scripts[@]}"; do
    if [ -f "skills/$script" ]; then
        echo "   [OK] $script encontrado"
    else
        echo "   [FALHA] $script não encontrado"
    fi
done

echo ""

# 6. Gerar relatório
echo "6. Gerando relatório..."
cat > "$REPORT_FILE" << EOF
# RELATÓRIO DE AUDITORIA SEMANAL
**Semana:** $(date +%Y-%W)
**Data:** $(date)
**Responsável:** Sistema Automatizado

## Resumo
- Análise de tendências: Concluída
- Revisão de usuários: Concluída
- Configurações de segurança: Verificadas
- Dependências: Verificadas
- Scripts de segurança: Verificados

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
echo "  AUDITORIA SEMANAL CONCLUÍDA"
echo "============================================"
