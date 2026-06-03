import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from scipy import stats

from data.loader import get_liquid, apply_filters
from components.theme import COLORS, fmt_brl, CHART_COLORS

dash.register_page(__name__, path='/tendencias', name='Tendências', order=3)

layout = html.Div([
    html.Div([
        html.Div('Tendências & Projeções', className='page-title'),
        html.Div('Série histórica completa · sazonalidade · projeção 6 meses · coorte de clientes', className='page-subtitle'),
    ], className='page-header'),

    html.Div([
        html.Div([
            html.Div([
                html.Div('Série Histórica Completa + Projeção 6 Meses', className='chart-title'),
                html.Div('Regressão linear com intervalo de confiança 80% e 95%', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='tend-series', config={'displayModeBar': True}, style={'height': '400px'}),
        ], className='chart-card'),
    ]),

    html.Div([
        html.Div([
            html.Div([
                html.Div('Índice de Sazonalidade', className='chart-title'),
                html.Div('Média histórica por mês normalizada — identifica meses mais fortes e mais fracos', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='tend-seasonality', config={'displayModeBar': False}, style={'height': '320px'}),
        ], className='chart-card'),

        html.Div([
            html.Div([
                html.Div('Decomposição do Crescimento', className='chart-title'),
                html.Div('Expansão de carteira vs. novos clientes vs. novos serviços', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='tend-decomp', config={'displayModeBar': False}, style={'height': '320px'}),
        ], className='chart-card'),
    ], className='grid-2'),

    html.Div([
        html.Div([
            html.Div([
                html.Div('Aceleração vs. Desaceleração', className='chart-title'),
                html.Div('Taxa de crescimento mensal — identifica pontos de inflexão', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='tend-growth-rate', config={'displayModeBar': False}, style={'height': '300px'}),
        ], className='chart-card'),

        html.Div([
            html.Div([
                html.Div('Análise de Coorte de Clientes', className='chart-title'),
                html.Div('Retenção por data de primeira NF — meses após aquisição', className='chart-subtitle'),
            ], className='chart-card-header'),
            dcc.Graph(id='tend-cohort', config={'displayModeBar': False}, style={'height': '300px'}),
        ], className='chart-card'),
    ], className='grid-2'),

], id='page-content')


@callback(
    Output('tend-series', 'figure'),
    Output('tend-seasonality', 'figure'),
    Output('tend-decomp', 'figure'),
    Output('tend-growth-rate', 'figure'),
    Output('tend-cohort', 'figure'),
    Input('filter-date', 'start_date'),
    Input('filter-date', 'end_date'),
    Input('filter-ano', 'value'),
    Input('filter-cliente', 'value'),
    Input('filter-produto', 'value'),
    Input('filter-valor-min', 'value'),
    Input('filter-valor-max', 'value'),
)
def update_tendencias(start_date, end_date, anos, cliente, produto, valor_min, valor_max):
    df_all = get_liquid()
    df = apply_filters(df_all, start_date, end_date, anos, cliente, produto, valor_min, valor_max)

    empty = go.Figure()
    empty.update_layout(title='Sem dados suficientes', height=300)

    # ── Série histórica completa (sem filtro de data para mostrar tudo) ──
    df_hist = get_liquid()
    if cliente and isinstance(cliente, str) and cliente.strip():
        df_hist = df_hist[df_hist['Nome'].str.contains(cliente.strip().upper(), na=False)]
    if produto and isinstance(produto, list) and len(produto) > 0:
        df_hist = df_hist[df_hist['Descricao'].isin(produto)]

    monthly_hist = df_hist.groupby('AnoMesStr')['Vlr.Total'].sum().sort_index()
    months = list(range(len(monthly_hist)))
    values = monthly_hist.values

    fig_series = go.Figure()

    if len(values) >= 4:
        slope, intercept, r, p, se = stats.linregress(months, values)
        trend_vals = [slope * m + intercept for m in months]

        # Projeção futura 6 meses
        last_idx = months[-1]
        future_months = list(range(last_idx + 1, last_idx + 7))
        future_vals = [slope * m + intercept for m in future_months]

        # Intervalo de confiança
        n = len(months)
        x_mean = np.mean(months)
        s_err = np.sqrt(np.sum((values - np.array(trend_vals)) ** 2) / (n - 2))

        all_future_x = future_months
        ci_95 = [stats.t.ppf(0.975, n - 2) * s_err * np.sqrt(1 + 1/n + (x - x_mean)**2 / np.sum((np.array(months) - x_mean)**2)) for x in all_future_x]
        ci_80 = [stats.t.ppf(0.9, n - 2) * s_err * np.sqrt(1 + 1/n + (x - x_mean)**2 / np.sum((np.array(months) - x_mean)**2)) for x in all_future_x]

        # Gerar labels futuros
        last_date = pd.to_datetime(monthly_hist.index[-1])
        future_labels = [(last_date + pd.DateOffset(months=i+1)).strftime('%Y-%m') for i in range(6)]

        all_labels = list(monthly_hist.index) + future_labels

        # Banda 95%
        fig_series.add_trace(go.Scatter(
            x=future_labels + future_labels[::-1],
            y=[v + c for v, c in zip(future_vals, ci_95)] + [v - c for v, c in zip(future_vals[::-1], ci_95[::-1])],
            fill='toself', fillcolor='rgba(255,101,0,0.07)',
            line=dict(width=0), showlegend=True, name='IC 95%',
            hoverinfo='skip',
        ))
        # Banda 80%
        fig_series.add_trace(go.Scatter(
            x=future_labels + future_labels[::-1],
            y=[v + c for v, c in zip(future_vals, ci_80)] + [v - c for v, c in zip(future_vals[::-1], ci_80[::-1])],
            fill='toself', fillcolor='rgba(255,101,0,0.12)',
            line=dict(width=0), showlegend=True, name='IC 80%',
            hoverinfo='skip',
        ))
        # Projeção
        fig_series.add_trace(go.Scatter(
            x=future_labels, y=future_vals,
            mode='lines+markers',
            line=dict(color=COLORS['primary'], width=2, dash='dash'),
            marker=dict(size=6, symbol='diamond', color=COLORS['primary']),
            name='Projeção',
            hovertemplate='<b>Projeção %{x}</b><br>R$ %{y:,.0f}<extra></extra>',
        ))

    # Linha histórica
    fig_series.add_trace(go.Scatter(
        x=list(monthly_hist.index), y=list(values),
        mode='lines+markers',
        fill='tozeroy', fillcolor='rgba(255,101,0,0.05)',
        line=dict(color=COLORS['primary'], width=2.5),
        marker=dict(size=5, color=COLORS['primary']),
        name='Receita Real',
        hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>',
    ))

    fig_series.add_vrect(
        x0=list(monthly_hist.index)[-1], x1=future_labels[-1] if len(values) >= 4 else list(monthly_hist.index)[-1],
        fillcolor='rgba(255,101,0,0.03)', line_width=0,
        annotation_text='Projeção', annotation_position='top left',
        annotation_font=dict(color=COLORS['warning'], size=11),
    )
    fig_series.update_layout(
        title='Série Histórica Completa + Projeção 6 Meses',
        xaxis_title='', yaxis_title='R$',
        yaxis_tickformat=',.0f',
        legend=dict(orientation='h', y=1.1),
        height=380,
        hovermode='x unified',
    )

    # ── Sazonalidade ──
    df_szn = df_hist.groupby(['Ano', 'Mes'])['Vlr.Total'].sum().reset_index()
    df_szn = df_szn[df_szn['Ano'] < df_szn['Ano'].max()]  # exclui ano parcial
    szn_avg = df_szn.groupby('Mes')['Vlr.Total'].mean()
    szn_idx = szn_avg / szn_avg.mean() * 100

    meses_label = {1:'Jan',2:'Fev',3:'Mar',4:'Abr',5:'Mai',6:'Jun',
                   7:'Jul',8:'Ago',9:'Set',10:'Out',11:'Nov',12:'Dez'}
    szn_idx.index = [meses_label.get(m, m) for m in szn_idx.index]

    colors_szn = [COLORS['success'] if v >= 100 else COLORS['danger'] for v in szn_idx.values]
    fig_szn = go.Figure(go.Bar(
        x=list(szn_idx.index), y=szn_idx.values,
        marker_color=colors_szn, marker_opacity=0.85,
        hovertemplate='<b>%{x}</b><br>Índice: %{y:.1f} (base 100)<extra></extra>',
    ))
    fig_szn.add_hline(y=100, line_dash='dot', line_color=COLORS['text_muted'],
                      annotation_text='Base 100 (média)', annotation_font=dict(color=COLORS['text_muted']))
    fig_szn.update_layout(
        title='Índice de Sazonalidade Mensal (base 100 = média histórica)',
        xaxis_title='', yaxis_title='Índice',
        height=300,
    )

    # ── Decomposição do crescimento ──
    if len(monthly_hist) >= 13:
        curr_year = df_hist['Ano'].max()
        prev_year = curr_year - 1

        df_curr = df_hist[df_hist['Ano'] == curr_year]
        df_prev = df_hist[df_hist['Ano'] == prev_year]

        clientes_curr = set(df_curr['Nome'].unique())
        clientes_prev = set(df_prev['Nome'].unique())

        novos = clientes_curr - clientes_prev
        retidos = clientes_curr & clientes_prev
        perdidos = clientes_prev - clientes_curr

        rec_novos = df_curr[df_curr['Nome'].isin(novos)]['Vlr.Total'].sum()
        rec_retidos_curr = df_curr[df_curr['Nome'].isin(retidos)]['Vlr.Total'].sum()
        rec_retidos_prev = df_prev[df_prev['Nome'].isin(retidos)]['Vlr.Total'].sum()
        rec_expansao = max(0, rec_retidos_curr - rec_retidos_prev)
        rec_retencao = rec_retidos_prev
        rec_perdidos = df_prev[df_prev['Nome'].isin(perdidos)]['Vlr.Total'].sum()

        categorias = ['Receita Retida\n(clientes existentes)', 'Expansão\n(crescimento carteira)', 'Novos\nClientes', 'Clientes\nPerdidos']
        valores = [rec_retencao, rec_expansao, rec_novos, -rec_perdidos]
        cores = [COLORS['info'], COLORS['success'], COLORS['primary'], COLORS['danger']]

        fig_decomp = go.Figure(go.Bar(
            x=categorias, y=[abs(v) for v in valores],
            marker_color=cores, marker_opacity=0.85,
            customdata=valores,
            hovertemplate='<b>%{x}</b><br>R$ %{customdata:,.0f}<extra></extra>',
        ))
        fig_decomp.update_layout(
            title=f'Decomposição de Receita {curr_year} vs. {prev_year}',
            yaxis_title='R$', yaxis_tickformat=',.0f',
            height=300,
        )
    else:
        fig_decomp = empty

    # ── Taxa de crescimento mensal ──
    growth_rate = monthly_hist.pct_change() * 100
    growth_rate = growth_rate.dropna()

    colors_gr = [COLORS['success'] if v >= 0 else COLORS['danger'] for v in growth_rate.values]
    fig_growth = go.Figure()
    fig_growth.add_trace(go.Bar(
        x=list(growth_rate.index), y=growth_rate.values,
        marker_color=colors_gr, marker_opacity=0.85,
        name='Taxa M/M',
        hovertemplate='<b>%{x}</b><br>Crescimento: %{y:+.1f}%<extra></extra>',
    ))

    ma3 = growth_rate.rolling(3).mean()
    fig_growth.add_trace(go.Scatter(
        x=list(ma3.index), y=ma3.values,
        mode='lines', name='Média Móvel 3M',
        line=dict(color=COLORS['warning'], width=2),
        hovertemplate='<b>%{x}</b><br>MM3: %{y:+.1f}%<extra></extra>',
    ))
    fig_growth.add_hline(y=0, line_dash='solid', line_color=COLORS['border'], line_width=1)
    fig_growth.update_layout(
        title='Taxa de Crescimento Mensal M/M (%)',
        xaxis_title='', yaxis_title='%',
        legend=dict(orientation='h', y=1.1),
        height=280,
    )

    # ── Coorte ──
    df_cohort_src = get_liquid()
    primeira_nf = df_cohort_src.groupby('Nome')['Emissao'].min().reset_index()
    primeira_nf.columns = ['Nome', 'primeira_nf']
    primeira_nf['CoorteAno'] = primeira_nf['primeira_nf'].dt.year.astype(str)

    df_cohort_merge = df_cohort_src.merge(primeira_nf, on='Nome')
    df_cohort_merge['meses_desde_inicio'] = (
        (df_cohort_merge['Emissao'].dt.to_period('M') - df_cohort_merge['primeira_nf'].dt.to_period('M'))
        .apply(lambda x: x.n if hasattr(x, 'n') else 0)
    )
    df_cohort_merge = df_cohort_merge[df_cohort_merge['meses_desde_inicio'] <= 23]

    cohort_data = df_cohort_merge.groupby(['CoorteAno', 'meses_desde_inicio'])['Nome'].nunique().unstack(fill_value=0)
    cohort_size = cohort_data[0] if 0 in cohort_data.columns else cohort_data.iloc[:, 0]
    cohort_pct = cohort_data.div(cohort_size, axis=0) * 100
    cohort_pct = cohort_pct.iloc[:, :13]

    if cohort_pct.empty:
        fig_cohort = empty
    else:
        fig_cohort = go.Figure(go.Heatmap(
            z=cohort_pct.values,
            x=[f'Mês {c}' for c in cohort_pct.columns],
            y=cohort_pct.index.tolist(),
            colorscale=[[0, COLORS['surface2']], [0.5, COLORS['primary_dark']], [1, COLORS['primary']]],
            hovertemplate='<b>Coorte %{y} · %{x}</b><br>Retenção: %{z:.1f}%<extra></extra>',
            text=[[f'{v:.0f}%' for v in row] for row in cohort_pct.values],
            texttemplate='%{text}',
            showscale=True,
            colorbar=dict(title='Retenção %', tickfont=dict(color=COLORS['text_secondary'])),
            zmin=0, zmax=100,
        ))
        fig_cohort.update_layout(
            title='Análise de Coorte · Retenção de Clientes por Ano de Aquisição',
            xaxis_title='Meses após primeira NF',
            yaxis_title='Ano da primeira NF',
            height=280,
        )

    return fig_series, fig_szn, fig_decomp, fig_growth, fig_cohort
