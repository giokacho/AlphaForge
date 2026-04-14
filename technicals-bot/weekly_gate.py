import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

def calculate_weekly_gate(df_weekly):
    """
    Calculates weekly gate parameters including 200/50 EMA logic and ADX.
    Returns a dictionary of the calculated metrics and decisions.
    """
    if df_weekly.empty:
        return {}
        
    close = df_weekly['Close'].iloc[-1]
    
    # EMAs using pandas ewm span
    ema200 = df_weekly['Close'].ewm(span=200, adjust=False).mean().iloc[-1]
    ema50 = df_weekly['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
    
    # Rule 1: close vs 200 EMA
    dist_pct = abs(close - ema200) / ema200
    if dist_pct <= 0.005:  # within 0.5 percent
        rule1 = "NEUTRAL"
    elif close > ema200:
        rule1 = "BULL"
    else:
        rule1 = "BEAR"
        
    # Rule 2: 50 EMA vs 200 EMA
    if ema50 > ema200:
        rule2 = "BULL"
    else:
        rule2 = "BEAR"
        
    # Gate decision
    if rule1 == "BULL" and rule2 == "BULL":
        gate = "LONG_ONLY"
        transitioning = False
    elif rule1 == "BEAR" and rule2 == "BEAR":
        gate = "SHORT_ONLY"
        transitioning = False
    else:
        gate = "BOTH_ALLOWED"
        transitioning = True

    # Calculate ADX 14 Using True Range and Directional Movement
    period = 14
    df = df_weekly.copy()
    
    # True Range
    df['TR1'] = abs(df['High'] - df['Low'])
    df['TR2'] = abs(df['High'] - df['Close'].shift(1))
    df['TR3'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['TR1', 'TR2', 'TR3']].max(axis=1)

    # Directional Movement
    df['up_move'] = df['High'] - df['High'].shift(1)
    df['down_move'] = df['Low'].shift(1) - df['Low']

    df['+DM'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0.0)
    df['-DM'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0.0)
    
    # Wilder's Smoothing
    alpha = 1 / period
    tr_smooth = df['TR'].ewm(alpha=alpha, adjust=False).mean()
    plus_dm_smooth = df['+DM'].ewm(alpha=alpha, adjust=False).mean()
    minus_dm_smooth = df['-DM'].ewm(alpha=alpha, adjust=False).mean()
    
    df['+DI'] = 100 * (plus_dm_smooth / tr_smooth)
    df['-DI'] = 100 * (minus_dm_smooth / tr_smooth)
    
    # DX and ADX
    df['DX'] = 100 * abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'] + 1e-10)
    adx_val = df['DX'].ewm(alpha=alpha, adjust=False).mean().iloc[-1]
    
    # ADX Scoring Rules
    if adx_val > 20:
        adx_quality = "STRONG"
        score_cap = 10.0
    elif 15 <= adx_val <= 20:
        adx_quality = "WEAK"
        score_cap = 7.0
    else:
        adx_quality = "RANGING"
        score_cap = 5.5
        
    return {
        "ema200": float(ema200),
        "ema50": float(ema50),
        "close": float(close),
        "rule1": rule1,
        "rule2": rule2,
        "gate": gate,
        "transitioning": transitioning,
        "adx_14": float(adx_val),
        "adx_quality": adx_quality,
        "score_cap": float(score_cap)
    }

def process_weekly_gates():
    # Local import — fetch_all_assets is only needed when running standalone.
    # run_technicals.py passes data in directly; do not import at module level.
    from data_fetcher import fetch_all_assets
    print("Fetching data to calculate Weekly Gates...")
    data = fetch_all_assets()
    results = {}
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    for asset_name, dfs in data.items():
        if "weekly" in dfs and not dfs["weekly"].empty:
            gate_data = calculate_weekly_gate(dfs["weekly"])
            gate_data["date"] = today_date
            results[asset_name] = gate_data
            
            print(f"Asset: {asset_name}")
            print(f"  Gate: {gate_data['gate']}")
            print(f"  ADX: {gate_data['adx_14']:.2f} -> {gate_data['adx_quality']} (Score Cap: {gate_data['score_cap']})\n")
    
    # Create outputs folder if it does not exist
    output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_file = os.path.join(output_dir, 'weekly_gate.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)
        
    print(f"Saved results to {output_file}")

if __name__ == "__main__":
    process_weekly_gates()
