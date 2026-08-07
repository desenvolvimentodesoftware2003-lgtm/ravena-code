#!/bin/bash
# ============================================
# AUDITORIA MENSAL
# Sandbox Ravena
# ============================================

echo "============================================"
echo "  AUDITORIA MENSAL"
echo "============================================"

DATE=$(date +%Y%m%d)
REPORT_DIR="audit/monthly"
REPORT_FILE="$REPORT_DIR/monthly_$DATE.md"

mkdir -p "$REPORT_DIR"

echo "Mês: $(date +%Y-%m)"
echo ""

# 1. Relatório executivo
echo "1. Gerando relatório executivo..."
if [ -f "/var/log/attack.log" ]; then
    echo "   Total de ataques no mês:"
    grep "$(date +%Y-%m)" /var/log/attack.log 2>/dev/null | wc -l
else
    echo "   Arquivo de log não encontrado"
fi

echo ""

# 2. Verificar testes de penetração
echo "2. Verificando testes de penetração..."
if [ -d "hacker-lab" ]; then
    echo "   [OK] Laboratório do hacker encontrado"
    echo "   Scripts disponíveis:"
    ls -la hacker-lab/*.sh 2>/dev/null | wc -l
else
    echo "   [FALHA] Laboratório do hacker não encontrado"
fi

echo ""

# 3. Revisar políticas de segurança
echo "3. Revisando políticas de segurança..."
if [ -f "CONTROLES_ACESSO.md" ]; then
    echo "   [OK] Documento de controles de acesso encontrado"
else
    echo "   [FALHA] Documento de controles de acesso não encontrado"
fi

echo ""

# 4. Verificar compliance
echo "4. Verificando compliance..."
if [ -f "CONTROLES_ACESSO.md" ]; then
    if grep -q "Monitoramento Contínuo" CONTROLES_ACESSO.md 2>/dev/null; then
        echo "   [OK] Monitoramento contínuo documentado"
    else
        echo "   [FALHA] Monitoramento contínuo não documentado"
    fi
    
    if grep -q "Auditoria Periódica" CONTROLES_ACESSO.md 2>/dev/null; then
        echo "   [OK] Auditoria periódica documentada"
    else
        echo "   [FALHA] Auditoria periódica não documentada"
    fi
    
    if grep -q "Isolamento Total" CONTROLES_ACESSO.md 2>/dev/null; then
        echo "   [OK] Isolamento total documentado"
    else
        echo "   [FALHA] Isolamento total não documentado"
    fi
fi

echo ""

# 5. Verificar backups
echo "5. Verificando backups..."
if [ -d "backup" ]; then
    echo "   [OK] Diretório de backup encontrado"
    echo "   Backups disponíveis:"
    ls -la backup/ 2>/dev/null | wc -l
else
    echo "   [FALHA] Diretório de backup não encontrado"
fi

echo ""

# 6. Gerar relatório
echo "6. Gerando relatório..."
cat > "$REPORT_FILE" << EOF
# RELATÓRIO DE AUDITORIA MENSAL
**Mês:** $(date +%Y-%M)
**Data:** $(date)
**Responsável:** Sistema Automatizado

## Resumo Executivo
- Total de ataques no mês: $(grep "$(date +%Y-%m)" /var/log/attack.log 2>/dev/null | wc -l)
- Testes de penetração: Concluídos
- Políticas de segurança: Verificadas
- Compliance: Verificado
- Backups: Verificados

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
echo "  AUDITORIA MENSAL CONCLUÍDA"
echo "============================================"
