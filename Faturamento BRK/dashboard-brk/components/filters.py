from dash import html, dcc
from data.loader import get_date_bounds, get_anos, get_all_clients, get_all_products

_DROPDOWN_STYLE = {
    'minWidth': '200px',
    'maxWidth': '280px',
    'fontSize': '12px',
}

_DROPDOWN_DARK = {
    'backgroundColor': '#1A1A22',
    'color': '#F8FAFC',
}


def build_filter_bar():
    min_date, max_date = get_date_bounds()
    anos = get_anos()
    clientes = get_all_clients()
    produtos = get_all_products()

    return html.Div(
        id='filter-bar',
        children=[
            html.Span('Filtros:', className='filter-label'),

            # ── Período ──
            html.Div([
                html.Span('Período', className='filter-label'),
                dcc.DatePickerRange(
                    id='filter-date',
                    start_date=min_date.date(),
                    end_date=max_date.date(),
                    min_date_allowed=min_date.date(),
                    max_date_allowed=max_date.date(),
                    display_format='DD/MM/YYYY',
                    calendar_orientation='horizontal',
                    number_of_months_shown=1,
                    day_size=28,
                    with_portal=False,
                    style={'fontSize': '11px'},
                ),
            ], className='filter-group'),

            # ── Ano ──
            html.Div([
                html.Span('Ano', className='filter-label'),
                dcc.Dropdown(
                    id='filter-ano',
                    options=[{'label': str(a), 'value': a} for a in anos],
                    multi=True,
                    placeholder='Todos',
                    style={'minWidth': '150px', 'fontSize': '12px'},
                ),
            ], className='filter-group'),

            # ── Cliente (multi-select, pesquisável, com limpar) ──
            html.Div([
                html.Span('Cliente', className='filter-label'),
                dcc.Dropdown(
                    id='filter-cliente',
                    options=[{'label': c, 'value': c} for c in clientes],
                    multi=True,
                    searchable=True,
                    clearable=True,
                    placeholder='Todos os clientes...',
                    style=_DROPDOWN_STYLE,
                    maxHeight=300,
                    optionHeight=32,
                ),
            ], className='filter-group'),

            # ── Serviço (multi-select, pesquisável, com limpar) ──
            html.Div([
                html.Span('Serviço', className='filter-label'),
                dcc.Dropdown(
                    id='filter-produto',
                    options=[{'label': p, 'value': p} for p in produtos],
                    multi=True,
                    searchable=True,
                    clearable=True,
                    placeholder='Todos os serviços...',
                    style=_DROPDOWN_STYLE,
                    maxHeight=300,
                    optionHeight=32,
                ),
            ], className='filter-group'),

            # ── Série ──
            html.Div([
                html.Span('Série', className='filter-label'),
                dcc.Dropdown(
                    id='filter-serie',
                    options=[
                        {'label': 'Todas', 'value': 'ALL'},
                        {'label': 'RPS',   'value': 'RPS'},
                        {'label': 'Série 1','value': '1'},
                    ],
                    value='ALL',
                    clearable=False,
                    style={'minWidth': '100px', 'fontSize': '12px'},
                ),
            ], className='filter-group'),
        ],
    )
