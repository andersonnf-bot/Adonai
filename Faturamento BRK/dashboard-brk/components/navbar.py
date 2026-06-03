from dash import html, dcc


PAGES = [
    {'path': '/',            'label': 'Visão Executiva',  'icon': '📊'},
    {'path': '/clientes',    'label': 'Clientes',          'icon': '🏢'},
    {'path': '/produtos',    'label': 'Produtos & Serviços','icon': '📦'},
    {'path': '/tendencias',  'label': 'Tendências',         'icon': '📈'},
]


def build_navbar(pathname='/'):
    links = []
    for page in PAGES:
        is_active = pathname == page['path']
        links.append(
            dcc.Link(
                [
                    html.Span(page['icon'], className='nav-icon'),
                    html.Span(page['label']),
                ],
                href=page['path'],
                className='nav-link active' if is_active else 'nav-link',
                refresh=False,
            )
        )

    return html.Div(
        id='sidebar',
        children=[
            html.Div(
                [
                    html.Div('Nstech', className='sidebar-nstech-label'),
                    html.Div(
                        [
                            html.Span('BRK', className='sidebar-brk-title'),
                            html.Span('Tecnologia', className='sidebar-brk-sub'),
                        ],
                        className='sidebar-brk-row',
                    ),
                    html.Div('Faturamento Analytics', className='sidebar-logo-sub'),
                ],
                className='sidebar-logo',
            ),
            html.Div(
                [
                    html.Div('Módulos', className='sidebar-section-label'),
                    *links,
                ],
                className='sidebar-nav',
            ),
            html.Div(
                [
                    html.Div('Nstech Group', style={'fontWeight': '600', 'color': '#64748B', 'fontSize': '11px'}),
                    html.Div('BRK Tecnologia · 2026', style={'color': '#475569', 'fontSize': '10px', 'marginTop': '2px'}),
                ],
                className='sidebar-footer',
            ),
        ],
    )
