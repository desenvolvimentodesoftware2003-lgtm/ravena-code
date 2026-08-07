@echo off
REM ============================================
REM CONFIGURAÇÃO AUTOMÁTICA - SANDBOX RAVENA
REM ============================================

echo ============================================
echo   CONFIGURAÇÃO AUTOMÁTICA
echo   Sandbox Ravena
echo ============================================
echo.

REM Verificar se está no diretório correto
if not exist "docker-compose.yml" (
    echo [ERRO] Execute este script no diretório sandbox-ravena
    pause
    exit /b 1
)

REM Fase 1: Verificar pré-requisitos
echo [FASE 1] Verificando pré-requisitos...
echo ----------------------------------------

REM Verificar Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Docker não está instalado
    echo [INFO] Instale Docker: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM Verificar Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Docker Compose não está instalado
    echo [INFO] Instale Docker Compose: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python não está instalado
    echo [INFO] Instale Python: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Todos os pré-requisitos estão instalados
echo.

REM Fase 2: Instalar dependências Python
echo [FASE 2] Instalando dependências Python...
echo ----------------------------------------

pip install -r requirements.txt
pip install psycopg2-binary jinja2 requests

echo [OK] Dependências instaladas
echo.

REM Fase 3: Criar diretórios
echo [FASE 3] Criando estrutura de diretórios...
echo ----------------------------------------

if not exist "logs\nginx" mkdir logs\nginx
if not exist "logs\redis" mkdir logs\redis
if not exist "logs\postgres" mkdir logs\postgres
if not exist "data\postgres" mkdir data\postgres
if not exist "data\elasticsearch" mkdir data\elasticsearch
if not exist "monitoring\grafana" mkdir monitoring\grafana

echo [OK] Diretórios criados
echo.

REM Fase 4: Copiar variáveis de ambiente
echo [FASE 4] Configurando variáveis de ambiente...
echo ----------------------------------------

if not exist ".env" (
    copy .env.example .env
    echo [OK] Arquivo .env criado
) else (
    echo [INFO] Arquivo .env já existe
)

echo.

REM Fase 5: Iniciar containers
echo [FASE 5] Iniciando containers Docker...
echo ----------------------------------------

docker-compose up -d

echo [OK] Containers iniciados
echo.

REM Fase 6: Aguardar inicialização
echo [FASE 6] Aguardando serviços inicializarem...
echo ----------------------------------------

echo Aguardando 30 segundos para inicialização completa...
timeout /t 30 /nobreak >nul

echo Verificando se o servidor está respondendo...
set /a counter=0
:check_server
curl -s http://localhost:8080/health | findstr "healthy" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Servidor Ravena está saudável
    goto server_ok
)
set /a counter+=1
if %counter% GEQ 30 (
    echo [ERRO] Servidor não respondeu após 60 segundos
    goto server_ok
)
echo [INFO] Aguardando servidor... (%counter%/30)
timeout /t 2 /nobreak >nul
goto check_server

:server_ok
echo.

REM Fase 7: Executar testes básicos
echo [FASE 7] Executando testes básicos...
echo ----------------------------------------

REM Verificar se o servidor está rodando
curl -s http://localhost:8080/health >nul 2>&1
if not errorlevel 1 (
    echo [OK] Servidor respondendo
) else (
    echo [ERRO] Servidor não está respondendo
)

REM Verificar banco de dados
docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -c "SELECT 1;" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Banco de dados conectado
) else (
    echo [ERRO] Falha na conexão com banco
)

echo.

REM Fase 8: Gerar relatório inicial
echo [FASE 8] Gerando relatório inicial...
echo ----------------------------------------

python monitoring\generate_report.py

echo.

REM Resumo final
echo ============================================
echo   CONFIGURAÇÃO CONCLUÍDA
echo ============================================
echo.
echo SANDBOX RAVENA ESTÁ PRONTA!
echo.
echo PRÓXIMOS PASSOS:
echo 1. Acesse a aplicação: http://localhost:8080
echo 2. Execute os testes: python tests\security_tests.py
echo 3. Acesse o Grafana: http://localhost:3000
echo 4. Acesse o Kibana: http://localhost:5601
echo.
echo COMANDOS ÚTEIS:
echo - Verificar sandbox: verify_sandbox.bat
echo - Parar sandbox: stop_sandbox.bat
echo - Limpar dados: cleanup.bat
echo.
echo CREDENCIAIS:
echo - Aplicação: attacker_001 / test123
echo - Grafana: admin / sandbox_monitor_123
echo - Banco: ravena_test / sandbox_password_123
echo.
echo ============================================
pause
