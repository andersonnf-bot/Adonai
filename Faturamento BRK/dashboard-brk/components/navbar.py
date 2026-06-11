from dash import html, dcc

from components.i18n import t


PAGES = [
    {'path': '/',            'key': 'nav_overview', 'icon': '📊'},
    {'path': '/clientes',    'key': 'nav_clientes', 'icon': '🏢'},
    {'path': '/produtos',    'key': 'nav_produtos', 'icon': '📦'},
    {'path': '/tendencias',  'key': 'nav_tend',     'icon': '📈'},
]


def build_navbar(pathname='/', lang='pt'):
    links = []
    for page in PAGES:
        is_active = pathname == page['path']
        links.append(
            dcc.Link(
                [
                    html.Span(page['icon'], className='nav-icon'),
                    html.Span(t(page['key'], lang)),
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
                    html.Div(t('nav_tagline', lang), className='sidebar-logo-sub'),
                ],
                className='sidebar-logo',
            ),
            html.Div(
                [
                    html.Div(t('nav_modulos', lang), className='sidebar-section-label'),
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
