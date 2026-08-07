@echo off
REM ============================================
REM SCRIPT PARA PARAR A SANDBOX
REM ============================================

echo ============================================
echo   PARANDO SANDBOX RAVENA
echo ============================================
echo.

REM Perguntar confirmação
set /p confirm="Tem certeza que deseja parar a sandbox? (s/n): "
if not "%confirm%"=="s" (
    echo [INFO] Operação cancelada
    pause
    exit /b 0
)

REM Parar containers
echo [INFO] Parando containers...
docker-compose down

echo.
echo [OK] Sandbox parada com sucesso!
echo.
echo PARA INICIAR NOVAMENTE:
echo   start_sandbox.bat
echo.
echo PARA LIMPAR TODOS OS DADOS:
echo   cleanup.bat
echo.
echo ============================================
pause
