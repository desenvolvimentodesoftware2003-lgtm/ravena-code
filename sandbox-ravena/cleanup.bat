@echo off
REM ============================================
REM SCRIPT PARA LIMPAR A SANDBOX
REM ============================================

echo ============================================
echo   LIMPANDO SANDBOX RAVENA
echo ============================================
echo.

REM Perguntar confirmação
set /p confirm="Tem certeza que deseja limpar todos os dados? (s/n): "
if not "%confirm%"=="s" (
    echo [INFO] Operação cancelada
    pause
    exit /b 0
)

REM Parar e remover containers
echo [INFO] Parando e removendo containers...
docker-compose down -v

REM Remover dados
echo [INFO] Removendo dados persistidos...
if exist "data\postgres" rmdir /s /q data\postgres
if exist "data\elasticsearch" rmdir /s /q data\elasticsearch
if exist "logs" rmdir /s /q logs

echo.
echo [OK] Limpeza concluída!
echo.
echo PARA REINICIAR A SANDBOX:
echo   start_sandbox.bat
echo.
echo ============================================
pause
