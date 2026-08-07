#!/bin/bash
# ============================================
# SCRIPT PARA PARAR A SANDBOX
# ============================================

echo "============================================"
echo "  PARANDO SANDBOX RAVENA"
echo "============================================"
echo ""

# Perguntar confirmação
read -p "Tem certeza que deseja parar a sandbox? (s/n): " confirm
if [ "$confirm" != "s" ]; then
    echo "[INFO] Operação cancelada"
    exit 0
fi

echo "[INFO] Parando containers..."
docker-compose down

echo "[OK] Sandbox parada com sucesso!"
echo ""
echo "PARA INICIAR NOVAMENTE:"
echo "  ./start_sandbox.sh"
echo ""
echo "PARA LIMPAR TODOS OS DADOS:"
echo "  ./cleanup.sh"
echo ""
echo "============================================"
