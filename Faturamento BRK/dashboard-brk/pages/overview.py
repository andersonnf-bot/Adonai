import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from data.loader import get_liquid, apply_filters
from components.kpis import kpi_card, kpi_grid
from components.insights import insight_panel
from components.theme import COLORS, fmt_brl, CHART_COLORS

dash.register_page(__name__, path='/', name='Visão Executiva', order=0)

layout = html.Div([
    html.Div([
        html.Div([
            html.Div('Visão Executiva', className='page-title'),
            html.Div('Consolidado de faturamento · BRK Nstech', className='page-subtitle'),
        ]),
        html.Span('', id='overview-partial-tag'),
    ], className='page-header', style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'flex-start'}),

    html.Div(id='overview-insights'),
    html.Div(id='overview-kpis'),

    html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Div('Receita Mensal', className='chart-title'),
                    html.Div('Evolução com linha de tendência · barras por série', className='chart-subtitle'),
                ]),
            ], className='chart-card-header'),
            dcc.Graph(id='overview-chart-monthly', config={'displayModeBar': False}),
        ], className='chart-card'),

        html.Div([
            html.Div([
                html.Div([
                    html.Div('YoY · Comparativo Anual', className='chart-title'),
                    html.Div('Receita mensal sobreposta por ano', className='chart-subtitle'),
                ]),
            ], className='chart-card-header'),
            dcc.Graph(id='overview-chart-yoy', config={'displayModeBar': False}),
        ], className='chart-card'),
    ], className='grid-2'),

    html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Div('Composição por Serviço', className='chart-title'),
                    html.Div('Treemap · todos os 204 serviços', className='chart-subtitle'),
                ]),
            ], className='chart-card-header'),
            dcc.Graph(id='overview-chart-treemap', config={'displayModeBar': False}, style={'height': '420px'}),
        ], className='chart-card'),

        html.Div([
            html.Div([
                html.Div([
                    html.Div('Concentração de Clientes', className='chart-title'),
                    html.Div('Distribuição da receita por faixa de cliente', className='chart-subtitle'),
                ]),
            ], className='chart-card-header'),
            dcc.Graph(id='overview-chart-concentration', config={'displayModeBar': False}, style={'height': '420px'}),
        ], className='chart-card'),
    ], className='grid-2'),

    html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Div('Heatmap · Receita por Mês × Ano', className='chart-title'),
                    html.Div('Identifica sazonalidade e variações históricas', className='chart-subtitle'),
                ]),
            ], className='chart-card-header'),
            dcc.Graph(id='overview-chart-heatmap', config={'displayModeBar': False}),
        ], className='chart-card'),

        html.Div([
            html.Div([
                html.Div([
                    html.Div('Acumulado do Ano', className='chart-title'),
                    html.Div('Running total · ano atual vs. anterior', className='chart-subtitle'),
                ]),
            ], className='chart-card-header'),
            dcc.Graph(id='overview-chart-cumulative', config={'displayModeBar': False}),
        ], className='chart-card'),
    ], className='grid-2'),

], id='page-content')


@callback(
    Output('overview-kpis', 'children'),
    Output('overview-insights', 'children'),
    Output('overview-chart-monthly', 'figure'),
    Output('overview-chart-yoy', 'figure'),
    Output('overview-chart-treemap', 'figure'),
    Output('overview-chart-concentration', 'figure'),
    Output('overview-chart-heatmap', 'figure'),
    Output('overview-chart-cumulative', 'figure'),
    Input('filter-date', 'start_date'),
    Input('filter-date', 'end_date'),
    Input('filter-ano', 'value'),
    Input('filter-cliente', 'value'),
    Input('filter-produto', 'value'),
    Input('filter-valor-min', 'value'),
    Input('filter-valor-max', 'value'),
)
def update_overview(start_date, end_date, anos, cliente, produto, valor_min, valor_max):
    df_all = get_liquid()
    df = apply_filters(df_all, start_date, end_date, anos, cliente, produto, valor_min, valor_max)


    # ── KPIs ──
    receita_total = df['Vlr.Total'].sum()
    receita_liquida = df[~df['Serie'].isin({'RET', 'DAV'})]['Vlr.Total'].sum()
    clientes_ativos = df['Nome'].nunique()
    nfs = df['Num. Docto.'].nunique()
    itens = len(df)
    ticket_medio = df.groupby('Num. Docto.')['Vlr.Total'].sum().mean() if nfs > 0 else 0
    qtd_total = df['Quantidade'].sum()
    servicos_distintos = df['Descricao'].nunique()

    monthly = df.groupby('AnoMesStr')['Vlr.Total'].sum().sort_index()
    mrr = monthly.iloc[-3:].mean() if len(monthly) >= 3 else monthly.mean()

    delta_receita = None
    if len(monthly) >= 2:
        half = len(monthly) // 2
        first_half = monthly.iloc[:half].sum()
        second_half = monthly.iloc[half:].sum()
        if first_half > 0:
            delta_receita = (second_half - first_half) / first_half * 100

    cards = kpi_grid([
        kpi_card('Receita Total', receita_total, '💰', delta_receita, 'vs. metade anterior do período'),
        kpi_card('Receita Líquida', receita_liquida, '✅', None, 'excluindo RET e DAV'),
        kpi_card('MRR', mrr, '📅', None, 'média últimos 3 meses'),
        kpi_card('Clientes Ativos', clientes_ativos, '🏢', None, 'com ao menos 1 NF', value_fmt='int'),
        kpi_card('NFs Emitidas', nfs, '🧾', None, 'no período', value_fmt='int'),
        kpi_card('Itens Faturados', itens, '📋', None, 'linhas de NF', value_fmt='int'),
        kpi_card('Ticket Médio NF', ticket_medio, '🎯'),
        kpi_card('Unidades Faturadas', qtd_total, '📦', None, 'total de UN', value_fmt='int'),
        kpi_card('Serviços Distintos', servicos_distintos, '⚙️', None, 'produtos faturados', value_fmt='int'),
    ])

    insights = insight_panel(df)

    # ── Gráfico Mensal ──
    monthly_full = df.groupby('AnoMesStr')['Vlr.Total'].sum().reset_index()
    monthly_full.columns = ['Mês', 'Receita']
    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(
        x=monthly_full['Mês'], y=monthly_full['Receita'],
        name='Receita', marker_color=COLORS['primary'],
        marker_opacity=0.85,
        hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>',
    ))
    if len(monthly_full) >= 3:
        z = np.polyfit(range(len(monthly_full)), monthly_full['Receita'], 1)
        trend = np.poly1d(z)(range(len(monthly_full)))
        fig_monthly.add_trace(go.Scatter(
            x=monthly_full['Mês'], y=trend,
            name='Tendência', line=dict(color=COLORS['info'], width=2, dash='dot'),
            hovertemplate='Tendência: R$ %{y:,.0f}<extra></extra>',
        ))
    fig_monthly.update_layout(
        title='Receita Mensal com Tendência',
        xaxis_title='', yaxis_title='R$',
        yaxis_tickformat=',.0f',
        legend=dict(orientation='h', y=1.1),
        height=320,
    )

    # ── YoY ──
    df['AnoNum'] = df['Ano'].astype(int)
    yoy = df.groupby(['AnoNum', 'Mes'])['Vlr.Total'].sum().reset_index()
    meses_label = {1:'Jan',2:'Fev',3:'Mar',4:'Abr',5:'Mai',6:'Jun',
                   7:'Jul',8:'Ago',9:'Set',10:'Out',11:'Nov',12:'Dez'}
    yoy['MesLabel'] = yoy['Mes'].map(meses_label)
    fig_yoy = go.Figure()
    anos_list = sorted(yoy['AnoNum'].unique())
    for i, ano in enumerate(anos_list):
        d = yoy[yoy['AnoNum'] == ano].sort_values('Mes')
        color = CHART_COLORS[i % len(CHART_COLORS)]
        dash_style = 'dot' if ano == max(anos_list) else 'solid'
        fig_yoy.add_trace(go.Scatter(
            x=d['MesLabel'], y=d['Vlr.Total'],
            name=str(ano), mode='lines+markers',
            line=dict(color=color, width=2, dash=dash_style),
            marker=dict(size=5),
            hovertemplate=f'<b>{ano}</b> %{{x}}<br>R$ %{{y:,.0f}}<extra></extra>',
        ))
    fig_yoy.update_layout(
        title='Comparativo Anual (YoY)',
        xaxis_title='', yaxis_title='R$',
        yaxis_tickformat=',.0f',
        legend=dict(orientation='h', y=1.1),
        height=320,
    )

    # ── Treemap ──
    treemap_data = df.groupby('Descricao')['Vlr.Total'].sum().reset_index()
    treemap_data = treemap_data[treemap_data['Vlr.Total'] > 0].sort_values('Vlr.Total', ascending=False)
    treemap_data['text'] = treemap_data.apply(
        lambda r: f"{r['Descricao']}<br>{fmt_brl(r['Vlr.Total'])}", axis=1
    )
    fig_treemap = go.Figure(go.Treemap(
        labels=treemap_data['Descricao'],
        parents=[''] * len(treemap_data),
        values=treemap_data['Vlr.Total'],
        textinfo='label+value',
        texttemplate='%{label}<br>R$ %{value:,.0f}',
        hovertemplate='<b>%{label}</b><br>Receita: R$ %{value:,.0f}<br>Participação: %{percentRoot:.1%}<extra></extra>',
        marker=dict(
            colorscale=[[0, COLORS['surface2']], [0.3, COLORS['primary_dark']], [1, COLORS['primary']]],
            showscale=False,
        ),
    ))
    fig_treemap.update_layout(title='Composição por Serviço · Todos os Serviços', height=400, margin=dict(t=40, l=0, r=0, b=0))

    # ── Concentração ──
    client_rev = df.groupby('Nome')['Vlr.Total'].sum().sort_values(ascending=False).reset_index()
    client_rev['rank'] = range(1, len(client_rev) + 1)
    client_rev['cumsum'] = client_rev['Vlr.Total'].cumsum()
    client_rev['cumpct'] = client_rev['cumsum'] / client_rev['Vlr.Total'].sum() * 100

    faixas = ['Top 1', 'Top 2-10', 'Top 11-50', 'Top 51-100', 'Demais']
    slices = [
        client_rev.iloc[:1]['Vlr.Total'].sum(),
        client_rev.iloc[1:10]['Vlr.Total'].sum(),
        client_rev.iloc[10:50]['Vlr.Total'].sum(),
        client_rev.iloc[50:100]['Vlr.Total'].sum(),
        client_rev.iloc[100:]['Vlr.Total'].sum(),
    ]
    fig_conc = go.Figure(go.Pie(
        labels=faixas, values=slices,
        hole=0.55,
        marker=dict(colors=[COLORS['danger'], COLORS['warning'], COLORS['primary'], COLORS['info'], COLORS['text_muted']]),
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>R$ %{value:,.0f}<br>%{percent}<extra></extra>',
    ))
    fig_conc.update_layout(
        title='Distribuição de Receita por Faixa de Cliente',
        showlegend=True,
        legend=dict(orientation='v'),
        height=400,
        annotations=[dict(text=f'{len(client_rev)}<br>clientes', x=0.5, y=0.5,
                          font=dict(size=14, color=COLORS['text']), showarrow=False)],
    )

    # ── Heatmap ──
    pivot = df.groupby(['Ano', 'Mes'])['Vlr.Total'].sum().unstack(fill_value=0)
    meses_cols = [meses_label.get(c, str(c)) for c in pivot.columns]
    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values / 1_000_000,
        x=meses_cols,
        y=[str(int(a)) for a in pivot.index],
        colorscale=[[0, COLORS['surface2']], [0.5, COLORS['primary_dark']], [1, COLORS['primary']]],
        hovertemplate='<b>%{y} · %{x}</b><br>R$ %{z:.2f}M<extra></extra>',
        text=[[f'R$ {v:.1f}M' for v in row] for row in pivot.values / 1_000_000],
        texttemplate='%{text}',
        showscale=True,
        colorbar=dict(tickfont=dict(color=COLORS['text_secondary'])),
    ))
    fig_heat.update_layout(
        title='Heatmap · Receita Mensal por Ano (R$ MM)',
        xaxis_title='', yaxis_title='',
        height=300,
    )

    # ── Acumulado ──
    anos_disponiveis = sorted(df['Ano'].dropna().unique().astype(int))
    fig_cum = go.Figure()
    if len(anos_disponiveis) >= 1:
        for i, ano in enumerate(anos_disponiveis[-3:]):
            d = df[df['Ano'] == ano].groupby('Mes')['Vlr.Total'].sum().sort_index().cumsum().reset_index()
            d['MesLabel'] = d['Mes'].map(meses_label)
            color = CHART_COLORS[i % len(CHART_COLORS)]
            dash_style = 'dot' if ano == max(anos_disponiveis) else 'solid'
            fill = 'tozeroy' if ano == max(anos_disponiveis) else 'none'
            fig_cum.add_trace(go.Scatter(
                x=d['MesLabel'], y=d['Vlr.Total'],
                name=str(ano), mode='lines',
                line=dict(color=color, width=2.5, dash=dash_style),
                fill=fill,
                fillcolor=f'rgba(255,101,0,0.08)' if fill != 'none' else None,
                hovertemplate=f'<b>{ano}</b> %{{x}}<br>Acumulado: R$ %{{y:,.0f}}<extra></extra>',
            ))
    fig_cum.update_layout(
        title='Receita Acumulada no Ano (Running Total)',
        xaxis_title='', yaxis_title='R$',
        yaxis_tickformat=',.0f',
        legend=dict(orientation='h', y=1.1),
        height=320,
    )

    return cards, insights, fig_monthly, fig_yoy, fig_treemap, fig_conc, fig_heat, fig_cum
