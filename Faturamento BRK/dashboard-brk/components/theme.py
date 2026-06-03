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
        return f'R$ {v/1_000_000:.1f}M'
    if v >= 1_000:
        return f'R$ {v/1_000:.0f}K'
    return f'R$ {v:.0f}'


def fmt_pct(value, decimals=1):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return '—'
    return f'{value:+.{decimals}f}%'


def pct_color(value):
    if value is None:
        return COLORS['text_secondary']
    if value > 0:
        return COLORS['success']
    if value < 0:
        return COLORS['danger']
    return COLORS['text_secondary']


import numpy as np
