@echo off
REM ============================================================
REM  Instala tudo o que o SDR IA precisa (uma vez só).
REM  Dê DUPLO CLIQUE neste arquivo após instalar o Python.
REM ============================================================
cd /d "%~dp0"

echo Verificando o Python...
python --version
if errorlevel 1 (
    echo.
    echo [ERRO] Python nao encontrado. Instale em https://www.python.org/downloads/
    echo Marque a opcao "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

echo.
echo Instalando as dependencias (pode demorar alguns minutos)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Pronto! Agora voce pode abrir o painel com run-dashboard.bat
pause
