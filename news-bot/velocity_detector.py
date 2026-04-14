import os
import json
import glob

SCORE_HISTORY_FILE = "score_history.json"

def fetch_last_macro_regime():
    """
    Helper function to dynamically read the macro regime from the macro-bot's latest report
    if the directory structure is in place.
    """
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "macro-bot", "reports")
    
    if not os.path.exists(reports_dir):
        return "UNKNOWN"
        
    # Search for the most recently saved report
    files = glob.glob(os.path.join(reports_dir, "*"))
    if not files:
        return "UNKNOWN"
        
    latest_file = max(files, key=os.path.getmtime)
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            content = f.read().upper()
            if "RISK_ON" in content or "RISK ON" in content:
                return "RISK_ON"
            elif "RISK_OFF" in content or "RISK OFF" in content:
                return "RISK_OFF"
    except Exception:
        pass
        
    return "UNKNOWN"

def track_narrative_velocity(today_scores):
    """
    Calculates differences between today's multi-asset sentiment scores and yesterday's saves.
    Flags high-volatility narrative shifts (> 0.25 absolute move).
    """
    if os.path.exists(SCORE_HISTORY_FILE):
        try:
            with open(SCORE_HISTORY_FILE, 'r') as f:
                yesterday_scores = json.load(f)
        except json.JSONDecodeError:
            yesterday_scores = {}
    else:
        # Create with default values if it doesn't exist
        yesterday_scores = {"gold_score": 0.0, "spx_score": 0.0, "nq_score": 0.0}
        with open(SCORE_HISTORY_FILE, 'w') as f:
            json.dump(yesterday_scores, f)
            
    def_gold = yesterday_scores.get("gold_score", 0.0)
    def_spx = yesterday_scores.get("spx_score", 0.0)
    def_nq = yesterday_scores.get("nq_score", 0.0)
        
    today_gold = today_scores.get("gold_score", 0.0)
    today_spx = today_scores.get("spx_score", 0.0)
    today_nq = today_scores.get("nq_score", 0.0)
    
    gold_change = today_gold - def_gold
    spx_change = today_spx - def_spx
    nq_change = today_nq - def_nq
    
    shifting_assets = []
    if abs(gold_change) > 0.25:
        shifting_assets.append("gold")
    if abs(spx_change) > 0.25:
        shifting_assets.append("spx")
    if abs(nq_change) > 0.25:
        shifting_assets.append("nq")
        
    return {
        "gold_change": round(gold_change, 4),
        "spx_change": round(spx_change, 4),
        "nq_change": round(nq_change, 4),
        "shifting_assets": shifting_assets
    }

def detect_contradictions(asset_scores, hawkishness_score, macro_regime):
    """
    Hunts for logical misalignment between macro signals and micro asset pricing.
    Saves today's scores down to disk prior to return.
    """
    triggered_conditions = []
    
    gold = asset_scores.get("gold_score", 0.0)
    spx = asset_scores.get("spx_score", 0.0)
    nq = asset_scores.get("nq_score", 0.0)
    geopol_risk = asset_scores.get("geopolitical_risk", 0.0)
    
    regime = str(macro_regime).upper()
    
    # Rules Matrix
    if regime == "RISK_ON" and gold > 0.5:
        triggered_conditions.append("Macro regime is RISK_ON but overall gold_score is above 0.5")
        
    if regime == "RISK_ON" and hawkishness_score > 0.5:
        triggered_conditions.append("Macro regime is RISK_ON but hawkishness_score is above 0.5")
        
    if regime == "RISK_OFF" and spx > 0.4:
        triggered_conditions.append("Macro regime is RISK_OFF but spx_score is above 0.4")
        
    if geopol_risk > 0.7 and nq > 0.3:
        triggered_conditions.append("Geopolitical risk is above 0.7 but nq_score is above 0.3")

    contradiction_flag = len(triggered_conditions) > 0
    
    explanation = "No major fundamental contradictions detected across active regimes."
    if contradiction_flag:
        # Default explanatory context picks the most egregious hit (the first one)
        explanation = f"Contradiction detected: {triggered_conditions[0]}."

    # Final Step: Dump current state to file
    try:
        with open(SCORE_HISTORY_FILE, 'w') as f:
            json.dump(asset_scores, f, indent=4)
    except Exception as e:
        print(f"Warning: Failed to save score_history.json: {e}")
        
    return contradiction_flag, triggered_conditions, explanation

if __name__ == "__main__":
    # Ensure a dummy state exists or gets created
    print("Testing Velocity & Contradictions Node...\n")
    
    mock_today_scores = {
        "gold_score": 0.8,
        "spx_score": 0.5,
        "nq_score": 0.4,
        "geopolitical_risk": 0.8
    }
    
    # 1. Test Velocity Output
    velocity_res = track_narrative_velocity(mock_today_scores)
    print("=== NARRATIVE VELOCITY SCORECARD ===")
    print(json.dumps(velocity_res, indent=2))
    
    # 2. Test Contradictions Matrix
    # We simulate reading from the secondary bot, but fallback to arbitrary RISK_ON
    live_regime = fetch_last_macro_regime()
    test_regime = live_regime if live_regime != "UNKNOWN" else "RISK_ON"
    mock_hawk_score = 0.6
    
    flag, triggers, explanation = detect_contradictions(mock_today_scores, mock_hawk_score, test_regime)
    
    print("\n=== MACRO CONTRADICTION MATRIX ===")
    print(f"Contradiction Flag: {flag}")
    print(f"Triggers Active: {json.dumps(triggers, indent=2)}")
    print(f"Analyst Note: {explanation}")
