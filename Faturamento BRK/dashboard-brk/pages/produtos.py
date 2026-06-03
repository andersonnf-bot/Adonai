import dash
from dash import html, dcc, callback, Input, Output, dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from data.loader import get_liquid, apply_filters
from components.theme import COLORS, fmt_brl, CHART_COLORS

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
        html.Div('Produtos & Serviços', className='page-title'),
        html.Div('Análise completa do portfólio · 204 serviços', className='page-subtitle'),
    ], className='page-header'),

    html.Div([
        html.Div([
            html.Div([
                html.Div('Matriz de Portfólio', className='chart-title'),
                html.Div('Receita × Crescimento M/M × Volume — todos os serviços', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='produtos-bubble', config={'displayModeBar': False}, style={'height': '450px'}),
        ], className='chart-card'),

        html.Div([
            html.Div([
                html.Div('Ranking Completo de Serviços', className='chart-title'),
                html.Div('Ordenável · todos os 204 serviços', className='chart-subtitle'),
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
    Input('filter-date', 'start_date'),
    Input('filter-date', 'end_date'),
    Input('filter-ano', 'value'),
    Input('filter-cliente', 'value'),
    Input('filter-produto', 'value'),
    Input('filter-valor-min', 'value'),
    Input('filter-valor-max', 'value'),
)
def update_produtos(start_date, end_date, anos, cliente, produto, valor_min, valor_max):
    df_all = get_liquid()
    df = apply_filters(df_all, start_date, end_date, anos, cliente, produto, valor_min, valor_max)

    if df.empty:
        empty_fig = go.Figure()
        empty_fig.update_layout(title='Sem dados')
        return empty_fig, [], []

    monthly = df.groupby(['Descricao', 'AnoMesStr'])['Vlr.Total'].sum().unstack(fill_value=0)
    months_sorted = sorted(monthly.columns)
    monthly = monthly[months_sorted]

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
            return '🚀 Crescendo'
        if pd.notna(row['var_mom']) and row['var_mom'] <= -15:
            return '📉 Em queda'
        if row['clientes'] == 1:
            return '⚠️ Mono-cliente'
        return '➡️ Estável'

    agg['Status'] = agg.apply(status_svc, axis=1)
    agg = agg.sort_values('receita', ascending=False).reset_index(drop=True)
    agg['Rank'] = agg.index + 1

    # Bubble chart
    bubble_data = agg[agg['receita'] > 0].copy()
    bubble_data['var_mom_clean'] = bubble_data['var_mom'].fillna(0)
    bubble_data['label_short'] = bubble_data['Descricao'].str[:30]

    color_vals = bubble_data['var_mom_clean'].clip(-50, 50)

    fig_bubble = go.Figure(go.Scatter(
        x=bubble_data['receita'] / 1_000_000,
        y=bubble_data['var_mom_clean'],
        mode='markers+text',
        marker=dict(
            size=np.sqrt(bubble_data['quantidade'].clip(1)) * 0.8,
            sizemode='area',
            sizeref=2. * bubble_data['quantidade'].clip(1).max() ** 0.5 / (60 ** 2),
            color=color_vals,
            colorscale=[
                [0, COLORS['danger']],
                [0.5, COLORS['text_muted']],
                [1, COLORS['success']],
            ],
            showscale=True,
            colorbar=dict(title='Var M/M %', tickfont=dict(color=COLORS['text_secondary'])),
            line=dict(color=COLORS['border'], width=0.5),
        ),
        text=bubble_data['label_short'],
        textfont=dict(size=9, color=COLORS['text_secondary']),
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
    fig_bubble.add_hline(y=0, line_dash='dot', line_color=COLORS['border'])
    fig_bubble.update_layout(
        title='Matriz Portfólio · Receita (R$MM) × Crescimento M/M% × Volume',
        xaxis_title='Receita Total (R$ MM)',
        yaxis_title='Variação M/M (%)',
        height=430,
        xaxis=dict(tickformat='.1f'),
    )

    # Table
    records = []
    for _, r in agg.iterrows():
        records.append({
            '#': int(r['Rank']),
            'Serviço': r['Descricao'],
            'Receita Total': f"R$ {r['receita']:,.0f}",
            '% Portfólio': f"{r['pct']:.2f}%",
            'Último Mês': f"R$ {r['ult_mes']:,.0f}" if pd.notna(r.get('ult_mes')) else '—',
            'Var. M/M': f"{r['var_mom']:+.1f}%" if pd.notna(r['var_mom']) else '—',
            'Var. 3M': f"{r['var_3m']:+.1f}%" if pd.notna(r['var_3m']) else '—',
            'Clientes': int(r['clientes']),
            'Ticket Médio': f"R$ {r['ticket']:,.2f}" if pd.notna(r['ticket']) else '—',
            'Status': r['Status'],
        })

    columns = [{'name': c, 'id': c} for c in records[0].keys()] if records else []
    return fig_bubble, records, columns


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
)
def update_produto_detail(active_cell, table_data, start_date, end_date, anos, cliente, valor_min, valor_max):
    if not active_cell or not table_data:
        return html.Div(
            '👆 Clique em um serviço na tabela para análise detalhada.',
            style={'color': COLORS['text_muted'], 'padding': '16px', 'fontSize': '13px'},
        )

    row = table_data[active_cell['row']]
    servico = row['Serviço']

    df_all = get_liquid()
    df_base = apply_filters(df_all, start_date, end_date, anos, cliente, None, valor_min, valor_max)

    df_svc = df_base[df_base['Descricao'] == servico]
    if df_svc.empty:
        return html.Div('Sem dados para este serviço no período.', style={'color': COLORS['text_muted']})

    # Evolução mensal
    monthly = df_svc.groupby('AnoMesStr').agg(
        receita=('Vlr.Total', 'sum'),
        quantidade=('Quantidade', 'sum'),
        ticket=('Vlr.Unitario', 'mean'),
    ).sort_index().reset_index()

    fig_evo = go.Figure()
    fig_evo.add_trace(go.Bar(
        x=monthly['AnoMesStr'], y=monthly['receita'],
        name='Receita', marker_color=COLORS['primary'], marker_opacity=0.85,
        yaxis='y',
        hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>',
    ))
    fig_evo.add_trace(go.Scatter(
        x=monthly['AnoMesStr'], y=monthly['quantidade'],
        name='Qtd', line=dict(color=COLORS['info'], width=2),
        yaxis='y2', mode='lines+markers', marker=dict(size=4),
        hovertemplate='<b>%{x}</b><br>Qtd: %{y:,.0f}<extra></extra>',
    ))
    fig_evo.update_layout(
        title=f'Evolução Mensal · {servico}',
        yaxis=dict(title='Receita (R$)', tickformat=',.0f'),
        yaxis2=dict(title='Quantidade', overlaying='y', side='right', showgrid=False),
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
        title='Ticket Médio ao Longo do Tempo (detectar reajustes)',
        xaxis_title='', yaxis_title='R$ / unidade',
        yaxis_tickformat=',.2f',
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
        data=cli_svc[['Nome', 'Receita', '%', 'quantidade', 'nfs']].rename(
            columns={'Nome': 'Cliente', 'quantidade': 'Qtd', 'nfs': 'NFs'}
        ).to_dict('records'),
        columns=[{'name': c, 'id': c} for c in ['Cliente', 'Receita', '%', 'Qtd', 'NFs']],
        page_size=15,
        sort_action='native',
        **_CELL,
    )

    receita_total_svc = df_svc['Vlr.Total'].sum()
    clientes_count = df_svc['GrupoEcon'].nunique()

    return html.Div([
        html.Div([
            html.Div(servico, style={'fontSize': '16px', 'fontWeight': '700', 'color': COLORS['text']}),
            html.Div([
                html.Span(fmt_brl(receita_total_svc), style={'fontSize': '20px', 'fontWeight': '700', 'color': COLORS['primary']}),
                html.Span(f' · {clientes_count} clientes ativos', style={'fontSize': '13px', 'color': COLORS['text_secondary'], 'marginLeft': '8px'}),
            ]),
        ], style={'marginBottom': '20px', 'paddingBottom': '16px', 'borderBottom': f'1px solid {COLORS["border"]}'}),

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
                    html.Div('Todos os Clientes que Contratam este Serviço', className='chart-title'),
                ], className='chart-card-header'),
                cli_table,
            ], className='chart-card'),
        ]),
    ], className='chart-card')
