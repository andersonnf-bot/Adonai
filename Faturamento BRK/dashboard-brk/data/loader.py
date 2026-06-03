import pandas as pd
import numpy as np
from pathlib import Path
import glob

EXCLUDE_SERIES = {'RET', 'DAV'}

# Palavras genéricas do setor que NÃO identificam uma marca/grupo
_GENERIC_PREFIXES = {
    # Transporte / logística
    'TRANSPORTES', 'TRANSPORTADORA', 'TRANSPORTE', 'TRANS',
    'EXPRESSO', 'EXPRESSO.', 'RODOVIARIO', 'RODOVIARIOS',
    'RODO', 'RODOTRANSPORTE', 'FRETE',
    'LOGISTICA', 'LOG', 'LOGISTIC', 'LOGISTICS',
    'RAPIDO', 'RAPIDOS', 'VELOZ', 'SPEED',
    # Cooperativas genéricas
    'COOPERATIVA', 'COOP',
    # Palavras societárias / comerciais
    'EMPRESA', 'EMPRESAS', 'GRUPO', 'GRUPOS', 'HOLDING',
    'COMERCIO', 'COMERCIAL', 'INDUSTRIA', 'INDUSTRIAS',
    'SERVICOS', 'SERVICO', 'SOLUCOES', 'SOLUCAO',
    # Geográficos genéricos
    'BRASIL', 'NACIONAL', 'REGIONAL', 'NORTE', 'SUL', 'LESTE', 'OESTE',
    'NOVA', 'NOVO', 'INTER', 'SUPER', 'MEGA', 'MULTI',
    # Letras isoladas e siglas comuns de iniciação
    *[chr(c) for c in range(ord('A'), ord('Z') + 1)],
    # Nomes próprios frequentes de MEI/individual
    'ANTONIO', 'JOSE', 'JOAO', 'CARLOS', 'PAULO', 'PEDRO',
    'MARIA', 'LUIZ', 'LUIS', 'ROBERTO', 'FRANCISCO', 'ANDRE',
    'MARCOS', 'MARCIO', 'FABIO', 'DANIEL', 'RAFAEL', 'LUCAS',
    'FAST',  # FAST SHOP != FAST FRIOS != FAST SOLUTION
}


def _extract_grupo(nome: str) -> str:
    """
    Retorna o nome do grupo econômico do cliente.
    Usa a primeira palavra como grupo quando ela identifica uma marca real.
    Palavras genéricas do setor retornam o nome completo (sem agrupamento).
    """
    if not nome or not isinstance(nome, str):
        return nome or ''
    words = nome.strip().upper().split()
    if not words:
        return nome
    first = words[0].rstrip('.')
    if first in _GENERIC_PREFIXES:
        return nome  # mantém nome completo, sem agrupamento
    return first  # usa primeira palavra como grupo (ex: UNILEVER, AMAZON, KLABIN)

def _find_data_file():
    # Busca em ordem de prioridade: pasta data/ local, pasta pai (local Windows), raiz do projeto
    search_paths = [
        Path(__file__).parent,           # dashboard-brk/data/  (cloud / Render)
        Path(__file__).parent.parent.parent,  # Faturamento BRK/     (Windows local)
        Path(__file__).parent.parent,    # dashboard-brk/       (fallback)
    ]
    for base in search_paths:
        xlsx_files = [
            f for f in base.glob('*.xlsx')
            if not f.name.startswith('~$')
        ]
        if xlsx_files:
            return max(xlsx_files, key=lambda f: f.stat().st_mtime)
    raise FileNotFoundError('Nenhum arquivo .xlsx encontrado. Verifique a pasta de dados.')

def _find_sheet(xl):
    for name in xl.sheet_names:
        if any(k in name for k in ['Itens', 'NF', 'Notas', 'Fatura']):
            return name
    return xl.sheet_names[0]

_cache = {}


def load_data():
    if 'raw' in _cache:
        return _cache['raw'], _cache['liquid']

    data_path = _find_data_file()
    xl = pd.ExcelFile(data_path, engine='openpyxl')
    sheet = _find_sheet(xl)
    df = xl.parse(sheet)

    df['Emissao'] = pd.to_datetime(df['Emissao'], errors='coerce')
    df['Nome'] = df['Nome'].str.strip().str.upper()
    df['Descricao'] = df['Descricao'].str.strip().str.upper()
    df['Serie'] = df['Serie'].str.strip().str.upper()
    df['Produto'] = df['Produto'].fillna('SEM_CODIGO').str.strip()
    df['Cliente'] = df['Cliente'].fillna('').str.strip()

    df['Ano'] = df['Emissao'].dt.year.astype('Int64')
    df['Mes'] = df['Emissao'].dt.month.astype('Int64')
    df['AnoMesStr'] = df['Emissao'].dt.strftime('%Y-%m')
    df['Trimestre'] = df['Emissao'].dt.to_period('Q').astype(str)
    df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
    df['Vlr.Total'] = pd.to_numeric(df['Vlr.Total'], errors='coerce').fillna(0)
    df['Vlr.Unitario'] = pd.to_numeric(df['Vlr.Unitario'], errors='coerce').fillna(0)

    # Grupo econômico: agrupa entidades da mesma marca (ex: todas as Unilever)
    df['GrupoEcon'] = df['Nome'].apply(_extract_grupo)

    df_raw = df.copy()
    df_liquid = df[~df['Serie'].isin(EXCLUDE_SERIES)].copy()

    _cache['raw'] = df_raw
    _cache['liquid'] = df_liquid
    return df_raw, df_liquid


def get_liquid():
    _, df = load_data()
    return df


def _parse_valor(v):
    """Converte string formatada em pt-BR (ex: '1.500.000') para float."""
    if v is None or str(v).strip() == '':
        return None
    if isinstance(v, (int, float)):
        return float(v)
    # Remove R$, espaços, pontos de milhar; troca vírgula decimal por ponto
    cleaned = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def apply_filters(df, date_start=None, date_end=None, anos=None,
                  cliente=None, produto=None, valor_min=None, valor_max=None):
    mask = pd.Series(True, index=df.index)

    if date_start:
        mask &= df['Emissao'] >= pd.to_datetime(date_start)
    if date_end:
        mask &= df['Emissao'] <= pd.to_datetime(date_end)
    if anos:
        mask &= df['Ano'].isin([int(a) for a in anos])

    # cliente: filtra por GrupoEcon (agrupa entidades da mesma marca)
    if cliente:
        if isinstance(cliente, list) and len(cliente) > 0:
            mask &= df['GrupoEcon'].isin(cliente)
        elif isinstance(cliente, str) and cliente.strip():
            mask &= df['GrupoEcon'].str.contains(cliente.strip().upper(), na=False)

    # produto: lista multi-select (vazia = todos)
    if produto:
        if isinstance(produto, list) and len(produto) > 0:
            mask &= df['Descricao'].isin(produto)
        elif isinstance(produto, str) and produto.strip():
            mask &= df['Descricao'].str.contains(produto.strip().upper(), na=False)

    # range de faturamento por cliente total (filtra clientes pelo total acumulado)
    vmin = _parse_valor(valor_min)
    vmax = _parse_valor(valor_max)
    if vmin is not None or vmax is not None:
        client_totals = df[mask].groupby('Nome')['Vlr.Total'].sum()
        if vmin is not None and vmin > 0:
            client_totals = client_totals[client_totals >= vmin]
        if vmax is not None and vmax > 0:
            client_totals = client_totals[client_totals <= vmax]
        mask &= df['Nome'].isin(client_totals.index)

    return df[mask]


def get_date_bounds():
    df = get_liquid()
    return df['Emissao'].min(), df['Emissao'].max()


def get_all_clients():
    """Retorna grupos econômicos únicos para o filtro (ex: UNILEVER em vez de 4 entidades)."""
    df = get_liquid()
    return sorted(df['GrupoEcon'].dropna().unique().tolist())


def get_all_products():
    df = get_liquid()
    return sorted(df['Descricao'].dropna().unique().tolist())


def get_anos():
    df = get_liquid()
    return sorted(df['Ano'].dropna().unique().astype(int).tolist())
