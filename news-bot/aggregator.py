import json
import os
import csv
from datetime import datetime

def aggregate_final_sentiment(
    asset_results, 
    hawk_results, 
    velocity_results, 
    contradiction_results, 
    fred_results, 
    alpha_vantage_average
):
    """
    Takes partitioned intelligence from various analysis models and combines them.
    Calculates specific divergence and sentiment weighted averages mathematically.
    """
    # Defensive gets for scores prioritizing 0.0 fallbacks if keys misalign
    gold_score = asset_results.get("gold_score", 0.0)
    spx_score = asset_results.get("spx_score", 0.0)
    nq_score = asset_results.get("nq_score", 0.0)
    earnings_tone = asset_results.get("earnings_tone", 0.0)
    
    # 1. Calculate overall sentiment as a weighted macro average
    overall_sentiment = (
        (gold_score * 0.25) + 
        (spx_score * 0.35) + 
        (nq_score * 0.25) + 
        (earnings_tone * 0.15)
    )
    
    # 2. Calculate Institutional divergence
    # If alpha drops below our scraped news composite, retail is over-optimistic or instos are distributing.
    institutional_vs_retail_divergence = alpha_vantage_average - overall_sentiment
    
    # 3. Pull Event Risk String
    forward_event_risk = fred_results.get("event_risk_level", "Unknown")
    
    # 4. Final Aggregation Dict Schema
    final_scores = {
        "overall_sentiment": round(overall_sentiment, 4),
        "fed_hawkishness": hawk_results.get("hawkishness_score", 0.0),
        "geopolitical_risk": asset_results.get("geopolitical_risk", 0.0),
        "earnings_tone": earnings_tone,
        "narrative_momentum": velocity_results,
        "institutional_divergence": round(institutional_vs_retail_divergence, 4),
        "gold_score": gold_score,
        "spx_score": spx_score,
        "nq_score": nq_score,
        "contradiction_flag": contradiction_results.get("flag", False),
        "contradiction_reason": contradiction_results.get("explanation", ""),
        "dominant_narrative": asset_results.get("dominant_narrative", ""),
        "forward_event_risk": forward_event_risk,
        "top_3_headlines": asset_results.get("top_3_headlines", [])
    }
    
    return final_scores

def save_news_output(final_scores):
    """
    Persists the daily intelligence run. Dumps full JSON mapping for external parsing 
    and cascades high-level indicators into a continuous CSV time-series log.
    """
    outputs_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    
    today_date = datetime.now().strftime("%Y-%m-%d")
    json_filename = f"{today_date}_news_scores.json"
    json_path = os.path.join(outputs_dir, json_filename)
    
    # 1. Save Full JSON payload for today's run
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(final_scores, f, indent=4)
        
    # 2. Append Macro indicators to CSV Tracker Sequence
    csv_path = os.path.join(outputs_dir, "news_history.csv")
    csv_exists = os.path.isfile(csv_path)
    
    headers = [
        "date", "overall_sentiment", "fed_hawkishness", "gold_score", 
        "spx_score", "nq_score", "contradiction_flag", "dominant_narrative", 
        "forward_event_risk"
    ]
    
    # Clean string mapping, avoiding dictionary KeyErrors
    row_data = {
        "date": today_date,
        "overall_sentiment": final_scores.get("overall_sentiment", 0.0),
        "fed_hawkishness": final_scores.get("fed_hawkishness", 0.0),
        "gold_score": final_scores.get("gold_score", 0.0),
        "spx_score": final_scores.get("spx_score", 0.0),
        "nq_score": final_scores.get("nq_score", 0.0),
        "contradiction_flag": final_scores.get("contradiction_flag", False),
        "dominant_narrative": final_scores.get("dominant_narrative", ""),
        "forward_event_risk": final_scores.get("forward_event_risk", "Unknown")
    }
    
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not csv_exists:
            writer.writeheader()
        writer.writerow(row_data)
        
    print(f"Saved completed JSON output to: {json_path}")

if __name__ == "__main__":
    # Simulate dummy test inputs exactly matching dictionaries returned by other scripts
    mock_asset_scores = {
        "gold_score": 0.8,
        "spx_score": 0.5,
        "nq_score": 0.4,
        "earnings_tone": 0.7,
        "geopolitical_risk": 0.65,
        "dominant_narrative": "Market continues to price soft-landing despite risks",
        "top_3_headlines": [
            "CPI misses expectations signaling cooling inflation.", 
            "Oil drops following production increase.", 
            "Earnings beat offsets fears."
        ]
    }
    
    mock_hawk_scores = {"hawkishness_score": -0.25, "key_phrase": "Inflation prints show accommodation path"}
    mock_velocity = {"gold_change": 0.10, "shifting_assets": []}
    mock_contradiction = {"flag": False, "explanation": "No major fundamental contradictions detected across active regimes."}
    
    mock_fred = {"event_risk_level": "HIGH"}
    mock_alpha_vantage_average = 0.9  # very bullish setup assumption
    
    print("Testing Aggregator Consolidation...\n")
    final_res = aggregate_final_sentiment(
        asset_results=mock_asset_scores,
        hawk_results=mock_hawk_scores,
        velocity_results=mock_velocity,
        contradiction_results=mock_contradiction,
        fred_results=mock_fred,
        alpha_vantage_average=mock_alpha_vantage_average
    )
    
    print("=== FINAL SENTIMENT OUTPUT ===")
    print(json.dumps(final_res, indent=4))
    
    print("\nSimulating disk persist operation...")
    save_news_output(final_res)
