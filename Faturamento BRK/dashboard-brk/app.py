import os

import dash
from dash import html, dcc, callback, Input, Output, State, ClientsideFunction
import dash_bootstrap_components as dbc
from flask import request, Response

from components.theme import COLORS
from components.navbar import build_navbar
from components.filters import build_filter_bar
from components.i18n import t

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap',
    ],
    suppress_callback_exceptions=True,
    title='BRK Analytics · Nstech',
    update_title=None,
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
)

server = app.server

# ── Autenticação básica ──
# Credenciais via variáveis de ambiente (Render → Environment), com padrão
# para uso imediato. O navegador pede login uma vez e memoriza na sessão.
_AUTH_USER = os.environ.get('DASH_USER', 'brk')
_AUTH_PASS = os.environ.get('DASH_PASS', 'Nstech@2026')


@server.before_request
def _requer_login():
    # localhost dispensa login (apenas fora do Render — lá a env RENDER existe)
    if os.environ.get('RENDER') is None and request.remote_addr in ('127.0.0.1', '::1'):
        return None
    auth = request.authorization
    if auth and auth.username == _AUTH_USER and auth.password == _AUTH_PASS:
        return None
    return Response(
        'Acesso restrito · BRK Analytics', 401,
        {'WWW-Authenticate': 'Basic realm="BRK Analytics"'},
    )

app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        html.Div(id='theme-dummy', style={'display': 'none'}),
        html.Div(id='sidebar-container'),
        html.Div(
            [
                build_filter_bar(),
                html.Div(
                    dash.page_container,
                    id='page-wrapper',
                ),
            ],
            id='main-content',
        ),
    ],
    id='app-shell',
)


@callback(
    Output('sidebar-container', 'children'),
    Input('url', 'pathname'),
    Input('lang-select', 'value'),
)
def update_sidebar(pathname, lang):
    return build_navbar(pathname or '/', lang or 'pt')


# ── Aplica o tema no shell (CSS troca as variáveis via data-theme) ──
app.clientside_callback(
    """
    function(tema) {
        var shell = document.getElementById('app-shell');
        if (shell) { shell.setAttribute('data-theme', tema || 'dark'); }
        return '';
    }
    """,
    Output('theme-dummy', 'children'),
    Input('theme-select', 'value'),
)


# ── Traduz rótulos e placeholders da barra de filtros ──
@callback(
    Output('f-lbl-filtros', 'children'),
    Output('f-lbl-periodo', 'children'),
    Output('f-lbl-ano', 'children'),
    Output('f-lbl-cliente', 'children'),
    Output('f-lbl-servico', 'children'),
    Output('f-lbl-fat', 'children'),
    Output('filter-ano', 'placeholder'),
    Output('filter-cliente', 'placeholder'),
    Output('filter-produto', 'placeholder'),
    Output('filter-valor-min', 'placeholder'),
    Output('filter-valor-max', 'placeholder'),
    Input('lang-select', 'value'),
)
def traduz_filtros(lang):
    lang = lang or 'pt'
    return (
        t('f_filtros', lang), t('f_periodo', lang), t('f_ano', lang),
        t('f_cliente', lang), t('f_servico', lang), t('f_fat', lang),
        t('f_todos', lang), t('f_buscar', lang), t('f_todos_srv', lang),
        t('f_min', lang), t('f_max', lang),
    )


# ── Formata campo Mín ao sair do campo (on blur) ──
app.clientside_callback(
    """
    function(n_blur, value) {
        if (!value || value.toString().trim() === '') return '';
        var raw = value.toString().replace(/[^0-9,]/g, '').replace(',', '.');
        var num = parseFloat(raw);
        if (isNaN(num)) return value;
        return num.toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 0});
    }
    """,
    Output('filter-valor-min', 'value'),
    Input('filter-valor-min', 'n_blur'),
    State('filter-valor-min', 'value'),
    prevent_initial_call=True,
)

# ── Formata campo Máx ao sair do campo (on blur) ──
app.clientside_callback(
    """
    function(n_blur, value) {
        if (!value || value.toString().trim() === '') return '';
        var raw = value.toString().replace(/[^0-9,]/g, '').replace(',', '.');
        var num = parseFloat(raw);
        if (isNaN(num)) return value;
        return num.toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 0});
    }
    """,
    Output('filter-valor-max', 'value'),
    Input('filter-valor-max', 'n_blur'),
    State('filter-valor-max', 'value'),
    prevent_initial_call=True,
)




if __name__ == '__main__':
    print('\n' + '='*60)
    print('  BRK Analytics Platform · Nstech Group')
    print('  Carregando dados...')
    from data.loader import load_data
    df_raw, df_liquid = load_data()
    print(f'  [OK] {len(df_liquid):,} registros liquidos carregados')
    print(f'  [OK] {df_liquid["Nome"].nunique():,} clientes')
    print(f'  [OK] {df_liquid["Descricao"].nunique():,} servicos')
    print(f'  [OK] R$ {df_liquid["Vlr.Total"].sum()/1e6:.1f}M em receita')
    print('  [>>] Iniciando em http://localhost:8050')
    print('='*60 + '\n')
    app.run(debug=False, port=8050)
