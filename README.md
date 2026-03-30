# S&P 500 Market Crash Simulator

**Simulating financial contagion across the S&P 500 using an object-oriented graph model.**

> CSC111 Final Project -- University of Toronto, Winter 2026
> Arnab Karmokar, Brian Chang, Derek Sun, Johnny Li

## Overview

When a major company crashes, the effects rarely stay contained. Shared supply chains, sector dependencies, and investor sentiment can trigger a domino effect of losses across the entire market -- a phenomenon known as **financial contagion**.

This project models the S&P 500 as a **weighted graph** where each node represents a company and each edge reflects a correlation in historical price movements during the COVID-19 market downturn (January--August 2020). Users can select any company to initiate a simulated crash and observe in real time how the shock propagates through the network.

**Research Question:** If one company crashes, how does the shock propagate through the S&P 500 network, and which companies are most vulnerable?

## Features

- **Real market data** pulled via `yfinance`, covering the 2020 COVID-19 crash period
- **Deterministic contagion model** where crash impact propagates recursively through correlated companies
- **Interactive web dashboard** built with Dash and Plotly featuring:
  - Crash simulation with user-defined ticker and crash severity
  - Network graph with 503 companies and ~24,000 correlation edges
  - Bar chart of the most affected companies showing both percentage and monetary loss
  - Live stats (companies affected, total market loss, post-crash market cap)
  - Company search with graph highlighting and detailed info card
  - Clickable bar chart entries that auto-populate the search

## How It Works

### Graph Construction

Each S&P 500 company is a `Company` vertex in a `MarketNetwork` graph. Edges are created between two companies if their **Pearson correlation coefficient satisfies r >= 0.7**, computed on log-returns of daily adjusted closing prices.

Edges are weighted by correlation strength -- higher weight means stronger co-movement.

### Contagion Simulation

Starting from a user-selected company with a given crash percentage, the simulation performs a recursive graph traversal:

1. The selected company's market cap is reduced by the crash percentage
2. For each correlated neighbor, the crash impact is attenuated by the edge weight (crash % x correlation)
3. If the attenuated impact exceeds 1%, the crash spreads to that neighbor
4. The process continues recursively until the impact dissipates below the threshold

### Visualization

- **Green nodes** = stable companies
- **Red nodes** = affected companies (darker red = more severe loss)
- **Star marker** = the initially crashed company
- A bar chart shows the top 15 most affected companies with both % loss and dollar loss
- Company search highlights nodes on the graph and shows detailed company information

## Tech Stack

- **Python** (core language)
- **yfinance** -- historical stock data retrieval
- **NetworkX** -- graph construction and layout computation
- **Plotly / Dash** -- interactive web-based visualization and dashboard
- **NumPy** -- log-return and Pearson correlation computation

## Data

The project analyzes the COVID-19 crash period:

| Crisis | Date Range |
|---|---|
| COVID-19 Crash | January 2020 -- August 2020 |

Data includes 503 S&P 500 companies with ~158 trading days of adjusted closing prices, market capitalization, sector, sub-industry, and founding year.

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Run the simulation
python main.py
```

The app launches at `http://127.0.0.1:8050`. Open it in your browser.

**How to use:**
1. Enter a ticker symbol (e.g. `AAPL`) and crash percentage (e.g. `50`)
2. Click **Simulate Crash** to see contagion spread through the network
3. Click any bar in the chart to view that company's details
4. Use **Search Company** to find and highlight any company on the graph
5. Click **Reset** to return to the baseline sector view

## Project Structure

| File | Description |
|---|---|
| `main.py` | Entry point -- builds network and launches dashboard |
| `classes.py` | Core graph model (`Company`, `MarketNetwork`, crash simulation) |
| `visualization.py` | Dash app, Plotly figures, and all UI components |
| `data_fetcher.py` | Scrapes S&P 500 data from Wikipedia and yfinance |
| `sp500_covid_data.json` | Pre-fetched dataset (503 companies, COVID-19 period) |
| `requirements.txt` | Python dependencies |

## References

1. Kenton, W. "S&P 500 Index." *Investopedia*. [Link](https://www.investopedia.com/terms/s/sp500.asp)
2. Gratton, P. "The Fall of the Market in the Fall of 2008." *Investopedia*. [Link](https://www.investopedia.com/articles/economics/09/subprime-market-2008.asp)
3. Frazier, L. "The Coronavirus Crash of 2020." *Forbes*, 2021. [Link](https://www.forbes.com/sites/lizfrazierpeck/2021/02/11/the-coronavirus-crash-of-2020-and-the-investing-lesson-it-taught-us/)
4. "Introduction to Graphs." *GeeksforGeeks*. [Link](https://www.geeksforgeeks.org/dsa/introduction-to-graphs-data-structure-and-algorithm-tutorials/)
5. "Basic Object Oriented Data Model." *GeeksforGeeks*, 2021. [Link](https://www.geeksforgeeks.org/dbms/basic-object-oriented-data-model/)
6. *NetworkX Documentation*. [Link](https://networkx.org/documentation/stable/)
7. "What Is YFinance Library?" *GeeksforGeeks*, 2025. [Link](https://www.geeksforgeeks.org/machine-learning/what-is-yfinance-library/)
8. "Pearson Correlation Coefficient." *GeeksforGeeks*. [Link](https://www.geeksforgeeks.org/maths/pearson-correlation-coefficient/)
9. "What Is NetworkX?" *NVIDIA Glossary*. [Link](https://www.nvidia.com/en-us/glossary/networkx/)
10. Holtz, Y. "Plotly." *The Python Graph Gallery*. [Link](https://python-graph-gallery.com/plotly/)
