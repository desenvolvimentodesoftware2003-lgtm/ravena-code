#!/bin/bash
# ============================================
# SCRIPT PRINCIPAL - EXECUÇÃO COMPLETA
# ============================================

echo "============================================"
echo "  EXECUÇÃO COMPLETA - SANDBOX RAVENA"
echo "============================================"
echo ""

# Verificar se a sandbox está rodando
echo "[INFO] Verificando se a sandbox está rodando..."
if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "[AVISO] Sandbox não está rodando"
    echo "[INFO] Iniciando sandbox..."
    ./start_sandbox.sh
    sleep 15
fi

echo "[OK] Sandbox está rodando"
echo ""

# Fase 1: Limpeza
echo "[FASE 1] Limpando dados anteriores..."
docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -c "TRUNCATE attack_log CASCADE;"
docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -c "TRUNCATE audit_log CASCADE;"
echo ""

# Fase 2: Executar testes
echo "[FASE 2] Executando testes de segurança..."
python tests/security_tests.py
echo ""

# Fase 3: Gerar relatório
echo "[FASE 3] Gerando relatório..."
python monitoring/generate_report.py
echo ""

# Fase 4: Exibir resumo
echo "============================================"
echo "  EXECUÇÃO CONCLUÍDA"
echo "============================================"
echo ""
echo "PRÓXIMOS PASSOS:"
echo "1. Abra o relatório HTML gerado"
echo "2. Analise os resultados"
echo "3. Implemente as correções necessárias"
echo "4. Re-execute os testes após correções"
echo ""
echo "PARA VISUALIZAR LOGS EM TEMPO REAL:"
echo "  docker-compose logs -f"
echo ""
echo "PARA ACESSAR O BANCO:"
echo "  docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox"
echo ""
echo "PARA PARAR A SANDBOX:"
echo "  docker-compose down"
echo ""
echo "============================================"
