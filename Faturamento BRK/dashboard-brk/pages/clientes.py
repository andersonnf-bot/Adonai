import dash
from dash import html, dcc, callback, Input, Output, dash_table
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from data.loader import get_liquid, apply_filters
from components.theme import COLORS, fmt_brl, CHART_COLORS

dash.register_page(__name__, path='/clientes', name='Clientes', order=1)

_TABLE_STYLE = {
    'style_table': {'overflowX': 'auto', 'borderRadius': '8px'},
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
        {'if': {'filter_query': '{Status} = "🚀 Crescendo"'}, 'color': COLORS['success']},
        {'if': {'filter_query': '{Status} = "🔴 Churn Risk"'}, 'color': '#FF8080'},
        {'if': {'filter_query': '{Status} = "⚫ Inativo"'}, 'color': COLORS['text_muted']},
        {'if': {'filter_query': '{Status} = "📉 Em queda"'}, 'color': COLORS['danger']},
    ],
}

layout = html.Div([
    html.Div([
        html.Div('Análise de Clientes', className='page-title'),
        html.Div(f'Todos os clientes · faturamento completo por período', className='page-subtitle'),
    ], className='page-header'),

    html.Div([
        html.Div([
            html.Div([
                html.Div('Receita Total por Cliente', className='chart-title'),
                html.Div('Ranking completo · ordenável · paginado', className='chart-subtitle'),
            ], className='chart-card-header'),
            dash_table.DataTable(
                id='clientes-table',
                page_size=20,
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


def _compute_status(row, now):
    dias = (now - row['ultima_nf']).days if pd.notna(row['ultima_nf']) else 9999
    mom = row['var_mom']
    if dias >= 180:
        return '⚫ Inativo'
    if dias >= 60:
        return '🔴 Churn Risk'
    if pd.notna(mom) and mom >= 15:
        return '🚀 Crescendo'
    if pd.notna(mom) and mom <= -15:
        return '📉 Em queda'
    return '➡️ Estável'


@callback(
    Output('clientes-table', 'data'),
    Output('clientes-table', 'columns'),
    Input('filter-date', 'start_date'),
    Input('filter-date', 'end_date'),
    Input('filter-ano', 'value'),
    Input('filter-cliente', 'value'),
    Input('filter-produto', 'value'),
    Input('filter-valor-min', 'value'),
    Input('filter-valor-max', 'value'),
)
def update_table(start_date, end_date, anos, cliente, produto, valor_min, valor_max):
    df_all = get_liquid()
    df = apply_filters(df_all, start_date, end_date, anos, cliente, produto, valor_min, valor_max)
    if serie and serie != 'ALL':
        df = df[df['Serie'] == serie]

    if df.empty:
        return [], []

    now = df['Emissao'].max()

    monthly = df.groupby(['Nome', 'AnoMesStr'])['Vlr.Total'].sum().unstack(fill_value=0)
    months_sorted = sorted(monthly.columns)
    monthly = monthly[months_sorted]

    agg = df.groupby('Nome').agg(
        receita=('Vlr.Total', 'sum'),
        nfs=('Num. Docto.', 'nunique'),
        servicos=('Descricao', 'nunique'),
        quantidade=('Quantidade', 'sum'),
        ultima_nf=('Emissao', 'max'),
        primeira_nf=('Emissao', 'min'),
    ).reset_index()

    if len(months_sorted) >= 2:
        agg['ult_mes'] = agg['Nome'].map(monthly[months_sorted[-1]])
        agg['pen_mes'] = agg['Nome'].map(monthly[months_sorted[-2]])
        agg['var_mom'] = ((agg['ult_mes'] - agg['pen_mes']) / agg['pen_mes'].replace(0, np.nan) * 100)
    else:
        agg['ult_mes'] = agg['receita']
        agg['pen_mes'] = np.nan
        agg['var_mom'] = np.nan

    agg['dias_sem_nf'] = (now - agg['ultima_nf']).dt.days
    agg['ticket_medio'] = agg['receita'] / agg['nfs'].replace(0, np.nan)
    agg['Status'] = agg.apply(_compute_status, axis=1, now=now)
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
            'Cliente': r['Nome'] + novo_tag,
            'Receita Total': f"R$ {r['receita']:,.0f}",
            '% da Carteira': f"{r['pct_total']:.2f}%",
            'Último Mês': f"R$ {r['ult_mes']:,.0f}" if pd.notna(r['ult_mes']) else '—',
            'Var. M/M': f"{r['var_mom']:+.1f}%" if pd.notna(r['var_mom']) else '—',
            'NFs': int(r['nfs']),
            'Serviços': int(r['servicos']),
            'Ticket Médio NF': f"R$ {r['ticket_medio']:,.0f}" if pd.notna(r['ticket_medio']) else '—',
            'Última NF': r['ultima_nf'].strftime('%d/%m/%Y') if pd.notna(r['ultima_nf']) else '—',
            'Dias sem NF': int(r['dias_sem_nf']) if pd.notna(r['dias_sem_nf']) else '—',
            'Status': r['Status'],
        })

    columns = [{'name': c, 'id': c, 'type': 'text'} for c in records[0].keys()] if records else []

    return records, columns


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
)
def update_detail(active_cell, table_data, start_date, end_date, anos, cliente, produto, valor_min, valor_max):
    if not active_cell or not table_data:
        return html.Div(
            '👆 Clique em um cliente na tabela para ver análise detalhada.',
            style={'color': COLORS['text_muted'], 'padding': '16px', 'fontSize': '13px'},
        )

    row = table_data[active_cell['row']]
    nome = row['Cliente'].replace(' ✨', '').strip()

    df_all = get_liquid()
    df_base = apply_filters(df_all, start_date, end_date, anos, None, produto, valor_min, valor_max)
    if serie and serie != 'ALL':
        df_base = df_base[df_base['Serie'] == serie]

    df_cli = df_base[df_base['Nome'] == nome]
    if df_cli.empty:
        return html.Div('Sem dados para este cliente no período.', style={'color': COLORS['text_muted']})

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
        title=f'Evolução Mensal · {nome}',
        xaxis_title='', yaxis_title='R$',
        yaxis_tickformat=',.0f',
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
        title=f'Mix de Serviços · {nome}',
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
        columns=[{'name': c, 'id': c} for c in ['Serviço', 'Receita', '% do Cliente']],
        page_size=15,
        sort_action='native',
        style_table={'borderRadius': '8px', 'overflowX': 'auto'},
        style_header={**_TABLE_STYLE['style_header']},
        style_cell={**_TABLE_STYLE['style_cell']},
        style_data_conditional=_TABLE_STYLE['style_data_conditional'],
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
        columns=[{'name': c, 'id': c} for c in ['Número NF', 'Data', 'Serie', 'Valor', 'Itens']],
        page_size=10,
        sort_action='native',
        style_table={'borderRadius': '8px', 'overflowX': 'auto'},
        style_header={**_TABLE_STYLE['style_header']},
        style_cell={**_TABLE_STYLE['style_cell']},
        style_data_conditional=_TABLE_STYLE['style_data_conditional'],
    )

    receita_total_cli = df_cli['Vlr.Total'].sum()
    receita_total_cart = df_base['Vlr.Total'].sum()
    pct_carteira = receita_total_cli / receita_total_cart * 100 if receita_total_cart > 0 else 0

    return html.Div([
        html.Div([
            html.Div(nome, style={'fontSize': '16px', 'fontWeight': '700', 'color': COLORS['text']}),
            html.Div([
                html.Span(f'{fmt_brl(receita_total_cli)}', style={'fontSize': '20px', 'fontWeight': '700', 'color': COLORS['primary']}),
                html.Span(f' · {pct_carteira:.2f}% da carteira', style={'fontSize': '13px', 'color': COLORS['text_secondary'], 'marginLeft': '8px'}),
            ]),
        ], style={'marginBottom': '20px', 'paddingBottom': '16px', 'borderBottom': f'1px solid {COLORS["border"]}'}),

        html.Div([
            html.Div([
                html.Div([
                    html.Div('Evolução Mensal', className='chart-title'),
                ], className='chart-card-header'),
                dcc.Graph(figure=fig_evo, config={'displayModeBar': False}),
            ], className='chart-card'),
            html.Div([
                html.Div([
                    html.Div('Mix de Serviços', className='chart-title'),
                ], className='chart-card-header'),
                dcc.Graph(figure=fig_mix, config={'displayModeBar': False}),
            ], className='chart-card'),
        ], className='grid-2'),

        html.Div([
            html.Div([
                html.Div([
                    html.Div('Todos os Serviços Contratados', className='chart-title'),
                ], className='chart-card-header'),
                svc_table,
            ], className='chart-card'),
            html.Div([
                html.Div([
                    html.Div('Notas Fiscais Emitidas', className='chart-title'),
                ], className='chart-card-header'),
                nfs_table,
            ], className='chart-card'),
        ], className='grid-2'),
    ], className='chart-card')
