import os
import glob
import json
import time
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))

# Memory caching to avoid thrashing disk IO
_cache_payload = None
_cache_time = 0.0
CACHE_TTL = 60.0

def fetch_json(glob_pattern: str, direct_path: bool = False) -> dict:
    """Safely loads a JSON file, resolving globs to find the most recent."""
    if direct_path:
        target = glob_pattern
        if not os.path.isfile(target):
            return {"_status": "MISSING_FILE"}
    else:
        files = glob.glob(glob_pattern)
        if not files:
            return {"_status": "MISSING_FILE"}
        target = max(files, key=os.path.getmtime)
        
    try:
        with open(target, 'r', encoding='utf-8') as f:
            data = json.load(f)
            data["_status"] = "OK"  # Inject healthy status
            return data
    except Exception as e:
        return {"_status": f"LOAD_ERROR", "_error": str(e)}

def load_latest_data() -> dict:
    """Reads all system JSON outputs and aggregates them into a dashboard payload."""
    global _cache_payload, _cache_time
    now = time.time()
    
    if _cache_payload is not None and (now - _cache_time) < CACHE_TTL:
        return _cache_payload
        
    # File Paths resolving up to the core AlphaForge outputs
    tech_glob = os.path.join(PROJECT_ROOT, "technicals-bot", "outputs", "*_technicals.json")
    cot_glob  = os.path.join(PROJECT_ROOT, "cot-bot", "outputs", "*_cot.json")
    news_glob = os.path.join(PROJECT_ROOT, "news-bot", "outputs", "*_news_scores.json")
    debt_glob = os.path.join(PROJECT_ROOT, "debate-bot", "outputs", "*_debate.json")
    risk_glob = os.path.join(PROJECT_ROOT, "risk-engine", "outputs", "*_trade_sheet.json")
    
    ctx_path  = os.path.join(PROJECT_ROOT, "shared", "combined_context.json")
    verd_path = os.path.join(PROJECT_ROOT, "shared", "final_verdict.json")
    
    # Safely load all components
    tech_data = fetch_json(tech_glob)
    cot_data  = fetch_json(cot_glob)
    news_data = fetch_json(news_glob)
    debt_data = fetch_json(debt_glob)
    risk_data = fetch_json(risk_glob)
    
    ctx_data  = fetch_json(ctx_path, direct_path=True)
    verd_data = fetch_json(verd_path, direct_path=True)
    
    dashboard_payload = {
        "pipeline_status": {
            "technicals":  tech_data.get("_status"),
            "cot":         cot_data.get("_status"),
            "news":        news_data.get("_status"),
            "debate":      debt_data.get("_status"),
            "trade_sheet": risk_data.get("_status"),
            "context":     ctx_data.get("_status"),
            "verdict":     verd_data.get("_status"),
        },
        "signals":      verd_data,
        "macro":        ctx_data.get("macro_data", {}) if ctx_data.get("_status") == "OK" else {"_status": ctx_data.get("_status")},
        "combined_risk_level": ctx_data.get("combined_risk_level", "UNKNOWN"),
        "news":         news_data,
        "cot":          cot_data,
        "technicals":   tech_data,
        "debate":       debt_data,
        "trade_sheet":  risk_data,
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    _cache_payload = dashboard_payload
    _cache_time = now
    
    return dashboard_payload
