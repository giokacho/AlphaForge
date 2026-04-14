import json
import requests
from datetime import datetime, timedelta
from config import FRED_API_KEY

def fetch_event_risk():
    series_list = ["DGS10", "DGS2", "CPIAUCSL", "UNRATE", "GDP", "FEDFUNDS", "BAMLH0A0HYM2"]
    
    event_risk = {
        "fresh_releases": [],
        "monitored_series": [],
        "event_risk_level": "LOW"
    }
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    url = "https://api.stlouisfed.org/fred/series/observations"
    
    has_today = False
    has_yesterday = False
    
    for series in series_list:
        try:
            params = {
                "series_id": series,
                "api_key": FRED_API_KEY,
                "sort_order": "desc",
                "limit": 2,
                "file_type": "json"
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "error_message" in data:
                print(f"Warning: API error for {series}: {data['error_message']}")
                continue
                
            observations = data.get("observations", [])
            if not observations:
                continue
                
            most_recent = observations[0]
            obs_date_str = most_recent.get("date")
            obs_value = most_recent.get("value")
            
            try:
                obs_date = datetime.strptime(obs_date_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
                
            event_risk["monitored_series"].append({
                "series": series,
                "last_update": obs_date_str
            })
            
            if obs_date == today or obs_date == yesterday:
                event_risk["fresh_releases"].append({
                    "series": series,
                    "value": obs_value
                })
                
                if obs_date == today:
                    has_today = True
                elif obs_date == yesterday:
                    has_yesterday = True
                    
        except Exception as e:
            print(f"Warning: Failed to fetch FRED series {series}: {e}")
            
    if has_today:
        event_risk["event_risk_level"] = "HIGH"
    elif has_yesterday:
        event_risk["event_risk_level"] = "MEDIUM"
        
    return event_risk

if __name__ == "__main__":
    result = fetch_event_risk()
    print("FRED Event Risk Report:")
    print(json.dumps(result, indent=2))
