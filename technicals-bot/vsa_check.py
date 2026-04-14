import pandas as pd

def run_vsa_check(df_daily, signal_direction):
    """
    Evaluates Volume Spread Analysis (VSA) rules on the most recent daily candle.
    Used as an external gating check to flag exhaustion or hidden intent.
    """
    if df_daily is None or df_daily.empty or len(df_daily) < 20:
        return {"hard_cancel": False, "vsa_flag": "NONE", "score_adjustment": 0.0}
        
    df = df_daily.copy()
    
    # Extract calculations from the most recent completed daily candle
    open_p = df['Open'].iloc[-1]
    close_p = df['Close'].iloc[-1]
    high_p = df['High'].iloc[-1]
    low_p = df['Low'].iloc[-1]
    vol = df['Volume'].iloc[-1]
    
    vol_prev1 = df['Volume'].iloc[-2]
    vol_prev2 = df['Volume'].iloc[-3]
    
    volume_20avg = df['Volume'].rolling(20).mean().iloc[-1]
    
    spread_series = df['High'] - df['Low']
    spread_10avg = spread_series.rolling(10).mean().iloc[-1]
    
    body = abs(close_p - open_p)
    candle_spread = high_p - low_p
    
    up_bar = close_p > open_p
    down_bar = close_p < open_p
    
    hard_cancel = False
    vsa_flag = "NONE"
    score_adjustment = 0.0
    
    # Rule 1: Effort vs Result
    if vol > 1.5 * volume_20avg and body < 0.3 * candle_spread:
        if up_bar and signal_direction == 'LONG':
            close_pos = (close_p - low_p) / candle_spread if candle_spread > 0 else 0.5
            if close_pos > 0.6:
                score_adjustment -= 0.5
                vsa_flag = "ABSORPTION_POSSIBLE"
            elif close_pos < 0.4:
                return {"hard_cancel": True, "vsa_flag": "HARD_CANCEL", "score_adjustment": 0.0}
        if down_bar and signal_direction == 'SHORT':
            return {"hard_cancel": True, "vsa_flag": "HARD_CANCEL", "score_adjustment": 0.0}
            
        if up_bar and signal_direction == 'SHORT':
            score_adjustment += 0.5
            vsa_flag = "EFFORT_VS_RESULT_SUPPORT"
        if down_bar and signal_direction == 'LONG':
            score_adjustment += 0.5
            vsa_flag = "EFFORT_VS_RESULT_SUPPORT"
            
    # Rule 2: Stopping Volume
    if vol > 2.0 * volume_20avg and candle_spread < 0.5 * spread_10avg:
        if down_bar and signal_direction == 'LONG':
            score_adjustment += 0.5
            if vsa_flag == "NONE": vsa_flag = "STOPPING_VOLUME"
            else: vsa_flag += "+STOPPING_VOLUME"
        elif up_bar and signal_direction == 'SHORT':
            score_adjustment += 0.5
            if vsa_flag == "NONE": vsa_flag = "STOPPING_VOLUME"
            else: vsa_flag += "+STOPPING_VOLUME"
            
    # Rule 3: No Demand
    if up_bar and candle_spread < 0.5 * spread_10avg and vol < vol_prev1 and vol < vol_prev2:
        if signal_direction == 'LONG':
            score_adjustment -= 0.5
            if vsa_flag == "NONE": vsa_flag = "NO_DEMAND"
            else: vsa_flag += "+NO_DEMAND"
            
    # Rule 4: No Supply
    if down_bar and candle_spread < 0.5 * spread_10avg and vol < vol_prev1 and vol < vol_prev2:
        if signal_direction == 'SHORT':
            score_adjustment -= 0.5
            if vsa_flag == "NONE": vsa_flag = "NO_SUPPLY"
            else: vsa_flag += "+NO_SUPPLY"
            
    if hard_cancel:
        vsa_flag = "HARD_CANCEL"
    elif score_adjustment > 0:
        vsa_flag = "SUPPORTIVE"
    elif score_adjustment < 0:
        vsa_flag = "WEAKENING"
    else:
        vsa_flag = "NONE"
        
    return {
        "hard_cancel": bool(hard_cancel),
        "vsa_flag": str(vsa_flag),
        "score_adjustment": float(score_adjustment)
    }

if __name__ == "__main__":
    from data_fetcher import fetch_all_assets
    from daily_signal import calculate_daily_signal
    
    print("Testing VSA Final Check Process...")
    all_data = fetch_all_assets()
    wg_mock = {"gate": "BOTH_ALLOWED"} 
    
    for asset, dfs in all_data.items():
        if "daily" in dfs and not dfs["daily"].empty:
            df_d = dfs["daily"]
            
            daily_res = calculate_daily_signal(df_d, wg_mock)
            sig_dir = daily_res.get('signal', 'NO_SIGNAL')
            
            print(f"\n--- {asset} ---")
            print(f"Signal Direction: {sig_dir}")
            
            if sig_dir not in ['LONG', 'SHORT']:
                print("Skipping VSA (requires LONG or SHORT status).")
                continue
                
            vsa_results = run_vsa_check(df_d, sig_dir)
            
            print(f"Hard Cancel:      {vsa_results['hard_cancel']}")
            print(f"VSA Flag:         {vsa_results['vsa_flag']}")
            print(f"Score Adjustment: {vsa_results['score_adjustment']}")
