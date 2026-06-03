import pandas as pd
import numpy as np
from dash import html


def _item(icon, text_html, kind='info'):
    return html.Div(
        [
            html.Span(icon, className='insight-icon'),
            html.Div(text_html, className='insight-text'),
        ],
        className=f'insight-item {kind}',
    )


def compute_insights(df: pd.DataFrame) -> list:
    insights = []
    if df.empty:
        return [_item('ℹ️', html.Span('Sem dados para o período selecionado.'), 'info')]

    now = df['Emissao'].max()

    # ── Receita mensal recente ──
    monthly = (
        df.groupby('AnoMesStr')['Vlr.Total'].sum()
        .sort_index()
    )

    if len(monthly) >= 3:
        last = monthly.iloc[-1]
        prev = monthly.iloc[-2]
        if prev > 0:
            delta = (last - prev) / prev * 100
            if delta < -10:
                insights.append(_item(
                    '🔴',
                    html.Span([
                        'Queda de ',
                        html.Strong(f'{abs(delta):.1f}%'),
                        f' na receita do último mês ({monthly.index[-1]}) vs. mês anterior.',
                    ]),
                    'critical',
                ))
            elif delta > 15:
                insights.append(_item(
                    '🚀',
                    html.Span([
                        'Crescimento de ',
                        html.Strong(f'{delta:.1f}%'),
                        f' na receita do último mês ({monthly.index[-1]}) vs. mês anterior.',
                    ]),
                    'positive',
                ))

    # ── Concentração ──
    client_rev = df.groupby('GrupoEcon')['Vlr.Total'].sum()
    total = client_rev.sum()
    top10_pct = client_rev.nlargest(10).sum() / total * 100 if total > 0 else 0
    if top10_pct > 40:
        insights.append(_item(
            '⚠️',
            html.Span([
                html.Strong(f'{top10_pct:.1f}%'),
                ' da receita concentrada nos Top 10 clientes — risco de dependência.',
            ]),
            'warning',
        ))

    # ── Churn risk ──
    ultima_nf = df.groupby('GrupoEcon')['Emissao'].max()
    churn_risk = ultima_nf[(now - ultima_nf).dt.days.between(60, 179)]
    if len(churn_risk) > 0:
        insights.append(_item(
            '🔶',
            html.Span([
                html.Strong(f'{len(churn_risk)} clientes'),
                ' sem faturamento nos últimos 60–179 dias — risco de churn.',
            ]),
            'warning',
        ))

    inativos = ultima_nf[(now - ultima_nf).dt.days >= 180]
    if len(inativos) > 0:
        insights.append(_item(
            '🔴',
            html.Span([
                html.Strong(f'{len(inativos)} clientes'),
                ' inativos (sem NF há 180+ dias).',
            ]),
            'critical',
        ))

    # ── Melhor cliente ──
    if not client_rev.empty:
        top_cli = client_rev.idxmax()
        top_val = client_rev.max()
        from components.theme import fmt_brl
        insights.append(_item(
            '🏆',
            html.Span([
                'Maior cliente: ',
                html.Strong(top_cli),
                f' com {fmt_brl(top_val)} no período.',
            ]),
            'positive',
        ))

    # ── Serviço em crescimento ──
    if len(monthly) >= 6:
        prod_monthly = df.groupby(['AnoMesStr', 'Descricao'])['Vlr.Total'].sum().unstack(fill_value=0)
        recent_3 = prod_monthly.iloc[-3:].sum()
        prev_3 = prod_monthly.iloc[-6:-3].sum()
        growth = ((recent_3 - prev_3) / prev_3.replace(0, np.nan) * 100).dropna()
        if not growth.empty:
            top_growth_svc = growth.idxmax()
            top_growth_val = growth.max()
            if top_growth_val > 20:
                insights.append(_item(
                    '📈',
                    html.Span([
                        'Serviço em aceleração: ',
                        html.Strong(top_growth_svc.title()),
                        f' (+{top_growth_val:.1f}% últimos 3 meses vs. anteriores).',
                    ]),
                    'positive',
                ))

    # ── Novos clientes ──
    first_nf = df.groupby('GrupoEcon')['Emissao'].min()
    cutoff = now - pd.Timedelta(days=90)
    novos = first_nf[first_nf >= cutoff]
    if len(novos) > 0:
        insights.append(_item(
            '✨',
            html.Span([
                html.Strong(f'{len(novos)} novos clientes'),
                ' incorporados nos últimos 90 dias.',
            ]),
            'positive',
        ))

    # ── Serviço único cliente ──
    svc_clients = df.groupby('Descricao')['GrupoEcon'].nunique()
    mono = svc_clients[svc_clients == 1]
    if len(mono) > 0:
        insights.append(_item(
            '🔍',
            html.Span([
                html.Strong(f'{len(mono)} serviços'),
                ' são consumidos por apenas 1 cliente — risco de concentração de produto.',
            ]),
            'warning',
        ))

    return insights if insights else [_item('✅', html.Span('Nenhum alerta identificado para o período.'), 'positive')]


def insight_panel(df: pd.DataFrame):
    items = compute_insights(df)
    return html.Div(
        [
            html.Div(
                ['⚡ ', html.Span('Inteligência Automática de Negócio')],
                className='insight-panel-title',
            ),
            html.Div(items, className='insight-grid'),
        ],
        className='insight-panel',
    )
