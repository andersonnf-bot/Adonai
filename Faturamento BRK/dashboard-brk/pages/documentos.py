import dash
from dash import html, dcc, callback, Input, Output, dash_table
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from data.loader import load_data, apply_filters
from components.theme import COLORS, fmt_brl

dash.register_page(__name__, path='/documentos', name='Documentos', order=4)

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
        {'if': {'filter_query': '{Série} = "RET"'}, 'color': COLORS['danger']},
        {'if': {'filter_query': '{Série} = "DAV"'}, 'color': COLORS['warning']},
    ],
}

layout = html.Div([
    html.Div([
        html.Div('Documentos & Faturamento Operacional', className='page-title'),
        html.Div('Notas fiscais completas · todas as séries · rastreabilidade total', className='page-subtitle'),
    ], className='page-header'),

    html.Div(id='doc-kpis', style={'marginBottom': '20px'}),

    html.Div([
        html.Div([
            html.Div([
                html.Div('Volume de NFs por Mês', className='chart-title'),
                html.Div('Quantidade de documentos emitidos por série', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='doc-chart-volume', config={'displayModeBar': False}, style={'height': '300px'}),
        ], className='chart-card'),

        html.Div([
            html.Div([
                html.Div('Distribuição de Valor por NF', className='chart-title'),
                html.Div('Histograma · identifica NFs muito pequenas ou muito grandes', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='doc-chart-hist', config={'displayModeBar': False}, style={'height': '300px'}),
        ], className='chart-card'),
    ], className='grid-2'),

    html.Div([
        html.Div([
            html.Div([
                html.Div('Impacto de Cancelamentos e Devoluções', className='chart-title'),
                html.Div('Séries RET e DAV vs. receita bruta total', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='doc-chart-ret', config={'displayModeBar': False}, style={'height': '280px'}),
        ], className='chart-card'),

        html.Div([
            html.Div([
                html.Div('Ticket Médio por NF ao Longo do Tempo', className='chart-title'),
                html.Div('Identifica variações no valor médio dos documentos', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='doc-chart-ticket', config={'displayModeBar': False}, style={'height': '280px'}),
        ], className='chart-card'),
    ], className='grid-2'),

    html.Div([
        html.Div([
            html.Div([
                html.Div('Todas as Notas Fiscais', className='chart-title'),
                html.Div('Paginada · ordenável · exportável por filtro', className='chart-subtitle'),
            ], className='chart-card-header'),
            dash_table.DataTable(
                id='doc-table-nfs',
                page_size=25,
                sort_action='native',
                filter_action='native',
                filter_options={'case': 'insensitive'},
                export_format='csv',
                export_headers='display',
                **_CELL,
            ),
        ], className='chart-card'),
    ]),

    html.Div(id='doc-nf-detail', style={'marginTop': '20px'}),
], id='page-content')


@callback(
    Output('doc-kpis', 'children'),
    Output('doc-chart-volume', 'figure'),
    Output('doc-chart-hist', 'figure'),
    Output('doc-chart-ret', 'figure'),
    Output('doc-chart-ticket', 'figure'),
    Output('doc-table-nfs', 'data'),
    Output('doc-table-nfs', 'columns'),
    Input('filter-date', 'start_date'),
    Input('filter-date', 'end_date'),
    Input('filter-ano', 'value'),
    Input('filter-cliente', 'value'),
    Input('filter-produto', 'value'),
    Input('filter-valor-min', 'value'),
    Input('filter-valor-max', 'value'),
)
def update_documentos(start_date, end_date, anos, cliente, produto, valor_min, valor_max):
    df_raw, df_liquid = load_data()

    df_raw_f = apply_filters(df_raw, start_date, end_date, anos, cliente, produto, valor_min, valor_max)
    df_liq_f = apply_filters(df_liquid, start_date, end_date, anos, cliente, produto, valor_min, valor_max)
    df_show = df_raw_f

    # ── KPIs ──
    from components.kpis import kpi_card, kpi_grid
    nfs_bruto = df_raw_f['Num. Docto.'].nunique()
    nfs_liq = df_liq_f['Num. Docto.'].nunique()
    rec_bruta = df_raw_f['Vlr.Total'].sum()
    rec_liq = df_liq_f['Vlr.Total'].sum()
    ret_count = df_raw_f[df_raw_f['Serie'] == 'RET']['Num. Docto.'].nunique()
    ret_val = df_raw_f[df_raw_f['Serie'] == 'RET']['Vlr.Total'].sum()
    ticket = df_raw_f.groupby('Num. Docto.')['Vlr.Total'].sum().mean() if nfs_bruto > 0 else 0

    kpis = kpi_grid([
        kpi_card('NFs Emitidas (bruto)', nfs_bruto, '🧾', None, 'todas as séries', value_fmt='int'),
        kpi_card('NFs Líquidas', nfs_liq, '✅', None, 'excluindo RET e DAV', value_fmt='int'),
        kpi_card('Receita Bruta', rec_bruta, '💰'),
        kpi_card('Receita Líquida', rec_liq, '✅'),
        kpi_card('Cancelamentos (RET)', ret_count, '🚫', None, f'= {fmt_brl(ret_val)}', value_fmt='int'),
        kpi_card('Ticket Médio NF', ticket, '🎯'),
    ])

    # ── Volume mensal por série ──
    vol = df_raw_f.groupby(['AnoMesStr', 'Serie'])['Num. Docto.'].nunique().unstack(fill_value=0).reset_index()
    serie_cores = {'RPS': COLORS['primary'], '1': COLORS['info'], 'RET': COLORS['danger'], 'DAV': COLORS['warning']}
    fig_vol = go.Figure()
    for s in ['RPS', '1', 'RET', 'DAV']:
        if s in vol.columns:
            fig_vol.add_trace(go.Bar(
                x=vol['AnoMesStr'], y=vol[s],
                name=s,
                marker_color=serie_cores.get(s, COLORS['text_muted']),
                hovertemplate=f'<b>%{{x}} · {s}</b><br>NFs: %{{y}}<extra></extra>',
            ))
    fig_vol.update_layout(
        barmode='stack',
        title='Volume de NFs por Mês e Série',
        xaxis_title='', yaxis_title='Quantidade de NFs',
        legend=dict(orientation='h', y=1.1),
        height=280,
    )

    # ── Histograma de valor ──
    nf_vals = df_liq_f.groupby('Num. Docto.')['Vlr.Total'].sum()
    nf_vals = nf_vals[nf_vals > 0]
    fig_hist = go.Figure(go.Histogram(
        x=nf_vals.clip(upper=nf_vals.quantile(0.98)),
        nbinsx=50,
        marker_color=COLORS['primary'],
        marker_opacity=0.8,
        hovertemplate='R$ %{x:,.0f}<br>Qtd NFs: %{y}<extra></extra>',
    ))
    fig_hist.update_layout(
        title='Distribuição de Valor por NF (excluindo outliers top 2%)',
        xaxis_title='Valor da NF (R$)',
        yaxis_title='Quantidade',
        height=280,
    )

    # ── RET/DAV ao longo do tempo ──
    df_ret = df_raw_f[df_raw_f['Serie'].isin(['RET', 'DAV'])]
    df_brut_m = df_raw_f.groupby('AnoMesStr')['Vlr.Total'].sum().reset_index()
    df_ret_m = df_ret.groupby('AnoMesStr')['Vlr.Total'].sum().reset_index() if not df_ret.empty else pd.DataFrame(columns=['AnoMesStr', 'Vlr.Total'])

    fig_ret = go.Figure()
    fig_ret.add_trace(go.Bar(
        x=df_brut_m['AnoMesStr'], y=df_brut_m['Vlr.Total'],
        name='Receita Bruta', marker_color=COLORS['primary'], marker_opacity=0.6,
        hovertemplate='<b>%{x}</b><br>Bruta: R$ %{y:,.0f}<extra></extra>',
    ))
    if not df_ret_m.empty:
        fig_ret.add_trace(go.Bar(
            x=df_ret_m['AnoMesStr'], y=df_ret_m['Vlr.Total'],
            name='RET/DAV', marker_color=COLORS['danger'],
            hovertemplate='<b>%{x}</b><br>Cancelamentos: R$ %{y:,.0f}<extra></extra>',
        ))
    fig_ret.update_layout(
        barmode='overlay',
        title='Impacto de Cancelamentos (RET/DAV) sobre Receita',
        xaxis_title='', yaxis_title='R$',
        yaxis_tickformat=',.0f',
        legend=dict(orientation='h', y=1.1),
        height=260,
    )

    # ── Ticket médio por mês ──
    ticket_m = df_liq_f.groupby('AnoMesStr').apply(
        lambda g: g.groupby('Num. Docto.')['Vlr.Total'].sum().mean()
    ).reset_index()
    ticket_m.columns = ['AnoMes', 'TicketMedio']

    fig_ticket = go.Figure(go.Scatter(
        x=ticket_m['AnoMes'], y=ticket_m['TicketMedio'],
        mode='lines+markers',
        line=dict(color=COLORS['warning'], width=2.5),
        marker=dict(size=5),
        fill='tozeroy', fillcolor='rgba(245,158,11,0.06)',
        hovertemplate='<b>%{x}</b><br>Ticket Médio: R$ %{y:,.0f}<extra></extra>',
    ))
    fig_ticket.update_layout(
        title='Ticket Médio por NF ao Longo do Tempo',
        xaxis_title='', yaxis_title='R$',
        yaxis_tickformat=',.0f',
        height=260,
    )

    # ── Tabela de NFs ──
    nfs_agg = df_show.groupby('Num. Docto.').agg(
        Data=('Emissao', 'first'),
        Serie=('Serie', 'first'),
        Cliente=('Nome', 'first'),
        Itens=('Descricao', 'count'),
        Valor=('Vlr.Total', 'sum'),
        Servicos=('Descricao', lambda x: ', '.join(x.unique()[:3])),
    ).reset_index().sort_values('Data', ascending=False)

    nfs_agg['Data'] = nfs_agg['Data'].dt.strftime('%d/%m/%Y')
    nfs_agg['Valor Fmt'] = nfs_agg['Valor'].map(lambda v: f'R$ {v:,.0f}')

    records = nfs_agg.rename(columns={
        'Num. Docto.': 'Número NF',
        'Valor Fmt': 'Valor Total',
        'Servicos': 'Serviços (resumo)',
    })[['Número NF', 'Data', 'Serie', 'Cliente', 'Itens', 'Valor Total', 'Serviços (resumo)']].to_dict('records')

    columns = [{'name': c, 'id': c, 'type': 'text'} for c in records[0].keys()] if records else []

    return kpis, fig_vol, fig_hist, fig_ret, fig_ticket, records, columns


@callback(
    Output('doc-nf-detail', 'children'),
    Input('doc-table-nfs', 'active_cell'),
    Input('doc-table-nfs', 'data'),
    Input('filter-date', 'start_date'),
    Input('filter-date', 'end_date'),
)
def show_nf_detail(active_cell, table_data, start_date, end_date):
    if not active_cell or not table_data:
        return html.Div(
            '👆 Clique em uma NF para ver todos os seus itens.',
            style={'color': COLORS['text_muted'], 'padding': '16px', 'fontSize': '13px'},
        )

    row = table_data[active_cell['row']]
    num_nf = row['Número NF']

    df_raw, _ = load_data()
    df_nf = df_raw[df_raw['Num. Docto.'] == num_nf]

    if df_nf.empty:
        return html.Div('NF não encontrada.', style={'color': COLORS['text_muted']})

    itens = df_nf[['Produto', 'Descricao', 'Quantidade', 'Vlr.Unitario', 'Vlr.Total']].copy()
    itens['Vlr.Unitario'] = itens['Vlr.Unitario'].map(lambda v: f'R$ {v:,.4f}')
    itens['Vlr.Total'] = itens['Vlr.Total'].map(lambda v: f'R$ {v:,.2f}')
    itens['Quantidade'] = itens['Quantidade'].map(lambda v: f'{int(v):,}')

    detail_table = dash_table.DataTable(
        data=itens.rename(columns={
            'Produto': 'Cód. Produto', 'Descricao': 'Descrição',
            'Vlr.Unitario': 'Vlr. Unitário', 'Vlr.Total': 'Vlr. Total',
        }).to_dict('records'),
        columns=[{'name': c, 'id': c} for c in ['Cód. Produto', 'Descrição', 'Quantidade', 'Vlr. Unitário', 'Vlr. Total']],
        sort_action='native',
        **_CELL,
    )

    total_nf = df_nf['Vlr.Total'].sum()
    cliente_nf = df_nf['Nome'].iloc[0]
    data_nf = df_nf['Emissao'].iloc[0].strftime('%d/%m/%Y')
    serie_nf = df_nf['Serie'].iloc[0]

    return html.Div([
        html.Div([
            html.Div(f'NF {num_nf} · {serie_nf}', style={'fontSize': '15px', 'fontWeight': '700', 'color': COLORS['text']}),
            html.Div(f'{cliente_nf} · {data_nf} · {fmt_brl(total_nf)}', style={'color': COLORS['text_secondary'], 'fontSize': '13px', 'marginTop': '4px'}),
        ], style={'marginBottom': '16px'}),
        detail_table,
    ], className='chart-card')
