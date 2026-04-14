# config.py

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_key_here":
    raise ValueError(
        "[macro-bot] GEMINI_API_KEY is missing or still set to the placeholder. "
        "Set a real key in macro-bot/.env before running."
    )

FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY or FRED_API_KEY == "your_key_here":
    raise ValueError(
        "[macro-bot] FRED_API_KEY is missing or still set to the placeholder. "
        "Set a real key in macro-bot/.env before running."
    )

THRESHOLDS = {
    "VIX_BEARISH_ABOVE": 25,
    "VIX_BULLISH_BELOW": 15,
    "HY_SPREAD_BEARISH_ABOVE": 600,
    "HY_SPREAD_BULLISH_BELOW": 350,
    "BREADTH_BEARISH_BELOW": 40,
    "BREADTH_BULLISH_ABOVE": 60,
    "YIELD_CURVE_INVERSION": 0,
    "MOVE_BEARISH_ABOVE": 130
}
