from __future__ import annotations
import json
from typing import Any
import numpy as np


class Company:
    """ A vertex representing a company in the S&P 500 network.

    Instance Attributes:
        - ticker: The unique stock ticker symbol (i.e., "AAPL").
        - name: The full legal name of the company.
        - sector: The GICS Sector classification (i.e., "Industrials").
        - sub_industry: The GICS Sub-Industry classification (e.g., "Industrial Conglomerates").
        - founded: The year the company was founded.
        - history: A mapping from dates "YYYY-MM-DD" to adjusted closing prices.
        - crashed: Boolean value for whether the company is crashed
        - crash_percentage: A float from 0.0 to 1.0 representing "by how much" the stock has crashed.
        - neighbors: A mapping from neighboring Company objects to their edge weight \
                     (Pearson correlation coefficient r).

    Representation Invariants:
        - self.ticker is not None
        - 0.0 <= self.crash_percentage <= 1.0
        - self.status in {"Stable", "Crashed"}
        - all(0.0 <= self.neighbors[neighbor] <= 1.0 for neighbor in self.neighbors)
    """
    ticker: str
    name: str
    sector: str
    sub_industry: str
    hq_location: str
    founded: str
    history: dict[str, float]
    crashed: bool
    crash_percentage: float
    market_cap: float
    neighbors: dict[Company, float]

    def __init__(self, ticker, data):
        """Initialize a new company with the provided data excerpted from the S&P 500 JSON.
        """
        self.ticker = ticker
        self.name = data.get("name")
        self.sector = data.get("sector")
        self.sub_industry = data.get("sub_industry")
        self.hq_location = data.get("hq_location")
        self.founded = data.get("founded")
        self.history = data.get("history", {})
        self.crashed = False
        self.crash_percentage = 0.0
        self.market_cap = data.get("market_cap")
        self.neighbors = {}

    def crash_company(self, crash_percentage: float) -> None:
        """Recursively revaluate company value based off of effects of crash.

        Preconditions:
            - 0 < crash_percentage <= 1
        """
        self.crashed = True
        self.crash_percentage = crash_percentage
        self.market_cap *= 1 - crash_percentage
        for company in self.neighbors:
            wave_crash = crash_percentage * self.neighbors[company]
            if wave_crash > 0.01 and not company.crashed:
                company.crash_company(wave_crash)


class MarketNetwork:
    """ A graph-based model of the S&P 500 market network.

    Instance Attributes:
        - companies: A collection of the companies contained in this MarketNetwork. Maps tickers to Company instance.

    Representation Invariants:
        - all(ticker == self.companies[ticker].ticker for ticker in self.companies)
    """
    companies: dict[str, Company]

    def __init__(self) -> None:
        """Initialize an empty MarketNetwork (graph) with no companies or edges."""
        self.companies = {}

    def add_company(self, ticker: str, data: dict[str, Any]) -> None:
        """Add a new Company (vertex) to the graph.

        If the ticker already exists, this will overwrite the existing company data.
        """
        self.companies[ticker] = Company(ticker, data)

    def add_edge(self, ticker1: str, ticker2: str, weight: float) -> None:
        """Add a weighted, undirected edge between ticker1 and ticker2.

        The weight represents the Pearson correlation coefficient between the two
        companies.

        Preconditions:
            - ticker1 in self.companies
            - ticker2 in self.companies
            - 0.0 <= weight <= 1.0
        """
        company1 = self.companies[ticker1]
        company2 = self.companies[ticker2]
        company1.neighbors[company2] = weight
        company2.neighbors[company1] = weight

    def simulate_crash(self, crash_ticker: str, crash_percentage: float) -> dict[str, float]:
        """Simulate a crash of a company in the MarketNetwork by mutating self and its effects on other companies within
         the network.

        Preconditions:
            - crash_ticker in self.companies
            - 0 < crash_percentage <= 1
        """
        pre_crash_dict = {}
        post_crash_dict = {}
        affected_dict = {}
        for company in self.companies:
            pre_crash_dict[company] = self.companies[company].market_cap
        crash_company_vertex = self.companies[crash_ticker]
        crash_company_vertex.crash_company(crash_percentage)
        for company in self.companies:
            post_crash_dict[company] = self.companies[company].market_cap
            if pre_crash_dict[company] != post_crash_dict[company]:
                affected_dict[company] = post_crash_dict[company]/pre_crash_dict[company]
        return affected_dict

    def to_networkx(self) -> Any:
        """Convert this MarketNetwork into a networkx.Graph for layout computation.

        Each node has attributes: 'sector', 'market_cap', 'name', 'sub_industry'.
        Each edge has a 'weight' attribute (Pearson correlation coefficient).
        """
        import networkx as nx
        g = nx.Graph()
        for ticker, company in self.companies.items():
            g.add_node(ticker, sector=company.sector, market_cap=company.market_cap,
                       name=company.name, sub_industry=company.sub_industry)
        visited = set()
        for ticker, company in self.companies.items():
            for neighbor, weight in company.neighbors.items():
                edge = (min(ticker, neighbor.ticker), max(ticker, neighbor.ticker))
                if edge not in visited:
                    visited.add(edge)
                    g.add_edge(ticker, neighbor.ticker, weight=weight)
        return g

    def reset_market(self, affected_dict: dict[str, float]) -> None:
        """Reset self by mutating based off inputted dictionary.

        Preconditions:
            - all([ticker in self.companies for ticker in affected_dict])
            - all([0 < percentage <= 1 for percentage in affected_dict.values()])
        """
        for company in affected_dict:
            self.companies[company].crashed = False
            self.companies[company].crash_percentage = 0.0
            self.companies[company].market_cap /= affected_dict[company]


def construct_market_network(json_file: str, strength_value: float = 0.7) -> MarketNetwork:
    """ Convert S&P 500 JSON data into a MarketNetwork graph.

    Preconditions:
        - 0.0 <= threshold <= 1.0
        - json_file leads to a valid JSON containing 'STOCKS' data.

    """
    with open(json_file) as file:
        data = json.load(file)
    stock_data = data["STOCKS"]
    network = MarketNetwork()
    for ticker, details in stock_data.items():
        network.add_company(ticker, details)
    returns = {}
    tickers = list(network.companies.keys())
    for ticker in tickers:
        history = network.companies[ticker].history
        sorted_dates = sorted(history.keys())
        prices = [history[date] for date in sorted_dates]
        if len(prices) > 1:
            returns[ticker] = np.diff(np.log(np.array(prices)))
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            ticker1, ticker2 = tickers[i], tickers[j]
            if ticker1 in returns and ticker2 in returns:
                return1, return2 = returns[ticker1], returns[ticker2]
                length = min(len(return1), len(return2))
                if length > 20:
                    res = np.corrcoef(return1[:length], return2[:length])[0, 1]
                    if res >= strength_value:
                        network.add_edge(ticker1, ticker2, round(float(res), 4))
    return network


if __name__ == "__main__":
    DATA_FILE = "sp500_covid_data.json"
    strength_value = 0.7
    my_network = construct_market_network(DATA_FILE, strength_value)
    total_companies = len(my_network.companies)
    total_edges = sum(len(c.neighbors) for c in my_network.companies.values()) // 2
    print("\n--- Graph Statistics ---")
    print(f"Total Vertices (Companies): {total_companies}")
    print(f"Total Edges (Correlations > {strength_value}): {total_edges}")
    test_ticker = "AAPL"
    if test_ticker in my_network.companies:
        apple = my_network.companies[test_ticker]
        print(f"\n--- Spot Check: {test_ticker} ({apple.name}) ---")
        print(f"Sector: {apple.sector}")
        print(f"Number of strongly correlated neighbors: {len(apple.neighbors)}")
        top_neighbors = sorted(
            apple.neighbors.items(),
            key=lambda item: item[1],
            reverse=True
        )[:5]
        print("Top 5 Neighbors:")
        for neighbor_obj, weight in top_neighbors:
            print(f"- {neighbor_obj.ticker}: {weight}")
    else:
        print(f"\nWarning: {test_ticker} not found in the dataset.")
