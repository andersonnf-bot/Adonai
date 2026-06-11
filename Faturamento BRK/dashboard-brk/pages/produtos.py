import dash
from dash import html, dcc, callback, Input, Output, dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from data.loader import get_liquid, apply_filters, last_month_is_partial
from components.theme import (COLORS, fmt_brl, CHART_COLORS,
                              TBL_BRL, TBL_BRL_2, TBL_PCT, TBL_PCT_SIGNED, col_num,
                              get_palette, plotly_template, table_styles)
from components.i18n import t

dash.register_page(__name__, path='/produtos', name='Produtos & Serviços', order=2)

_CELL = {
    'style_table': {'overflowX': 'auto', 'borderRadius': '8px'},
    'style_header': {
        'backgroundColor': COLORS['surface2'], 'color': COLORS['text_secondary'],
        'fontWeight': '600', 'fontSize': '11px', 'textTransform': 'uppercase',
        'letterSpacing': '0.5px', 'border': f'1px solid {COLORS["border"]}', 'padding': '10px 12px',
    },
    'style_cell': {
        'backgroundColor': COLORS['surface'], 'color': COLORS['text'],
        'border': f'1px solid {COLORS["border"]}', 'fontSize': '12px',
        'padding': '8px 12px', 'fontFamily': 'Inter, sans-serif',
        'overflow': 'hidden', 'textOverflow': 'ellipsis', 'maxWidth': '260px',
    },
    'style_data_conditional': [
        {'if': {'row_index': 'odd'}, 'backgroundColor': COLORS['surface2']},
    ],
}

layout = html.Div([
    html.Div([
        html.Div('Produtos & Serviços', id='p-title', className='page-title'),
        html.Div('Análise completa do portfólio de serviços', id='p-sub', className='page-subtitle'),
    ], className='page-header'),

    html.Div([
        html.Div([
            html.Div([
                html.Div('Matriz de Portfólio', id='p-c1t', className='chart-title'),
                html.Div('Receita × Crescimento M/M × Volume — todos os serviços', id='p-c1s', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='produtos-bubble', config={'displayModeBar': False}, style={'height': '450px'}),
        ], className='chart-card'),

        html.Div([
            html.Div([
                html.Div('Ranking Completo de Serviços', id='p-c2t', className='chart-title'),
                html.Div('Ordenável · portfólio completo', id='p-c2s', className='chart-subtitle'),
            ], className='chart-card-header'),
            dash_table.DataTable(
                id='produtos-table',
                page_size=20,
                sort_action='native',
                filter_action='native',
                filter_options={'case': 'insensitive'},
                **_CELL,
            ),
        ], className='chart-card'),
    ]),

    html.Div(id='produto-detail', style={'marginTop': '20px'}),
], id='page-content')


@callback(
    Output('produtos-bubble', 'figure'),
    Output('produtos-table', 'data'),
    Output('produtos-table', 'columns'),
    Output('produtos-table', 'style_header'),
    Output('produtos-table', 'style_cell'),
    Output('produtos-table', 'style_data_conditional'),
    Output('p-title', 'children'), Output('p-sub', 'children'),
    Output('p-c1t', 'children'), Output('p-c1s', 'children'),
    Output('p-c2t', 'children'), Output('p-c2s', 'children'),
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
def update_produtos(start_date, end_date, anos, cliente, produto, valor_min, valor_max,
                    tema, lang):
    tema = tema or 'dark'
    lang = lang or 'pt'
    pal  = get_palette(tema)
    ts   = table_styles(tema)
    extras = (ts['style_header'], ts['style_cell'], [ts['zebra']],
              t('p_title', lang), t('p_sub', lang),
              t('p_matriz', lang), t('p_matriz_sub', lang),
              t('p_rank', lang), t('p_rank_sub', lang))
    df_all = get_liquid()
    df = apply_filters(df_all, start_date, end_date, anos, cliente, produto, valor_min, valor_max)

    if df.empty:
        empty_fig = go.Figure()
        empty_fig.update_layout(title=t('t_vazio', lang), template=plotly_template(tema))
        return empty_fig, [], [], *extras

    monthly = df.groupby(['Descricao', 'AnoMesStr'])['Vlr.Total'].sum().unstack(fill_value=0)
    months_sorted = sorted(monthly.columns)
    monthly = monthly[months_sorted]
    # variação M/M sobre meses completos — mês parcial geraria queda falsa
    if last_month_is_partial(df) and len(months_sorted) >= 3:
        months_sorted = months_sorted[:-1]

    agg = df.groupby('Descricao').agg(
        receita=('Vlr.Total', 'sum'),
        clientes=('Nome', 'nunique'),
        quantidade=('Quantidade', 'sum'),
        ticket=('Vlr.Unitario', 'mean'),
        nfs=('Num. Docto.', 'nunique'),
    ).reset_index()

    if len(months_sorted) >= 2:
        agg['ult_mes'] = agg['Descricao'].map(monthly[months_sorted[-1]])
        agg['pen_mes'] = agg['Descricao'].map(monthly[months_sorted[-2]])
        agg['var_mom'] = ((agg['ult_mes'] - agg['pen_mes']) / agg['pen_mes'].replace(0, np.nan) * 100)
    else:
        agg['ult_mes'] = agg['receita']
        agg['pen_mes'] = np.nan
        agg['var_mom'] = np.nan

    if len(months_sorted) >= 6:
        agg['rec_3m'] = agg['Descricao'].map(monthly[months_sorted[-3:]].sum(axis=1))
        agg['rec_3m_prev'] = agg['Descricao'].map(monthly[months_sorted[-6:-3]].sum(axis=1))
        agg['var_3m'] = ((agg['rec_3m'] - agg['rec_3m_prev']) / agg['rec_3m_prev'].replace(0, np.nan) * 100)
    else:
        agg['var_3m'] = agg['var_mom']

    total = agg['receita'].sum()
    agg['pct'] = agg['receita'] / total * 100

    def status_svc(row):
        if pd.notna(row['var_mom']) and row['var_mom'] >= 15:
            return t('st_cresc', lang)
        if pd.notna(row['var_mom']) and row['var_mom'] <= -15:
            return t('st_queda', lang)
        if row['clientes'] == 1:
            return t('st_mono', lang)
        return t('st_estavel', lang)

    agg['Status'] = agg.apply(status_svc, axis=1)
    agg = agg.sort_values('receita', ascending=False).reset_index(drop=True)
    agg['Rank'] = agg.index + 1

    # Bubble chart — corta receitas < R$ 1 mil: sem isso a escala log estica
    # até microvalores (µ) e os ticks ficam ilegíveis
    bubble_data = agg[agg['receita'] >= 1000].copy()
    bubble_data['var_mom_clean'] = bubble_data['var_mom'].fillna(0)
    # outliers de variação (mudança de escopo, base pequena) esmagavam o eixo
    bubble_data['var_plot'] = bubble_data['var_mom_clean'].clip(-100, 100)
    # rótulo apenas nos 12 maiores — acima disso vira mancha ilegível
    top_labels = set(bubble_data.nlargest(12, 'receita')['Descricao'])
    bubble_data['label_short'] = np.where(
        bubble_data['Descricao'].isin(top_labels),
        bubble_data['Descricao'].str[:28], '',
    )

    color_vals = bubble_data['var_mom_clean'].clip(-50, 50)

    fig_bubble = go.Figure(go.Scatter(
        x=bubble_data['receita'] / 1_000_000,
        y=bubble_data['var_plot'],
        mode='markers+text',
        marker=dict(
            size=np.sqrt(bubble_data['quantidade'].clip(1)) * 0.8,
            sizemode='area',
            sizeref=2. * bubble_data['quantidade'].clip(1).max() ** 0.5 / (60 ** 2),
            sizemin=4,
            color=color_vals,
            colorscale=[
                [0, COLORS['danger']],
                [0.5, COLORS['text_muted']],
                [1, COLORS['success']],
            ],
            showscale=True,
            colorbar=dict(title='Var M/M %', tickfont=dict(color=pal['text_secondary'])),
            line=dict(color=pal['border'], width=0.5),
        ),
        text=bubble_data['label_short'],
        textfont=dict(size=9, color=pal['text_secondary']),
        textposition='top center',
        customdata=bubble_data[['Descricao', 'clientes', 'receita', 'var_mom_clean', 'quantidade']].values,
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            'Receita: R$ %{customdata[2]:,.0f}<br>'
            'Crescimento M/M: %{customdata[3]:+.1f}%<br>'
            'Clientes: %{customdata[1]}<br>'
            'Qtd: %{customdata[4]:,.0f}<extra></extra>'
        ),
    ))
    fig_bubble.add_hline(y=0, line_dash='dot', line_color=pal['border'])
    fig_bubble.update_layout(
        template=plotly_template(tema),
        title=t('g_matriz', lang),
        xaxis_title=t('eixo_rec_log', lang),
        yaxis_title=t('eixo_var_mm', lang),
        height=430,
        # escala log espalha os serviços — antes 90% ficava amontoado perto do zero
        # (sem tickformat fixo: em log os ticks variam ordens de magnitude)
        xaxis=dict(type='log'),
        yaxis=dict(range=[-115, 115]),
    )

    # Table
    records = []
    for _, r in agg.iterrows():
        records.append({
            '#': int(r['Rank']),
            'Serviço': r['Descricao'],
            'Receita Total': round(float(r['receita'])),
            '% Portfólio': round(float(r['pct']), 2),
            'Último Mês': round(float(r['ult_mes'])) if pd.notna(r.get('ult_mes')) else None,
            'Var. M/M': round(float(r['var_mom']), 1) if pd.notna(r['var_mom']) else None,
            'Var. 3M': round(float(r['var_3m']), 1) if pd.notna(r['var_3m']) else None,
            'Clientes': int(r['clientes']),
            'Ticket Médio': round(float(r['ticket']), 2) if pd.notna(r['ticket']) else None,
            'Status': r['Status'],
        })

    columns = [
        {'name': '#', 'id': '#', 'type': 'numeric'},
        {'name': t('col_servico', lang), 'id': 'Serviço', 'type': 'text'},
        {'name': t('col_rtotal', lang), 'id': 'Receita Total', 'type': 'numeric', 'format': TBL_BRL},
        {'name': t('col_pct_portf', lang), 'id': '% Portfólio', 'type': 'numeric', 'format': TBL_PCT},
        {'name': t('col_ult_mes', lang), 'id': 'Último Mês', 'type': 'numeric', 'format': TBL_BRL},
        {'name': t('col_var_mm', lang), 'id': 'Var. M/M', 'type': 'numeric', 'format': TBL_PCT_SIGNED},
        {'name': t('col_var_3m', lang), 'id': 'Var. 3M', 'type': 'numeric', 'format': TBL_PCT_SIGNED},
        {'name': t('col_clientes', lang), 'id': 'Clientes', 'type': 'numeric'},
        {'name': t('col_ticket', lang), 'id': 'Ticket Médio', 'type': 'numeric', 'format': TBL_BRL_2},
        {'name': t('col_status', lang), 'id': 'Status', 'type': 'text'},
    ] if records else []
    return fig_bubble, records, columns, *extras


@callback(
    Output('produto-detail', 'children'),
    Input('produtos-table', 'active_cell'),
    Input('produtos-table', 'data'),
    Input('filter-date', 'start_date'),
    Input('filter-date', 'end_date'),
    Input('filter-ano', 'value'),
    Input('filter-cliente', 'value'),
    Input('filter-valor-min', 'value'),
    Input('filter-valor-max', 'value'),
    Input('theme-select', 'value'),
    Input('lang-select', 'value'),
)
def update_produto_detail(active_cell, table_data, start_date, end_date, anos, cliente, valor_min, valor_max,
                          tema, lang):
    tema = tema or 'dark'
    lang = lang or 'pt'
    ts   = table_styles(tema)
    pal  = get_palette(tema)
    if not active_cell or not table_data:
        return html.Div(
            t('p_clique', lang),
            style={'color': pal['text_muted'], 'padding': '16px', 'fontSize': '13px'},
        )

    row = table_data[active_cell['row']]
    servico = row['Serviço']

    df_all = get_liquid()
    df_base = apply_filters(df_all, start_date, end_date, anos, cliente, None, valor_min, valor_max)

    df_svc = df_base[df_base['Descricao'] == servico]
    if df_svc.empty:
        return html.Div(t('p_sem', lang), style={'color': pal['text_muted']})

    # Evolução mensal
    monthly = df_svc.groupby('AnoMesStr').agg(
        receita=('Vlr.Total', 'sum'),
        quantidade=('Quantidade', 'sum'),
        ticket=('Vlr.Unitario', 'mean'),
    ).sort_index().reset_index()

    fig_evo = go.Figure()
    fig_evo.add_trace(go.Bar(
        x=monthly['AnoMesStr'], y=monthly['receita'],
        name=t('g_receita', lang), marker_color=COLORS['primary'], marker_opacity=0.85,
        yaxis='y',
        hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>',
    ))
    fig_evo.add_trace(go.Scatter(
        x=monthly['AnoMesStr'], y=monthly['quantidade'],
        name=t('g_qtd', lang), line=dict(color=COLORS['info'], width=2),
        yaxis='y2', mode='lines+markers', marker=dict(size=4),
        hovertemplate='<b>%{x}</b><br>Qtd: %{y:,.0f}<extra></extra>',
    ))
    fig_evo.update_layout(
        template=plotly_template(tema),
        title=t('d_evo_srv', lang, srv=servico),
        yaxis=dict(title=t('eixo_receita', lang), tickformat=',.0f'),
        yaxis2=dict(title=t('eixo_qtd', lang), overlaying='y', side='right', showgrid=False),
        xaxis=dict(tickformat='%m/%Y', hoverformat='%m/%Y'),
        legend=dict(orientation='h', y=1.1),
        height=320,
    )

    # Ticket médio
    fig_ticket = go.Figure(go.Scatter(
        x=monthly['AnoMesStr'], y=monthly['ticket'],
        mode='lines+markers',
        line=dict(color=COLORS['warning'], width=2.5),
        marker=dict(size=6),
        fill='tozeroy', fillcolor='rgba(245,158,11,0.06)',
        hovertemplate='<b>%{x}</b><br>Ticket Médio: R$ %{y:,.2f}<extra></extra>',
    ))
    fig_ticket.update_layout(
        template=plotly_template(tema),
        title=t('d_ticket_t', lang),
        xaxis_title='', yaxis_title=t('d_ticket_y', lang),
        yaxis_tickformat=',.2f',
        xaxis=dict(tickformat='%m/%Y', hoverformat='%m/%Y'),
        height=280,
    )

    # Clientes que consomem este serviço
    cli_svc = df_svc.groupby('GrupoEcon').agg(
        receita=('Vlr.Total', 'sum'),
        quantidade=('Quantidade', 'sum'),
        nfs=('Num. Docto.', 'nunique'),
    ).reset_index().sort_values('receita', ascending=False)
    total_svc = cli_svc['receita'].sum()
    cli_svc['%'] = (cli_svc['receita'] / total_svc * 100).map('{:.2f}%'.format)
    cli_svc['Receita'] = cli_svc['receita'].map(lambda v: f'R$ {v:,.0f}')

    cli_table = dash_table.DataTable(
        data=cli_svc[['GrupoEcon', 'Receita', '%', 'quantidade', 'nfs']].rename(
            columns={'GrupoEcon': 'Cliente', 'quantidade': 'Qtd', 'nfs': 'NFs'}
        ).to_dict('records'),
        columns=[
            {'name': t('col_cliente', lang), 'id': 'Cliente'},
            {'name': t('col_rtotal', lang), 'id': 'Receita'},
            {'name': '%', 'id': '%'},
            {'name': t('col_qtd', lang), 'id': 'Qtd'},
            {'name': t('col_nfs', lang), 'id': 'NFs'},
        ],
        page_size=15,
        sort_action='native',
        style_table=ts['style_table'],
        style_header=ts['style_header'],
        style_cell=ts['style_cell'],
        style_data_conditional=[ts['zebra']],
    )

    receita_total_svc = df_svc['Vlr.Total'].sum()
    clientes_count = df_svc['GrupoEcon'].nunique()

    return html.Div([
        html.Div([
            html.Div(servico, className='detail-name'),
            html.Div([
                html.Span(fmt_brl(receita_total_svc), className='detail-val'),
                html.Span(t('d_cli_ativos', lang, n=clientes_count), className='detail-ctx'),
            ]),
        ], style={'marginBottom': '20px', 'paddingBottom': '16px', 'borderBottom': f'1px solid {pal["border"]}'}),

        html.Div([
            html.Div([
                dcc.Graph(figure=fig_evo, config={'displayModeBar': False}),
            ], className='chart-card'),
            html.Div([
                dcc.Graph(figure=fig_ticket, config={'displayModeBar': False}),
            ], className='chart-card'),
        ], className='grid-2'),

        html.Div([
            html.Div([
                html.Div([
                    html.Div(t('d_cli_srv', lang), className='chart-title'),
                ], className='chart-card-header'),
                cli_table,
            ], className='chart-card'),
        ]),
    ], className='chart-card')
