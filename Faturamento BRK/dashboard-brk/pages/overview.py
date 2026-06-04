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
    MESES_LABEL = {1:'Jan',2:'Fev',3:'Mar',4:'Abr',5:'Mai',6:'Jun',
                   7:'Jul',8:'Ago',9:'Set',10:'Out',11:'Nov',12:'Dez'}
    df_all = get_liquid()
    df = apply_filters(df_all, start_date, end_date, anos, cliente, produto, valor_min, valor_max)


    # ── KPIs ──
    monthly = df.groupby('AnoMesStr', observed=True)['Vlr.Total'].sum().sort_index()
    n = len(monthly)

    # 1. Receita Líquida
    receita_liquida = float(df[~df['Serie'].astype(str).isin({'RET', 'DAV'})]['Vlr.Total'].sum())

    # 2. MRR — média dos últimos 3 meses
    mrr = float(monthly.iloc[-3:].mean()) if n >= 3 else float(monthly.mean()) if n > 0 else 0.0

    # helper: variação %
    def _var(atual, anterior):
        return (atual - anterior) / anterior * 100 if anterior > 0 else None

    # 3. Crescimento Anual (YoY) — ano atual vs ano anterior completo
    now_ts  = pd.Timestamp(df['Emissao'].max())
    ano_cur = now_ts.year
    df_ano_cur  = df[df['Ano'] == ano_cur]
    df_ano_prev = df[df['Ano'] == ano_cur - 1]
    fat_ano     = float(df_ano_cur['Vlr.Total'].sum())
    fat_ano_ant = float(df_ano_prev['Vlr.Total'].sum())
    delta_ano   = _var(fat_ano, fat_ano_ant)

    # 4. Crescimento Semestral — últimos 6M vs 6M anteriores
    fat_6m      = float(monthly.iloc[-6:].sum())  if n >= 6  else float(monthly.sum())
    fat_6m_prev = float(monthly.iloc[-12:-6].sum()) if n >= 12 else float(monthly.iloc[:-6].sum()) if n >= 7 else 0.0
    delta_6m    = _var(fat_6m, fat_6m_prev)

    # 5. Crescimento Trimestral — últimos 3M vs 3M anteriores
    fat_3m      = float(monthly.iloc[-3:].sum())  if n >= 3 else float(monthly.sum())
    fat_3m_prev = float(monthly.iloc[-6:-3].sum()) if n >= 6 else float(monthly.iloc[:-3].sum()) if n >= 4 else 0.0
    delta_3m    = _var(fat_3m, fat_3m_prev)

    # 6. Crescimento Mensal — último mês vs mês anterior
    fat_1m      = float(monthly.iloc[-1]) if n >= 1 else 0.0
    fat_1m_prev = float(monthly.iloc[-2]) if n >= 2 else 0.0
    delta_1m    = _var(fat_1m, fat_1m_prev)

    # 7. Clientes no período selecionado
    clientes_periodo = int(df['GrupoEcon'].nunique())

    # 8. Clientes faturados no último mês
    ultimo_mes = monthly.index[-1] if n >= 1 else None
    clientes_ult_mes = int(
        df[df['AnoMesStr'].astype(str) == ultimo_mes]['GrupoEcon'].nunique()
    ) if ultimo_mes else 0

    # 9. Ticket médio por cliente/mês
    if clientes_periodo > 0 and n > 0:
        ticket_cliente_mes = float(df['Vlr.Total'].sum()) / clientes_periodo / n
    else:
        ticket_cliente_mes = 0.0

    # 10. Ticket médio dos Top 5 serviços/mês
    top5_svc = (
        df.groupby('Descricao', observed=True)['Vlr.Total'].sum()
        .nlargest(5).index
    )
    ticket_top5 = float(
        df[df['Descricao'].isin(top5_svc)]
        .groupby(['Descricao', 'AnoMesStr'], observed=True)['Vlr.Total'].sum()
        .groupby('Descricao', observed=True).mean()
        .mean()
    ) if len(top5_svc) > 0 and n > 0 else 0.0

    cards = kpi_grid([
        kpi_card('Receita Líquida',          receita_liquida,    '✅', None,      'excluindo RET e DAV'),
        kpi_card('MRR',                      mrr,                '📅', None,      'média últimos 3 meses'),
        kpi_card('Faturado no Ano',          fat_ano,            '📆', delta_ano, f'vs. {ano_cur - 1} completo'),
        kpi_card('Faturado 6 Meses',         fat_6m,             '📊', delta_6m,  'vs. 6 meses anteriores'),
        kpi_card('Faturado Trimestre',       fat_3m,             '📈', delta_3m,  'vs. trimestre anterior'),
        kpi_card('Faturado Mês',             fat_1m,             '🗓️', delta_1m,  'vs. mês anterior'),
        kpi_card('Clientes no Período',      clientes_periodo,   '🏢', None,      'grupos econômicos ativos', value_fmt='int'),
        kpi_card('Clientes Último Mês',      clientes_ult_mes,   '👥', None,      f'faturados em {ultimo_mes or "—"}', value_fmt='int'),
        kpi_card('Ticket Médio Cliente/Mês', ticket_cliente_mes, '🎯', None,      'receita ÷ clientes ÷ meses'),
        kpi_card('Ticket Top 5 Serviços/Mês',ticket_top5,       '🏆', None,      'média mensal dos 5 maiores serviços'),
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
    # Usa numero do mes no eixo X para garantir ordem cronologica correta
    MESES_LABEL = {1:'Jan',2:'Fev',3:'Mar',4:'Abr',5:'Mai',6:'Jun',
                   7:'Jul',8:'Ago',9:'Set',10:'Out',11:'Nov',12:'Dez'}
    df['AnoNum'] = df['Ano'].astype(int)
    yoy = df.groupby(['AnoNum', 'Mes'])['Vlr.Total'].sum().reset_index()
    fig_yoy = go.Figure()
    anos_list = sorted(yoy['AnoNum'].unique())
    for i, ano in enumerate(anos_list):
        d = yoy[yoy['AnoNum'] == ano].sort_values('Mes')
        color = CHART_COLORS[i % len(CHART_COLORS)]
        dash_style = 'dot' if ano == max(anos_list) else 'solid'
        fig_yoy.add_trace(go.Scatter(
            x=d['Mes'], y=d['Vlr.Total'],          # numero do mes — ordem garantida
            name=str(ano), mode='lines+markers',
            line=dict(color=color, width=2, dash=dash_style),
            marker=dict(size=5),
            customdata=d['Mes'].map(MESES_LABEL),
            hovertemplate=f'<b>{ano}</b> %{{customdata}}<br>R$ %{{y:,.0f}}<extra></extra>',
        ))
    fig_yoy.update_layout(
        title='Comparativo Anual (YoY)',
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, 13)),
            ticktext=list(MESES_LABEL.values()),   # Jan, Fev, ... Dez
            title='',
        ),
        yaxis_title='R$',
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
    client_rev = df.groupby('GrupoEcon')['Vlr.Total'].sum().sort_values(ascending=False).reset_index()
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
    # Reindexar para garantir todos os meses em ordem (1-12)
    pivot = pivot.reindex(columns=range(1, 13), fill_value=0)
    meses_cols = [MESES_LABEL.get(c, str(c)) for c in pivot.columns]
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
            color = CHART_COLORS[i % len(CHART_COLORS)]
            dash_style = 'dot' if ano == max(anos_disponiveis) else 'solid'
            fill = 'tozeroy' if ano == max(anos_disponiveis) else 'none'
            fig_cum.add_trace(go.Scatter(
                x=d['Mes'], y=d['Vlr.Total'],   # numero do mes — ordem cronologica
                name=str(ano), mode='lines',
                line=dict(color=color, width=2.5, dash=dash_style),
                fill=fill,
                fillcolor=f'rgba(255,101,0,0.08)' if fill != 'none' else None,
                customdata=d['Mes'].map(MESES_LABEL),
                hovertemplate=f'<b>{ano}</b> %{{customdata}}<br>Acumulado: R$ %{{y:,.0f}}<extra></extra>',
            ))
    fig_cum.update_layout(
        title='Receita Acumulada no Ano (Running Total)',
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, 13)),
            ticktext=list(MESES_LABEL.values()),
            title='',
        ),
        yaxis_title='R$',
        yaxis_tickformat=',.0f',
        legend=dict(orientation='h', y=1.1),
        height=320,
    )

    return cards, insights, fig_monthly, fig_yoy, fig_treemap, fig_conc, fig_heat, fig_cum
