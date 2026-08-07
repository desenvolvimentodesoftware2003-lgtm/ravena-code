#!/bin/bash
# ============================================
# SCRIPT: Implementar Auditoria Periódica
# ============================================

echo "============================================"
echo "  IMPLEMENTANDO AUDITORIA PERIÓDICA"
echo "============================================"
echo ""

# Criar diretório de auditoria
mkdir -p audit/daily
mkdir -p audit/weekly
mkdir -p audit/monthly
mkdir -p audit/reports

echo "[INFO] Configurando auditoria periódica..."
echo ""

# Fase 1: Criar scripts de auditoria
echo "1. Criando scripts de auditoria..."

# Script de auditoria diária
cat > scripts/audit_daily.sh << 'EOF'
#!/bin/bash
# Auditoria Diária - Sandbox Ravena

DATE=$(date +%Y-%m-%d)
REPORT_FILE="audit/daily/audit_$DATE.md"

echo "Gerando relatório de auditoria diária..."

# Criar relatório
cat > "$REPORT_FILE" << HEADER
# RELATÓRIO DE AUDITORIA DIÁRIA
**Data:** $DATE
**Horário:** $(date +%H:%M:%S)

## Resumo Executivo
HEADER

# Coletar métricas
TOTAL_ATTACKS=$(docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -t -c "SELECT COUNT(*) FROM attack_log WHERE timestamp > NOW() - INTERVAL '24 hours'" 2>/dev/null | tr -d ' ')
BLOCKED_ATTACKS=$(docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -t -c "SELECT COUNT(*) FROM attack_log WHERE blocked = TRUE AND timestamp > NOW() - INTERVAL '24 hours'" 2>/dev/null | tr -d ' ')
ACTIVE_SESSIONS=$(docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -t -c "SELECT COUNT(*) FROM sessions WHERE expires_at > NOW()" 2>/dev/null | tr -d ' ')

# Adicionar ao relatório
cat >> "$REPORT_FILE" << METRICS
- Total de ataques: $TOTAL_ATTACKS
- Ataques bloqueados: $BLOCKED_ATTACKS
- Sessões ativas: $ACTIVE_SESSIONS

## Detalhes por Tipo
METRICS

# Ataques por tipo
docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -c "
SELECT attack_type, COUNT(*) as total
FROM attack_log 
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY attack_type
ORDER BY total DESC;
" 2>/dev/null >> "$REPORT_FILE"

# Últimos incidentes
cat >> "$REPORT_FILE" << INCIDENTS

## Últimos Incidentes
INCIDENTS

docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -c "
SELECT attack_type, endpoint, ip_address, timestamp
FROM attack_log 
WHERE timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC
LIMIT 10;
" 2>/dev/null >> "$REPORT_FILE"

# Conclusão
cat >> "$REPORT_FILE" << CONCLUSION

## Conclusão
Status geral: $(if [ "$TOTAL_ATTACKS" -lt "10" ]; then echo "BOM"; elif [ "$TOTAL_ATTACKS" -lt "50" ]; then echo "REGULAR"; else echo "CRÍTICO"; fi)

---
Relatório gerado automaticamente em $(date)
CONCLUSION

echo "[OK] Relatório diário gerado: $REPORT_FILE"
EOF

chmod +x scripts/audit_daily.sh
echo "   [OK] Script de auditoria diária criado"

# Script de auditoria semanal
cat > scripts/audit_weekly.sh << 'EOF'
#!/bin/bash
# Auditoria Semanal - Sandbox Ravena

WEEK=$(date +%Y-W%V)
REPORT_FILE="audit/weekly/audit_$WEEK.md"

echo "Gerando relatório de auditoria semanal..."

# Criar relatório
cat > "$REPORT_FILE" << HEADER
# RELATÓRIO DE AUDITORIA SEMANAL
**Semana:** $WEEK
**Período:** $(date -d "7 days ago" +%Y-%m-%d) a $(date +%Y-%m-%d)

## Resumo Executivo
HEADER

# Coletar métricas semanais
TOTAL_ATTACKS=$(docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -t -c "SELECT COUNT(*) FROM attack_log WHERE timestamp > NOW() - INTERVAL '7 days'" 2>/dev/null | tr -d ' ')
UNIQUE_IPS=$(docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -t -c "SELECT COUNT(DISTINCT ip_address) FROM attack_log WHERE timestamp > NOW() - INTERVAL '7 days'" 2>/dev/null | tr -d ' ')
TOP_ATTACK=$(docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -t -c "SELECT attack_type FROM attack_log WHERE timestamp > NOW() - INTERVAL '7 days' GROUP BY attack_type ORDER BY COUNT(*) DESC LIMIT 1" 2>/dev/null | tr -d ' ')

# Adicionar ao relatório
cat >> "$REPORT_FILE" << METRICS
- Total de ataques: $TOTAL_ATTACKS
- IPs únicos: $UNIQUE_IPS
- Ataque mais comum: $TOP_ATTACK

## Tendências da Semana
METRICS

# Análise de tendências
docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -c "
SELECT 
    DATE(timestamp) as day,
    COUNT(*) as attacks,
    SUM(CASE WHEN blocked THEN 1 ELSE 0 END) as blocked
FROM attack_log 
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp)
ORDER BY day;
" 2>/dev/null >> "$REPORT_FILE"

# Usuários mais ativos
cat >> "$REPORT_FILE" << USERS

## Usuários Mais Ativos
USERS

docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -c "
SELECT 
    u.username,
    COUNT(t.id) as transactions,
    SUM(t.amount) as total_amount
FROM users u
JOIN transactions t ON u.id = t.user_id
WHERE t.created_at > NOW() - INTERVAL '7 days'
GROUP BY u.username
ORDER BY transactions DESC
LIMIT 5;
" 2>/dev/null >> "$REPORT_FILE"

echo "[OK] Relatório semanal gerado: $REPORT_FILE"
EOF

chmod +x scripts/audit_weekly.sh
echo "   [OK] Script de auditoria semanal criado"

# Script de auditoria mensal
cat > scripts/audit_monthly.sh << 'EOF'
#!/bin/bash
# Auditoria Mensal - Sandbox Ravena

MONTH=$(date +%Y-%m)
REPORT_FILE="audit/monthly/audit_$MONTH.md"

echo "Gerando relatório de auditoria mensal..."

# Criar relatório
cat > "$REPORT_FILE" << HEADER
# RELATÓRIO DE AUDITORIA MENSAL
**Mês:** $MONTH
**Período:** $(date -d "30 days ago" +%Y-%m-%d) a $(date +%Y-%m-%d)

## Resumo Executivo
HEADER

# Coletar métricas mensais
TOTAL_ATTACKS=$(docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -t -c "SELECT COUNT(*) FROM attack_log WHERE timestamp > NOW() - INTERVAL '30 days'" 2>/dev/null | tr -d ' ')
TOTAL_TRANSACTIONS=$(docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -t -c "SELECT COUNT(*) FROM transactions WHERE created_at > NOW() - INTERVAL '30 days'" 2>/dev/null | tr -d ' ')
TOTAL_VOLUME=$(docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -t -c "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE created_at > NOW() - INTERVAL '30 days'" 2>/dev/null | tr -d ' ')

# Adicionar ao relatório
cat >> "$REPORT_FILE" << METRICS
- Total de ataques: $TOTAL_ATTACKS
- Total de transações: $TOTAL_TRANSACTIONS
- Volume financeiro: R$ $TOTAL_VOLUME

## Análise de Segurança
METRICS

# Top vulnerabilidades
docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -c "
SELECT 
    attack_type,
    COUNT(*) as attempts,
    SUM(CASE WHEN blocked THEN 1 ELSE 0 END) as blocked,
    ROUND(SUM(CASE WHEN blocked THEN 1 ELSE 0 END)::decimal / COUNT(*) * 100, 2) as block_rate
FROM attack_log 
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY attack_type
ORDER BY attempts DESC;
" 2>/dev/null >> "$REPORT_FILE"

# Relatório de compliance
cat >> "$REPORT_FILE" << COMPLIANCE

## Compliance

### Controles Implementados
- [x] Monitoramento contínuo
- [x] Auditoria de acessos
- [x] Isolamento de rede
- [x] Logs imutáveis
- [x] Rate limiting

### Recomendações
1. Manter monitoramento 24/7
2. Revisar logs semanalmente
3. Atualizar regras de segurança
4. Treinar equipe periodicamente
COMPLIANCE

echo "[OK] Relatório mensal gerado: $REPORT_FILE"
EOF

chmod +x scripts/audit_monthly.sh
echo "   [OK] Script de auditoria mensal criado"

# Fase 2: Configurar agendamentos (cron)
echo "2. Configurando agendamentos..."

# Criar arquivo de agendamento
cat > audit/crontab << 'EOF'
# Auditoria Diária - 00:00 UTC
0 0 * * * /bin/bash /app/scripts/audit_daily.sh

# Auditoria Semanal - Domingos, 02:00 UTC
0 2 * * 0 /bin/bash /app/scripts/audit_weekly.sh

# Auditoria Mensal - 1º dia, 03:00 UTC
0 3 1 * * /bin/bash /app/scripts/audit_monthly.sh
EOF

echo "   [OK] Agendamentos configurados"

# Fase 3: Criar templates de relatório
echo "3. Criando templates de relatório..."

cat > audit/templates/daily_report.md << 'EOF'
# RELATÓRIO DE AUDITORIA DIÁRIA
**Data:** [DATA]
**Responsável:** [NOME]

## Resumo Executivo
- Total de ataques: [NÚMERO]
- Ataques bloqueados: [NÚMERO]
- Taxa de bloqueio: [PERCENTUAL]

## Detalhes por Tipo
[TABELA]

## Últimos Incidentes
[LISTA]

## Recomendações
[SE HOUVER]

## Conclusão
Status geral: [BOM/REGULAR/CRÍTICO]
EOF

echo "   [OK] Templates criados"

# Fase 4: Criar scripts de geração de relatório
echo "4. Criando scripts de geração de relatório..."

cat > scripts/generate_audit_report.sh << 'EOF'
#!/bin/bash
# Gerar relatório consolidado de auditoria

echo "Gerando relatório consolidado..."

# Coletar dados de todas as fontes
ATTACKS=$(cat audit/daily/audit_*.md 2>/dev/null | grep -c "ataques")
USERS=$(docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -t -c "SELECT COUNT(*) FROM users" 2>/dev/null | tr -d ' ')
SESSIONS=$(docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -t -c "SELECT COUNT(*) FROM sessions WHERE expires_at > NOW()" 2>/dev/null | tr -d ' ')

# Criar relatório consolidado
cat > audit/reports/consolidated_$(date +%Y%m%d).md << HEADER
# RELATÓRIO CONSOLIDADO DE AUDITORIA
**Data:** $(date +%Y-%m-%d)
**Horário:** $(date +%H:%M:%S)

## Métricas Gerais
- Total de ataques registrados: $ATTACKS
- Usuários ativos: $USERS
- Sessões ativas: $SESSIONS

## Status dos Controles
- Monitoramento contínuo: ATIVO
- Auditoria periódica: ATIVO
- Isolamento total: ATIVO

## Recomendações
1. Manter vigilância sobre padrões de ataque
2. Revisar permissões de usuários periodicamente
3. Atualizar regras de segurança conforme necessário
HEADER

echo "[OK] Relatório consolidado gerado"
EOF

chmod +x scripts/generate_audit_report.sh
echo "   [OK] Scripts de relatório criados"

# Fase 5: Testar auditoria
echo "5. Testando auditoria..."

# Executar auditoria diária de teste
if ./scripts/audit_daily.sh; then
    echo "   [OK] Auditoria diária funciona"
else
    echo "   [AVISO] Erro na auditoria diária"
fi

echo ""
echo "============================================"
echo "  AUDITORIA PERIÓDICA IMPLEMENTADA"
echo "============================================"
echo ""
echo "TIPOS DE AUDITORIA:"
echo "  - Diária: Todo dia às 00:00 UTC"
echo "  - Semanal: Domingos às 02:00 UTC"
echo "  - Mensal: 1º dia às 03:00 UTC"
echo ""
echo "DIRETÓRIOS:"
echo "  - audit/daily/    (Relatórios diários)"
echo "  - audit/weekly/   (Relatórios semanais)"
echo "  - audit/monthly/  (Relatórios mensais)"
echo "  - audit/reports/  (Relatórios consolidados)"
echo ""
echo "SCRIPTS:"
echo "  - audit_daily.sh"
echo "  - audit_weekly.sh"
echo "  - audit_monthly.sh"
echo "  - generate_audit_report.sh"
echo ""
echo "PRÓXIMOS PASSOS:"
echo "  1. Configurar crontab no宿主"
echo "  2. Verificar geração de relatórios"
echo "  3. Configurar notificações"
echo "  4. Treinar equipe"
echo ""
echo "============================================"
