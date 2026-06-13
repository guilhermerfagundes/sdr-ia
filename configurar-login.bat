@echo off
REM ============================================================
REM  Define seu usuario e senha de login do painel.
REM  Rode uma vez antes de usar o painel.
REM ============================================================
cd /d "%~dp0"
python tools\set_password.py
echo.
pause
