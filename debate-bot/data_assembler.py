import os
import json

def assemble_data_block():
    """
    Reads shared/combined_context.json, extracts and formats all relevant fields 
    into a clean structured string for an AI API call.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    file_path = os.path.join(project_root, 'shared', 'combined_context.json')
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Context file not found at: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    macro = data.get("macro_data", {})
    if isinstance(macro, str):
        # Fallback if macro is stored as a direct string instead of dict
        macro = {}

    macro_block = f"""MACRO REGIME SECTION
--------------------
Regime Label (Current Market State): {macro.get('regime_label', macro.get('regime', data.get('macro_regime', 'UNKNOWN')))}
Total Score (Macro conviction): {macro.get('total_score', 'N/A')}
Vix Score (Volatility): {macro.get('vix_score', 'N/A')}
HY Spread Score (Credit Risk): {macro.get('hy_spread_score', 'N/A')}
Yield Curve Score (Bond Market): {macro.get('yield_curve_score', 'N/A')}
Net Liquidity 4 Week Change (Cash Flowing in/out): {macro.get('net_liquidity_4wk_change', 'N/A')}
Combined Risk Level (Master Risk Filter): {data.get('combined_risk_level', 'N/A')}
"""

    news = data.get("news_data", {})
    news_block = f"""NEWS SENTIMENT SECTION
----------------------
Overall Sentiment Score (-1.0 to +1.0, extreme bearish to extreme bullish): {news.get('overall_sentiment', 'N/A')}
Gold Score (Asset specific news sentiment): {news.get('gold_score', 'N/A')}
SPX Score (Asset specific news sentiment): {news.get('spx_score', 'N/A')}
NQ Score (Asset specific news sentiment): {news.get('nq_score', 'N/A')}
Geopolitical Risk (Current global tensions context): {news.get('geopolitical_risk', 'N/A')}
Dominant Narrative (Main story driving markets): {news.get('dominant_narrative', 'N/A')}
Contradiction Flag (True if internal metrics disagree, meaning higher risk): {news.get('contradiction_flag', 'N/A')}
Contradiction Reason (Explanation of what metrics are disagreeing): {news.get('contradiction_reason', 'N/A')}
Forward Event Risk (Impending high impact news items): {news.get('forward_event_risk', 'N/A')}
"""

    techs = data.get("technicals_data", {}).get("assets", {})
    tech_block = "TECHNICALS SECTION\n------------------\n"
    
    nq_signal = "NO_SIGNAL"
    nq_score = 0
    spx_signal = "NO_SIGNAL"
    spx_score = 0
    
    for target in ["GLD", "SPY", "QQQ"]:
        # Map back to Gold, SPX, NQ naming conventionally
        asset_label = "Gold" if target == "GLD" else ("SPX" if target == "SPY" else "NQ")
        a_data = techs.get(target, {})
        
        d_sig = a_data.get("daily_signal", {}).get("signal", "NO_SIGNAL")
        f_score = a_data.get("final_score", {})
        c_score = f_score.get("final_score", 0)
        s_strength = f_score.get("signal_strength", "NONE")
        e_mode = a_data.get("entry_timer", {}).get("mode", "N/A")
        w_gate = a_data.get("weekly_gate", {}).get("gate", "NEUTRAL")
        v_flag = a_data.get("vsa_check", {}).get("vsa_flag", "NONE")
        stops = a_data.get("stops_targets", {})
        s_loss = stops.get("stop_loss", 0.0)
        t1 = stops.get("target_1", 0.0)
        t2 = stops.get("target_2", 0.0)
        
        # Factor breakdown showing each as plus 1 zero or minus 1
        f1 = f_score.get("F1", 0)
        f2 = f_score.get("F2", 0)
        f3 = f_score.get("F3", 0)
        f4 = f_score.get("F4", 0)
        
        if asset_label == "SPX":
            spx_signal = d_sig
            spx_score = c_score
        if asset_label == "NQ":
            nq_signal = d_sig
            nq_score = c_score
            
        tech_block += f"""Asset: {asset_label}
Signal Direction (LONG/SHORT/NO_SIGNAL): {d_sig}
Conviction Score (Out of 10): {c_score}
Signal Strength Label (Categorized strength): {s_strength}
Entry Mode (Aggressive or Conservative): {e_mode}
Weekly Gate (Higher timeframe backdrop filter): {w_gate}
Factor Breakdown (F1=Trend, F2=Momentum, F3=Vol, F4=Supp/Res. +1, 0, or -1): F1:{f1} F2:{f2} F3:{f3} F4:{f4}
VSA Flag (Volume Spread Analysis Confirmation): {v_flag}
Stop Loss (Price to exit): {s_loss}
Target 1 (Primary objective): {t1}
Target 2 (Secondary objective): {t2}
"""

    rel_block = "RELATIONSHIP SIGNALS\n--------------------\n"
    outperf_text = "Neutral / Not enough data to determine comparative outperformance."
    if nq_signal == "LONG" and spx_signal == "LONG":
        if nq_score > spx_score:
            outperf_text = "NQ is OUTPERFORMING SPX to the upside."
        elif nq_score < spx_score:
            outperf_text = "NQ is UNDERPERFORMING SPX to the upside."
        else:
            outperf_text = "NQ and SPX are performing equally to the upside."
    elif nq_signal == "SHORT" and spx_signal == "SHORT":
        if nq_score > spx_score:
            outperf_text = "NQ is OUTPERFORMING SPX to the downside (leading the selloff)."
        elif nq_score < spx_score:
            outperf_text = "NQ is UNDERPERFORMING SPX to the downside (showing relative strength)."
        else:
            outperf_text = "NQ and SPX are performing equally to the downside."
    elif nq_signal == "LONG" and spx_signal != "LONG":
        outperf_text = "NQ is OUTPERFORMING SPX (NQ is LONG, SPX is not)."
    elif nq_signal == "SHORT" and spx_signal != "SHORT":
        outperf_text = "NQ is OUTPERFORMING SPX to the downside (NQ is SHORT, SPX is not)."
    elif spx_signal == "LONG" and nq_signal != "LONG":
        outperf_text = "NQ is UNDERPERFORMING SPX (SPX is LONG, NQ is not)."
    elif spx_signal == "SHORT" and nq_signal != "SHORT":
        outperf_text = "NQ is UNDERPERFORMING SPX to the downside (SPX is SHORT, NQ is not)."

    rel_block += f"Outperformance Measure: {outperf_text}\n"

    cot = data.get("cot_data", {}).get("assets", {})
    cot_block = "COT POSITIONING\n---------------\n"
    for target in ["GLD", "SPY", "QQQ"]:
        asset_label = "Gold" if target == "GLD" else ("SPX" if target == "SPY" else "NQ")
        a_cot = cot.get(asset_label, {})
        bias = a_cot.get("institutional_bias", "N/A")
        extreme = a_cot.get("positioning_extreme", "N/A")
        crowding = a_cot.get("crowding_risk", "N/A")
        
        cot_block += f"Asset: {asset_label}\n"
        cot_block += f"Institutional Bias: {bias}\n"
        cot_block += f"Positioning Extreme: {extreme}\n"
        cot_block += f"Crowding Risk: {crowding}\n\n"

    final_output = f"{macro_block}\n{news_block}\n{tech_block}\n{rel_block}\n{cot_block}"
    return final_output


def get_data_block():
    """
    Calls assemble_data_block and catches FileNotFoundError to handle gracefully.
    Returns the block or None.
    """
    try:
        return assemble_data_block()
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        return None
    except Exception as e:
        print(f"Warning: Failed to assemble data block: {e}")
        return None


if __name__ == "__main__":
    block = get_data_block()
    if block:
        print(block)
