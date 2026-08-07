#!/bin/bash
# ============================================
# SCRIPT DE LIMPEZA - SANDBOX RAVENA
# ============================================

echo "============================================"
echo "  LIMPANDO SANDBOX RAVENA"
echo "============================================"
echo ""

# Perguntar confirmação
read -p "Tem certeza que deseja limpar todos os dados? (s/n): " confirm
if [ "$confirm" != "s" ]; then
    echo "[INFO] Operação cancelada"
    exit 0
fi

echo "[INFO] Parando containers..."
docker-compose down -v

echo "[INFO] Removendo dados persistidos..."
rm -rf data/postgres/*
rm -rf data/elasticsearch/*
rm -rf logs/*

echo "[INFO] Limpeza concluída!"
echo ""
echo "Para reiniciar a sandbox:"
echo "  ./start_sandbox.sh"
