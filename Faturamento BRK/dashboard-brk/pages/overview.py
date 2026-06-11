import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from data.loader import get_liquid, apply_filters, last_month_is_partial
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
                    html.Div('Treemap · portfólio completo de serviços', className='chart-subtitle'),
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
                    html.Div('Sazonalidade · Receita Média por Mês', className='chart-title'),
                    html.Div('Padrão histórico — identifica meses fortes e fracos', className='chart-subtitle'),
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
    Output('overview-partial-tag', 'children'),
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

    # Mês parcial (export cortado no meio do mês) sai das comparações:
    # senão MRR, trimestre e var. mensal apontam queda falsa todo início de mês
    parcial = last_month_is_partial(df)
    mes_parcial = str(monthly.index[-1]) if (parcial and n >= 1) else None
    monthly_c = monthly.iloc[:-1] if (parcial and n >= 2) else monthly
    nc = len(monthly_c)

    # 1. Receita Líquida
    receita_liquida = float(df[~df['Serie'].astype(str).isin({'RET', 'DAV'})]['Vlr.Total'].sum())

    # 2. MRR — média dos últimos 3 meses completos
    mrr = float(monthly_c.iloc[-3:].mean()) if nc >= 3 else float(monthly_c.mean()) if nc > 0 else 0.0

    # helper: variação %
    def _var(atual, anterior):
        return (atual - anterior) / anterior * 100 if anterior > 0 else None

    # 3. Crescimento Anual — YTD vs mesmo período do ano anterior
    # (comparar ano parcial contra ano-calendário completo distorce o sinal)
    now_ts  = pd.Timestamp(df['Emissao'].max())
    ano_cur = now_ts.year
    corte_prev  = now_ts - pd.DateOffset(years=1)
    df_ano_cur  = df[df['Ano'] == ano_cur]
    df_ano_prev = df[(df['Ano'] == ano_cur - 1) & (df['Emissao'] <= corte_prev)]
    fat_ano     = float(df_ano_cur['Vlr.Total'].sum())
    fat_ano_ant = float(df_ano_prev['Vlr.Total'].sum())
    delta_ano   = _var(fat_ano, fat_ano_ant)

    # 4. Crescimento Semestral — últimos 6M completos vs 6M anteriores
    fat_6m      = float(monthly_c.iloc[-6:].sum())  if nc >= 6  else float(monthly_c.sum())
    fat_6m_prev = float(monthly_c.iloc[-12:-6].sum()) if nc >= 12 else float(monthly_c.iloc[:-6].sum()) if nc >= 7 else 0.0
    delta_6m    = _var(fat_6m, fat_6m_prev)

    # 5. Crescimento Trimestral — últimos 3M completos vs 3M anteriores
    fat_3m      = float(monthly_c.iloc[-3:].sum())  if nc >= 3 else float(monthly_c.sum())
    fat_3m_prev = float(monthly_c.iloc[-6:-3].sum()) if nc >= 6 else float(monthly_c.iloc[:-3].sum()) if nc >= 4 else 0.0
    delta_3m    = _var(fat_3m, fat_3m_prev)

    # 6. Crescimento Mensal — último mês completo vs anterior
    fat_1m      = float(monthly_c.iloc[-1]) if nc >= 1 else 0.0
    fat_1m_prev = float(monthly_c.iloc[-2]) if nc >= 2 else 0.0
    delta_1m    = _var(fat_1m, fat_1m_prev)

    # 7. Clientes no período selecionado
    clientes_periodo = int(df['GrupoEcon'].nunique())

    # 8. Clientes faturados no último mês completo
    ultimo_mes = monthly_c.index[-1] if nc >= 1 else None
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
        kpi_card('MRR',                      mrr,                '📅', None,      'média últimos 3 meses completos'),
        kpi_card('Faturado no Ano',          fat_ano,            '📆', delta_ano, f'vs. mesmo período de {ano_cur - 1}'),
        kpi_card('Faturado 6 Meses',         fat_6m,             '📊', delta_6m,  'vs. 6 meses anteriores'),
        kpi_card('Faturado Trimestre',       fat_3m,             '📈', delta_3m,  'vs. trimestre anterior'),
        kpi_card('Faturado Mês',             fat_1m,             '🗓️', delta_1m,  f'{ultimo_mes or "—"} vs. mês anterior'),
        kpi_card('Clientes no Período',      clientes_periodo,   '🏢', None,      'grupos econômicos ativos', value_fmt='int'),
        kpi_card('Clientes Último Mês',      clientes_ult_mes,   '👥', None,      f'faturados em {ultimo_mes or "—"}', value_fmt='int'),
        kpi_card('Ticket Médio Cliente/Mês', ticket_cliente_mes, '🎯', None,      'receita ÷ clientes ÷ meses'),
        kpi_card('Ticket Top 5 Serviços/Mês',ticket_top5,       '🏆', None,      'média mensal dos 5 maiores serviços'),
    ])

    insights = insight_panel(df)

    # ── Gráfico Mensal com Tendência + IC + Anotação Anomalia ──
    monthly_full = df.groupby('AnoMesStr', observed=True)['Vlr.Total'].sum().reset_index()
    monthly_full.columns = ['Mês', 'Receita']
    # mês parcial aparece no gráfico (esmaecido), mas fica fora da tendência
    n_fit = len(monthly_full) - (1 if parcial else 0)
    opacidades = [0.85] * len(monthly_full)
    if parcial and len(monthly_full) >= 1:
        opacidades[-1] = 0.35
    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(
        x=monthly_full['Mês'], y=monthly_full['Receita'],
        name='Receita', marker_color=COLORS['primary'],
        marker_opacity=opacidades,
        hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>',
    ))
    if parcial and len(monthly_full) >= 1:
        fig_monthly.add_annotation(
            x=monthly_full['Mês'].iloc[-1], y=float(monthly_full['Receita'].iloc[-1]),
            text='parcial', showarrow=False, yshift=12,
            font=dict(size=10, color=COLORS['text_muted']),
        )
    if n_fit >= 6:
        xs = np.arange(n_fit)
        ys = monthly_full['Receita'].values[:n_fit]
        z    = np.polyfit(xs, ys, 1)
        poly = np.poly1d(z)
        trend  = poly(xs)
        # IC 80% — baseado nos resíduos
        residuos = ys - trend
        std_res  = float(np.std(residuos))
        ic_upper = trend + 1.28 * std_res
        ic_lower = trend - 1.28 * std_res
        # Banda de IC — eixo X recortado nos mesmos meses do ajuste (sem o parcial)
        meses_fit = list(monthly_full['Mês'].iloc[:n_fit])
        fig_monthly.add_trace(go.Scatter(
            x=meses_fit + meses_fit[::-1],
            y=list(ic_upper) + list(ic_lower)[::-1],
            fill='toself', fillcolor='rgba(30,144,255,0.08)',
            line=dict(color='rgba(0,0,0,0)'),
            name='IC 80%', hoverinfo='skip',
        ))
        fig_monthly.add_trace(go.Scatter(
            x=meses_fit, y=trend,
            name='Tendência', line=dict(color=COLORS['info'], width=2, dash='dot'),
            hovertemplate='Tendência: R$ %{y:,.0f}<extra></extra>',
        ))
        # Detecta meses anômalos (> 2,5σ acima da tendência) e anota
        for i, (mes, rec) in enumerate(zip(monthly_full['Mês'], ys)):
            if rec - trend[i] > 2.5 * std_res:
                fig_monthly.add_annotation(
                    x=mes, y=float(rec),
                    text='⚡', showarrow=False,
                    font=dict(size=14), yshift=10,
                    hovertext=f'Pico atípico: R$ {rec/1e6:.1f}M<br>+{(rec-trend[i])/1e6:.1f}M acima da tendência',
                )
    fig_monthly.update_layout(
        title='Receita Mensal · Tendência + IC 80% (⚡ = pico atípico)',
        xaxis_title='', yaxis_title='R$',
        yaxis_tickformat=',.0f',
        # mm/aaaa no eixo e no hover — o padrão do Plotly mostra meses em inglês
        xaxis=dict(tickformat='%m/%Y', hoverformat='%m/%Y'),
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

    # ── Concentração com alerta de risco ──
    client_rev = df.groupby('GrupoEcon', observed=True)['Vlr.Total'].sum().sort_values(ascending=False).reset_index()
    total_rev  = float(client_rev['Vlr.Total'].sum())
    top1_pct   = float(client_rev.iloc[0]['Vlr.Total']) / total_rev * 100 if len(client_rev) > 0 else 0
    top1_nome  = str(client_rev.iloc[0]['GrupoEcon']) if len(client_rev) > 0 else '—'
    top5_pct   = float(client_rev.iloc[:5]['Vlr.Total'].sum()) / total_rev * 100 if len(client_rev) >= 5 else 0
    top10_pct  = float(client_rev.iloc[:10]['Vlr.Total'].sum()) / total_rev * 100 if len(client_rev) >= 10 else 0

    faixas = ['Top 1', 'Top 2-10', 'Top 11-50', 'Top 51-100', 'Demais']
    slices = [
        client_rev.iloc[:1]['Vlr.Total'].sum(),
        client_rev.iloc[1:10]['Vlr.Total'].sum(),
        client_rev.iloc[10:50]['Vlr.Total'].sum(),
        client_rev.iloc[50:100]['Vlr.Total'].sum(),
        client_rev.iloc[100:]['Vlr.Total'].sum(),
    ]
    # Cor do Top1 varia conforme nível de risco
    top1_color = COLORS['danger'] if top1_pct > 10 else COLORS['warning'] if top1_pct > 7 else COLORS['success']
    risco_label = '🔴 Alto' if top1_pct > 10 else '🟡 Moderado' if top1_pct > 7 else '🟢 Saudável'

    # sort=False mantém as fatias na ordem das faixas — senão o Plotly reordena
    # por valor e as cores deixam de corresponder às faixas
    fig_conc = go.Figure(go.Pie(
        labels=faixas, values=slices,
        hole=0.55,
        sort=False, direction='clockwise',
        marker=dict(colors=[top1_color, COLORS['purple'], COLORS['primary'], COLORS['info'], COLORS['text_muted']]),
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>R$ %{value:,.0f}<br>%{percent}<extra></extra>',
    ))
    fig_conc.update_layout(
        title=f'Concentração de Receita · Risco: {risco_label}',
        showlegend=True,
        legend=dict(orientation='v'),
        height=400,
        annotations=[dict(
            text=f'<b>{top1_nome}</b><br>{top1_pct:.1f}%<br>Top 1',
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=11, color=top1_color),
        )],
    )
    # Linha de referência no Pareto — curva de concentração acumulada
    client_rev['cumpct'] = client_rev['Vlr.Total'].cumsum() / total_rev * 100

    # ── Sazonalidade — receita média por mês (todos os anos) ──
    # mês parcial fora da média: senão o mês corrente puxa a média para baixo
    df_saz = df.copy()
    if parcial and mes_parcial:
        df_saz = df_saz[df_saz['AnoMesStr'].astype(str) != mes_parcial]
    df_saz['mes_num'] = df_saz['Emissao'].dt.month
    saz = df_saz.groupby(['Ano', 'mes_num'], observed=True)['Vlr.Total'].sum().reset_index()
    saz_media = saz.groupby('mes_num')['Vlr.Total'].mean().reset_index()
    saz_media['mes_label'] = saz_media['mes_num'].map(MESES_LABEL)
    media_geral = float(saz_media['Vlr.Total'].mean())

    # Cor das barras: acima da média = verde/laranja, abaixo = azul apagado
    bar_colors = [
        COLORS['primary'] if v >= media_geral else COLORS['text_muted']
        for v in saz_media['Vlr.Total']
    ]

    fig_heat = go.Figure()
    fig_heat.add_trace(go.Bar(
        x=saz_media['mes_label'], y=saz_media['Vlr.Total'],
        name='Média mensal',
        marker_color=bar_colors,
        marker_opacity=0.9,
        hovertemplate='<b>%{x}</b><br>Média histórica: R$ %{y:,.0f}<extra></extra>',
    ))
    # Linha de média geral
    fig_heat.add_hline(
        y=media_geral,
        line_dash='dot', line_color=COLORS['warning'], line_width=1.5,
        annotation_text=f'Média geral: {fmt_brl(media_geral)}',
        annotation_font_color=COLORS['warning'],
        annotation_position='bottom right',
    )
    # Destaque nos meses acima da média
    mes_forte = saz_media.loc[saz_media['Vlr.Total'].idxmax(), 'mes_label']
    mes_fraco = saz_media.loc[saz_media['Vlr.Total'].idxmin(), 'mes_label']
    fig_heat.update_layout(
        title=f'Sazonalidade · Receita Média por Mês (🟠 acima da média) · Pico: {mes_forte} · Vale: {mes_fraco}',
        xaxis_title='', yaxis_title='R$',
        yaxis_tickformat=',.0f',
        showlegend=False,
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

    # ── Tag de mês parcial no cabeçalho ──
    if parcial and mes_parcial:
        ultimo_dia = df['Emissao'].max().strftime('%d/%m/%Y')
        tag = html.Span(
            f'⚠️ dados até {ultimo_dia} · {mes_parcial} é mês parcial '
            f'(fora das variações e médias)',
            style={
                'fontSize': '11px', 'color': COLORS['warning'],
                'border': f'1px solid {COLORS["warning"]}', 'borderRadius': '6px',
                'padding': '4px 10px', 'whiteSpace': 'nowrap',
            },
        )
    else:
        tag = ''

    return tag, cards, insights, fig_monthly, fig_yoy, fig_treemap, fig_conc, fig_heat, fig_cum
