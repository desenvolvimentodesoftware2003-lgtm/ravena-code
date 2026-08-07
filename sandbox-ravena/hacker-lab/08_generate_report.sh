#!/bin/bash
# ============================================
# GERAR RELATÓRIO DE TESTES
# Sandbox Ravena
# ============================================

echo "============================================"
echo "  GERANDO RELATÓRIO DE TESTES"
echo "============================================"

REPORT_DIR="$HOME/hacker-lab/reports"
REPORT_FILE="$REPORT_DIR/report_$(date +%Y%m%d_%H%M%S).md"

mkdir -p "$REPORT_DIR"

cat > "$REPORT_FILE" << HEADER
# RELATÓRIO DE TESTES DE SEGURANÇA
**Data:** $(date)
**Alvo:** Sandbox Ravena
**Agente:** Hacker Lab

## Resumo
- Portas escaneadas
- Vulnerabilidades testadas
- Resultados coletados

## Testes Realizados

### 1. Varredura de Portas
\`\`\`
$(./01_port_scan.sh 2>/dev/null | head -50)
\`\`\`

### 2. SQL Injection
\`\`\`
$(./02_sql_injection.sh 2>/dev/null | head -50)
\`\`\`

### 3. XSS
\`\`\`
$(./03_xss_test.sh 2>/dev/null | head -50)
\`\`\`

### 4. Brute Force
\`\`\`
$(./04_brute_force.sh 2>/dev/null | head -50)
\`\`\`

### 5. IDOR
\`\`\`
$(./05_idor_test.sh 2>/dev/null | head -50)
\`\`\`

### 6. Path Traversal
\`\`\`
$(./06_path_traversal.sh 2>/dev/null | head -50)
\`\`\`

## Conclusões
[Preencher com base nos resultados]

## Recomendações
[Preencher com base nas vulnerabilidades encontradas]

---
Relatório gerado automaticamente
HEADER

echo "Relatório gerado: $REPORT_FILE"
echo ""
echo "============================================"
echo "  RELATÓRIO CONCLUÍDO"
echo "============================================"
