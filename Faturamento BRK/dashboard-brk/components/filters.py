from dash import html, dcc
from data.loader import get_date_bounds, get_anos, get_all_products

_DROP = {'fontSize': '12px'}


def build_filter_bar():
    min_date, max_date = get_date_bounds()
    anos = get_anos()
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
                    number_of_months_shown=1,
                    day_size=28,
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
                    style={'minWidth': '150px', **_DROP},
                ),
            ], className='filter-group'),

            # ── Cliente — busca livre + limpar ──
            html.Div([
                html.Span('Cliente', className='filter-label'),
                html.Div([
                    dcc.Input(
                        id='filter-cliente',
                        type='text',
                        placeholder='Buscar cliente...',
                        debounce=True,
                        className='filter-text-input',
                    ),
                    html.Button(
                        '✕',
                        id='btn-clear-cliente',
                        n_clicks=0,
                        className='filter-clear-btn',
                        title='Limpar filtro',
                    ),
                ], style={'display': 'flex', 'alignItems': 'center', 'gap': '4px'}),
            ], className='filter-group'),

            # ── Serviço — dropdown multi-select igual ao Ano ──
            html.Div([
                html.Span('Serviço', className='filter-label'),
                dcc.Dropdown(
                    id='filter-produto',
                    options=[{'label': p.title(), 'value': p} for p in produtos],
                    multi=True,
                    searchable=True,
                    clearable=True,
                    placeholder='Todos os serviços...',
                    style={'minWidth': '220px', 'maxWidth': '300px', **_DROP},
                    maxHeight=280,
                    optionHeight=32,
                ),
            ], className='filter-group'),

            # ── Range de Faturamento ──
            html.Div([
                html.Span('Faturamento (R$)', className='filter-label'),
                html.Div([
                    dcc.Input(
                        id='filter-valor-min',
                        type='number',
                        placeholder='Mín',
                        min=0,
                        step=1000,
                        debounce=True,
                        className='filter-valor-input',
                    ),
                    html.Span('—', style={'color': '#475569', 'fontSize': '11px', 'padding': '0 4px'}),
                    dcc.Input(
                        id='filter-valor-max',
                        type='number',
                        placeholder='Máx',
                        min=0,
                        step=1000,
                        debounce=True,
                        className='filter-valor-input',
                    ),
                ], style={'display': 'flex', 'alignItems': 'center', 'gap': '2px'}),
            ], className='filter-group'),
        ],
    )
