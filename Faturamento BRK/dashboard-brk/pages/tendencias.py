import dash
from dash import html, dcc, callback, Input, Output, dash_table
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from data.loader import get_liquid, apply_filters
from components.theme import (COLORS, fmt_brl, CHART_COLORS,
                              TBL_BRL, TBL_BRL_SIGNED, TBL_PCT, TBL_PCT_SIGNED, col_num)
from components.kpis import kpi_card, kpi_grid

dash.register_page(__name__, path='/tendencias', name='Tendências', order=3)

# ── Thresholds padrão ──
TH_CRESCIMENTO  = 15    # var% mínima para "Crescendo"
TH_QUEDA        = -15   # var% máxima para "Em Queda"
TH_RISCO        = -30   # var% para "Em Risco"
TH_INATIVO_DIAS = 90    # dias sem NF para "Inativo"
TH_NOVO_DIAS    = 90    # dias desde 1ª NF para "Novo"

_CELL = {
    'style_table': {'overflowX': 'auto', 'borderRadius': '8px'},
    'style_header': {
        'backgroundColor': COLORS['surface2'], 'color': COLORS['text_secondary'],
        'fontWeight': '600', 'fontSize': '11px', 'textTransform': 'uppercase',
        'letterSpacing': '0.5px', 'border': f'1px solid {COLORS["border"]}',
        'padding': '10px 12px', 'whiteSpace': 'nowrap',
    },
    'style_cell': {
        'backgroundColor': COLORS['surface'], 'color': COLORS['text'],
        'border': f'1px solid {COLORS["border"]}', 'fontSize': '12px',
        'padding': '8px 12px', 'fontFamily': 'Inter, sans-serif',
        'overflow': 'hidden', 'textOverflow': 'ellipsis', 'maxWidth': '200px',
    },
    'style_data_conditional': [
        {'if': {'row_index': 'odd'}, 'backgroundColor': COLORS['surface2']},
        {'if': {'filter_query': '{Status} contains "Crescendo"'},  'color': COLORS['success']},
        {'if': {'filter_query': '{Status} contains "Queda"'},      'color': COLORS['danger']},
        {'if': {'filter_query': '{Status} contains "Risco"'},      'color': '#FF6060'},
        {'if': {'filter_query': '{Status} contains "Inativo"'},    'color': COLORS['text_muted']},
        {'if': {'filter_query': '{Status} contains "Novo"'},       'color': COLORS['primary']},
        {'if': {'filter_query': '{Status} contains "Recuperado"'}, 'color': COLORS['info']},
        {'if': {'filter_query': '{HS} >= 70'},                     'color': COLORS['success']},
        {'if': {'filter_query': '{HS} < 30'},                      'color': COLORS['danger']},
    ],
}

layout = html.Div([
    # ── Cabeçalho ──
    html.Div([
        html.Div([
            html.Div('Radar Gerencial de Clientes', className='page-title'),
            html.Div(
                'Crescimento · Retenção · Risco · Oportunidade · Health Score',
                className='page-subtitle'
            ),
        ]),
        html.Div([
            html.Span('Thresholds: ', className='filter-label'),
            html.Span(
                f'Crescimento >{TH_CRESCIMENTO}% · Queda <{abs(TH_QUEDA)}% · '
                f'Inativo >{TH_INATIVO_DIAS}d',
                style={'fontSize': '11px', 'color': COLORS['text_muted']}
            ),
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '6px'}),
    ], className='page-header', style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'flex-start'}),

    # ── KPIs ──
    html.Div(id='tend-kpis', style={'marginBottom': '20px'}),

    # ── Insights automáticos ──
    html.Div(id='tend-insights', style={'marginBottom': '20px'}),

    # ── Matriz estratégica + Heatmap ──
    html.Div([
        html.Div([
            html.Div([
                html.Div('Matriz de Ação Gerencial', className='chart-title'),
                html.Div('Participação na receita × crescimento · priorização comercial', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='tend-matrix', config={'displayModeBar': False}, style={'height': '460px'}),
        ], className='chart-card'),

        html.Div([
            html.Div([
                html.Div('Heatmap de Clientes · Top 50', className='chart-title'),
                html.Div('Volume mensal faturado · identifica crescimento, queda e abandono', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='tend-heatmap', config={'displayModeBar': False}, style={'height': '460px'}),
        ], className='chart-card'),
    ], className='grid-2'),

    # ── Rankings ──
    html.Div([
        html.Div([
            html.Div([
                html.Div('🚀 Top 20 — Maior Crescimento', className='chart-title'),
                html.Div('Receita adicional gerada · oportunidade de expansão', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='tend-rank-top', config={'displayModeBar': False}, style={'height': '520px'}),
        ], className='chart-card'),

        html.Div([
            html.Div([
                html.Div('⚠️ Top 20 — Maior Queda', className='chart-title'),
                html.Div('Receita perdida · ação imediata de retenção', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='tend-rank-bot', config={'displayModeBar': False}, style={'height': '520px'}),
        ], className='chart-card'),
    ], className='grid-2'),

    # ── Tabela gerencial ──
    html.Div([
        html.Div([
            html.Div([
                html.Div('Central de Gestão de Clientes', className='chart-title'),
                html.Div('Todos os clientes · Health Score · Status · Ordenável · Exportável', className='chart-subtitle'),
            ], className='chart-card-header'),
            dash_table.DataTable(
                id='tend-table',
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

    # ── Painel de detalhe ──
    html.Div(id='tend-detail', style={'marginTop': '20px'}),

], id='page-content')


# ────────────────────────────────────────────────
#  CALLBACK PRINCIPAL
# ────────────────────────────────────────────────
@callback(
    Output('tend-kpis',     'children'),
    Output('tend-insights', 'children'),
    Output('tend-matrix',   'figure'),
    Output('tend-heatmap',  'figure'),
    Output('tend-rank-top', 'figure'),
    Output('tend-rank-bot', 'figure'),
    Output('tend-table',    'data'),
    Output('tend-table',    'columns'),
    Input('filter-date',      'start_date'),
    Input('filter-date',      'end_date'),
    Input('filter-ano',       'value'),
    Input('filter-cliente',   'value'),
    Input('filter-produto',   'value'),
    Input('filter-valor-min', 'value'),
    Input('filter-valor-max', 'value'),
)
def update_radar(start_date, end_date, anos, cliente, produto, valor_min, valor_max):
    df_all = get_liquid()
    df = apply_filters(df_all, start_date, end_date, anos, cliente, produto, valor_min, valor_max)

    empty_fig = go.Figure()
    empty_fig.update_layout(
        title='Sem dados para o período/filtro selecionado',
        height=400,
    )

    if df.empty:
        return html.Div('Sem dados.'), html.Div(), empty_fig, empty_fig, empty_fig, empty_fig, [], []

    now = pd.Timestamp(df['Emissao'].max())

    # ── Receita mensal por cliente ──
    monthly = (
        df.groupby(['GrupoEcon', 'AnoMesStr'], observed=True)['Vlr.Total']
        .sum().unstack(fill_value=0)
    )
    months = sorted(monthly.columns)
    monthly = monthly.reindex(columns=months, fill_value=0)
    n = len(months)

    # ── Agregação base ──
    agg = df.groupby('GrupoEcon', observed=True).agg(
        receita    = ('Vlr.Total',   'sum'),
        nfs        = ('Num. Docto.', 'nunique'),
        servicos   = ('Descricao',   'nunique'),
        ultima_nf  = ('Emissao',     'max'),
        primeira_nf= ('Emissao',     'min'),
    ).reset_index()
    agg['GrupoEcon'] = agg['GrupoEcon'].astype(str)

    # ── Variações ──
    if n >= 2:
        agg['rec_ult'] = agg['GrupoEcon'].map(monthly[months[-1]]).fillna(0)
        agg['rec_pen'] = agg['GrupoEcon'].map(monthly[months[-2]]).fillna(0)
        with np.errstate(divide='ignore', invalid='ignore'):
            agg['var_mom'] = np.where(
                agg['rec_pen'] > 0,
                (agg['rec_ult'] - agg['rec_pen']) / agg['rec_pen'] * 100,
                np.nan
            )
    else:
        agg['rec_ult'] = agg['receita']
        agg['rec_pen'] = 0.0
        agg['var_mom'] = np.nan

    if n >= 6:
        r3  = monthly[months[-3:]].sum(axis=1)
        r3p = monthly[months[-6:-3]].sum(axis=1)
        agg['rec_3m']      = agg['GrupoEcon'].map(r3).fillna(0)
        agg['rec_3m_prev'] = agg['GrupoEcon'].map(r3p).fillna(0)
        with np.errstate(divide='ignore', invalid='ignore'):
            agg['var_3m'] = np.where(
                agg['rec_3m_prev'] > 0,
                (agg['rec_3m'] - agg['rec_3m_prev']) / agg['rec_3m_prev'] * 100,
                np.nan
            )
        agg['delta_abs'] = agg['rec_3m'] - agg['rec_3m_prev']
    elif n >= 2:
        agg['rec_3m']      = agg['rec_ult']
        agg['rec_3m_prev'] = agg['rec_pen']
        agg['var_3m']      = agg['var_mom']
        agg['delta_abs']   = agg['rec_ult'] - agg['rec_pen']
    else:
        agg['var_3m']    = np.nan
        agg['delta_abs'] = 0.0

    # ── Recência ──
    agg['dias'] = (now - agg['ultima_nf']).dt.days.fillna(999).astype(int)

    # ── Clientes recuperados ──
    recuperados = set()
    if n >= 4:
        zero_antes = set(monthly.index[(monthly[months[-4:-2]].sum(axis=1) == 0)])
        ativos_agora = set(monthly.index[monthly[months[-1]] > 0])
        recuperados = zero_antes & ativos_agora

    # ── Classificação ──
    def classify(row):
        dias = int(row['dias'])
        v    = row['var_3m'] if pd.notna(row['var_3m']) else 0.0
        g    = row['GrupoEcon']
        nova = pd.notna(row['primeira_nf']) and (now - row['primeira_nf']).days <= TH_NOVO_DIAS

        if nova:              return '🆕 Novo'
        if g in recuperados:  return '🔄 Recuperado'
        if dias >= TH_INATIVO_DIAS: return '⚫ Inativo'
        if v >= TH_CRESCIMENTO:     return '🟢 Crescendo'
        if v <= TH_RISCO:           return '🔴 Em Risco'
        if v <= TH_QUEDA:           return '🟠 Em Queda'
        return '🟡 Estável'

    agg['Status'] = agg.apply(classify, axis=1)

    # ── Health Score 0-100 ──
    max_svc = max(float(agg['servicos'].max()), 1)
    meses_p = max(n, 1)

    def health(row):
        v  = float(row['var_3m']) if pd.notna(row['var_3m']) else 0.0
        d  = float(row['dias'])
        g  = min(max((v + 50) / 100, 0.0), 1.0) * 35
        r  = 25 if d <= 30 else 18 if d <= 60 else 10 if d <= 90 else 3 if d <= 180 else 0
        fr = min(float(row['nfs']) / meses_p / 2, 1.0) * 20
        dv = min(float(row['servicos']) / max_svc, 1.0) * 20
        return int(round(g + r + fr + dv))

    agg['HS'] = agg.apply(health, axis=1)
    agg['Health'] = agg['HS'].apply(
        lambda s: '🟢 Saudável' if s >= 70 else '🟡 Atenção' if s >= 45 else '🔴 Risco' if s >= 20 else '⚫ Perdido'
    )

    # ── Upsell / Cross-sell ──
    med_svc = float(agg['servicos'].median()) if len(agg) > 0 else 1
    med_rec = float(agg['receita'].median())   if len(agg) > 0 else 0
    agg['Upsell']    = np.where((agg['var_3m'].fillna(0) > 10) & (agg['servicos'] <= med_svc), '📈 Sim', '—')
    agg['CrossSell'] = np.where((agg['servicos'] == 1) & (agg['receita'] > med_rec),            '🔀 Sim', '—')

    # ── Participação ──
    total = float(agg['receita'].sum())
    agg['pct'] = (agg['receita'] / total * 100).round(2) if total > 0 else 0.0

    # ────────────── KPIs ──────────────
    st = agg['Status']
    crescendo  = (st.str.contains('Crescendo')).sum()
    estavel    = (st.str.contains('Estável')).sum()
    queda      = (st.str.contains('Queda') | st.str.contains('Risco')).sum()
    inativo    = (st.str.contains('Inativo')).sum()
    novo       = (st.str.contains('Novo')).sum()
    recuperado = (st.str.contains('Recuperado')).sum()

    rec_expansao = float(agg.loc[agg['delta_abs'] > 0, 'delta_abs'].sum())
    rec_risco    = float(agg.loc[
        agg['Status'].str.contains('Queda|Risco|Inativo'), 'receita'
    ].sum())
    upsell_n = (agg['Upsell'] == '📈 Sim').sum()

    kpis = kpi_grid([
        kpi_card('Crescendo',       crescendo,     '🟢', None, 'clientes em expansão',     value_fmt='int'),
        kpi_card('Estáveis',        estavel,       '🟡', None, 'oscilação normal',          value_fmt='int'),
        kpi_card('Em Queda/Risco',  queda,         '🔴', None, 'requerem atenção imediata', value_fmt='int'),
        kpi_card('Inativos',        inativo,       '⚫', None, f'sem NF > {TH_INATIVO_DIAS}d', value_fmt='int'),
        kpi_card('Novos',           novo,          '🆕', None, 'últimos 90 dias',           value_fmt='int'),
        kpi_card('Recuperados',     recuperado,    '🔄', None, 'retornaram após pausa',     value_fmt='int'),
        kpi_card('Receita em Expansão', rec_expansao, '💰', None, 'gerada por clientes em crescimento'),
        kpi_card('Receita em Risco',    rec_risco,    '⚠️', None, 'clientes em queda/inativos'),
        kpi_card('Potencial Upsell',    upsell_n,     '📈', None, 'clientes com oportunidade', value_fmt='int'),
    ])

    # ────────────── INSIGHTS ──────────────
    insights_items = []

    top_cresc = agg[agg['delta_abs'] > 0].nlargest(10, 'delta_abs')
    if not top_cresc.empty:
        pct_exp = top_cresc['delta_abs'].sum() / rec_expansao * 100 if rec_expansao > 0 else 0
        insights_items.append(html.Div([
            html.Span('📈', className='insight-icon'),
            html.Div(html.Span([
                'Os ', html.Strong('10 clientes de maior crescimento'), f' geraram ',
                html.Strong(f'{fmt_brl(top_cresc["delta_abs"].sum())}'),
                f' ({pct_exp:.0f}% da expansão total).'
            ]), className='insight-text'),
        ], className='insight-item positive'))

    if rec_risco > 0:
        pct_r = rec_risco / total * 100 if total > 0 else 0
        insights_items.append(html.Div([
            html.Span('⚠️', className='insight-icon'),
            html.Div(html.Span([
                'Receita em risco: ', html.Strong(fmt_brl(rec_risco)),
                f' ({pct_r:.1f}% do faturamento) — clientes em queda ou inativos.'
            ]), className='insight-text'),
        ], className='insight-item critical'))

    if upsell_n > 0:
        insights_items.append(html.Div([
            html.Span('🚀', className='insight-icon'),
            html.Div(html.Span([
                html.Strong(f'{upsell_n} clientes'),
                ' com potencial imediato de upsell — crescendo mas consumindo poucos serviços.'
            ]), className='insight-text'),
        ], className='insight-item positive'))

    criticos = agg[agg['Status'].str.contains('Risco') & (agg['pct'] > 2)]
    if not criticos.empty:
        pct_crit = criticos['pct'].sum()
        insights_items.append(html.Div([
            html.Span('🔴', className='insight-icon'),
            html.Div(html.Span([
                html.Strong(f'{len(criticos)} clientes críticos'),
                f' representam {pct_crit:.1f}% da receita e estão em forte queda — ação imediata.'
            ]), className='insight-text'),
        ], className='insight-item critical'))

    if inativo > 0:
        insights_items.append(html.Div([
            html.Span('⚫', className='insight-icon'),
            html.Div(html.Span([
                html.Strong(f'{inativo} clientes inativos'),
                f' há mais de {TH_INATIVO_DIAS} dias — oportunidade de reativação.'
            ]), className='insight-text'),
        ], className='insight-item warning'))

    if recuperado > 0:
        insights_items.append(html.Div([
            html.Span('🔄', className='insight-icon'),
            html.Div(html.Span([
                html.Strong(f'{recuperado} clientes recuperados'),
                ' voltaram a faturar após pausa — monitorar consolidação.'
            ]), className='insight-text'),
        ], className='insight-item info'))

    insights = html.Div([
        html.Div(['⚡ ', html.Span('Insights Gerenciais')], className='insight-panel-title'),
        html.Div(insights_items or [html.Div('Nenhum alerta identificado.', style={'color': COLORS['text_muted']})],
                 className='insight-grid'),
    ], className='insight-panel')

    # ────────────── MATRIZ ESTRATÉGICA ──────────────
    STATUS_COLOR = {
        '🟢 Crescendo':  COLORS['success'],
        '🟡 Estável':    COLORS['warning'],
        '🟠 Em Queda':   '#FF8C00',
        '🔴 Em Risco':   COLORS['danger'],
        '⚫ Inativo':    COLORS['text_muted'],
        '🆕 Novo':       COLORS['primary'],
        '🔄 Recuperado': COLORS['info'],
    }

    fig_matrix = go.Figure()

    for status, color in STATUS_COLOR.items():
        sub = agg[agg['Status'] == status]
        if sub.empty:
            continue
        fig_matrix.add_trace(go.Scatter(
            x=sub['pct'].astype(float),
            # variação limitada a ±200% — outliers esmagavam todos os pontos no eixo
            y=sub['var_3m'].fillna(0).astype(float).clip(-100, 200),
            mode='markers',
            name=status,
            marker=dict(
                # sizemin garante que clientes pequenos continuem visíveis
                size=np.sqrt(sub['receita'].astype(float).clip(1)) / 250,
                sizemin=5,
                color=color,
                opacity=0.82,
                line=dict(color='rgba(255,255,255,0.15)', width=0.5),
            ),
            customdata=sub[['GrupoEcon', 'receita', 'var_3m', 'HS', 'pct']].values,
            hovertemplate=(
                '<b>%{customdata[0]}</b><br>'
                'Receita: R$ %{customdata[1]:,.0f}<br>'
                'Crescimento 3M: %{customdata[2]:+.1f}%<br>'
                'Health Score: %{customdata[3]}<br>'
                'Part. Receita: %{customdata[4]:.2f}%<extra></extra>'
            ),
        ))

    # Linhas de quadrante
    med_pct = float(agg['pct'].median()) if len(agg) > 0 else 1.0
    fig_matrix.add_vline(x=med_pct, line_dash='dot', line_color=COLORS['border'], line_width=1)
    fig_matrix.add_hline(y=0, line_dash='dot', line_color=COLORS['border'], line_width=1)

    # Labels dos quadrantes
    for txt, x, y in [
        ('⭐ Estrelas',     0.92, 0.95),
        ('🚀 Oportunidades',0.08, 0.95),
        ('⚠️ Atenção',      0.92, 0.05),
        ('❌ Críticos',     0.08, 0.05),
    ]:
        fig_matrix.add_annotation(
            xref='paper', yref='paper', x=x, y=y,
            text=txt, showarrow=False,
            font=dict(size=11, color=COLORS['text_muted']),
            opacity=0.7,
        )

    fig_matrix.update_layout(
        title='Matriz de Ação Gerencial · % Receita × Crescimento 3M',
        xaxis_title='Participação na Receita (%)',
        yaxis_title='Crescimento 3 Meses (%, limitado a ±200)',
        yaxis=dict(range=[-115, 215]),
        legend=dict(orientation='h', y=-0.18, font=dict(size=11)),
        height=440,
    )

    # ────────────── HEATMAP TOP 50 ──────────────
    top50 = agg.nlargest(50, 'receita')['GrupoEcon'].astype(str).tolist()
    hm_data = monthly.loc[monthly.index.astype(str).isin(top50)].copy()
    hm_data.index = hm_data.index.astype(str)
    hm_data = hm_data.reindex([c for c in top50 if c in hm_data.index])

    if not hm_data.empty:
        fig_heat = go.Figure(go.Heatmap(
            z=hm_data.values.astype(float) / 1000,
            x=list(hm_data.columns),
            y=list(hm_data.index),
            colorscale=[
                [0.0,  COLORS['surface2']],
                [0.3,  COLORS['primary_dark']],
                [1.0,  COLORS['primary']],
            ],
            hovertemplate='<b>%{y}</b><br>%{x}<br>R$ %{z:.0f}K<extra></extra>',
            showscale=True,
            colorbar=dict(title='R$ K', tickfont=dict(color=COLORS['text_secondary'], size=10)),
        ))
        fig_heat.update_layout(
            title='Heatmap · Faturamento Mensal Top 50 Clientes (R$ K)',
            xaxis=dict(tickfont=dict(size=9), title=''),
            yaxis=dict(tickfont=dict(size=9), title='', autorange='reversed'),
            height=440,
            margin=dict(l=180, r=30, t=50, b=40),
        )
    else:
        fig_heat = empty_fig

    # ────────────── RANKINGS ──────────────
    cresceu = agg[agg['delta_abs'] > 0].nlargest(20, 'delta_abs')
    caiu    = agg[agg['delta_abs'] < 0].nsmallest(20, 'delta_abs')

    def ranking_fig(data, col, title, color, prefix='+'):
        if data.empty:
            f = go.Figure()
            f.update_layout(title=title, height=500)
            return f
        data = data.copy()
        data['label'] = data['GrupoEcon'].astype(str).str[:35]
        data['val']   = data[col].abs().astype(float)
        data['pct_v'] = data['var_3m'].fillna(0).astype(float)
        data = data.sort_values('val')
        f = go.Figure(go.Bar(
            x=data['val'],
            y=data['label'],
            orientation='h',
            marker=dict(
                color=data['pct_v'],
                colorscale=[[0, color], [1, color]],
                opacity=0.85,
                line=dict(width=0),
            ),
            customdata=data[['GrupoEcon', col, 'var_3m', 'HS', 'Status']].values,
            hovertemplate=(
                '<b>%{customdata[0]}</b><br>'
                f'Variação: R$ %{{customdata[1]:,.0f}}<br>'
                'Crescimento 3M: %{customdata[2]:+.1f}%<br>'
                'Health Score: %{customdata[3]}<br>'
                'Status: %{customdata[4]}<extra></extra>'
            ),
            text=data['val'].apply(lambda v: fmt_brl(v)),
            textposition='outside',
            textfont=dict(size=10, color=COLORS['text_secondary']),
        ))
        f.update_layout(
            title=title,
            xaxis_title='R$', yaxis_title='',
            xaxis_tickformat=',.0f',
            height=500,
            margin=dict(l=10, r=80, t=50, b=40),
        )
        return f

    fig_top = ranking_fig(cresceu, 'delta_abs', 'Top 20 — Maior Crescimento (R$)', COLORS['success'])
    fig_bot = ranking_fig(caiu,    'delta_abs', 'Top 20 — Maior Queda (R$)',       COLORS['danger'])

    # ────────────── TABELA GERENCIAL ──────────────
    agg_s = agg.sort_values('receita', ascending=False).reset_index(drop=True)
    agg_s['Rank'] = agg_s.index + 1

    records = []
    for _, r in agg_s.iterrows():
        records.append({
            '#':              int(r['Rank']),
            'Cliente':        str(r['GrupoEcon']),
            'Receita Total':  round(float(r['receita'])),
            'Rec. Período Ant.': round(float(r['rec_3m_prev'])) if pd.notna(r.get('rec_3m_prev')) else None,
            'Var. R$':        round(float(r['delta_abs'])) if pd.notna(r.get('delta_abs')) else None,
            'Var. %':         round(float(r['var_3m']), 1) if pd.notna(r['var_3m']) else None,
            'Status':         str(r['Status']),
            'HS':             int(r['HS']),
            'Health':         str(r['Health']),
            'Última Compra':  r['ultima_nf'].strftime('%d/%m/%Y') if pd.notna(r['ultima_nf']) else '—',
            'Dias s/ Compra': int(r['dias']),
            'Serviços':       int(r['servicos']),
            'Part. %':        round(float(r['pct']), 2),
            'Upsell':         str(r['Upsell']),
            'Cross-sell':     str(r['CrossSell']),
        })

    cols = [
        {'name': '#', 'id': '#', 'type': 'numeric'},
        {'name': 'Cliente', 'id': 'Cliente', 'type': 'text'},
        col_num('Receita Total', TBL_BRL),
        col_num('Rec. Período Ant.', TBL_BRL),
        col_num('Var. R$', TBL_BRL_SIGNED),
        col_num('Var. %', TBL_PCT_SIGNED),
        {'name': 'Status', 'id': 'Status', 'type': 'text'},
        {'name': 'HS', 'id': 'HS', 'type': 'numeric'},
        {'name': 'Health', 'id': 'Health', 'type': 'text'},
        {'name': 'Última Compra', 'id': 'Última Compra', 'type': 'text'},
        {'name': 'Dias s/ Compra', 'id': 'Dias s/ Compra', 'type': 'numeric'},
        {'name': 'Serviços', 'id': 'Serviços', 'type': 'numeric'},
        col_num('Part. %', TBL_PCT),
        {'name': 'Upsell', 'id': 'Upsell', 'type': 'text'},
        {'name': 'Cross-sell', 'id': 'Cross-sell', 'type': 'text'},
    ] if records else []

    return kpis, insights, fig_matrix, fig_heat, fig_top, fig_bot, records, cols


# ────────────────────────────────────────────────
#  CALLBACK DETALHE DO CLIENTE
# ────────────────────────────────────────────────
@callback(
    Output('tend-detail', 'children'),
    Input('tend-table',       'active_cell'),
    Input('tend-table',       'data'),
    Input('filter-date',      'start_date'),
    Input('filter-date',      'end_date'),
    Input('filter-ano',       'value'),
    Input('filter-produto',   'value'),
    Input('filter-valor-min', 'value'),
    Input('filter-valor-max', 'value'),
)
def update_detail(active_cell, table_data, start_date, end_date, anos, produto, valor_min, valor_max):
    if not active_cell or not table_data:
        return html.Div(
            '👆 Clique em qualquer cliente na tabela para ver análise detalhada.',
            style={'color': COLORS['text_muted'], 'padding': '16px', 'fontSize': '13px'},
        )

    row   = table_data[active_cell['row']]
    grupo = row['Cliente']
    hs    = row['HS']
    status= row['Status']

    df_all  = get_liquid()
    df_base = apply_filters(df_all, start_date, end_date, anos, None, produto, valor_min, valor_max)
    df_cli  = df_base[df_base['GrupoEcon'].astype(str) == grupo]

    if df_cli.empty:
        return html.Div('Sem dados para este cliente.', style={'color': COLORS['text_muted']})

    # Evolução mensal (últimos 24 meses)
    monthly = df_cli.groupby('AnoMesStr', observed=True)['Vlr.Total'].sum().sort_index().tail(24)

    # Cor do Health Score
    hs_color = COLORS['success'] if hs >= 70 else COLORS['warning'] if hs >= 45 else COLORS['danger']

    fig_evo = go.Figure()
    fig_evo.add_trace(go.Bar(
        x=list(monthly.index), y=[float(v) for v in monthly.values],
        name='Receita', marker_color=COLORS['primary'], marker_opacity=0.8,
        hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>',
    ))
    ma3 = monthly.rolling(3).mean()
    fig_evo.add_trace(go.Scatter(
        x=list(ma3.index), y=[float(v) if pd.notna(v) else None for v in ma3.values],
        name='Média 3M', line=dict(color=COLORS['info'], width=2, dash='dot'),
        hovertemplate='MM3: R$ %{y:,.0f}<extra></extra>',
    ))
    fig_evo.update_layout(
        title=f'Evolução Mensal · {grupo}',
        xaxis_title='', yaxis_title='R$', yaxis_tickformat=',.0f',
        legend=dict(orientation='h', y=1.1), height=300,
    )

    # Mix de serviços
    svc = df_cli.groupby('Descricao', observed=True)['Vlr.Total'].sum().sort_values(ascending=False)
    svc_total = float(svc.sum())
    fig_svc = go.Figure(go.Pie(
        labels=[str(s) for s in svc.index],
        values=[float(v) for v in svc.values],
        hole=0.55,
        hovertemplate='<b>%{label}</b><br>R$ %{value:,.0f} · %{percent}<extra></extra>',
        textinfo='label+percent',
        textfont=dict(size=10),
    ))
    fig_svc.update_layout(
        title='Mix de Serviços', height=320,
        showlegend=False,
        annotations=[dict(
            text=f'{len(svc)}<br>serviços',
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=13, color=COLORS['text']),
        )],
    )

    # Métricas rápidas
    rec_total = float(df_cli['Vlr.Total'].sum())
    nfs       = df_cli['Num. Docto.'].nunique()
    ticket    = rec_total / nfs if nfs > 0 else 0
    ultima    = df_cli['Emissao'].max().strftime('%d/%m/%Y')
    primeira  = df_cli['Emissao'].min().strftime('%d/%m/%Y')
    n_meses   = len(monthly)
    freq      = nfs / max(n_meses, 1)

    return html.Div([
        # Header do cliente
        html.Div([
            html.Div([
                html.Div(grupo, style={'fontSize': '17px', 'fontWeight': '700', 'color': COLORS['text']}),
                html.Div([
                    html.Span(status, style={'fontSize': '13px', 'marginRight': '16px'}),
                    html.Span(f'Health Score: ', style={'color': COLORS['text_muted'], 'fontSize': '12px'}),
                    html.Span(f'{hs}/100', style={'fontWeight': '700', 'color': hs_color, 'fontSize': '16px'}),
                    html.Span(f' · {row["Health"]}', style={'color': hs_color, 'fontSize': '12px'}),
                ], style={'marginTop': '4px', 'display': 'flex', 'alignItems': 'center'}),
            ]),
            html.Div([
                html.Span(fmt_brl(rec_total), style={'fontSize': '22px', 'fontWeight': '800', 'color': COLORS['primary']}),
                html.Span(f" · {float(row['Part. %']):.2f}% da carteira".replace('.', ','), style={'color': COLORS['text_secondary'], 'fontSize': '12px', 'marginLeft': '8px'}),
            ]),
        ], style={
            'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
            'marginBottom': '20px', 'paddingBottom': '16px', 'borderBottom': f'1px solid {COLORS["border"]}',
        }),

        # KPIs do cliente
        html.Div([
            html.Div([html.Div('NFs Emitidas', className='kpi-label'), html.Div(f'{nfs:,}', className='kpi-value'), html.Div('no período', className='kpi-context')], className='kpi-card'),
            html.Div([html.Div('Ticket Médio NF', className='kpi-label'), html.Div(fmt_brl(ticket), className='kpi-value'), html.Div('por nota fiscal', className='kpi-context')], className='kpi-card'),
            html.Div([html.Div('Frequência', className='kpi-label'), html.Div(f'{freq:.1f}', className='kpi-value'), html.Div('NFs por mês', className='kpi-context')], className='kpi-card'),
            html.Div([html.Div('Serviços Distintos', className='kpi-label'), html.Div(str(len(svc)), className='kpi-value'), html.Div('produtos contratados', className='kpi-context')], className='kpi-card'),
            html.Div([html.Div('Primeira Compra', className='kpi-label'), html.Div(primeira, className='kpi-value', style={'fontSize': '18px'}), html.Div('início do relacionamento', className='kpi-context')], className='kpi-card'),
            html.Div([html.Div('Última Compra', className='kpi-label'), html.Div(ultima, className='kpi-value', style={'fontSize': '18px'}), html.Div(f'{row["Dias s/ Compra"]} dias atrás', className='kpi-context')], className='kpi-card'),
        ], className='kpi-grid', style={'marginBottom': '20px'}),

        # Gráficos
        html.Div([
            html.Div([
                html.Div([html.Div('Evolução Mensal · Últimos 24 Meses', className='chart-title'), html.Div('Barras + Média Móvel 3 Meses', className='chart-subtitle')], className='chart-card-header'),
                dcc.Graph(figure=fig_evo, config={'displayModeBar': False}),
            ], className='chart-card'),
            html.Div([
                html.Div([html.Div('Mix de Serviços', className='chart-title'), html.Div(f'{len(svc)} serviços contratados', className='chart-subtitle')], className='chart-card-header'),
                dcc.Graph(figure=fig_svc, config={'displayModeBar': False}),
            ], className='chart-card'),
        ], className='grid-2'),

    ], className='chart-card')
