#!/bin/bash
# ============================================
# AUTO_START.SH - Inicialização Automática
# Archiso - Arch Linux Customizado
# ============================================
# Este script é executado automaticamente
# no boot para iniciar a Ravena.
# ============================================

# Aguardar sistema inicializar
sleep 10

# Verificar se a Ravena está instalada
if [ -d "/opt/ravena" ]; then
    echo "Iniciando Ravena Security Sandbox..."
    
    # Iniciar serviços
    /opt/ravena/scripts/start_ravena.sh
    
    # Mostrar IP
    IP=$(hostname -I | awk '{print $1}')
    echo ""
    echo "============================================"
    echo "  RAVENA INICIADA"
    echo "============================================"
    echo ""
    echo "URL: http://${IP:-localhost}:8080"
    echo ""
    echo "============================================"
fi
