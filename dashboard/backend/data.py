import time
import database

# Memory cache to avoid hammering SQLite on every request
_cache_payload = None
_cache_time = 0.0
CACHE_TTL = 60.0

def invalidate_cache():
    global _cache_payload, _cache_time
    _cache_payload = None
    _cache_time = 0.0

def _fetch(bot_name: str) -> dict:
    result = database.get_latest_output(bot_name)
    if result is None:
        return {"_status": "MISSING_FILE"}
    result["_status"] = "OK"
    return result

def load_latest_data() -> dict:
    global _cache_payload, _cache_time
    now = time.time()

    if _cache_payload is not None and (now - _cache_time) < CACHE_TTL:
        return _cache_payload

    tech_data = _fetch("technicals")
    cot_data  = _fetch("cot")
    news_data = _fetch("news")
    debt_data = _fetch("debate")
    risk_data = _fetch("risk")
    macro_data = _fetch("macro")

    dashboard_payload = {
        "pipeline_status": {
            "technicals":  tech_data.get("_status"),
            "cot":         cot_data.get("_status"),
            "news":        news_data.get("_status"),
            "debate":      debt_data.get("_status"),
            "trade_sheet": risk_data.get("_status"),
            "context":     macro_data.get("_status"),
            "verdict":     debt_data.get("_status"),
        },
        "signals":            debt_data,
        "macro":              macro_data if macro_data.get("_status") == "OK" else {"_status": macro_data.get("_status")},
        "combined_risk_level": news_data.get("combined_risk_level", "UNKNOWN"),
        "news":               news_data,
        "cot":                cot_data,
        "technicals":         tech_data,
        "debate":             debt_data,
        "trade_sheet":        risk_data,
        "last_updated":       database.get_latest_run_time() or "N/A"
    }

    _cache_payload = dashboard_payload
    _cache_time = now
    return dashboard_payload
