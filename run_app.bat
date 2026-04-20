@echo off
echo ====================================================
echo      INICIANDO GESTÃO AGRO CAFÉ (PAULO)
echo ====================================================

:: Verifica se o ambiente virtual existe
if not exist venv (
    echo [!] Ambiente virtual 'venv' não encontrado.
    echo [!] Criando ambiente virtual...
    python -m venv venv
)

:: Ativa o ambiente virtual
echo [+] Ativando ambiente virtual...
call venv\Scripts\activate

:: Atualiza as dependências
echo [+] Verificando dependências (isso pode levar alguns segundos)...
pip install -r requirements.txt --quiet

:: Inicia o servidor Flask
echo [+] Iniciando o servidor...
echo [+] O sistema estará disponível em: http://127.0.0.1:5000
echo.
python app.py

:: Mantém a janela aberta caso o servidor pare
echo.
echo [!] O servidor parou.
pause
