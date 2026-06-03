@echo off
chcp 65001 >nul
title BRK Analytics - Atualizacao de Dados
color 0A

echo.
echo  ============================================
echo   BRK Analytics - Atualizacao Mensal
echo  ============================================
echo.

REM ── Verifica se o Python está disponível
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python nao encontrado. Instale o Python primeiro.
    pause
    exit /b 1
)

REM ── Caminho da pasta de dados (pasta pai do dashboard)
set PASTA_DADOS=%~dp0..

echo  Passo 1/4: Verificando novo arquivo de dados...
echo.

REM ── Procura o arquivo xlsx mais recente na pasta pai
set NOVO_ARQUIVO=
for /f "delims=" %%f in ('dir /b /od "%PASTA_DADOS%\*.xlsx" 2^>nul') do set NOVO_ARQUIVO=%%f

if "%NOVO_ARQUIVO%"=="" (
    echo  [AVISO] Nenhum arquivo .xlsx encontrado em:
    echo  %PASTA_DADOS%
    echo.
    echo  Coloque o novo arquivo de faturamento na pasta:
    echo  %PASTA_DADOS%
    echo.
    pause
    exit /b 1
)

echo  Arquivo encontrado: %NOVO_ARQUIVO%
echo.
echo  Este arquivo sera usado para atualizar o dashboard.
echo  Deseja continuar? (S/N)
set /p CONFIRMA=  Resposta:

if /i not "%CONFIRMA%"=="S" (
    echo.
    echo  Operacao cancelada.
    pause
    exit /b 0
)

echo.
echo  Passo 2/4: Validando estrutura do arquivo...
cd /d "%~dp0"

python -c "
import pandas as pd
import sys
import glob
import os

pasta = os.path.join(os.path.dirname(os.path.abspath('.')), '')
arquivos = glob.glob(os.path.join(r'%PASTA_DADOS%', '*.xlsx'))
if not arquivos:
    print('[ERRO] Nenhum arquivo .xlsx encontrado.')
    sys.exit(1)

arquivo = max(arquivos, key=os.path.getmtime)
print(f'  Lendo: {os.path.basename(arquivo)}')

try:
    xl = pd.ExcelFile(arquivo)
    abas = xl.sheet_names
    print(f'  Abas encontradas: {abas}')

    aba_nf = [a for a in abas if 'Itens' in a or 'NF' in a or 'Notas' in a]
    if not aba_nf:
        print('[AVISO] Aba de NFs nao identificada automaticamente.')
        print(f'Abas disponiveis: {abas}')
        sys.exit(1)

    df = pd.read_excel(arquivo, sheet_name=aba_nf[0], nrows=5)
    cols_esperadas = {'Cliente', 'Nome', 'Emissao', 'Vlr.Total', 'Serie'}
    cols_encontradas = set(df.columns)
    faltando = cols_esperadas - cols_encontradas
    if faltando:
        print(f'[AVISO] Colunas nao encontradas: {faltando}')
        print(f'Colunas do arquivo: {list(df.columns)}')
        sys.exit(1)

    df_full = pd.read_excel(arquivo, sheet_name=aba_nf[0])
    print(f'  Registros: {len(df_full):,}')
    print(f'  Periodo: {pd.to_datetime(df_full[\"Emissao\"], errors=\"coerce\").min().strftime(\"%d/%m/%Y\")} a {pd.to_datetime(df_full[\"Emissao\"], errors=\"coerce\").max().strftime(\"%d/%m/%Y\")}')
    print(f'  Receita total: R$ {pd.to_numeric(df_full[\"Vlr.Total\"], errors=\"coerce\").sum():,.0f}')
    print('[OK] Arquivo validado com sucesso!')
except Exception as e:
    print(f'[ERRO] {e}')
    sys.exit(1)
" 2>&1

if errorlevel 1 (
    echo.
    echo  [ERRO] Falha na validacao. Verifique o arquivo e tente novamente.
    pause
    exit /b 1
)

echo.
echo  Passo 3/4: Enviando para o GitHub...
cd /d "%~dp0.."

git add "Faturamento BRK\*.xlsx" 2>nul
git add "*.xlsx" 2>nul

for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set dt=%%a
set MES=%dt:~4,2%
set ANO=%dt:~0,4%

git commit -m "dados: atualiza faturamento %MES%/%ANO%"

if errorlevel 1 (
    echo.
    echo  [AVISO] Nenhuma alteracao detectada ou erro no commit.
    echo  O arquivo pode ja estar atualizado.
) else (
    git push origin main
    if errorlevel 1 (
        echo  [ERRO] Falha ao enviar para o GitHub.
        echo  Verifique sua conexao e permissoes.
        pause
        exit /b 1
    )
    echo  [OK] Dados enviados para o GitHub!
)

echo.
echo  Passo 4/4: Concluido!
echo.
echo  ============================================
echo   Dashboard atualizado com sucesso!
echo   Em 2-3 minutos o link estara atualizado.
echo  ============================================
echo.
pause
