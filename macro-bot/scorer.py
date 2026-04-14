from config import THRESHOLDS

def score_macro(macro_data):
    scores = {}
    missing_indicators = []
    
    # helper for checking None
    def add_missing(name):
        scores[name] = 0
        if name not in missing_indicators:
            missing_indicators.append(name)

    # 1. VIX
    vix = macro_data.get('VIX')
    if vix is not None:
        if vix > THRESHOLDS['VIX_BEARISH_ABOVE']:
            scores['VIX'] = -1
        elif vix < THRESHOLDS['VIX_BULLISH_BELOW']:
            scores['VIX'] = 1
        else:
            scores['VIX'] = 0
    else:
        add_missing('VIX')
            
    # 2. HY Spread 
    hy_spread = macro_data.get('HY_Spread')
    if hy_spread is not None:
        hy_bps = hy_spread * 100
        if hy_bps > THRESHOLDS['HY_SPREAD_BEARISH_ABOVE']:
            scores['HY_Spread'] = -1
        elif hy_bps < THRESHOLDS['HY_SPREAD_BULLISH_BELOW']:
            scores['HY_Spread'] = 1
        else:
            scores['HY_Spread'] = 0
    else:
        add_missing('HY_Spread')
            
    # 3. Breadth
    breadth = macro_data.get('Breadth')
    if breadth is not None:
        if breadth < THRESHOLDS['BREADTH_BEARISH_BELOW']:
            scores['Breadth'] = -1
        elif breadth > THRESHOLDS['BREADTH_BULLISH_ABOVE']:
            scores['Breadth'] = 1
        else:
            scores['Breadth'] = 0
    else:
        add_missing('Breadth')
            
    # 4. MOVE
    move = macro_data.get('MOVE')
    if move is not None:
        if move > THRESHOLDS['MOVE_BEARISH_ABOVE']:
            scores['MOVE'] = -1
        else:
            scores['MOVE'] = 0
    else:
        add_missing('MOVE')
            
    # 5. Yield Curve
    us10y = macro_data.get('US10Y')
    us2y = macro_data.get('US2Y')
    if us10y is not None and us2y is not None:
        yield_curve = us10y - us2y
        if yield_curve < THRESHOLDS['YIELD_CURVE_INVERSION']:
            scores['Yield_Curve'] = -1
        else:
            scores['Yield_Curve'] = 0
    else:
        add_missing('Yield_Curve')
        if us10y is None: add_missing('US10Y')
        if us2y is None: add_missing('US2Y')
            
    # 6. Net Liquidity 4W Change
    nl_4w = macro_data.get('net_liquidity_4w_change')
    if nl_4w is not None:
        if nl_4w < 0:
            scores['Net_Liquidity_4w'] = -1
        elif nl_4w > 0:
            scores['Net_Liquidity_4w'] = 1
        else:
            scores['Net_Liquidity_4w'] = 0
    else:
        add_missing('Net_Liquidity_4w')
            
    # Sum all scores
    total_score = sum(scores.values())
    
    # Determine regime
    if total_score > 2:
        regime = "RISK_ON"
    elif total_score < -2:
        regime = "RISK_OFF"
    else:
        regime = "TRANSITION"
        
    return {
        "individual_scores": scores,
        "total_score": total_score,
        "regime": regime,
        "missing_indicators": missing_indicators
    }

if __name__ == "__main__":
    from data_fetcher import fetch_macro_data, calculate_net_liquidity
    import pprint
    
    print("Fetching macro data to test scorer...")
    data = fetch_macro_data()
    data = calculate_net_liquidity(data)
    
    result = score_macro(data)
    
    print("\n--- Scoring Result ---")
    pprint.pprint(result)
