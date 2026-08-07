#!/bin/bash
# ============================================
# INSTALAÇÃO COMPLETA - SANDBOX RAVENA
# ============================================
# Este script instala e configura toda a sandbox
# de uma vez, incluindo dependências, Docker e
# todos os componentes de segurança.
# ============================================

echo "============================================"
echo "  INSTALAÇÃO COMPLETA - SANDBOX RAVENA"
echo "============================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funções auxiliares
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[AVISO]${NC} $1"; }
log_error() { echo -e "${RED}[ERRO]${NC} $1"; }

# Verificar se está rodando como root (Linux) ou admin (Windows)
check_permissions() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ "$EUID" -ne 0 ]; then
            log_warn "Execute como root: sudo ./install_all.sh"
        fi
    fi
}

# ============================================
# 1. INSTALAR DEPENDÊNCIAS DO SISTEMA
# ============================================

install_system_deps() {
    log_info "1. Instalando dependências do sistema..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux (Ubuntu/Debian)
        apt-get update
        apt-get install -y curl wget git python3 python3-pip docker.io docker-compose
        
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows (Git Bash/MSYS2)
        log_info "Windows detectado - verificando ferramentas..."
        
        # Verificar Docker
        if command -v docker &> /dev/null; then
            log_ok "Docker encontrado"
        else
            log_warn "Docker não encontrado - instale manualmente"
            log_info "Baixe: https://docs.docker.com/desktop/install/windows-install/"
        fi
        
        # Verificar Python
        if command -v python3 &> /dev/null; then
            log_ok "Python3 encontrado"
        else
            log_warn "Python3 não encontrado"
        fi
        
        # Verificar pip
        if command -v pip3 &> /dev/null; then
            log_ok "pip3 encontrado"
        else
            log_warn "pip3 não encontrado"
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew update
        brew install python3 docker docker-compose
    fi
    
    log_ok "Dependências do sistema instaladas"
}

# ============================================
# 2. INSTALAR DEPENDÊNCIAS PYTHON
# ============================================

install_python_deps() {
    log_info "2. Instalando dependências Python..."
    
    # Verificar se pip está disponível
    if command -v pip3 &> /dev/null; then
        pip3 install -r requirements.txt
        log_ok "Dependências Python instaladas"
    elif command -v pip &> /dev/null; then
        pip install -r requirements.txt
        log_ok "Dependências Python instaladas"
    else
        log_warn "pip não encontrado - instale manualmente"
    fi
}

# ============================================
# 3. CONFIGURAR DOCKER
# ============================================

setup_docker() {
    log_info "3. Configurando Docker..."
    
    if command -v docker &> /dev/null; then
        # Verificar se Docker está rodando
        if docker info &> /dev/null; then
            log_ok "Docker está rodando"
        else
            log_warn "Docker não está rodando - tentando iniciar..."
            if [[ "$OSTYPE" == "linux-gnu"* ]]; then
                systemctl start docker
            elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
                log_info "Inicie o Docker Desktop manualmente"
            fi
        fi
        
        # Verificar docker-compose
        if command -v docker-compose &> /dev/null; then
            log_ok "docker-compose encontrado"
        else
            log_warn "docker-compose não encontrado"
        fi
    else
        log_warn "Docker não encontrado"
    fi
}

# ============================================
# 4. CRIAR ESTRUTURA DE DIRETÓRIOS
# ============================================

create_directories() {
    log_info "4. Criando estrutura de diretórios..."
    
    # Diretórios principais
    mkdir -p hacker-lab/{scans,logs,reports,tools}
    mkdir -p scripts
    mkdir -p skills
    mkdir -p monitoring/{prometheus,grafana,alerts}
    mkdir -p config
    mkdir -p nginx
    mkdir -p init-scripts
    mkdir -p audit/{daily,weekly,monthly,reports,templates}
    mkdir -p logs
    
    log_ok "Estrutura de diretórios criada"
}

# ============================================
# 5. CONFIGURAR PERMISSÕES
# ============================================

setup_permissions() {
    log_info "5. Configurando permissões..."
    
    # Tornar scripts executáveis
    chmod +x *.sh 2>/dev/null || true
    chmod +x hacker-lab/*.sh 2>/dev/null || true
    chmod +x scripts/*.sh 2>/dev/null || true
    
    log_ok "Permissões configuradas"
}

# ============================================
# 6. VALIDAR DOCKER-COMPOSE
# ============================================

validate_docker_compose() {
    log_info "6. Validando docker-compose.yml..."
    
    if command -v docker-compose &> /dev/null; then
        if docker-compose config > /dev/null 2>&1; then
            log_ok "docker-compose.yml é válido"
        else
            log_error "docker-compose.yml tem erros"
        fi
    elif command -v docker &> /dev/null; then
        if docker compose config > /dev/null 2>&1; then
            log_ok "docker-compose.yml é válido"
        else
            log_error "docker-compose.yml tem erros"
        fi
    else
        log_warn "Não foi possível validar docker-compose.yml"
    fi
}

# ============================================
# 7. INICIAR SANDBOX
# ============================================

start_sandbox() {
    log_info "7. Iniciando sandbox..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
        log_ok "Sandbox iniciada com docker-compose"
    elif command -v docker &> /dev/null; then
        docker compose up -d
        log_ok "Sandbox iniciada com docker compose"
    else
        log_warn "Docker não disponível - sandbox não iniciada"
    fi
}

# ============================================
# 8. AGUARDAR SERVIÇOS
# ============================================

wait_services() {
    log_info "8. Aguardando serviços inicializarem..."
    
    # Aguardar 30 segundos para serviços iniciarem
    for i in {1..30}; do
        echo -ne "\rAguardando... $i/30"
        sleep 1
    done
    echo ""
    
    log_ok "Serviços inicializados"
}

# ============================================
# 9. VERIFICAR SERVIÇOS
# ============================================

check_services() {
    log_info "9. Verificando serviços..."
    
    # Verificar se app.py está respondendo
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        log_ok "App está respondendo na porta 8080"
    else
        log_warn "App não está respondendo na porta 8080"
    fi
    
    # Verificar PostgreSQL
    if command -v docker &> /dev/null; then
        if docker ps | grep -q "ravena-db"; then
            log_ok "PostgreSQL está rodando"
        else
            log_warn "PostgreSQL não está rodando"
        fi
    fi
    
    # Verificar Redis
    if command -v docker &> /dev/null; then
        if docker ps | grep -q "ravena-redis"; then
            log_ok "Redis está rodando"
        else
            log_warn "Redis não está rodando"
        fi
    fi
}

# ============================================
# 10. EXECUTAR VALIDAÇÃO
# ============================================

run_validation() {
    log_info "10. Executando validação final..."
    
    if [ -f "validate_system.sh" ]; then
        bash validate_system.sh
    else
        log_warn "Script de validação não encontrado"
    fi
}

# ============================================
# PRINCIPAL
# ============================================

main() {
    echo ""
    log_info "Iniciando instalação completa da Sandbox Ravena..."
    echo ""
    
    check_permissions
    install_system_deps
    install_python_deps
    setup_docker
    create_directories
    setup_permissions
    validate_docker_compose
    start_sandbox
    wait_services
    check_services
    run_validation
    
    echo ""
    echo "============================================"
    echo -e "${GREEN}  INSTALAÇÃO CONCLUÍDA${NC}"
    echo "============================================"
    echo ""
    echo "PRÓXIMOS PASSOS:"
    echo "1. Acesse http://localhost:8080"
    echo "2. Navegue até ~/hacker-lab para testes"
    echo "3. Execute ./validate_system.sh para verificar"
    echo ""
    echo "COMANDOS ÚTEIS:"
    echo "  docker-compose ps          # Ver containers"
    echo "  docker-compose logs -f     # Ver logs"
    echo "  docker-compose down        # Parar sandbox"
    echo "  cd ~/hacker-lab            # Laboratório"
    echo ""
}

# Executar principal
main
