import requests

def get_dynamic_watchlist():
    """
    Fetch top gainers and losers from NSE.
    """
    url = "https://www.nseindia.com/api/market-data-pre-open?key=NIFTY"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()

        symbols = []

        for item in data["data"][:20]:
            symbol = item["metadata"]["symbol"]
            symbols.append(f"NSE:{symbol}")

        return symbols

    except Exception as e:
        print("Market scanner error:", e)
        return []
