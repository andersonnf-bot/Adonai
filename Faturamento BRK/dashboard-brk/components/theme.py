import plotly.graph_objects as go
import plotly.io as pio

COLORS = {
    'bg': '#0B0B0F',
    'surface': '#141418',
    'surface2': '#1A1A22',
    'border': '#222230',
    'primary': '#FF6500',
    'primary_dark': '#CC5200',
    'primary_light': '#FF8533',
    'success': '#22C55E',
    'danger': '#EF4444',
    'warning': '#F59E0B',
    'info': '#06B6D4',
    'purple': '#8B5CF6',
    'text': '#F8FAFC',
    'text_secondary': '#94A3B8',
    'text_muted': '#475569',
}

CHART_COLORS = [
    '#FF6500', '#06B6D4', '#22C55E', '#8B5CF6',
    '#F59E0B', '#EF4444', '#EC4899', '#10B981',
    '#3B82F6', '#F97316', '#14B8A6', '#A855F7',
]

_template = go.layout.Template()
_template.layout = go.Layout(
    paper_bgcolor=COLORS['surface'],
    plot_bgcolor=COLORS['surface'],
    # pt-BR: vírgula decimal, ponto de milhar — vale para eixos e hovers de TODOS os gráficos
    separators=',.',
    font=dict(family='Inter, sans-serif', color=COLORS['text'], size=12),
    colorway=CHART_COLORS,
    title=dict(font=dict(size=14, color=COLORS['text']), x=0.01, xanchor='left'),
    legend=dict(
        bgcolor='rgba(0,0,0,0)',
        bordercolor=COLORS['border'],
        font=dict(color=COLORS['text_secondary'], size=11),
    ),
    xaxis=dict(
        gridcolor=COLORS['border'],
        linecolor=COLORS['border'],
        tickcolor=COLORS['border'],
        tickfont=dict(color=COLORS['text_secondary'], size=11),
        title_font=dict(color=COLORS['text_secondary']),
        zerolinecolor=COLORS['border'],
    ),
    yaxis=dict(
        gridcolor=COLORS['border'],
        linecolor=COLORS['border'],
        tickcolor=COLORS['border'],
        tickfont=dict(color=COLORS['text_secondary'], size=11),
        title_font=dict(color=COLORS['text_secondary']),
        zerolinecolor=COLORS['border'],
        automargin=True,
    ),
    margin=dict(l=75, r=20, t=50, b=40),
    hovermode='x unified',
    hoverlabel=dict(
        bgcolor=COLORS['surface2'],
        bordercolor=COLORS['border'],
        font=dict(color=COLORS['text'], size=12),
        namelength=-1,   # sem truncamento do nome da série
        align='left',
    ),
)

pio.templates['nstech'] = _template
pio.templates.default = 'nstech'


def fmt_brl(value):
    v = float(value)  # garante compatibilidade com numpy float32/float64
    if v >= 1_000_000:
        return f'R$ {v/1_000_000:.1f}M'.replace('.', ',')
    if v >= 1_000:
        return f'R$ {v/1_000:.0f}K'
    return f'R$ {v:.0f}'


def fmt_pct(value, decimals=1):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return '—'
    return f'{value:+.{decimals}f}%'.replace('.', ',')


def pct_color(value):
    if value is None:
        return COLORS['text_secondary']
    if value > 0:
        return COLORS['success']
    if value < 0:
        return COLORS['danger']
    return COLORS['text_secondary']


import numpy as np

# ── Formatos numéricos pt-BR para dash_table ──
# Colunas numéricas (em vez de strings "R$ 1,234") permitem ordenação correta
from dash.dash_table.Format import Format, Group, Scheme, Sign, Symbol

TBL_BRL = Format(
    symbol=Symbol.yes, symbol_prefix='R$ ',
    group=Group.yes, groups=3, group_delimiter='.', decimal_delimiter=',',
    precision=0, scheme=Scheme.fixed,
)
TBL_BRL_2 = Format(
    symbol=Symbol.yes, symbol_prefix='R$ ',
    group=Group.yes, groups=3, group_delimiter='.', decimal_delimiter=',',
    precision=2, scheme=Scheme.fixed,
)
TBL_BRL_SIGNED = Format(
    symbol=Symbol.yes, symbol_prefix='R$ ',
    group=Group.yes, groups=3, group_delimiter='.', decimal_delimiter=',',
    precision=0, scheme=Scheme.fixed, sign=Sign.positive,
)
TBL_PCT = Format(
    symbol=Symbol.yes, symbol_suffix='%',
    decimal_delimiter=',', precision=2, scheme=Scheme.fixed,
)
TBL_PCT_SIGNED = Format(
    symbol=Symbol.yes, symbol_suffix='%',
    decimal_delimiter=',', precision=1, scheme=Scheme.fixed, sign=Sign.positive,
)


def col_num(name, fmt):
    """Coluna numérica de dash_table com formato pt-BR."""
    return {'name': name, 'id': name, 'type': 'numeric', 'format': fmt}
