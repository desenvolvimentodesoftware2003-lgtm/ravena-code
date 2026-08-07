@echo off
REM ============================================
REM SCRIPT PARA INICIAR A SANDBOX
REM ============================================

echo ============================================
echo   INICIANDO SANDBOX RAVENA
echo ============================================
echo.

REM Verificar se está no diretório correto
if not exist "docker-compose.yml" (
    echo [ERRO] Execute este script no diretório sandbox-ravena
    pause
    exit /b 1
)

REM Iniciar containers
echo [INFO] Iniciando containers Docker...
docker-compose up -d

echo.
echo [OK] Sandbox iniciada com sucesso!
echo.
echo SERVIÇOS DISPONÍVEIS:
echo - Servidor Ravena: http://localhost:8080
echo - Grafana: http://localhost:3000
echo - Kibana: http://localhost:5601
echo.
echo CREDENCIAIS:
echo - Aplicação: attacker_001 / test123
echo - Grafana: admin / sandbox_monitor_123
echo.
echo ============================================
pause
