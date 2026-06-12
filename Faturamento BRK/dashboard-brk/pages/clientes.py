import dash
from dash import html, dcc, callback, Input, Output, dash_table
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from data.loader import get_liquid, apply_filters, last_month_is_partial
from components.theme import (COLORS, fmt_brl, CHART_COLORS,
                              TBL_BRL, TBL_PCT, TBL_PCT_SIGNED, col_num,
                              get_palette, plotly_template, table_styles)
from components.i18n import t

dash.register_page(__name__, path='/clientes', name='Clientes', order=1)

_TABLE_STYLE = {
    # rolagem contínua com cabeçalho fixo (sem paginação)
    'style_table': {'overflowX': 'auto', 'borderRadius': '8px',
                    'height': '640px', 'overflowY': 'auto'},
    'style_header': {
        'backgroundColor': COLORS['surface2'],
        'color': COLORS['text_secondary'],
        'fontWeight': '600',
        'fontSize': '11px',
        'textTransform': 'uppercase',
        'letterSpacing': '0.5px',
        'border': f'1px solid {COLORS["border"]}',
        'padding': '10px 12px',
    },
    'style_cell': {
        'backgroundColor': COLORS['surface'],
        'color': COLORS['text'],
        'border': f'1px solid {COLORS["border"]}',
        'fontSize': '12px',
        'padding': '8px 12px',
        'fontFamily': 'Inter, sans-serif',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
        'maxWidth': '220px',
    },
    'style_data_conditional': [
        {'if': {'row_index': 'odd'}, 'backgroundColor': COLORS['surface2']},
        {'if': {'filter_query': '{Status} contains "🚀"'}, 'color': COLORS['success']},
        {'if': {'filter_query': '{Status} contains "🔴"'}, 'color': '#FF8080'},
        {'if': {'filter_query': '{Status} contains "⚫"'}, 'color': COLORS['text_muted']},
        {'if': {'filter_query': '{Status} contains "📉"'}, 'color': COLORS['danger']},
    ],
}


def _status_conditionals(pal):
    cond = [
        {'if': {'row_index': 'odd'}, 'backgroundColor': pal['surface2']},
        {'if': {'filter_query': '{Status} contains "🚀"'}, 'color': pal['success']},
        {'if': {'filter_query': '{Status} contains "🔴"'}, 'color': '#FF8080'},
        {'if': {'filter_query': '{Status} contains "⚫"'}, 'color': pal['text_muted']},
        {'if': {'filter_query': '{Status} contains "📉"'}, 'color': pal['danger']},
    ]
    # variações: verde quando positivas, vermelho quando negativas
    for c in ('Var. M/M', 'Var. 3M', 'Var. 6M'):
        cond.append({'if': {'filter_query': f'{{{c}}} > 0', 'column_id': c},
                     'color': pal['success']})
        cond.append({'if': {'filter_query': f'{{{c}}} < 0', 'column_id': c},
                     'color': pal['danger']})
    return cond

layout = html.Div([
    html.Div([
        html.Div([
            html.Span('Análise de Clientes', id='cl-title', className='page-title'),
            html.Span('Todos os clientes · faturamento completo por período',
                      id='cl-sub', className='page-subtitle-inline'),
        ]),
    ], className='page-header-compact'),

    html.Div([
        html.Div([
            html.Div([
                html.Div('Receita Total por Cliente', id='cl-c1t', className='chart-title'),
                html.Div('Ranking completo · ordenável · paginado', id='cl-c1s', className='chart-subtitle'),
            ], className='chart-card-header'),
            dash_table.DataTable(
                id='clientes-table',
                # rolagem em vez de páginas: virtualização renderiza só as
                # linhas visíveis — suporta os ~2 mil clientes sem travar
                # (sem fixed_rows: combinado com virtualization entra em loop
                # de resize — bug do dash_table)
                page_action='none',
                virtualization=True,
                sort_action='native',
                filter_action='native',
                filter_options={'case': 'insensitive'},
                tooltip_delay=0,
                tooltip_duration=None,
                **_TABLE_STYLE,
            ),
        ], className='chart-card'),
    ]),

    html.Div(id='cliente-detail', style={'marginTop': '20px'}),
], id='page-content')


def _compute_status(row, now, lang='pt'):
    dias = (now - row['ultima_nf']).days if pd.notna(row['ultima_nf']) else 9999
    mom = row['var_mom']
    if dias >= 180:
        return t('st_inativo', lang)
    if dias >= 60:
        return t('st_churn', lang)
    if pd.notna(mom) and mom >= 15:
        return t('st_cresc', lang)
    if pd.notna(mom) and mom <= -15:
        return t('st_queda', lang)
    return t('st_estavel', lang)


@callback(
    Output('clientes-table', 'data'),
    Output('clientes-table', 'columns'),
    Output('clientes-table', 'style_header'),
    Output('clientes-table', 'style_cell'),
    Output('clientes-table', 'style_data_conditional'),
    Output('cl-title', 'children'), Output('cl-sub', 'children'),
    Output('cl-c1t', 'children'), Output('cl-c1s', 'children'),
    Input('filter-date', 'start_date'),
    Input('filter-date', 'end_date'),
    Input('filter-ano', 'value'),
    Input('filter-cliente', 'value'),
    Input('filter-produto', 'value'),
    Input('filter-valor-min', 'value'),
    Input('filter-valor-max', 'value'),
    Input('theme-select', 'value'),
    Input('lang-select', 'value'),
)
def update_table(start_date, end_date, anos, cliente, produto, valor_min, valor_max,
                 tema, lang):
    tema = tema or 'dark'
    lang = lang or 'pt'
    pal  = get_palette(tema)
    ts   = table_styles(tema)
    # minWidth estabiliza as colunas durante a rolagem virtualizada
    extras = (ts['style_header'],
              {**ts['style_cell'], 'minWidth': '105px'},
              _status_conditionals(pal),
              t('cl_title', lang), t('cl_sub', lang),
              t('cl_card', lang), t('cl_card_sub', lang))
    df_all = get_liquid()
    df = apply_filters(df_all, start_date, end_date, anos, cliente, produto, valor_min, valor_max)

    if df.empty:
        return [], [], *extras

    now = df['Emissao'].max()

    monthly = df.groupby(['GrupoEcon', 'AnoMesStr'])['Vlr.Total'].sum().unstack(fill_value=0)
    months_sorted = sorted(monthly.columns)
    monthly = monthly[months_sorted]
    # variação M/M sobre meses completos — mês parcial geraria queda falsa
    if last_month_is_partial(df) and len(months_sorted) >= 3:
        months_sorted = months_sorted[:-1]

    agg = df.groupby('GrupoEcon').agg(
        receita=('Vlr.Total', 'sum'),
        nfs=('Num. Docto.', 'nunique'),
        servicos=('Descricao', 'nunique'),
        quantidade=('Quantidade', 'sum'),
        ultima_nf=('Emissao', 'max'),
        primeira_nf=('Emissao', 'min'),
    ).reset_index()

    if len(months_sorted) >= 2:
        agg['ult_mes'] = agg['GrupoEcon'].map(monthly[months_sorted[-1]])
        agg['pen_mes'] = agg['GrupoEcon'].map(monthly[months_sorted[-2]])
        agg['var_mom'] = ((agg['ult_mes'] - agg['pen_mes']) / agg['pen_mes'].replace(0, np.nan) * 100)
    else:
        agg['ult_mes'] = agg['receita']
        agg['pen_mes'] = np.nan
        agg['var_mom'] = np.nan

    # médias móveis de faturamento (meses completos) + variação vs janela anterior
    def _janela(ini, fim):
        cols = months_sorted[ini:fim] if fim else months_sorted[ini:]
        return monthly[cols].sum(axis=1) if cols else None

    nm = len(months_sorted)
    for tam, alvo_media, alvo_var in ((3, 'media_3m', 'var_3m'), (6, 'media_6m', 'var_6m')):
        if nm >= tam:
            atual = _janela(-tam, None)
            agg[alvo_media] = agg['GrupoEcon'].map(atual / tam)
            if nm >= 2 * tam:
                anterior = _janela(-2 * tam, -tam)
                var = (atual / anterior.replace(0, np.nan) - 1) * 100
                agg[alvo_var] = agg['GrupoEcon'].map(var)
            else:
                agg[alvo_var] = np.nan
        else:
            agg[alvo_media] = np.nan
            agg[alvo_var] = np.nan

    agg['dias_sem_nf'] = (now - agg['ultima_nf']).dt.days
    agg['ticket_medio'] = agg['receita'] / agg['nfs'].replace(0, np.nan)
    agg['Status'] = agg.apply(_compute_status, axis=1, now=now, lang=lang)
    agg['Novo'] = (agg['primeira_nf'] >= now - pd.Timedelta(days=90))

    total = agg['receita'].sum()
    agg['pct_total'] = agg['receita'] / total * 100

    agg = agg.sort_values('receita', ascending=False).reset_index(drop=True)
    agg['Rank'] = agg.index + 1

    records = []
    for _, r in agg.iterrows():
        novo_tag = ' ✨' if r['Novo'] else ''
        records.append({
            '#': int(r['Rank']),
            'Cliente': r['GrupoEcon'] + novo_tag,
            'Receita Total': round(float(r['receita'])),
            '% da Carteira': round(float(r['pct_total']), 2),
            'Último Mês': round(float(r['ult_mes'])) if pd.notna(r['ult_mes']) else None,
            'Var. M/M': round(float(r['var_mom']), 1) if pd.notna(r['var_mom']) else None,
            'Média 3M': round(float(r['media_3m'])) if pd.notna(r['media_3m']) else None,
            'Var. 3M': round(float(r['var_3m']), 1) if pd.notna(r['var_3m']) else None,
            'Média 6M': round(float(r['media_6m'])) if pd.notna(r['media_6m']) else None,
            'Var. 6M': round(float(r['var_6m']), 1) if pd.notna(r['var_6m']) else None,
            'Última NF': r['ultima_nf'].strftime('%d/%m/%Y') if pd.notna(r['ultima_nf']) else '—',
            'Dias sem NF': int(r['dias_sem_nf']) if pd.notna(r['dias_sem_nf']) else None,
            'Status': r['Status'],
        })

    columns = [
        {'name': '#', 'id': '#', 'type': 'numeric'},
        {'name': t('col_cliente', lang), 'id': 'Cliente', 'type': 'text'},
        {'name': t('col_rtotal', lang), 'id': 'Receita Total', 'type': 'numeric', 'format': TBL_BRL},
        {'name': t('col_pct_cart', lang), 'id': '% da Carteira', 'type': 'numeric', 'format': TBL_PCT},
        {'name': t('col_ult_mes', lang), 'id': 'Último Mês', 'type': 'numeric', 'format': TBL_BRL},
        {'name': t('col_var_mm', lang), 'id': 'Var. M/M', 'type': 'numeric', 'format': TBL_PCT_SIGNED},
        {'name': t('col_media_3m', lang), 'id': 'Média 3M', 'type': 'numeric', 'format': TBL_BRL},
        {'name': t('col_var_3m_c', lang), 'id': 'Var. 3M', 'type': 'numeric', 'format': TBL_PCT_SIGNED},
        {'name': t('col_media_6m', lang), 'id': 'Média 6M', 'type': 'numeric', 'format': TBL_BRL},
        {'name': t('col_var_6m_c', lang), 'id': 'Var. 6M', 'type': 'numeric', 'format': TBL_PCT_SIGNED},
        {'name': t('col_ult_nf', lang), 'id': 'Última NF', 'type': 'text'},
        {'name': t('col_dias', lang), 'id': 'Dias sem NF', 'type': 'numeric'},
        {'name': t('col_status', lang), 'id': 'Status', 'type': 'text'},
    ] if records else []

    return records, columns, *extras


@callback(
    Output('cliente-detail', 'children'),
    Input('clientes-table', 'active_cell'),
    Input('clientes-table', 'data'),
    Input('filter-date', 'start_date'),
    Input('filter-date', 'end_date'),
    Input('filter-ano', 'value'),
    Input('filter-cliente', 'value'),
    Input('filter-produto', 'value'),
    Input('filter-valor-min', 'value'),
    Input('filter-valor-max', 'value'),
    Input('theme-select', 'value'),
    Input('lang-select', 'value'),
)
def update_detail(active_cell, table_data, start_date, end_date, anos, cliente, produto, valor_min, valor_max,
                  tema, lang):
    tema = tema or 'dark'
    lang = lang or 'pt'
    ts   = table_styles(tema)
    pal  = get_palette(tema)
    if not active_cell or not table_data:
        return html.Div(
            t('cl_clique', lang),
            style={'color': pal['text_muted'], 'padding': '16px', 'fontSize': '13px'},
        )

    row = table_data[active_cell['row']]
    nome = row['Cliente'].replace(' ✨', '').strip()

    df_all = get_liquid()
    df_base = apply_filters(df_all, start_date, end_date, anos, None, produto, valor_min, valor_max)

    df_cli = df_base[df_base['GrupoEcon'] == nome]
    if df_cli.empty:
        return html.Div(t('cl_sem', lang), style={'color': pal['text_muted']})

    # Evolução mensal
    monthly = df_cli.groupby('AnoMesStr')['Vlr.Total'].sum().sort_index().reset_index()
    monthly.columns = ['Mês', 'Receita']

    fig_evo = go.Figure()
    fig_evo.add_trace(go.Scatter(
        x=monthly['Mês'], y=monthly['Receita'],
        mode='lines+markers',
        fill='tozeroy',
        fillcolor='rgba(255,101,0,0.08)',
        line=dict(color=COLORS['primary'], width=2.5),
        marker=dict(size=6, color=COLORS['primary']),
        hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>',
    ))
    fig_evo.update_layout(
        template=plotly_template(tema),
        title=t('d_evo_de', lang, nome=nome),
        xaxis_title='', yaxis_title='R$',
        yaxis_tickformat=',.0f',
        xaxis=dict(tickformat='%m/%Y', hoverformat='%m/%Y'),
        height=300,
    )

    # Mix de serviços
    svc = df_cli.groupby('Descricao')['Vlr.Total'].sum().sort_values(ascending=False).reset_index()
    svc.columns = ['Serviço', 'Receita']
    fig_mix = go.Figure(go.Pie(
        labels=svc['Serviço'], values=svc['Receita'],
        hole=0.5,
        hovertemplate='<b>%{label}</b><br>R$ %{value:,.0f} · %{percent}<extra></extra>',
        textinfo='label+percent',
    ))
    fig_mix.update_layout(
        template=plotly_template(tema),
        title=t('d_mix_de', lang, nome=nome),
        height=350,
        showlegend=True,
        legend=dict(font=dict(size=10)),
    )

    # Tabela de serviços
    svc['% do Cliente'] = (svc['Receita'] / svc['Receita'].sum() * 100).map('{:.2f}%'.format)
    svc['Receita Fmt'] = svc['Receita'].map(fmt_brl)
    svc_records = svc[['Serviço', 'Receita Fmt', '% do Cliente']].rename(
        columns={'Receita Fmt': 'Receita'}
    ).to_dict('records')

    svc_table = dash_table.DataTable(
        data=svc_records,
        columns=[
            {'name': t('col_servico', lang), 'id': 'Serviço'},
            {'name': t('col_rtotal', lang), 'id': 'Receita'},
            {'name': t('col_pct_cli', lang), 'id': '% do Cliente'},
        ],
        page_size=15,
        sort_action='native',
        style_table={'borderRadius': '8px', 'overflowX': 'auto'},
        style_header=ts['style_header'],
        style_cell=ts['style_cell'],
        style_data_conditional=[ts['zebra']],
    )

    # Todas as NFs
    nfs = df_cli.groupby('Num. Docto.').agg(
        Data=('Emissao', 'first'),
        Serie=('Serie', 'first'),
        Valor=('Vlr.Total', 'sum'),
        Itens=('Descricao', 'count'),
    ).reset_index().sort_values('Data', ascending=False)
    nfs['Data'] = nfs['Data'].dt.strftime('%d/%m/%Y')
    nfs['Valor'] = nfs['Valor'].map(lambda v: f'R$ {v:,.0f}')
    nfs_records = nfs.rename(columns={'Num. Docto.': 'Número NF'}).to_dict('records')

    nfs_table = dash_table.DataTable(
        data=nfs_records,
        columns=[
            {'name': t('col_num_nf', lang), 'id': 'Número NF'},
            {'name': t('col_data', lang), 'id': 'Data'},
            {'name': 'Serie', 'id': 'Serie'},
            {'name': t('col_valor', lang), 'id': 'Valor'},
            {'name': t('col_itens', lang), 'id': 'Itens'},
        ],
        page_size=10,
        sort_action='native',
        style_table={'borderRadius': '8px', 'overflowX': 'auto'},
        style_header=ts['style_header'],
        style_cell=ts['style_cell'],
        style_data_conditional=[ts['zebra']],
    )

    receita_total_cli = df_cli['Vlr.Total'].sum()
    receita_total_cart = df_base['Vlr.Total'].sum()
    pct_carteira = receita_total_cli / receita_total_cart * 100 if receita_total_cart > 0 else 0

    pct_fmt = f'{pct_carteira:.2f}'.replace('.', ',')
    return html.Div([
        html.Div([
            html.Div(nome, className='detail-name'),
            html.Div([
                html.Span(f'{fmt_brl(receita_total_cli)}', className='detail-val'),
                html.Span(t('d_carteira', lang, pct=pct_fmt), className='detail-ctx'),
            ]),
        ], style={'marginBottom': '20px', 'paddingBottom': '16px', 'borderBottom': f'1px solid {pal["border"]}'}),

        html.Div([
            html.Div([
                html.Div([
                    html.Div(t('d_evolucao', lang), className='chart-title'),
                ], className='chart-card-header'),
                dcc.Graph(figure=fig_evo, config={'displayModeBar': False}),
            ], className='chart-card'),
            html.Div([
                html.Div([
                    html.Div(t('d_mix', lang), className='chart-title'),
                ], className='chart-card-header'),
                dcc.Graph(figure=fig_mix, config={'displayModeBar': False}),
            ], className='chart-card'),
        ], className='grid-2'),

        html.Div([
            html.Div([
                html.Div([
                    html.Div(t('d_serv_contr', lang), className='chart-title'),
                ], className='chart-card-header'),
                svc_table,
            ], className='chart-card'),
            html.Div([
                html.Div([
                    html.Div(t('d_nfs', lang), className='chart-title'),
                ], className='chart-card-header'),
                nfs_table,
            ], className='chart-card'),
        ], className='grid-2'),
    ], className='chart-card')
