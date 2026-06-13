@echo off
REM ============================================================
REM  Abre o painel do SDR IA no navegador.
REM  Basta dar DUPLO CLIQUE neste arquivo.
REM ============================================================
cd /d "%~dp0"

echo Iniciando o painel do SDR IA...
echo (Deixe esta janela preta aberta enquanto usar o painel.)
echo.

python -m streamlit run dashboard\app.py

echo.
echo O painel foi encerrado. Pode fechar esta janela.
pause
