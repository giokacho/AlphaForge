import requests
import pandas as pd
from typing import Optional

# Internal imports
try:
    from config import CFTC_MAPPING
except ImportError:
    CFTC_MAPPING = {"Gold": "088691", "SPX": "13874A", "NQ": "209742"}

def fetch_cot_data(market_name: str) -> pd.DataFrame:
    """
    Fetches the most recent 52 weeks of COT data for a given market name.

    Returns a DataFrame with columns:
    date, commercial_long, commercial_short, large_spec_long, large_spec_short, small_spec_long, small_spec_short, open_interest
    """
    url = "https://publicreporting.cftc.gov/resource/jun7-fc8e.json"

    params = {
        "$where": f"market_and_exchange_names='{market_name}'",
        "$limit": 52,
        "$order": "report_date_as_yyyy_mm_dd DESC"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Warning: Failed to fetch API data from {url}. It may be offline or the URL has changed.")
        print(f"Error details: {e}")
        data = []
        
    df = pd.DataFrame(data)
    
    if df.empty:
        # Return an empty DataFrame with the required schema
        return pd.DataFrame(columns=[
            "date", "commercial_long", "commercial_short", 
            "large_spec_long", "large_spec_short", 
            "small_spec_long", "small_spec_short",
            "open_interest"
        ])
        
    col_mapping = {
        "report_date_as_yyyy_mm_dd": "date",
        "comm_positions_long_all": "commercial_long",
        "comm_positions_short_all": "commercial_short",
        "noncomm_positions_long_all": "large_spec_long",
        "noncomm_positions_short_all": "large_spec_short",
        "nonrept_positions_long_all": "small_spec_long",
        "nonrept_positions_short_all": "small_spec_short",
        "open_interest_all": "open_interest"
    }
    
    # Rename matching columns
    df = df.rename(columns=col_mapping)
    
    # Ensure all required columns exist even if API returned partial data
    required_cols = [
        "date", "commercial_long", "commercial_short", 
        "large_spec_long", "large_spec_short", 
        "small_spec_long", "small_spec_short",
        "open_interest"
    ]
    
    for col in required_cols:
        if col not in df.columns:
            df[col] = pd.NA
            
    # Sometimes dates come back as full timestamps, so we convert string to standard date
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        
    return df[required_cols]

if __name__ == "__main__":
    print("Fetching COT data for Gold (088691)...")
    gold_code = CFTC_MAPPING.get("Gold", "088691")
    df_gold = fetch_cot_data(gold_code)
    print("\nFirst 3 rows for Gold:")
    print(df_gold.head(3))
