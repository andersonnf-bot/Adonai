import dash
from dash import html, dcc, callback, Input, Output, State, ClientsideFunction
import dash_bootstrap_components as dbc

from components.theme import COLORS
from components.navbar import build_navbar
from components.filters import build_filter_bar

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

app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
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
)
def update_sidebar(pathname):
    return build_navbar(pathname or '/')


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
