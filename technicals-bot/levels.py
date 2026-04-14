import numpy as np
import pandas as pd

def calculate_atr_regime(df_daily):
    """
    Calculates the ATR 14 regime and percentile, returning a risk multiplier.
    """
    df = df_daily.copy()
    high_s = df['High']
    low_s = df['Low']
    close_s = df['Close']
    
    df['TR1'] = abs(high_s - low_s)
    df['TR2'] = abs(high_s - close_s.shift(1))
    df['TR3'] = abs(low_s - close_s.shift(1))
    tr = df[['TR1', 'TR2', 'TR3']].max(axis=1)
    
    atr14 = tr.ewm(alpha=1/14, adjust=False).mean()
    current_atr = atr14.iloc[-1]
    
    past_atr = atr14.iloc[-252:].dropna().values
    if len(past_atr) > 0:
        atr_percentile = (np.sum(past_atr < current_atr) / len(past_atr)) * 100
    else:
        atr_percentile = 50.0
        
    if atr_percentile > 70:
        atr_multiplier = 2.0
    elif atr_percentile < 30:
        atr_multiplier = 1.2
    else:
        atr_multiplier = 1.5
        
    return {
        "atr_14": float(current_atr),
        "atr_percentile": float(atr_percentile),
        "atr_multiplier": float(atr_multiplier)
    }

def calculate_key_levels(df_daily):
    """
    Identifies nearest structure support/resistance and prior day boundaries.
    "Prior" implies excluding today's unclosed candle.
    """
    high_s = df_daily['High']
    low_s = df_daily['Low']
    close_s = df_daily['Close']
    
    # -6 to -1 gets the 5 days prior to today
    nearest_resistance = high_s.iloc[-6:-1].max()
    nearest_support = low_s.iloc[-6:-1].min()
    
    prior_day_high = high_s.iloc[-2]
    prior_day_low = low_s.iloc[-2]
    
    # -11 to -1 gets the 10 days prior to today
    ten_day_high = close_s.iloc[-11:-1].max()
    ten_day_low = close_s.iloc[-11:-1].min()
    
    return {
        "nearest_resistance": float(nearest_resistance),
        "nearest_support": float(nearest_support),
        "prior_day_high": float(prior_day_high),
        "prior_day_low": float(prior_day_low),
        "ten_day_high": float(ten_day_high),
        "ten_day_low": float(ten_day_low)
    }

def calculate_stops_and_targets(entry_price, direction, atr_regime):
    """
    Calculates dynamic stop loss and targets using the ATR multiplier regime.
    """
    atr_14 = atr_regime["atr_14"]
    multiplier = atr_regime["atr_multiplier"]
    
    if direction == "LONG":
        stop_loss = entry_price - (multiplier * atr_14)
        target_1 = entry_price + (multiplier * 2.0 * atr_14)
        target_2 = entry_price + (multiplier * 3.5 * atr_14)
    elif direction == "SHORT":
        stop_loss = entry_price + (multiplier * atr_14)
        target_1 = entry_price - (multiplier * 2.0 * atr_14)
        target_2 = entry_price - (multiplier * 3.5 * atr_14)
    else:
        return {}
        
    # Risk-Reward Ratio at Target 1
    risk = abs(entry_price - stop_loss)
    reward = abs(target_1 - entry_price)
    rr_ratio = reward / risk if risk > 0 else 0.0
    
    return {
        "entry_price": float(entry_price),
        "stop_loss": float(stop_loss),
        "target_1": float(target_1),
        "target_2": float(target_2),
        "rr_ratio": float(rr_ratio)
    }

if __name__ == "__main__":
    from data_fetcher import fetch_all_assets
    import json
    
    print("Testing levels.py modules...\n")
    all_data = fetch_all_assets()
    
    for asset, dfs in all_data.items():
        if "daily" in dfs and not dfs["daily"].empty:
            df = dfs["daily"]
            
            # Simulated dummy test signal parameters
            last_close = df["Close"].iloc[-1]
            test_dir = "LONG"
            
            regime = calculate_atr_regime(df)
            levels = calculate_key_levels(df)
            stops_targets = calculate_stops_and_targets(last_close, test_dir, regime)
            
            print(f"--- {asset} ---")
            print(f"ATR Regime:\n  {json.dumps(regime, indent=2)}")
            print(f"Key Levels:\n  {json.dumps(levels, indent=2)}")
            print(f"Stops & Targets (Simulated {test_dir} from {last_close:.2f}):\n  {json.dumps(stops_targets, indent=2)}\n")
