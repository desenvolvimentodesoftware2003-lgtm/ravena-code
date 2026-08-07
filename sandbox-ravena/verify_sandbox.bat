@echo off
REM ============================================
REM SCRIPT PARA VERIFICAR A SANDBOX
REM ============================================

echo ============================================
echo   VERIFICANDO SANDBOX RAVENA
echo ============================================
echo.

REM Verificar containers
echo 1. Verificando containers...
echo ----------------------------------------

docker ps --format "table {{.Names}}\t{{.Status}}" | findstr "ravena"
if errorlevel 1 (
    echo [ERRO] Nenhum container encontrado
) else (
    echo.
)

REM Verificar serviços
echo 2. Verificando serviços...
echo ----------------------------------------

REM Verificar servidor
curl -s http://localhost:8080/health >nul 2>&1
if not errorlevel 1 (
    echo [OK] Servidor Ravena: http://localhost:8080
) else (
    echo [ERRO] Servidor Ravena não está respondendo
)

REM Verificar Grafana
curl -s http://localhost:3000/api/health >nul 2>&1
if not errorlevel 1 (
    echo [OK] Grafana: http://localhost:3000
) else (
    echo [ERRO] Grafana não está respondendo
)

REM Verificar Kibana
curl -s http://localhost:5601/api/status >nul 2>&1
if not errorlevel 1 (
    echo [OK] Kibana: http://localhost:5601
) else (
    echo [ERRO] Kibana não está respondendo
)

REM Verificar Prometheus
curl -s http://localhost:9090/-/healthy >nul 2>&1
if not errorlevel 1 (
    echo [OK] Prometheus: http://localhost:9090
) else (
    echo [ERRO] Prometheus não está respondendo
)

REM Verificar Elasticsearch
curl -s http://localhost:9200/_cluster/health >nul 2>&1
if not errorlevel 1 (
    echo [OK] Elasticsearch: http://localhost:9200
) else (
    echo [ERRO] Elasticsearch não está respondendo
)

echo.

REM Verificar banco de dados
echo 3. Verificando banco de dados...
echo ----------------------------------------

docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -c "SELECT 1;" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Banco de dados conectado
) else (
    echo [ERRO] Falha na conexão com banco
)

echo.

REM Resumo
echo ============================================
echo   RESUMO DA VERIFICAÇÃO
echo ============================================
echo.
echo SERVIÇOS:
echo - Servidor Ravena: http://localhost:8080
echo - Grafana: http://localhost:3000
echo - Kibana: http://localhost:5601
echo - Prometheus: http://localhost:9090
echo - Elasticsearch: http://localhost:9200
echo.
echo CREDENCIAIS:
echo - Aplicação: attacker_001 / test123
echo - Grafana: admin / sandbox_monitor_123
echo - Banco: ravena_test / sandbox_password_123
echo.
echo PARA EXECUTAR TESTES:
echo   python tests\security_tests.py
echo.
echo PARA GERAR RELATÓRIO:
echo   python monitoring\generate_report.py
echo.
echo ============================================
pause
