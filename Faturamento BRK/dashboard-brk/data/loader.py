import pandas as pd
import numpy as np
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent.parent / 'faturamento_2023_24_25_26.xlsx'
SHEET = '2-Itens das Notas Fiscais de '
EXCLUDE_SERIES = {'RET', 'DAV'}

_cache = {}


def load_data():
    if 'raw' in _cache:
        return _cache['raw'], _cache['liquid']

    df = pd.read_excel(DATA_PATH, sheet_name=SHEET, engine='openpyxl')

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

    df_raw = df.copy()
    df_liquid = df[~df['Serie'].isin(EXCLUDE_SERIES)].copy()

    _cache['raw'] = df_raw
    _cache['liquid'] = df_liquid
    return df_raw, df_liquid


def get_liquid():
    _, df = load_data()
    return df


def apply_filters(df, date_start=None, date_end=None, anos=None, cliente=None, produto=None):
    mask = pd.Series(True, index=df.index)
    if date_start:
        mask &= df['Emissao'] >= pd.to_datetime(date_start)
    if date_end:
        mask &= df['Emissao'] <= pd.to_datetime(date_end)
    if anos:
        mask &= df['Ano'].isin([int(a) for a in anos])
    if cliente:
        mask &= df['Nome'].str.contains(cliente.upper(), na=False)
    if produto:
        mask &= df['Descricao'].str.contains(produto.upper(), na=False)
    return df[mask]


def get_date_bounds():
    df = get_liquid()
    return df['Emissao'].min(), df['Emissao'].max()


def get_all_clients():
    df = get_liquid()
    return sorted(df['Nome'].dropna().unique().tolist())


def get_all_products():
    df = get_liquid()
    return sorted(df['Descricao'].dropna().unique().tolist())


def get_anos():
    df = get_liquid()
    return sorted(df['Ano'].dropna().unique().astype(int).tolist())
