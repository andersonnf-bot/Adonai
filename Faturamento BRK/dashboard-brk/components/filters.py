from dash import html, dcc
from data.loader import get_date_bounds, get_anos


def build_filter_bar():
    min_date, max_date = get_date_bounds()
    anos = get_anos()

    return html.Div(
        id='filter-bar',
        children=[
            html.Span('Filtros:', className='filter-label'),

            html.Div([
                html.Span('Período', className='filter-label'),
                dcc.DatePickerRange(
                    id='filter-date',
                    start_date=min_date.date(),
                    end_date=max_date.date(),
                    min_date_allowed=min_date.date(),
                    max_date_allowed=max_date.date(),
                    display_format='DD/MM/YYYY',
                    style={'fontSize': '12px'},
                ),
            ], className='filter-group'),

            html.Div([
                html.Span('Ano', className='filter-label'),
                dcc.Dropdown(
                    id='filter-ano',
                    options=[{'label': str(a), 'value': a} for a in anos],
                    multi=True,
                    placeholder='Todos',
                    style={'minWidth': '160px', 'fontSize': '12px'},
                    className='dash-dropdown-dark',
                ),
            ], className='filter-group'),

            html.Div([
                html.Span('Cliente', className='filter-label'),
                dcc.Input(
                    id='filter-cliente',
                    type='text',
                    placeholder='Buscar cliente...',
                    debounce=True,
                    style={
                        'background': '#1A1A22',
                        'border': '1px solid #222230',
                        'color': '#F8FAFC',
                        'borderRadius': '6px',
                        'padding': '6px 10px',
                        'fontSize': '12px',
                        'width': '180px',
                    },
                ),
            ], className='filter-group'),

            html.Div([
                html.Span('Serviço', className='filter-label'),
                dcc.Input(
                    id='filter-produto',
                    type='text',
                    placeholder='Buscar serviço...',
                    debounce=True,
                    style={
                        'background': '#1A1A22',
                        'border': '1px solid #222230',
                        'color': '#F8FAFC',
                        'borderRadius': '6px',
                        'padding': '6px 10px',
                        'fontSize': '12px',
                        'width': '180px',
                    },
                ),
            ], className='filter-group'),

            html.Div([
                html.Span('Série', className='filter-label'),
                dcc.Dropdown(
                    id='filter-serie',
                    options=[
                        {'label': 'RPS', 'value': 'RPS'},
                        {'label': 'Série 1', 'value': '1'},
                        {'label': 'Todas', 'value': 'ALL'},
                    ],
                    value='ALL',
                    clearable=False,
                    style={'minWidth': '100px', 'fontSize': '12px'},
                ),
            ], className='filter-group'),
        ],
    )
