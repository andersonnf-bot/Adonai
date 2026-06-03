import pandas as pd
import numpy as np
from pathlib import Path
import glob

EXCLUDE_SERIES = {'RET', 'DAV'}

# Palavras genéricas do setor que NÃO identificam uma marca/grupo
_GENERIC_PREFIXES = {
    # ── Setor transporte / logística (palavras genéricas) ──
    'TRANSPORTES', 'TRANSPORTADORA', 'TRANSPORTE', 'TRANS',
    'EXPRESSO', 'RODOVIARIO', 'RODOVIARIOS', 'RODO', 'RODOTRANSPORTE', 'FRETE',
    'LOGISTICA', 'LOG', 'LOGISTIC', 'LOGISTICS',
    'RAPIDO', 'RAPIDOS', 'VELOZ', 'SPEED',
    # ── Cooperativas ──
    'COOPERATIVA', 'COOP',
    # ── Palavras societárias / comerciais genéricas ──
    'EMPRESA', 'EMPRESAS', 'GRUPO', 'GRUPOS', 'HOLDING',
    'COMERCIO', 'COMERCIAL', 'INDUSTRIA', 'INDUSTRIAS',
    'SERVICOS', 'SERVICO', 'SOLUCOES', 'SOLUCAO',
    'COMPANHIA', 'CIA',  # CIA BRASILEIRA DE LITIO != CIA DE MET
    # ── Geográficos genéricos ──
    'BRASIL', 'NACIONAL', 'REGIONAL', 'NORTE', 'SUL', 'LESTE', 'OESTE',
    'NOVA', 'NOVO', 'INTER', 'SUPER', 'MEGA', 'MULTI',
    'SAO', 'SÃO', 'VALE', 'CENTRO', 'CENTRAL',
    # ── Letras isoladas e siglas ambíguas ──
    *[chr(c) for c in range(ord('A'), ord('Z') + 1)],
    # ── Nomes próprios frequentes (MEI / individual) ──
    'ANTONIO', 'JOSE', 'JOAO', 'CARLOS', 'PAULO', 'PEDRO',
    'MARIA', 'LUIZ', 'LUIS', 'ROBERTO', 'FRANCISCO', 'ANDRE',
    'MARCOS', 'MARCIO', 'FABIO', 'DANIEL', 'RAFAEL', 'LUCAS',
    'LEANDRO', 'RODRIGO', 'THIAGO', 'NELSON', 'ANA', 'ALEX',
    'JAIR', 'JAIRO', 'FERNANDO', 'WELLINGTON', 'WILLIAN', 'MILTON',
    # ── Prefixos que geram agrupamentos incorretos ──
    # (empresas diferentes com mesma primeira palavra)
    'SOUZA',        # SOUZA CRUZ (tabaco) != SOUZA BARROS (transportes)
    'TCL',          # TCL SEMP (eletronicos) != TCL TRANSPORTE RODOVIARIO
    'OPEN',         # OPEN TECH (sistemas) != OPEN TRANSPORTES
    'GLOBAL',       # várias empresas GLOBAL sem relação
    'CARGO',        # CARGO MODAL != CARGO POLO
    'COSTA',        # 5 transportadoras diferentes com COSTA
    'RG',           # RG LOG != RG MASTER REPRESENTACOES
    'KM',           # KM CARGO != KM LOCACAO
    'ID',           # ID ARMAZENS != ID DO BRASIL
    'TK',           # TK LOGISTICA != TK TRANSPORTES
    'SILVA',        # nomes de família — empresas diferentes
    'MS',           # sigla ambígua — múltiplas empresas
    'ALL',          # ALL SUCATAS != ALL WASHED
    'VIA',          # 4 empresas diferentes com VIA
    'ALIANCA',      # ALIANCA CONTAINERS != ALIANCA NAVEGACAO != ALIANCA SERVICOS
    'IRMAOS',       # nomes de família — empresas diferentes
    'ECO',          # ECO ARMAZENS != ECO CARGO != ECO RAPIDO
    'PORTAL',       # PORTAL CARGO != PORTAL TRANSPORTES
    'TRUCK',        # TRUCK FENIX != TRUCK X
    'BCR',          # BCR CONTAINERES != BCR TRANSPORTES
    'RM',           # 4 empresas RM diferentes
    'LOGIC',        # LOGIC PHARMA != LOGIC SOLUCOES
    'RF',           # RF LOGISTICA != RF TRANSPORTES
    'GETLAR',       # GETLAR MOVEIS != GETLAR TRANSPORTE
    'CARGOX',       # pode ser mesma marca mas incerto
    'POLI',         # POLI LOGISTICA != POLI TRANSPORTES
    'KAIZEN',       # KAIZEN CARGO != KAIZEN LOGISTICA
    'GN',           # GN LOGISTICA != GN SERVICOS
    'DL',           # DL CARGO != DL LOGISTICA
    'TRES',         # TRES AMERICAS != TRES TRANSPORTES
    'FAST',         # FAST SHOP != FAST FRIOS != FAST SOLUTION
    'CASA',         # CASA CARDAO != CASA DA BOIA != CASA LIMPA
    'MARTINS',      # MARTINS COMERCIO (distribuidor) != MARTINS SILVESTRE
    'ORANGE',       # ORANGE CARGO != ORANGE LOGISTICA
    'AUTO',         # várias AUTO VIACAO sem relação
    'EURO',         # EURO PRUDENTE != EURO TRANSPORTES
    'CONCEITO',     # CONCEITO TRANSPORTES EIRELI != CONCEITO TRANSPORTES LOCACAO
    'DALLA',        # DALLA VALLE != DALLA VECCHIA
    'WINGS',        # WINGS TRANSPORTADORA != WINGS TRANSPORTES BRASIL
    # ── Identificados no double-check ──
    'DIOGO',        # DIOGO ADRIANO != DIOGO BRAMBILA (pessoas diferentes)
    'CS',           # CS NODARI != CS VENCATO
    'TB',           # TB CARGO LOGISTICA != TB TRANSPORTES
    'SANTOS',       # SANTOS GUARUJA != SANTOS TRANS
    'MENDES',       # MENDES E KOCH != MENDES TALENT (RH)
    'JR',           # JR LOG != JR TRANSPORTES
    'FA',           # FA DOS SANTOS != FA REIS
    'COMANDO',      # COMANDO DIESEL != COMANDO LOG
    'MG',           # MG TERRAPLANAGEM != MG TRANSPORTES
    'GW',           # GW CARGO != GW LOGISTICA
    'DAS',          # DAS NEVES != DAS TRANSPORTES
    'SP',           # SP ASSESSORIA != SP SOLUCOES
    'FN',           # FN EXPRESS != FN TRANSPORTE
    'AVANTE',       # AVANTE EXPRESS != AVANTE TRANSPORTES
    'PRIME',        # PRIME BR != PRIME CARGO
    'VIP',          # VIP 128 != VIP TRUCK
    'RS',           # RS LOG != RS TRANSPORTES
    'REIS',         # REIS SILVA != REIS TRANSPORTES
    'MELINSKI',     # MELINSKI & MELINSKI != MELINSKI E ROSSI
    'GHISOLFI',     # GHISOLFI LOGISTICA != GHISOLFI TRANSPORTES
    'PERBONI',      # PERBONI FLV != PERBONI SA (atividades distintas)
    'MARTINI',      # MARTINI MEAT (armazéns) != MARTINI TRANSPORTES
    'SS',           # SS TRANSPORTES LTDA ME != SS TRANSPORTES RIO PRETO
    'HORIZONTE',    # HORIZONTE JR (logística) != HORIZONTE TRANSPORTES
    # ── Identificados no double-check 2 ──
    'TRANSP',       # abreviação genérica: TRANSP ZAPPELLINI != TRANSP TEIXEIRA != TRANSP TOZZO
    'DIRECT',       # DIRECT EXPRESS LOGISTICA != DIRECT TRANSPORTE ARMAZENS (empresas distintas)
    'RIO',          # RIO BRANCO (alimentícios) != RIO EXPRESS (cargas) != RIO LOG EXPRESS
    'ALESSANDRO',   # ALESSANDRO EUSTAQUIO (pessoa) != ALESSANDRO TRANSPORTES (empresa)
    'LUSA',         # LUSA TRANSPORTES E MANUTENCOES != LUSA TRANSPORTES E REPRESENTACOES
    'R&R',          # R&R DIESEL TRANSPORTES != R&R ISA'S TRANSPORTES (donos diferentes)
    # ── Identificados pelo critério do segundo nome ──
    'VIANA',        # VIANA E GRACIERI (sócios) != VIANA E VIANA (sócios diferentes)
    'DDC',          # DDC CORDEIRO (Goianinha) != DDC SERVICOS DE ENTREGA (Mossoró) — 2o nome e cidade distintos
}


# Mapeamento manual: casos onde abreviação vs nome completo representam a mesma empresa
# Ex: "TRANSP TOZZO" e "TRANSPORTES TOZZO" → mesmo grupo
# Chave = nome exato no sistema | Valor = nome canônico do grupo
_MANUAL_GROUPS = {
    # TRANS KOTHE — R$ 2,3M
    'TRANS KOTHE TRANSP RODOVIARIOS SA':         'TRANS KOTHE',
    'TRANS KOTHE TRANSPORTES RODOVIARIOS SA':    'TRANS KOTHE',
    # GLOBAL TRANSP COM — R$ 734K (mesmo empresa, ponto no final)
    'GLOBAL TRANSP COM E REPRESENT LTDA':        'GLOBAL TRANSP COM',
    'GLOBAL TRANSP COM E REPRESENT. LTDA':       'GLOBAL TRANSP COM',
    # TRANSPORTADORA MACEDO RIBEIRAO PRETO — R$ 241K
    'TRANSPORTADORA MACEDO RIBEIRAO PRETO EIRELI': 'TRANSPORTADORA MACEDO RIBEIRAO PRETO',
    'TRANSPORTADORA MACEDO RIBEIRAO PRETO LTDA':   'TRANSPORTADORA MACEDO RIBEIRAO PRETO',
    # J M TRANSPORTES — R$ 217K
    'J M TRANSPORTES E DISTRIBUICAO LTDA - EPP': 'J M TRANSPORTES',
    'J M TRANSPORTES E DISTRIBUICAO LTDA EPP':   'J M TRANSPORTES',
    # TRANSPORTES VALE DO PIQUIRI — R$ 186K
    'TRANSPORTES ROD VALE DO PIQUIRI LTDA':           'TRANSPORTES VALE DO PIQUIRI',
    'TRANSPORTES RODOVIARIOS VALE DO PIQUIRI LTDA':   'TRANSPORTES VALE DO PIQUIRI',
    # TRANSPORTES TOZZO — R$ 175K
    'TRANSP TOZZO LTDA':       'TRANSPORTES TOZZO',
    'TRANSPORTES TOZZO LTDA':  'TRANSPORTES TOZZO',
    # N MINAS TRANSPORTES — R$ 109K
    'N MINAS TRANSPORTES E LOCACOES LTDA':   'N MINAS TRANSPORTES',
    'N. MINAS TRANSPORTES E LOCACOES LTDA.': 'N MINAS TRANSPORTES',
    # CIA CARGAS — R$ 81K
    'CIA CARGAS TRANSPORTES E LOGISTICA EIRELI': 'CIA CARGAS',
    'CIA CARGAS TRANSPORTES E LOGISTICA LTDA':   'CIA CARGAS',
    # CENTRAL LOGISTICA — R$ 65K
    'CENTRAL LOGISTICA E TRANSPORTE':      'CENTRAL LOGISTICA',
    'CENTRAL LOGISTICA E TRANSPORTES LTDA':'CENTRAL LOGISTICA',
    # TRANSPORTES ZAPPELLINI — R$ 61K
    'TRANSP RODOVIARIOS DE CARGA ZAPPELLINI LTDA': 'TRANSPORTES ZAPPELLINI',
    'TRANSPORTE ROD DE CARGAS ZAPPELLINI':          'TRANSPORTES ZAPPELLINI',
    # ALIANCA NAVEGACAO — R$ 55K
    'ALIANCA NAVEGACAO E LOGISTICA LTDA':  'ALIANCA NAVEGACAO',
    'ALIANCA NAVEGACAO LOGISTICA LTDA':    'ALIANCA NAVEGACAO',
    # HORIZONTE TRANSPORTES — R$ 34K
    'HORIZONTE TRANSPORTES EIRELI':        'HORIZONTE TRANSPORTES',
    'HORIZONTE TRANSPORTES EIRELI - EPP':  'HORIZONTE TRANSPORTES',
    # LUCAS ALLA — R$ 31K
    'LUCAS ALLA LOGISTICA EIRELI': 'LUCAS ALLA LOGISTICA',
    'LUCAS ALLA LOGISTICA LTDA':   'LUCAS ALLA LOGISTICA',
    # SAO JOSE ARMAZENS — R$ 19K
    'SAO JOSE ARMAZENS GERAIS & EXPORTACAO DE CAFE LTDA': 'SAO JOSE ARMAZENS GERAIS',
    'SAO JOSE ARMAZENS GERAIS E EXPORTACAO DE CAFE LTDA': 'SAO JOSE ARMAZENS GERAIS',
    # COSTA LESTE — R$ 18K
    'COSTA LESTE TRANSPORTE EIRELI':    'COSTA LESTE TRANSPORTE',
    'COSTA LESTE TRANSPORTE LTDA - ME': 'COSTA LESTE TRANSPORTE',
    # TRANSPORTES RANCHO GRANDE — R$ 18K
    'TRANSPORTADORA RANCHO GRANDE':      'TRANSPORTES RANCHO GRANDE',
    'TRANSPORTADORA RANCHO GRANDE LTDA': 'TRANSPORTES RANCHO GRANDE',
    # FAL FABRICA DE ALIMENTOS — R$ 20K
    'FAL FABRICA DE ALIMENTOS EIRELI':   'FAL FABRICA DE ALIMENTOS',
    'FAL- FABRICA DE ALIMENTOS EIRELI':  'FAL FABRICA DE ALIMENTOS',
    # TRANSPORTES SILVESTRIN — R$ 28K
    'TRANSPORTADORA SILVESTRIN LTDA':    'TRANSPORTES SILVESTRIN',
    'TRANSPORTES SILVESTRIN LTDA ME':    'TRANSPORTES SILVESTRIN',
    # CIA DO TRANSPORTE / CIA TRANSPORTES — R$ 32K
    'CIA DO TRANSPORTE LTDA ME': 'CIA TRANSPORTES',
    'CIA TRANSPORTES LTDA':      'CIA TRANSPORTES',
    # COOPERATIVA TRANSPORTES BENS MARAU — R$ 92K
    'COOPERATIVA DE TRANSPORTES DE BENS DE MARAU':      'COOPERATIVA TRANSPORTES BENS MARAU',
    'COOPERATIVA DE TRANSPORTES DE BENS DE MARAU LTDA': 'COOPERATIVA TRANSPORTES BENS MARAU',
}


def _extract_grupo(nome: str) -> str:
    """
    Retorna o nome do grupo econômico do cliente.
    1. Verifica mapeamento manual (casos de abreviação vs nome completo)
    2. Usa a primeira palavra como grupo quando identifica uma marca real.
    3. Palavras genéricas do setor retornam o nome completo (sem agrupamento).
    """
    if not nome or not isinstance(nome, str):
        return nome or ''
    nome_upper = nome.strip().upper()
    # 1. Mapeamento manual tem prioridade (abreviação vs nome completo)
    if nome_upper in _MANUAL_GROUPS:
        return _MANUAL_GROUPS[nome_upper]
    words = nome_upper.split()
    if not words:
        return nome
    first = words[0].rstrip('.')
    if first in _GENERIC_PREFIXES:
        return nome_upper  # mantém nome completo, sem agrupamento
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
