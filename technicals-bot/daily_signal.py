import pandas as pd
import numpy as np

def calculate_daily_signal(df_daily, weekly_gate):
    """
    Evaluates multi-factor signals based on daily data and weekly gates.
    Returns: dict with signals, factor scores, flags, and raw data.
    """
    if df_daily is None or len(df_daily) < 252:
        # Not enough data for robust calculation (Need 252 days for ATR percentile)
        # Will proceed with available if > 20 but 252 is ideal.
        pass
        
    df = df_daily.copy()
    close_s = df['Close']
    open_s = df['Open']
    high_s = df['High']
    low_s = df['Low']
    vol_s = df['Volume']
    
    today_close = close_s.iloc[-1]
    today_open = open_s.iloc[-1]
    today_high = high_s.iloc[-1]
    today_low = low_s.iloc[-1]
    today_vol = vol_s.iloc[-1]

    # -----------------------------
    # FACTOR 1: TREND
    # -----------------------------
    ema50 = close_s.ewm(span=50, adjust=False).mean()
    ema200 = close_s.ewm(span=200, adjust=False).mean()
    
    t_ema50 = ema50.iloc[-1]
    t_ema200 = ema200.iloc[-1]
    
    # Sub-rule A: EMA Trends
    if today_close > t_ema50 and t_ema50 > t_ema200:
        ema_status = "ema_bull"
    elif today_close < t_ema50 and today_close < t_ema200: # "close below both"
        ema_status = "ema_bear"
    else:
        ema_status = "neutral"
        
    # Sub-rule B: Structure Trend
    prior_10_high = close_s.iloc[-11:-1].max()
    prior_10_low = close_s.iloc[-11:-1].min()
    
    if today_close > prior_10_high:
        struct_status = "structure_bull"
    elif today_close < prior_10_low:
        struct_status = "structure_bear"
    else:
        struct_status = "neutral"
        
    # Factor 1 Score
    f1_score = 0
    if ema_status == "ema_bull" and struct_status == "structure_bull":
        f1_score = 1
    elif ema_status == "ema_bear" and struct_status == "structure_bear":
        f1_score = -1
        
    # STRUCTURE_CONFLICT flag
    weekly_decision = weekly_gate.get("gate", "NEUTRAL")
    structure_conflict = False
    if struct_status == "structure_bear" and weekly_decision in ["LONG_ONLY"]:
        structure_conflict = True
    elif struct_status == "structure_bull" and weekly_decision in ["SHORT_ONLY"]:
        structure_conflict = True

    # -----------------------------
    # FACTOR 2: MOMENTUM
    # -----------------------------
    ema12 = close_s.ewm(span=12, adjust=False).mean()
    ema26 = close_s.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - signal_line
    
    roc_5 = close_s.pct_change(periods=5) * 100
    
    t_hist = macd_hist.iloc[-1]
    y_hist = macd_hist.iloc[-2]
    
    t_roc = roc_5.iloc[-1]
    y_roc = roc_5.iloc[-2]
    
    f2_score = 0
    if t_hist > 0 and t_hist > y_hist and t_roc > 0 and t_roc > y_roc:
        f2_score = 1
    elif t_hist < 0 and t_hist < y_hist and t_roc < 0 and t_roc < y_roc:
        f2_score = -1
        
    # FRESH_CROSS flag (hist crossed zero in last 2 bars)
    # Checking if sign changed between today/yesterday or yesterday/day before
    fresh_cross = False
    if len(macd_hist) > 3:
        h1, h2, h3 = macd_hist.iloc[-1], macd_hist.iloc[-2], macd_hist.iloc[-3]
        if (h1 >= 0 > h2) or (h1 <= 0 < h2) or (h2 >= 0 > h3) or (h2 <= 0 < h3):
            fresh_cross = True

    # -----------------------------
    # FACTOR 3: VOLATILITY
    # -----------------------------
    df['TR1'] = abs(high_s - low_s)
    df['TR2'] = abs(high_s - close_s.shift(1))
    df['TR3'] = abs(low_s - close_s.shift(1))
    tr = df[['TR1', 'TR2', 'TR3']].max(axis=1)
    
    atr14 = tr.ewm(alpha=1/14, adjust=False).mean()
    current_atr = atr14.iloc[-1]
    
    # Percentile calculation
    atr_window = atr14.iloc[-252:].dropna().values
    if len(atr_window) > 0:
        pct_rank = (np.sum(atr_window < current_atr) / len(atr_window)) * 100
    else:
        pct_rank = 50.0
        
    f3_score = 0
    if pct_rank > 70:
        f3_score = -1
    elif pct_rank < 30 and f1_score != 0:
        f3_score = 1

    # -----------------------------
    # FACTOR 4: VOLUME INTENT
    # -----------------------------
    avg_vol_20 = vol_s.rolling(20).mean()
    t_avg_vol = avg_vol_20.iloc[-1]
    
    spread = high_s - low_s
    avg_spread_10 = spread.rolling(10).mean()
    t_avg_spread = avg_spread_10.iloc[-1]
    
    t_spread = spread.iloc[-1]
    t_body = abs(today_close - today_open)
    
    is_up_candle = today_close > today_open
    is_down_candle = today_close < today_open
    
    vol_prior_2_check = (today_vol < vol_s.iloc[-2]) and (today_vol < vol_s.iloc[-3])
    spread_under_50 = t_spread < (0.5 * t_avg_spread)
    
    scores_f4 = []
    
    # Cond 1: High vol AND close moved in F1 direction
    if today_vol > 1.5 * t_avg_vol:
        if f1_score == 1 and is_up_candle:
            scores_f4.append(1)
        elif f1_score == -1 and is_down_candle:
            scores_f4.append(-1)
            
    # Cond 2 & 3: Low spread & low vol (VSA logic)
    if spread_under_50 and vol_prior_2_check:
        if is_up_candle:
            scores_f4.append(-1)
        elif is_down_candle:
            scores_f4.append(1)
            
    # Cond 4: Volume > 1.5 average AND body < 30% spread
    if today_vol > 1.5 * t_avg_vol and t_body < (0.3 * t_spread):
        scores_f4.append(-1)
        
    f4_score = 0
    if len(scores_f4) == 1:
        f4_score = scores_f4[0]
    elif len(scores_f4) > 1:
        # Check conflicts
        if all(s == scores_f4[0] for s in scores_f4):
            f4_score = scores_f4[0]
        else:
            f4_score = 0
            
    # -----------------------------
    # FINAL SIGNAL SUMMATION
    # -----------------------------
    total_score = f1_score + f2_score + f3_score + f4_score
    
    signal = "NO_SIGNAL"
    if total_score >= 3 and weekly_decision in ["LONG_ONLY", "BOTH_ALLOWED"]:
        signal = "LONG"
    elif total_score <= -3 and weekly_decision in ["SHORT_ONLY", "BOTH_ALLOWED"]:
        signal = "SHORT"

    return {
        "signal": signal,
        "total_score": total_score,
        "factors": {
            "F1_Trend": f1_score,
            "F2_Momentum": f2_score,
            "F3_Volatility": f3_score,
            "F4_Volume": f4_score
        },
        "flags": {
            "STRUCTURE_CONFLICT": structure_conflict,
            "FRESH_CROSS": fresh_cross
        },
        "raw_metrics": {
            "close": float(today_close),
            "ema50": float(t_ema50),
            "ema200": float(t_ema200),
            "macd_hist": float(t_hist),
            "roc_5": float(t_roc),
            "atr_pct_rank": float(pct_rank)
        }
    }

if __name__ == "__main__":
    import json
    import os
    from data_fetcher import fetch_all_assets

    print("Running Daily Signals Test...")
    
    output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
    wg_path = os.path.join(output_dir, 'weekly_gate.json')
    
    weekly_gates = {}
    if os.path.exists(wg_path):
        with open(wg_path, 'r') as f:
            weekly_gates = json.load(f)
            
    all_data = fetch_all_assets()
    
    for asset, dfs in all_data.items():
        if "daily" in dfs and not dfs["daily"].empty:
            wg = weekly_gates.get(asset, {"gate": "BOTH_ALLOWED"})
            res = calculate_daily_signal(dfs["daily"], wg)
            
            print(f"\n--- {asset} ---")
            print(f"Weekly Gate: {wg.get('gate', 'BOTH_ALLOWED')}")
            print(f"Daily Signal: {res['signal']} (Score: {res['total_score']})")
            print(f"Factors: {res['factors']}")
            print(f"Flags: {res['flags']}")
