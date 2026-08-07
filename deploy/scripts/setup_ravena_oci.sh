#!/bin/bash

# =========================================================================
# SCRIPT DE CONFIGURAÇÃO — RAVENA AI v1.0.2-beta (OCI DEPLOY)
# =========================================================================
# Autor: Ravena AI Team | Atualizado: Junho 2026
# Este script automatiza a preparação do servidor Oracle Cloud para a Ravena.
# Uso: ssh na instância OCI e executar: bash setup_ravena_oci.sh
# =========================================================================

set -e  # Parar em caso de erro

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  RAVENA AI v1.0.2-beta — Setup Oracle Cloud (OCI)       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 1. Atualização do Sistema
echo "[1/8] Atualizando pacotes do sistema..."
sudo apt-get update -y && sudo apt-get upgrade -y

# 2. Instalação do Python 3.11+ e ferramentas
echo "[2/8] Instalando Python 3.11, pip e ferramentas essenciais..."
sudo apt-get install -y python3 python3-pip python3-venv git docker.io docker-compose curl wget

# 3. Habilitar Docker
echo "[3/8] Configurando Docker..."
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# 4. Clonar repositório do GitHub
echo "[4/8] Clonando repositório Ravena AIM do GitHub..."
if [ ! -d ~/ravena-aim ]; then
    git clone https://github.com/desenvolvimentodesoftware2003-lgtm/ravena-aim.git ~/ravena-aim
else
    echo "  → Repositório já existe. Atualizando..."
    cd ~/ravena-aim && git pull origin main
fi

# 5. Criar ambiente virtual e instalar dependências
echo "[5/8] Instalando dependências Python..."
cd ~/ravena-aim
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 6. Preparação do arquivo .env
echo "[6/8] Preparando configuração de secrets..."
if [ ! -f ~/ravena-aim/.env ]; then
    cp ~/ravena-aim/.env.example ~/ravena-aim/.env
    echo "  → Arquivo .env criado a partir do template."
    echo "  ⚠️  IMPORTANTE: Edite ~/ravena-aim/.env com suas chaves reais!"
else
    echo "  → Arquivo .env já existe. Mantendo configuração atual."
fi

# 7. Configurar OCI CLI
echo "[7/8] Verificando OCI CLI..."
if ! command -v oci &> /dev/null; then
    echo "  → Instalando OCI CLI..."
    bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)" -- --accept-all-defaults
    echo "  → OCI CLI instalada. Execute 'oci setup config' para configurar."
else
    echo "  → OCI CLI já instalada."
fi

# 8. Criar estrutura de dados persistentes
echo "[8/8] Criando diretórios de dados persistentes..."
mkdir -p ~/ravena-aim/data/{chroma,logs,models,backups}
chmod -R 755 ~/ravena-aim/data

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ SETUP CONCLUÍDO COM SUCESSO                         ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║  Próximos passos:                                        ║"
echo "║                                                          ║"
echo "║  1. Configure OCI CLI:                                   ║"
echo "║     $ oci setup config                                   ║"
echo "║                                                          ║"
echo "║  2. Edite o .env com suas chaves reais:                  ║"
echo "║     $ nano ~/ravena-aim/.env                             ║"
echo "║                                                          ║"
echo "║  3. Suba o sistema com Docker:                           ║"
echo "║     $ cd ~/ravena-aim && docker-compose -f               ║"
echo "║       docker/docker-compose.yml up -d                    ║"
echo "║                                                          ║"
echo "║  4. Verifique o health check:                            ║"
echo "║     $ python3 tests/health_check.py                      ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
