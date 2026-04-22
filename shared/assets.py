ASSETS = [
    {"name": "Gold",   "ticker": "GC=F",     "asset_class": "commodity", "cftc_name": "GOLD - COMMODITY EXCHANGE INC.",                        "cot_inverted": False, "risk_unit": "contracts"},
    {"name": "SPX",    "ticker": "^GSPC",    "asset_class": "equity",    "cftc_name": "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE",           "cot_inverted": False, "risk_unit": "shares"},
    {"name": "NQ",     "ticker": "^NDX",     "asset_class": "equity",    "cftc_name": "NASDAQ-100 Consolidated - CHICAGO MERCANTILE EXCHANGE",  "cot_inverted": False, "risk_unit": "shares"},
    {"name": "DOW",    "ticker": "^DJI",     "asset_class": "equity",    "cftc_name": "DOW JONES INDUSTRIAL AVG- $5 - CHICAGO BOARD OF TRADE", "cot_inverted": False, "risk_unit": "shares"},
    {"name": "BTC",    "ticker": "BTC-USD",  "asset_class": "crypto",    "cftc_name": "BITCOIN - CHICAGO MERCANTILE EXCHANGE",                 "cot_inverted": False, "risk_unit": "units"},
    {"name": "ETH",    "ticker": "ETH-USD",  "asset_class": "crypto",    "cftc_name": None,                                                     "cot_inverted": False, "risk_unit": "units"},
    {"name": "Oil",    "ticker": "CL=F",     "asset_class": "commodity", "cftc_name": "CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE", "cot_inverted": False, "risk_unit": "contracts"},
    {"name": "EURUSD", "ticker": "EURUSD=X", "asset_class": "fx",        "cftc_name": "EURO FX - CHICAGO MERCANTILE EXCHANGE",                 "cot_inverted": False, "risk_unit": "units"},
    {"name": "USDJPY", "ticker": "JPY=X",    "asset_class": "fx",        "cftc_name": "JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE",            "cot_inverted": True,  "risk_unit": "units"},
    {"name": "USDCAD", "ticker": "CAD=X",    "asset_class": "fx",        "cftc_name": "CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",         "cot_inverted": True,  "risk_unit": "units"},
]

ASSET_NAMES      = [a["name"]              for a in ASSETS]
TICKER_MAP       = {a["name"]:  a["ticker"]     for a in ASSETS}
NAME_FROM_TICKER = {a["ticker"]: a["name"]      for a in ASSETS}
CFTC_MAP         = {a["name"]:  a["cftc_name"]  for a in ASSETS if a["cftc_name"]}
COT_ASSETS       = [a["name"]              for a in ASSETS if a["cftc_name"]]
CRYPTO_ASSETS    = [a["name"]              for a in ASSETS if a["asset_class"] == "crypto"]
TICKER_UNITS     = {a["ticker"]: a["risk_unit"] for a in ASSETS}
COT_INVERTED     = {a["name"]:  a["cot_inverted"] for a in ASSETS}
