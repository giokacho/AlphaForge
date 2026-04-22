# config.py

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Required API keys — startup will abort if any of these are missing or
# still set to the placeholder value.
# ---------------------------------------------------------------------------
_REQUIRED_KEYS = {
    "NEWSAPI_KEY":      os.getenv("NEWSAPI_KEY"),
    "ALPHAVANTAGE_KEY": os.getenv("ALPHAVANTAGE_KEY"),
    "FRED_API_KEY":     os.getenv("FRED_API_KEY"),
}
for _name, _val in _REQUIRED_KEYS.items():
    if not _val or _val == "your_key_here":
        raise ValueError(
            f"[news-bot] {_name} is missing or still set to the placeholder. "
            f"Set a real key in news-bot/.env before running."
        )

NEWSAPI_KEY      = _REQUIRED_KEYS["NEWSAPI_KEY"]
ALPHAVANTAGE_KEY = _REQUIRED_KEYS["ALPHAVANTAGE_KEY"]
FRED_API_KEY     = _REQUIRED_KEYS["FRED_API_KEY"]

# ---------------------------------------------------------------------------
# Optional Reddit credentials — leave blank to disable the Reddit fetcher.
# ---------------------------------------------------------------------------
REDDIT_CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT    = os.getenv("REDDIT_USER_AGENT", "news-bot/1.0")

FOCUS_ASSETS = [
    "Gold", "SPX", "NQ", "DOW", "BTC", "ETH", "Oil",
    "EURUSD", "USDJPY", "USDCAD",
    "S&P500", "Nasdaq", "Dow Jones", "Bitcoin", "Ethereum",
    "crude oil", "Euro", "Japanese Yen", "Canadian Dollar",
    "Federal Reserve", "inflation", "interest rates",
    "recession", "Treasury", "dollar", "DXY", "forex",
]
