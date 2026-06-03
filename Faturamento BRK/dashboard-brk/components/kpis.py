from dash import html
import numbers
from components.theme import fmt_brl, fmt_pct, COLORS


def kpi_card(label, value, icon, delta=None, context=None, value_fmt='brl'):
    # Converte para float nativo (resolve float32/float64 do numpy)
    try:
        value = float(value)
    except (TypeError, ValueError):
        pass

    if value_fmt == 'brl':
        val_str = fmt_brl(value) if isinstance(value, numbers.Real) else str(value)
    elif value_fmt == 'int':
        val_str = f'{int(value):,}'.replace(',', '.')
    elif value_fmt == 'pct':
        val_str = f'{value:.1f}%' if isinstance(value, numbers.Real) else str(value)
    else:
        val_str = str(value)

    delta_el = []
    if delta is not None:
        cls = 'positive' if delta > 0 else ('negative' if delta < 0 else 'neutral')
        delta_el = [html.Span(fmt_pct(delta), className=f'kpi-delta {cls}')]

    ctx_el = []
    if context:
        ctx_el = [html.Span(context, className='kpi-context')]

    return html.Div(
        [
            html.Div(
                [
                    html.Span(label, className='kpi-label'),
                    html.Span(icon, className='kpi-icon'),
                ],
                className='kpi-card-header',
            ),
            html.Div(val_str, className='kpi-value'),
            html.Div(delta_el + ctx_el, className='kpi-footer'),
        ],
        className='kpi-card',
    )


def kpi_grid(cards):
    return html.Div(cards, className='kpi-grid')
