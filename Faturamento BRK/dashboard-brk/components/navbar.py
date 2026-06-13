from dash import html, dcc, get_asset_url

from components.i18n import t
from components.theme import fmt_brl
from data.loader import get_liquid, get_data_mtime


# idioma → (arquivo da bandeira, rótulo curto, nome p/ tooltip)
_LANGS = [
    ('pt', 'br.svg', 'PT', 'Português'),
    ('en', 'en.svg', 'EN', 'English'),
    ('es', 'es.svg', 'Español'.upper()[:2], 'Español'),
]


PAGES = [
    {'path': '/',            'key': 'nav_overview', 'icon': '📊'},
    {'path': '/clientes',    'key': 'nav_clientes', 'icon': '🏢'},
    {'path': '/produtos',    'key': 'nav_produtos', 'icon': '📦'},
    {'path': '/tendencias',  'key': 'nav_tend',     'icon': '📈'},
]


def _resumo_base(lang='pt'):
    """Mini-resumo dos dados na sidebar — preenche o vão abaixo dos módulos."""
    df = get_liquid()
    periodo = f"{df['Emissao'].min():%m/%Y} – {df['Emissao'].max():%m/%Y}"
    total = float(df['Vlr.Total'].sum())
    grupos = int(df['GrupoEcon'].nunique())
    servicos = int(df['Descricao'].nunique())
    return html.Div([
        html.Div(t('nav_resumo', lang), className='sidebar-resumo-title'),
        html.Div(['📅 ', html.Span(periodo, className='val')],
                 className='sidebar-resumo-row'),
        html.Div([html.Span(fmt_brl(total), className='val'),
                  f' · {t("nav_rec", lang)}'], className='sidebar-resumo-row'),
        html.Div([html.Span(f'{grupos:,}'.replace(',', '.'), className='val'),
                  f' · {t("nav_grupos", lang)}'], className='sidebar-resumo-row'),
        html.Div([html.Span(str(servicos), className='val'),
                  f' · {t("td_servicos", lang)}'], className='sidebar-resumo-row'),
    ], className='sidebar-resumo')


def sidebar_prefs():
    """Bloco ESTÁTICO de preferências (tema + idioma) — fica na sidebar, logo
    abaixo dos módulos. Mantido fora dos callbacks de navegação: os selects
    são Input de muitos callbacks e não podem ser recriados dinamicamente
    (recriá-los dentro da navbar criaria loop e perderia o estado)."""
    return html.Div(
        [
            dcc.Dropdown(
                id='theme-select',
                options=[
                    {'label': '☀️ Light', 'value': 'light'},
                    {'label': '🌙 Dark', 'value': 'dark'},
                ],
                value='light', clearable=False, searchable=False,
                persistence=True, persistence_type='local',
                style={'fontSize': '12px'},
            ),
            # Idioma: bandeirinhas clicáveis (SVG renderiza em qualquer SO —
            # emoji de bandeira não aparece no Windows, vira "BR"/"EN"). O
            # dropdown fica oculto só para guardar o valor e a persistência;
            # os callbacks de página seguem lendo Input('lang-select','value').
            html.Div(
                [
                    html.Button(
                        html.Img(src=get_asset_url(f'flags/{flag}'), alt=label,
                                 className='lang-flag-img'),
                        id=f'lang-{code}', n_clicks=0, title=nome,
                        className='lang-flag', **{'aria-label': nome},
                    )
                    for code, flag, label, nome in _LANGS
                ],
                className='lang-flags',
            ),
            dcc.Dropdown(
                id='lang-select',
                options=[{'label': c, 'value': c} for c, *_ in _LANGS],
                value='pt', clearable=False, searchable=False,
                persistence=True, persistence_type='local',
                style={'display': 'none'},
            ),
        ],
        className='sidebar-prefs',
    )


def sidebar_footer():
    """Rodapé ESTÁTICO: data de atualização da base (controle) + responsável."""
    mtime = get_data_mtime()
    data_txt = mtime.strftime('%d/%m/%Y') if mtime else '—'
    return html.Div(
        [
            html.Div([
                html.Span('🔄 ', className='foot-ico'),
                html.Span('Atualizado em ', className='foot-lbl'),
                html.Span(data_txt, className='foot-val'),
            ], className='sidebar-foot-row'),
            html.Div('Adonai · Anderson Ferreira', className='sidebar-foot-name'),
            html.Div('Gerente de Área', className='sidebar-foot-role'),
        ],
        className='sidebar-footer',
    )


def build_sidebar_nav(pathname='/', lang='pt'):
    """Bloco DINÂMICO: logo + lista de módulos (depende de idioma e da página
    ativa). Renderizado pelo callback de navegação."""
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

    return html.Div([
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
    ])


def sidebar_shell():
    """Estrutura ESTÁTICA da sidebar: dois containers dinâmicos (nav e resumo)
    intercalados com os blocos estáticos (preferências e rodapé). Definida no
    layout uma vez; os callbacks só repintam os containers internos."""
    return html.Div(
        id='sidebar',
        children=[
            html.Div(id='sidebar-nav-container'),
            sidebar_prefs(),
            html.Div(id='sidebar-resumo-container'),
            sidebar_footer(),
        ],
    )
