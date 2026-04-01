""" Fetches S&P 500 company metadata and historical stock price data from Wikipedia and yfinance, processes this
it into a structured format and saves it as a JSON file.
"""
import json
from datetime import datetime
import urllib.request
import time
import yfinance as yf
import pandas as pd

# source: https://joetatusko.com/2024/05/07/getting-the-sp-500-from-wikipedia-with-python/


def get_sp500_stocks() -> dict:
    """ Convert S&P 500 stocks information from Wikipedia page to DataFrame.

    Annotations:
     - Overrode default User-Agent using urllib.request.Request to prevent 403 Forbidden errors from Wikipedia's
       anti-bot filters.

    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request) as response:
        data = pd.read_html(response)[0]
    data = data.set_index("Symbol")
    return data.to_dict(orient="index")


def generate_json(sp500_dict: dict, filename: str) -> None:
    """ Generate json file.
    """
    tickers_hyphenated = [t.replace('.', '-') for t in sp500_dict.keys()]
    data = yf.download(
        tickers=tickers_hyphenated,
        start="2020-01-01",
        end="2020-08-18",
        interval="1d",
        auto_adjust=True
    )["Close"]
    yf_ticker_info = yf.Tickers(" ".join(tickers_hyphenated))
    result = {
        "METADATA": {
            "Last Updated": datetime.now().strftime("%Y-%m-%d"),
            "Description": "S&P 500 Historical Adj Prices (2020-01-01 to 2020-08-18)"
        },
        "STOCKS": {}
    }
    for ticker, details in sp500_dict.items():
        ticker_hyphenated = ticker.replace(".", "-")
        if ticker_hyphenated in data.columns:
            yf_ticker = yf_ticker_info.tickers[ticker_hyphenated]
            info = yf_ticker.info
            if not info or "marketCap" not in info:
                time.sleep(0.1)
                info = yf.Ticker(ticker_hyphenated).info
            historical_data = data[ticker_hyphenated].dropna()
            historical_data_dict = {date.strftime("%Y-%m-%d"): round(float(price), 4)
                                    for date, price in historical_data.items()}
            clean_year_founded = str(details.get('Founded', ''))[:4].strip()
            result["STOCKS"][ticker] = {
                "name": details.get('Security'),
                "sector": details.get('GICS Sector'),
                "sub_industry": details.get('GICS Sub-Industry'),
                "hq_location": details.get('Headquarters Location'),
                "founded": int(clean_year_founded),
                "history": historical_data_dict,
                "market_cap": round(float(info.get("marketCap", 0.0)), 2)
            }
    with open(filename, 'w') as file:
        json.dump(result, file, indent=4)


if __name__ == "__main__":
    stocks_metadata = get_sp500_stocks()
    generate_json(stocks_metadata, "sp500_covid_data.json")

    import doctest
    doctest.testmod()

    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['yfinance', 'pandas', 'json', 'datetime', 'urllib.request', 'time'],
        'allowed-io': ['get_sp500_stocks', 'generate_json'],
        'max-line-length': 120
    })
