# S&P 500 Market Crash Simulator

**Simulating financial contagion across the S&P 500 using an object-oriented graph model.**

> CSC111 Final Project -- University of Toronto, Winter 2026
> Arnab Karmokar, Brian Chang, Derek Sun, Johnny Li

## Overview

When a major company crashes, the effects rarely stay contained. Shared supply chains, sector dependencies, and investor sentiment can trigger a domino effect of losses across the entire market -- a phenomenon known as **financial contagion**.

This project models the S&P 500 as a **directed, weighted graph** where each node represents a company and each edge reflects a correlation in historical price movements during market downturns. Users can select any company to initiate a simulated crash and watch in real time as the shock propagates through the network.

**Research Question:** If one company crashes, how does the shock propagate through the S&P 500 network, and which companies are most vulnerable?

## Features

- **Real market data** pulled via `yfinance`, covering the 2008 Financial Crisis and the 2020 COVID-19 Crash
- **Probabilistic contagion model** where crash spread probability is weighted by historical correlation strength
- **Centrality analysis** (degree, betweenness, eigenvector) to identify systemically important companies
- **Interactive visualization** with a dynamic network map and synchronized centrality bar chart
- Adjustable contagion probability scaling and company selection

## How It Works

### Graph Construction

Each S&P 500 company is a `Vertex` in a `Graph`. Edges are created between two companies if:

- Their Pearson correlation coefficient satisfies **r > 0.7**, OR
- They experience simultaneous negative returns on more than **30% of trading days** during a crash period

Edges are weighted by correlation strength -- higher weight means stronger co-movement.

### Contagion Simulation

Starting from a user-selected company, the simulation performs a graph traversal with probabilistic spreading:

1. For each neighboring vertex, generate a random value `r` in `[0, 1]`
2. If `r < edge_weight`, the crash spreads to that neighbor
3. Affected companies are tracked in a visited set representing the spread over time

### Visualization

- **Green nodes** = stable companies
- **Red nodes** = affected companies
- Nodes gradually turn red as contagion spreads
- A bar chart updates alongside the network, ranking companies by centrality

## Tech Stack

- **Python** (core language)
- **yfinance** -- real-time and historical stock data retrieval
- **NetworkX** -- graph construction and centrality computation
- **Plotly / Pygame** -- interactive visualization and simulation display

## Data

The project analyzes two major crash periods:

| Crisis | Date Range |
|---|---|
| 2008 Financial Crisis | September 2008 -- March 2009 |
| COVID-19 Crash | February 2020 -- April 2020 |

Sample data record:
```
{'Date': '2008-09-15', 'Ticker': 'AAPL', 'Sector': 'Technology', 'Close': 4.96}
```

## Getting Started

```bash
# Install dependencies
pip install yfinance networkx plotly pygame

# Run the simulation
python main.py
```

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