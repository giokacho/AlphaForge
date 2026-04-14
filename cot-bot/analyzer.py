import pandas as pd
from typing import Optional

try:
    from fetcher import fetch_cot_data
    from config import ASSETS, CFTC_MAPPING
except ImportError:
    # Handle case where script might be executed from different dir
    from .fetcher import fetch_cot_data
    from .config import ASSETS, CFTC_MAPPING

def calculate_net_positions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds net position columns.
    commercial_net = commercial_long minus commercial_short
    large_spec_net = large_spec_long minus large_spec_short
    small_spec_net = small_spec_long minus small_spec_short
    """
    if df.empty:
        return df
        
    # Fill NAs with 0 for calculation purposes
    df['commercial_long'] = pd.to_numeric(df['commercial_long'], errors='coerce').fillna(0)
    df['commercial_short'] = pd.to_numeric(df['commercial_short'], errors='coerce').fillna(0)
    df['large_spec_long'] = pd.to_numeric(df['large_spec_long'], errors='coerce').fillna(0)
    df['large_spec_short'] = pd.to_numeric(df['large_spec_short'], errors='coerce').fillna(0)
    df['small_spec_long'] = pd.to_numeric(df['small_spec_long'], errors='coerce').fillna(0)
    df['small_spec_short'] = pd.to_numeric(df['small_spec_short'], errors='coerce').fillna(0)

    df['commercial_net'] = df['commercial_long'] - df['commercial_short']
    df['large_spec_net'] = df['large_spec_long'] - df['large_spec_short']
    df['small_spec_net'] = df['small_spec_long'] - df['small_spec_short']
    
    return df

def get_institutional_bias(df: pd.DataFrame) -> str:
    """
    Looks at the most recent row's commercial_net. 
    If commercial_net is positive set bias="LONG". 
    If negative set bias="SHORT". 
    If within 10% of zero set bias="NEUTRAL".
    """
    if df.empty or 'commercial_net' not in df.columns:
        return "NEUTRAL"
        
    # Assuming index 0 is the most recent date sorting from fetcher
    recent = df.iloc[0]
    
    comm_net = recent.get('commercial_net', 0)
    comm_long = recent.get('commercial_long', 0)
    comm_short = recent.get('commercial_short', 0)
    
    if pd.isna(comm_net) or pd.isna(comm_long) or pd.isna(comm_short):
        return "NEUTRAL"
    
    total_commercial = comm_long + comm_short
    
    if total_commercial == 0:
        return "NEUTRAL"
        
    threshold = 0.10 * total_commercial
    
    if abs(comm_net) <= threshold:
        return "NEUTRAL"
    elif comm_net > 0:
        return "LONG"
    else:
        return "SHORT"

def get_positioning_extreme(df: pd.DataFrame) -> dict:
    """
    Calculates the percentile rank of the most recent commercial_net value 
    against the full 52-week history using scipy.stats.percentileofscore.
    If above 90 or below 10, sets positioning_extreme=True.
    """
    if df.empty or 'commercial_net' not in df.columns:
        return {"extreme": False, "percentile": None}
        
    import scipy.stats
    
    recent_val = df.iloc[0]['commercial_net']
    history = df['commercial_net'].head(52).dropna().tolist()
    
    if not history:
        return {"extreme": False, "percentile": None}
        
    pct = scipy.stats.percentileofscore(history, recent_val, kind='rank')
    is_extreme = bool(pct > 90 or pct < 10)
    
    return {"extreme": is_extreme, "percentile": round(pct, 2)}

def get_crowding_risk(df: pd.DataFrame) -> dict:
    """
    Calculates large spec net as percentage of total open interest for the most recent row. 
    Below 30% = LOW, 30-50% = MEDIUM, Above 50% = HIGH.
    """
    if df.empty or 'large_spec_net' not in df.columns:
        return {"risk": "UNKNOWN", "percentage": None}
        
    recent = df.iloc[0]
    ls_net = abs(recent.get('large_spec_net', 0))
    
    oi = 0
    if 'open_interest' in recent:
        try:
            oi = float(recent['open_interest'])
        except (ValueError, TypeError):
            oi = 0
            
    if pd.isna(oi) or oi <= 0:
        print("WARNING: open_interest missing or 0. Falling back to sum of longs proxy.")
        oi = recent.get('commercial_long', 0) + recent.get('large_spec_long', 0) + recent.get('small_spec_long', 0)
        
    if pd.isna(oi) or oi <= 0:
        return {"risk": "UNKNOWN", "percentage": None}
        
    pct = (ls_net / oi) * 100
    
    if pct < 30:
        risk = "LOW"
    elif pct <= 50:
        risk = "MEDIUM"
    else:
        risk = "HIGH"
        
    return {"risk": risk, "percentage": round(pct, 2)}

if __name__ == "__main__":
    for asset in ASSETS:
        cftc_code = CFTC_MAPPING.get(asset)
        print(f"\n{'='*40}")
        print(f"Asset: {asset} (code {cftc_code})")
        print(f"{'='*40}")
        
        df = fetch_cot_data(cftc_code)
        df_net = calculate_net_positions(df)
        bias = get_institutional_bias(df_net)
        
        if not df_net.empty:
            recent = df_net.iloc[0]
            extreme_data = get_positioning_extreme(df_net)
            crowd_data = get_crowding_risk(df_net)
            
            print(f"Commercial Long:  {recent['commercial_long']}")
            print(f"Commercial Short: {recent['commercial_short']}")
            print(f"Commercial Net:   {recent['commercial_net']}")
            print(f"Large Spec Net:   {recent['large_spec_net']}")
            print(f"Small Spec Net:   {recent['small_spec_net']}")
            print(f"Positioning Extreme: {extreme_data['extreme']} (Percentile: {extreme_data['percentile']})")
            print(f"Crowding Risk:    {crowd_data['risk']} ({crowd_data['percentage']}%)")
        else:
            print("Data fetching returned empty.")
            
        print(f"=> Institutional Bias: {bias}")
        print("-" * 40)
