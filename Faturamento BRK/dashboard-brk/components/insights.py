import pandas as pd
import numpy as np
from dash import html

from data.loader import last_month_is_partial
from components.i18n import t as _t


def _pt(v, dec=1):
    """Número com vírgula decimal (pt-BR)."""
    return f'{v:.{dec}f}'.replace('.', ',')


def _item(icon, text_html, kind='info'):
    return html.Div(
        [
            html.Span(icon, className='insight-icon'),
            html.Div(text_html, className='insight-text'),
        ],
        className=f'insight-item {kind}',
    )


def compute_insights(df: pd.DataFrame, lang: str = 'pt') -> list:
    insights = []
    if df.empty:
        return [_item('ℹ️', html.Span(_t('i_sem_dados', lang)), 'info')]

    now = df['Emissao'].max()

    # ── Receita mensal recente ──
    monthly = (
        df.groupby('AnoMesStr', observed=True)['Vlr.Total'].sum()
        .sort_index()
    )
    # mês parcial fora da comparação — evita alerta falso de queda
    if last_month_is_partial(df) and len(monthly) >= 2:
        monthly = monthly.iloc[:-1]

    if len(monthly) >= 3:
        last = monthly.iloc[-1]
        prev = monthly.iloc[-2]
        if prev > 0:
            delta = (last - prev) / prev * 100
            if delta < -10:
                insights.append(_item(
                    '🔴',
                    html.Span([
                        _t('i_queda_pre', lang),
                        html.Strong(f'{_pt(abs(delta))}%'),
                        _t('i_queda_pos', lang, mes=monthly.index[-1]),
                    ]),
                    'critical',
                ))
            elif delta > 15:
                insights.append(_item(
                    '🚀',
                    html.Span([
                        _t('i_cresc_pre', lang),
                        html.Strong(f'{_pt(delta)}%'),
                        _t('i_cresc_pos', lang, mes=monthly.index[-1]),
                    ]),
                    'positive',
                ))

    # ── Concentração — alerta granular ──
    client_rev = df.groupby('GrupoEcon', observed=True)['Vlr.Total'].sum()
    total = float(client_rev.sum())
    top1_pct  = float(client_rev.max()) / total * 100 if total > 0 else 0
    top5_pct  = float(client_rev.nlargest(5).sum()) / total * 100 if total > 0 else 0
    top10_pct = float(client_rev.nlargest(10).sum()) / total * 100 if total > 0 else 0
    top1_nome = str(client_rev.idxmax()) if total > 0 else '—'

    if top1_pct > 10:
        insights.append(_item(
            '🔴',
            html.Span([
                _t('i_conc_alto_pre', lang),
                html.Strong(top1_nome),
                _t('i_conc_alto_pos', lang, pct=_pt(top1_pct)),
            ]),
            'critical',
        ))
    elif top1_pct > 7:
        insights.append(_item(
            '⚠️',
            html.Span([
                _t('i_conc_pre', lang),
                html.Strong(top1_nome),
                _t('i_conc_pos', lang, pct=_pt(top1_pct)),
            ]),
            'warning',
        ))

    if top10_pct > 40:
        insights.append(_item(
            '⚠️',
            html.Span([
                html.Strong(_t('i_top10_pre', lang, pct=_pt(top10_pct))),
                _t('i_top10_pos', lang, pct5=_pt(top5_pct)),
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
                html.Strong(_t('i_churn_pre', lang, n=len(churn_risk))),
                _t('i_churn_pos', lang),
            ]),
            'warning',
        ))

    inativos = ultima_nf[(now - ultima_nf).dt.days >= 180]
    if len(inativos) > 0:
        insights.append(_item(
            '🔴',
            html.Span([
                html.Strong(_t('i_churn_pre', lang, n=len(inativos))),
                _t('i_inat_pos', lang),
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
                _t('i_maior_pre', lang),
                html.Strong(top_cli),
                _t('i_maior_pos', lang, v=fmt_brl(top_val)),
            ]),
            'positive',
        ))

    # ── Serviço em crescimento ──
    if len(monthly) >= 6:
        prod_monthly = df.groupby(['AnoMesStr', 'Descricao'], observed=True)['Vlr.Total'].sum().unstack(fill_value=0)
        # alinha aos meses completos (sem o parcial) usados acima
        prod_monthly = prod_monthly.reindex(monthly.index, fill_value=0)
        recent_3 = prod_monthly.iloc[-3:].sum()
        prev_3 = prod_monthly.iloc[-6:-3].sum()
        # base mínima de R$ 50 mil — sem isso um serviço pequeno que cresce
        # gera insight de "+7.500%"
        base_ok = prev_3[prev_3 >= 50_000]
        growth = ((recent_3[base_ok.index] - base_ok) / base_ok * 100).dropna()
        if not growth.empty:
            top_growth_svc = growth.idxmax()
            top_growth_val = growth.max()
            if top_growth_val > 300:
                # crescimento explosivo: % vira ruído — mostra os valores
                from components.theme import fmt_brl as _brl
                insights.append(_item(
                    '📈',
                    html.Span([
                        _t('i_exp_pre', lang),
                        html.Strong(top_growth_svc.title()),
                        _t('i_exp_pos', lang,
                           de=_brl(float(base_ok[top_growth_svc])),
                           para=_brl(float(recent_3[top_growth_svc]))),
                    ]),
                    'positive',
                ))
            elif top_growth_val > 20:
                insights.append(_item(
                    '📈',
                    html.Span([
                        _t('i_acel_pre', lang),
                        html.Strong(top_growth_svc.title()),
                        _t('i_acel_pos', lang, pct=_pt(top_growth_val)),
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
                html.Strong(_t('i_novos_pre', lang, n=len(novos))),
                _t('i_novos_pos', lang),
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
                html.Strong(_t('i_mono_pre', lang, n=len(mono))),
                _t('i_mono_pos', lang),
            ]),
            'warning',
        ))

    return insights if insights else [_item('✅', html.Span(_t('i_nada', lang)), 'positive')]


def insight_panel(df: pd.DataFrame, lang: str = 'pt'):
    items = compute_insights(df, lang)
    return html.Div(
        [
            html.Div(
                ['⚡ ', html.Span(_t('i_panel', lang))],
                className='insight-panel-title',
            ),
            html.Div(items, className='insight-grid'),
        ],
        className='insight-panel',
    )
