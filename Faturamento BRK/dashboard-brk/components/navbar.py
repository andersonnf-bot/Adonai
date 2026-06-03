from dash import html, dcc


PAGES = [
    {'path': '/',            'label': 'Visão Executiva',  'icon': '📊'},
    {'path': '/clientes',    'label': 'Clientes',          'icon': '🏢'},
    {'path': '/produtos',    'label': 'Produtos & Serviços','icon': '📦'},
    {'path': '/tendencias',  'label': 'Tendências',         'icon': '📈'},
    {'path': '/documentos',  'label': 'Documentos',         'icon': '🧾'},
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
                    html.Div('BRK', className='sidebar-logo-title'),
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
                'Nstech Group · 2026',
                className='sidebar-footer',
            ),
        ],
    )
