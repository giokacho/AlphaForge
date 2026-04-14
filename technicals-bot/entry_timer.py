import pandas as pd
import numpy as np

def check_entry(df_4h, daily_signal, levels, atr_regime):
    """
    Timer evaluating exact 4H entry mechanics separating Pullback reversals from Trend Breakouts.
    """
    if df_4h is None or df_4h.empty:
        return {"entry_confirmed": False, "error": "Empty 4H data"}

    today_close = df_4h['Close'].iloc[-1]
    today_vol = df_4h['Volume'].iloc[-1]
    
    sig = daily_signal.get('signal', 'NO_SIGNAL')
    factors = daily_signal.get('factors', {})
    f1 = factors.get('F1_Trend', 0)
    f2 = factors.get('F2_Momentum', 0)
    
    # -----------------------------
    # DETERMINE ENTRY MODE
    # -----------------------------
    mode = "PULLBACK"
    if sig == 'LONG' and f1 == 1 and f2 == 1 and today_close > levels.get('ten_day_high', float('inf')):
        mode = "BREAKOUT"
    elif sig == 'SHORT' and f1 == -1 and f2 == -1 and today_close < levels.get('ten_day_low', float('-inf')):
        mode = "BREAKOUT"
        
    entry_confirmed = False
    condition_results = {}
    
    # Variables referenced
    atr14 = atr_regime.get('atr_14', 1.0)
    cond_a = False
    cond_b = False
    cond_c = False
    cond_x = False
    cond_y = False
    deeper_pullback = False

    if mode == "PULLBACK" and sig != "NO_SIGNAL":
        # Condition A: EMAs (21 and 50)
        ema21 = df_4h['Close'].ewm(span=21, adjust=False).mean()
        ema50 = df_4h['Close'].ewm(span=50, adjust=False).mean()
        
        touched_21 = False
        touched_50 = False
        
        # Check last 3 bars for 0.3% proximity
        for i in range(-3, 0):
            if i < -len(df_4h):
                break
            c = df_4h['Close'].iloc[i]
            e21 = ema21.iloc[i]
            e50 = ema50.iloc[i]
            
            if abs(c - e21) / e21 <= 0.003:
                touched_21 = True
            if abs(c - e50) / e50 <= 0.003:
                touched_50 = True
                
        if touched_50:
            cond_a = True
            deeper_pullback = True
        elif touched_21:
            if sig == 'LONG' and today_close > ema21.iloc[-1]:
                cond_a = True
            elif sig == 'SHORT' and today_close < ema21.iloc[-1]:
                cond_a = True
                
        # Condition B: MACD Momentum Exhaustion
        ema12 = df_4h['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df_4h['Close'].ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - signal_line
        
        if len(macd_hist) >= 2:
            h1 = macd_hist.iloc[-1]
            h2 = macd_hist.iloc[-2]
            if sig == 'LONG' and h1 > h2:  # Positive turn or less negative
                cond_b = True
            elif sig == 'SHORT' and h1 < h2: # Negative turn or less positive
                cond_b = True
                
        # Condition C: Structure Proximity
        if sig == 'LONG':
            dist = abs(today_close - levels.get('nearest_support', 0))
        else:
            dist = abs(today_close - levels.get('nearest_resistance', float('inf')))
            
        if dist <= 0.8 * atr14:
            cond_c = True
        elif dist > 1.5 * atr14:
            cond_c = False # strict
            
        # Entry Validation
        cnt = sum([cond_a, cond_b, cond_c])
        if cnt >= 2:
            entry_confirmed = True
            
        condition_results = {
            "cond_a_ema_touch": bool(cond_a),
            "cond_b_macd_turn": bool(cond_b),
            "cond_c_struct_prox": bool(cond_c),
            "deeper_pullback": bool(deeper_pullback)
        }

    elif mode == "BREAKOUT" and sig != "NO_SIGNAL":
        # Condition X: Prior Peak Penetration
        if sig == 'LONG':
            cond_x = today_close > levels.get('prior_day_high', float('inf'))
        else:
            cond_x = today_close < levels.get('prior_day_low', float('-inf'))
            
        # Condition Y: Volume Intent
        vol_20 = df_4h['Volume'].rolling(20).mean()
        t_vol_20 = vol_20.iloc[-1]
        
        cond_y = today_vol > t_vol_20
        
        if cond_x and cond_y:
            entry_confirmed = True
            
        condition_results = {
            "cond_x_price_break": bool(cond_x),
            "cond_y_vol_break": bool(cond_y)
        }

    # Execute exact entry zone bounding (+/- 0.2%)
    entry_zone = None
    if entry_confirmed:
        entry_zone = [today_close * 0.998, today_close * 1.002]

    return {
        "mode": mode,
        "signal_direction": sig,
        "conditions": condition_results,
        "entry_confirmed": entry_confirmed,
        "entry_zone": entry_zone
    }

if __name__ == "__main__":
    from data_fetcher import fetch_all_assets
    from daily_signal import calculate_daily_signal
    from levels import calculate_atr_regime, calculate_key_levels
    import json
    
    print("Testing 4H Entry Timer...")
    all_data = fetch_all_assets()

    # We mock weekly_gates to let the daily pipeline score cleanly
    wg_mock = {"gate": "BOTH_ALLOWED"} 

    for asset, dfs in all_data.items():
        if "daily" in dfs and not dfs["daily"].empty and "4h" in dfs and not dfs["4h"].empty:
            df_d = dfs["daily"]
            df_4h = dfs["4h"]
            
            # Simulated environment dependencies
            daily_res = calculate_daily_signal(df_d, wg_mock)
            
            # Note: The logic requires LONG or SHORT to process entries. 
            # If the current score doesn't naturally trigger LONG/SHORT, we simulate LONG just to verify math pathways.
            if daily_res['signal'] == "NO_SIGNAL":
                 daily_res['signal'] = "LONG"
                 daily_res['factors']['F1_Trend'] = 1
                 daily_res['factors']['F2_Momentum'] = 1
                 
            regime = calculate_atr_regime(df_d)
            levels_res = calculate_key_levels(df_d)
            
            entry = check_entry(df_4h, daily_res, levels_res, regime)
            print(f"\n--- {asset} Entry Output ---")
            print(json.dumps(entry, indent=2))
