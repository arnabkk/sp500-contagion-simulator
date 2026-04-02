"""Provides an interactive Dash web app for visualizing the S&P 500 market crash simulation.
Users enter a ticker and crash percentage, and the app displays a network graph and bar chart of affected companies.
"""
from __future__ import annotations

import math
import networkx as nx
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from dash import Dash, html, dcc, Input, Output, State, no_update, ctx

from classes import MarketNetwork, construct_market_network

# Sector colors
SECTOR_COLOURS = {
    'Information Technology': '#4C78A8', 'Health Care': '#54A24B',
    'Financials': '#E45756', 'Consumer Discretionary': '#F58518',
    'Communication Services': '#72B7B2', 'Industrials': '#EECA3B',
    'Consumer Staples': '#B279A2', 'Energy': '#FF9DA6',
    'Utilities': '#9D755D', 'Real Estate': '#BAB0AC', 'Materials': '#D67195',
}
STABLE_COLOUR = 'rgb(76, 175, 80)'


def _format_money(value: float) -> str:
    """Format a dollar value into a human-readable string (e.g. $1.2T, $340B)."""
    abs_val = abs(value)
    if abs_val >= 1e12:
        return f'${value / 1e12:,.1f}T'
    elif abs_val >= 1e9:
        return f'${value / 1e9:,.1f}B'
    elif abs_val >= 1e6:
        return f'${value / 1e6:,.1f}M'
    else:
        return f'${value:,.0f}'


def _scale_market_cap(market_cap: float) -> float:
    """Scale market cap to a reasonable node size using log scaling."""
    if market_cap <= 0:
        return 5
    return max(5, min(28, math.log10(market_cap) * 2.5 - 18))


def _crash_color(crash_pct: float) -> str:
    """Return an RGB color interpolating from green to red based on crash severity."""
    r = int(76 + (239 - 76) * crash_pct)
    g = int(175 - 145 * crash_pct)
    b = int(80 - 12 * crash_pct)
    return f'rgb({r}, {g}, {b})'


def _compute_layout(graph_nx: nx.Graph) -> dict[str, tuple[float, float]]:
    """Compute a spread-out spring layout using only the strongest edges."""
    layout_graph = nx.Graph()
    layout_graph.add_nodes_from(graph_nx.nodes(data=True))
    for u, v, data in graph_nx.edges(data=True):
        if data.get('weight', 0) > 0.85:
            layout_graph.add_edge(u, v, weight=data['weight'])
    return nx.spring_layout(
        layout_graph,
        k=3.5 / math.sqrt(len(layout_graph.nodes)),
        iterations=80, seed=42, scale=2.0
    )


def _make_edge_trace(graph_nx: nx.Graph,
                     pos: dict[str, tuple[float, float]]) -> go.Scatter:
    """Create the edge trace for the network graph."""
    x_edges, y_edges = [], []
    for u, v in graph_nx.edges:
        x_edges += [pos[u][0], pos[v][0], None]
        y_edges += [pos[u][1], pos[v][1], None]
    return go.Scatter(
        x=x_edges, y=y_edges, mode='lines',
        line={'color': 'rgba(100, 120, 160, 0.1)', 'width': 0.4},
        hoverinfo='none', showlegend=False
    )


def _style_figure(fig: go.Figure, title: str) -> None:
    """Apply basic styling to a figure."""
    fig.update_layout(
        title={'text': title, 'x': 0.5},
        showlegend=False, height=650,
        margin={'t': 50, 'l': 10, 'r': 30, 'b': 30},
    )
    fig.update_xaxes(showgrid=False, zeroline=False, visible=False, row=1, col=1)
    fig.update_yaxes(showgrid=False, zeroline=False, visible=False, row=1, col=1)
    fig.update_xaxes(title_text='Loss (%)', row=1, col=2, showgrid=True, zeroline=False)
    fig.update_yaxes(autorange='reversed', row=1, col=2)


def _build_baseline_figure(network: MarketNetwork,
                           graph_nx: nx.Graph,
                           pos: dict[str, tuple[float, float]]) -> go.Figure:
    """Build the baseline figure with nodes colored by sector."""
    fig = make_subplots(rows=1, cols=2, column_widths=[0.6, 0.4], horizontal_spacing=0.1)
    fig.add_trace(_make_edge_trace(graph_nx, pos), row=1, col=1)
    tickers = list(pos.keys())
    colors, sizes, hovers = [], [], []
    for t in tickers:
        c = network.companies[t]
        colors.append(SECTOR_COLOURS.get(c.info.sector, '#999'))
        sizes.append(_scale_market_cap(c.market_cap))
        hovers.append(f"<b>{t}</b><br>{c.info.name}<br>Sector: {c.info.sector}<br>"
                      f"Market Cap: {_format_money(c.market_cap)}")
    fig.add_trace(go.Scatter(
        x=[pos[tk][0] for tk in tickers], y=[pos[tk][1] for tk in tickers],
        mode='markers', marker={'size': sizes, 'color': colors, 'opacity': 0.85},
        text=hovers, hovertemplate='%{text}<extra></extra>', showlegend=False
    ), row=1, col=1)
    fig.add_trace(go.Bar(x=[0], y=['Run a simulation'], orientation='h',
                         showlegend=False), row=1, col=2)
    _style_figure(fig, 'S&P 500 Network — Sector View')
    return fig


def _build_crash_node_data(network: MarketNetwork,
                           tickers: list[str],
                           affected: dict[str, float],
                           original_caps: dict[str, float]) -> tuple[list, list, list, float]:
    """Build node colors, sizes, hover texts, and total loss for crash visualization."""
    colors, sizes, hovers = [], [], []
    total_loss = 0.0
    for tk in tickers:
        company = network.companies[tk]
        if tk in affected:
            loss_pct = 1.0 - affected[tk]
            dollar_loss = original_caps[tk] * loss_pct
            total_loss += dollar_loss
            colors.append(_crash_color(min(loss_pct * 2.5, 1.0)))
            sizes.append(max(_scale_market_cap(original_caps[tk]), 8))
            hovers.append(f"<b>{tk}</b><br>{company.info.name}<br>Loss: {loss_pct:.1%} "
                          f"({_format_money(dollar_loss)})")
        else:
            colors.append(STABLE_COLOUR)
            sizes.append(_scale_market_cap(company.market_cap))
            hovers.append(f"<b>{tk}</b><br>{company.info.name}<br>Stable")
    return colors, sizes, hovers, total_loss


def _add_crash_bar_chart(fig: go.Figure, affected: dict[str, float]) -> tuple[float, list[float]]:
    """Add a bar chart of top 15 most affected companies. Return (max_loss, bar_losses)."""
    sorted_affected = sorted(affected.items(), key=lambda x: x[1])[:15]
    bar_tickers = [tk for tk, _ in sorted_affected]
    bar_losses = [(1.0 - ratio) * 100 for _, ratio in sorted_affected]
    bar_colors = [_crash_color(min((1.0 - affected[tk]) * 2.5, 1.0)) for tk in bar_tickers]
    bar_text = [f'{loss:.1f}%' for loss in bar_losses]
    fig.add_trace(go.Bar(
        x=bar_losses, y=bar_tickers, orientation='h',
        marker={'color': bar_colors}, text=bar_text, textposition='outside',
        showlegend=False
    ), row=1, col=2)
    max_loss = max(bar_losses) if bar_losses else 100
    return max_loss, bar_losses


def _reset_market_state(network: MarketNetwork, original_caps: dict[str, float]) -> None:
    """Reset all companies to their original (pre-crash) state."""
    for ticker in network.companies:
        network.companies[ticker].crashed = False
        network.companies[ticker].crash_percentage = 0.0
        network.companies[ticker].market_cap = original_caps[ticker]


def _build_crash_figure(network: MarketNetwork,
                        graph_nx: nx.Graph,
                        pos: dict[str, tuple[float, float]],
                        crash_info: tuple[str, float],
                        original_caps: dict[str, float]) -> tuple[go.Figure, int, float]:
    """Simulate a crash and build the figure. Return (figure, affected_count, total_loss)."""
    crash_ticker, crash_pct = crash_info
    fig = make_subplots(rows=1, cols=2, column_widths=[0.6, 0.4], horizontal_spacing=0.1)
    affected = network.simulate_crash(crash_ticker, crash_pct)
    fig.add_trace(_make_edge_trace(graph_nx, pos), row=1, col=1)
    tickers = list(pos.keys())
    colors, sizes, hovers, total_loss = _build_crash_node_data(network, tickers, affected, original_caps)
    fig.add_trace(go.Scatter(
        x=[pos[t][0] for t in tickers], y=[pos[t][1] for t in tickers],
        mode='markers', marker={'size': sizes, 'color': colors, 'opacity': 0.9},
        text=hovers, hovertemplate='%{text}<extra></extra>', showlegend=False
    ), row=1, col=1)
    max_loss, _ = _add_crash_bar_chart(fig, affected)
    _reset_market_state(network, original_caps)
    _style_figure(fig, f'{crash_ticker} ({network.companies[crash_ticker].info.name}) — {int(crash_pct * 100)}% Crash')
    fig.update_xaxes(range=[0, max_loss * 1.5], row=1, col=2)
    return fig, len(affected), total_loss


def run_visualization(json_file: str, strength_value: float = 0.7) -> None:
    """Build the market network and launch the Dash app at http://127.0.0.1:8050.

    Preconditions:
        - json_file is a valid path to the S&P 500 JSON data file
        - 0.0 <= strength_value <= 1.0
    """
    network = construct_market_network(json_file, strength_value)
    print(f"Network built: {len(network.companies)} companies")
    graph_nx = network.to_networkx()
    pos = _compute_layout(graph_nx)
    original_caps = {t: c.market_cap for t, c in network.companies.items()}
    app = Dash(__name__, title='S&P 500 Crash Simulator')
    app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'}, children=[
        html.H1('S&P 500 Market Crash Simulator'),
        html.P('Simulating financial contagion across the S&P 500 during COVID-19 (2020)'),
        # controls and buttons
        html.Div(style={'display': 'flex', 'gap': '10px', 'alignItems': 'flex-end',
                        'marginBottom': '10px'}, children=[
            html.Div([
                html.Label('Ticker'),
                dcc.Input(id='ticker-input', type='text', placeholder='AAPL',
                          style={'display': 'block', 'padding': '6px', 'width': '100px'}),
            ]),
            html.Div([
                html.Label('Crash %'),
                dcc.Input(id='crash-input', type='number', placeholder='50',
                          min=1, max=100, step=1,
                          style={'display': 'block', 'padding': '6px', 'width': '80px'}),
            ]),
            html.Button('Simulate', id='simulate-btn', n_clicks=0,
                        style={'padding': '8px 20px', 'backgroundColor': '#E45756',
                               'color': 'white', 'border': 'none', 'cursor': 'pointer'}),
            html.Button('Reset', id='reset-btn', n_clicks=0,
                        style={'padding': '8px 20px', 'cursor': 'pointer'}),
            html.Span(id='error-msg', style={'color': 'red', 'fontWeight': 'bold'}),
        ]),
        # company info box (keep hidden until simulation runs)
        html.Div(id='company-info', style={'marginBottom': '10px'}),
        html.Div(id='stats-line', style={'marginBottom': '10px', 'fontSize': '14px'}),
        dcc.Graph(id='crash-graph',
                  figure=_build_baseline_figure(network, graph_nx, pos),
                  config={'displaylogo': False}),
    ])

    @app.callback(
        Output('crash-graph', 'figure'),
        Output('error-msg', 'children'),
        Output('stats-line', 'children'),
        Output('company-info', 'children'),
        Input('simulate-btn', 'n_clicks'),
        Input('reset-btn', 'n_clicks'),
        State('ticker-input', 'value'),
        State('crash-input', 'value'),
    )
    def update_graph(_sim_clicks: int, _reset_clicks: int,
                     ticker_val: str | None, crash_val: float | None) -> tuple:
        """Update the graph based on user inputs."""
        triggered = ctx.triggered_id
        if triggered == 'reset-btn':
            return _build_baseline_figure(network, graph_nx, pos), '', '', ''
        if triggered != 'simulate-btn':
            return no_update, '', no_update, no_update
        if not ticker_val or not ticker_val.strip():
            return no_update, 'Enter a ticker symbol.', no_update, no_update
        ticker = ticker_val.strip().upper()
        if ticker not in network.companies:
            return no_update, f'"{ticker}" not found.', no_update, no_update
        if crash_val is None or crash_val < 1 or crash_val > 100:
            return no_update, 'Crash % must be 1-100.', no_update, no_update
        fig, affected_count, total_loss = _build_crash_figure(
            network, graph_nx, pos, (ticker, crash_val / 100.0), original_caps
        )
        stats = f'Companies affected: {affected_count} | Total loss: {_format_money(total_loss)}'
        # build company info card
        company = network.companies[ticker]
        info_card = html.Div(
            style={'padding': '10px', 'border': '1px solid #ccc',
                   'borderRadius': '5px', 'backgroundColor': '#f9f9f9',
                   'maxWidth': '400px'},
            children=[
                html.H3(f'{company.info.name} ({ticker})', style={'margin': '0 0 5px 0'}),
                html.P(f'Sector: {company.info.sector}'),
                html.P(f'Sub-Industry: {company.info.sub_industry}'),
                html.P(f'Headquarters: {company.info.hq_location}'),
                html.P(f'Founded: {company.info.founded}'),
                html.P(f'Market Cap: {_format_money(original_caps[ticker])}'),
            ]
        )
        return fig, '', stats, info_card
    print("Server at http://127.0.0.1:8050 - Ctrl + C to stop.")
    app.run(debug=False)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['math', 'networkx', 'plotly.graph_objs',
                          'plotly.subplots', 'dash', 'classes'],
        'allowed-io': ['run_visualization'],
        'max-line-length': 120
    })
