"""CSC111 Winter 2026 Project 2: S&P 500 Market Crash Simulator (Visualization — No HTML)

Module Description
==================

This module provides interactive visualization of the S&P 500 market crash simulation
using NetworkX for graph layout and Plotly for rendering. User interaction happens
entirely through the terminal — no Dash, no HTML.

Copyright and Usage Information
===============================

This file is Copyright (c) 2026 Arnab Karmokar, Brian Chang, Derek Sun, Johnny Li
"""
from __future__ import annotations

import math
import networkx as nx
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from classes import MarketNetwork, construct_market_network

# GICS Sector color mapping
SECTOR_COLOURS = {
    'Information Technology': '#4C78A8',
    'Health Care': '#54A24B',
    'Financials': '#E45756',
    'Consumer Discretionary': '#F58518',
    'Communication Services': '#72B7B2',
    'Industrials': '#EECA3B',
    'Consumer Staples': '#B279A2',
    'Energy': '#FF9DA6',
    'Utilities': '#9D755D',
    'Real Estate': '#BAB0AC',
    'Materials': '#D67195',
}

STABLE_COLOUR = 'rgb(76, 175, 80)'
BG_CARD = '#1a1d29'
BG_GRAPH = '#141720'
TEXT_PRIMARY = '#e8eaed'
TEXT_SECONDARY = '#9aa0a6'
ACCENT_RED = '#ef4444'


def _format_money(value: float) -> str:
    """Format a dollar value into a human-readable string (e.g. $1.2T, $340B, $5.6M)."""
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
    """Return an RGB color string interpolating from green to red based on crash severity."""
    r = int(76 + (239 - 76) * crash_pct)
    g = int(175 - 145 * crash_pct)
    b = int(80 - 12 * crash_pct)
    return f'rgb({r}, {g}, {b})'


def _compute_layout(graph_nx: nx.Graph) -> dict[str, tuple[float, float]]:
    """Compute a spread-out layout by using only the strongest edges for positioning."""
    layout_graph = nx.Graph()
    layout_graph.add_nodes_from(graph_nx.nodes(data=True))
    for u, v, data in graph_nx.edges(data=True):
        if data.get('weight', 0) > 0.85:
            layout_graph.add_edge(u, v, weight=data['weight'])

    pos = nx.spring_layout(
        layout_graph,
        k=3.5 / math.sqrt(len(layout_graph.nodes)),
        iterations=80,
        seed=42,
        scale=2.0
    )
    return pos


def _make_edge_trace(graph_nx: nx.Graph,
                     pos: dict[str, tuple[float, float]]) -> go.Scatter:
    """Create the edge trace for the network graph."""
    x_edges, y_edges = [], []
    for u, v in graph_nx.edges:
        x_edges += [pos[u][0], pos[v][0], None]
        y_edges += [pos[u][1], pos[v][1], None]
    return go.Scatter(
        x=x_edges, y=y_edges, mode='lines',
        line=dict(color='rgba(100, 120, 160, 0.08)', width=0.4),
        hoverinfo='none', showlegend=False
    )


def _style_figure(fig: go.Figure, title: str) -> None:
    """Apply consistent dark-theme styling to a figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=TEXT_PRIMARY), x=0.5, y=0.98),
        showlegend=False,
        plot_bgcolor=BG_GRAPH,
        paper_bgcolor=BG_CARD,
        height=680,
        margin=dict(t=50, l=10, r=30, b=30),
        font=dict(color=TEXT_SECONDARY),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, visible=False, row=1, col=1)
    fig.update_yaxes(showgrid=False, zeroline=False, visible=False, row=1, col=1)
    fig.update_xaxes(
        title_text='Loss (%)', row=1, col=2,
        gridcolor='rgba(100,120,160,0.15)', showgrid=True, zeroline=False,
        tickfont=dict(color=TEXT_SECONDARY, size=10),
        title_font=dict(color=TEXT_SECONDARY, size=11)
    )
    fig.update_yaxes(
        autorange='reversed', row=1, col=2,
        tickfont=dict(color=TEXT_PRIMARY, size=11),
        gridcolor='rgba(100,120,160,0.08)'
    )


def _build_baseline_figure(network: MarketNetwork,
                           graph_nx: nx.Graph,
                           pos: dict[str, tuple[float, float]]) -> go.Figure:
    """Build the baseline figure with nodes colored by sector and no crash applied."""
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.62, 0.38],
        horizontal_spacing=0.12
    )

    fig.add_trace(_make_edge_trace(graph_nx, pos), row=1, col=1)

    tickers = list(pos.keys())
    x_vals = [pos[t][0] for t in tickers]
    y_vals = [pos[t][1] for t in tickers]
    colors, sizes, hover_texts = [], [], []

    for t in tickers:
        c = network.companies[t]
        colors.append(SECTOR_COLOURS.get(c.sector, '#999999'))
        sizes.append(_scale_market_cap(c.market_cap))
        hover_texts.append(
            f"<b>{t}</b><br>"
            f"{c.name}<br>"
            f"Sector: {c.sector}<br>"
            f"Market Cap: {_format_money(c.market_cap)}"
        )

    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals, mode='markers',
        marker=dict(size=sizes, color=colors, opacity=0.85,
                    line=dict(color='rgba(255,255,255,0.3)', width=0.5)),
        text=hover_texts, hovertemplate='%{text}<extra></extra>', showlegend=False
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=[0], y=['Simulate a crash to see results'],
        orientation='h', marker=dict(color='rgba(100,120,160,0.3)'), showlegend=False
    ), row=1, col=2)

    _style_figure(fig, 'S&P 500 Network — Sector View')
    return fig


def _build_crash_figure(network: MarketNetwork,
                        graph_nx: nx.Graph,
                        pos: dict[str, tuple[float, float]],
                        crash_ticker: str,
                        crash_pct: float,
                        original_caps: dict[str, float]) -> go.Figure:
    """Simulate a crash and build the resulting figure.

    Returns the figure after resetting the network state.
    """
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.62, 0.38],
        horizontal_spacing=0.12
    )

    affected = network.simulate_crash(crash_ticker, crash_pct)

    fig.add_trace(_make_edge_trace(graph_nx, pos), row=1, col=1)

    tickers = list(pos.keys())
    x_vals = [pos[t][0] for t in tickers]
    y_vals = [pos[t][1] for t in tickers]
    colors, sizes, hover_texts, symbols = [], [], [], []

    total_loss = 0.0
    for t in tickers:
        c = network.companies[t]
        if t in affected:
            loss_pct = 1.0 - affected[t]
            dollar_loss = original_caps[t] * loss_pct
            total_loss += dollar_loss
            colors.append(_crash_color(min(loss_pct * 2.5, 1.0)))
            sizes.append(max(_scale_market_cap(original_caps[t]), 8))
            hover_texts.append(
                f"<b>{t}</b><br>{c.name}<br>Sector: {c.sector}<br>"
                f"Loss: {loss_pct:.1%} ({_format_money(dollar_loss)})"
            )
        else:
            colors.append(STABLE_COLOUR)
            sizes.append(_scale_market_cap(c.market_cap))
            hover_texts.append(
                f"<b>{t}</b><br>{c.name}<br>Sector: {c.sector}<br>"
                f"Market Cap: {_format_money(c.market_cap)}<br>Status: Stable"
            )

        if t == crash_ticker:
            symbols.append('star')
            sizes[-1] = max(sizes[-1], 16)
        else:
            symbols.append('circle-dot')

    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals, mode='markers',
        marker=dict(size=sizes, color=colors, symbol=symbols, opacity=0.9,
                    line=dict(color='rgba(255,255,255,0.4)', width=0.5)),
        text=hover_texts, hovertemplate='%{text}<extra></extra>', showlegend=False
    ), row=1, col=1)

    # Bar chart — top 15 most affected
    sorted_affected = sorted(affected.items(), key=lambda x: x[1])[:15]
    bar_tickers = [t for t, _ in sorted_affected]
    bar_losses = [(1.0 - ratio) * 100 for _, ratio in sorted_affected]
    bar_labels = [f"{t}" for t in bar_tickers]
    bar_colors = [_crash_color(min((1.0 - affected[t]) * 2.5, 1.0)) for t in bar_tickers]

    bar_hovers = []
    for t, ratio in sorted_affected:
        loss_pct = 1.0 - ratio
        dollar_loss = original_caps[t] * loss_pct
        c = network.companies[t]
        bar_hovers.append(
            f"<b>{t}</b> ({c.name})<br>"
            f"Loss: {loss_pct:.1%}<br>"
            f"Market Cap Lost: {_format_money(dollar_loss)}"
        )

    bar_text = []
    for t, ratio in sorted_affected:
        loss_pct = 1.0 - ratio
        dollar_loss = original_caps[t] * loss_pct
        bar_text.append(f" {loss_pct:.1%}  |  {_format_money(dollar_loss)}")

    fig.add_trace(go.Bar(
        x=bar_losses, y=bar_labels, orientation='h',
        marker=dict(color=bar_colors, line=dict(color='rgba(255,255,255,0.1)', width=0.5)),
        text=bar_text,
        textposition='outside',
        textfont=dict(size=10, color=TEXT_SECONDARY),
        customdata=bar_hovers,
        hovertemplate='%{customdata}<extra></extra>',
        showlegend=False
    ), row=1, col=2)

    # Reset market state
    for t in network.companies:
        network.companies[t].crashed = False
        network.companies[t].crash_percentage = 0.0
        network.companies[t].market_cap = original_caps[t]

    company_name = network.companies[crash_ticker].name
    title = f'{crash_ticker} ({company_name}) — {int(crash_pct * 100)}% Crash'
    _style_figure(fig, title)

    max_loss = max(bar_losses) if bar_losses else 100
    fig.update_xaxes(range=[0, max_loss * 1.6], row=1, col=2)

    # Print stats to terminal
    print(f"\n--- Crash Results ---")
    print(f"Companies Affected: {len(affected)}")
    print(f"Total Market Loss:  {_format_money(total_loss)}")

    return fig


def run_visualization(json_file: str, strength_value: float = 0.7) -> None:
    """Build the market network and launch the interactive terminal-based visualization.

    Uses terminal input for crash parameters and opens Plotly figures in the browser.
    Press Ctrl+C to exit.

    Preconditions:
        - json_file is a valid path to the S&P 500 JSON data file
        - 0.0 <= strength_value <= 1.0
    """
    print("Building market network...")
    network = construct_market_network(json_file, strength_value)

    total_companies = len(network.companies)
    total_edges = sum(len(c.neighbors) for c in network.companies.values()) // 2
    total_market_cap = sum(c.market_cap for c in network.companies.values())
    print(f"Network built: {total_companies} companies, {total_edges} edges (r >= {strength_value})")
    print(f"Total Market Cap: {_format_money(total_market_cap)}")

    print("Computing graph layout...")
    graph_nx = network.to_networkx()
    pos = _compute_layout(graph_nx)
    original_caps = {t: c.market_cap for t, c in network.companies.items()}

    # Show the baseline sector view
    print("Opening baseline network view...")
    baseline_fig = _build_baseline_figure(network, graph_nx, pos)
    baseline_fig.show()

    # Interactive loop
    print("\n=== S&P 500 Market Crash Simulator ===")
    print("Enter a ticker and crash % to simulate, or type 'quit' to exit.\n")

    while True:
        ticker_input = input("Ticker (e.g. AAPL): ").strip().upper()
        if ticker_input in ('QUIT', 'EXIT', 'Q'):
            print("Exiting simulator.")
            break

        if ticker_input not in network.companies:
            print(f'Ticker "{ticker_input}" not found in S&P 500. Try again.')
            continue

        crash_input = input("Crash % (1-100): ").strip()
        try:
            crash_val = int(crash_input)
            if crash_val < 1 or crash_val > 100:
                print("Crash % must be between 1 and 100. Try again.")
                continue
        except ValueError:
            print("Invalid number. Try again.")
            continue

        crash_pct = crash_val / 100.0
        fig = _build_crash_figure(network, graph_nx, pos, ticker_input, crash_pct, original_caps)
        fig.show()
        print()


if __name__ == '__main__':
    DATA_FILE = 'sp500_covid_data.json'
    STRENGTH_THRESHOLD = 0.7
    run_visualization(DATA_FILE, STRENGTH_THRESHOLD)
