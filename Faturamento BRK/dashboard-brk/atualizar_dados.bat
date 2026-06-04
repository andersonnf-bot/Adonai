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
set DASHBOARD=%~dp0

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
echo  Passo 2/4: Validando e gerando parquet otimizado...
cd /d "%DASHBOARD%"

python -c "
import pandas as pd, sys, glob, os
sys.path.insert(0, r'%DASHBOARD%')
from data.loader import _extract_grupo, _find_sheet

pasta = r'%PASTA_DADOS%'
arquivos = [f for f in glob.glob(os.path.join(pasta, '*.xlsx')) if not os.path.basename(f).startswith('~$')]
if not arquivos:
    print('[ERRO] Nenhum arquivo .xlsx encontrado.')
    sys.exit(1)

arquivo = max(arquivos, key=os.path.getmtime)
print(f'  Lendo: {os.path.basename(arquivo)}')

try:
    xl = pd.ExcelFile(arquivo, engine='openpyxl')
    sheet = _find_sheet(xl)
    df = xl.parse(sheet)

    cols_esperadas = {'Nome', 'Emissao', 'Vlr.Total', 'Serie'}
    faltando = cols_esperadas - set(df.columns)
    if faltando:
        print(f'[ERRO] Colunas nao encontradas: {faltando}')
        sys.exit(1)

    df['Emissao']      = pd.to_datetime(df['Emissao'], errors='coerce')
    df['Nome']         = df['Nome'].str.strip().str.upper()
    df['Descricao']    = df['Descricao'].str.strip().str.upper()
    df['Serie']        = df['Serie'].str.strip().str.upper()
    df['Produto']      = df['Produto'].fillna('SEM_CODIGO').str.strip()
    df['Ano']          = df['Emissao'].dt.year.astype('Int64')
    df['Mes']          = df['Emissao'].dt.month.astype('Int64')
    df['AnoMesStr']    = df['Emissao'].dt.strftime('%Y-%m')
    df['Trimestre']    = df['Emissao'].dt.to_period('Q').astype(str)
    df['Quantidade']   = pd.to_numeric(df['Quantidade'],   errors='coerce').fillna(0).astype('float32')
    df['Vlr.Total']    = pd.to_numeric(df['Vlr.Total'],    errors='coerce').fillna(0).astype('float32')
    df['Vlr.Unitario'] = pd.to_numeric(df['Vlr.Unitario'], errors='coerce').fillna(0).astype('float32')
    df['GrupoEcon']    = df['Nome'].apply(_extract_grupo)

    for col in ['Observacao','Vendedor','Unidade','Loja','Cliente']:
        if col in df.columns:
            df.drop(columns=col, inplace=True)

    for col in ['Nome','GrupoEcon','Descricao','Serie','Produto','AnoMesStr','Trimestre']:
        if col in df.columns:
            df[col] = df[col].astype('category')

    out = os.path.join(r'%DASHBOARD%', 'data', 'faturamento.parquet')
    df.to_parquet(out, index=False)

    print(f'  Registros: {len(df):,}')
    print(f'  Periodo: {df[\"Emissao\"].min().strftime(\"%d/%m/%Y\")} a {df[\"Emissao\"].max().strftime(\"%d/%m/%Y\")}')
    print(f'  Receita total: R$ {df[\"Vlr.Total\"].astype(float).sum():,.0f}')
    print(f'  Grupos de clientes: {df[\"GrupoEcon\"].nunique():,}')
    print('[OK] Parquet gerado com sucesso!')

except Exception as e:
    print(f'[ERRO] {e}')
    sys.exit(1)
" 2>&1

if errorlevel 1 (
    echo.
    echo  [ERRO] Falha na geracao do parquet. Verifique o arquivo e tente novamente.
    pause
    exit /b 1
)

echo.
echo  Passo 3/4: Enviando para o GitHub...
cd /d "%~dp0.."

git add "Faturamento BRK\*.xlsx" 2>nul
git add "*.xlsx" 2>nul
git add "dashboard-brk\data\faturamento.parquet"

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
