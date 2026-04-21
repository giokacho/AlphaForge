import os
import json
import csv
import time
import requests
from datetime import datetime, timezone
import traceback
from filelock import FileLock, Timeout
from dotenv import load_dotenv

load_dotenv()

def post_to_backend(payload: dict) -> None:
    backend_url = os.getenv("ALPHAFORGE_BACKEND_URL", "http://localhost:8000")
    secret = os.getenv("INTERNAL_SECRET", "")
    try:
        resp = requests.post(
            f"{backend_url}/internal/update/debate",
            json=payload,
            headers={"x-internal-key": secret},
            timeout=10
        )
        resp.raise_for_status()
        print(f"--> Backend POST /internal/update/debate -> {resp.status_code}")
    except Exception as e:
        print(f"--> Backend POST failed (non-fatal): {e}")

from data_assembler import get_data_block
from debaters import run_bull_bot, run_bear_bot
from synthesizer import run_synthesis

def run_all_debaters(data_block):
    bull_result = run_bull_bot(data_block)
    bear_result = run_bear_bot(data_block)
    
    # Mocking risk_result as part of this layer or pulling it dynamically
    # Since there wasn't a strict risk_bot defined in the directory previously.
    risk_result = {
        "regime_uncertainty": "NORMAL",
        "risk_score": 5,
        "top_tail_risk": "Mock Tail Risk",
        "data_contradictions": ["Mock contradiction 1", "Mock contradiction 2"]
    }
    return bull_result, bear_result, risk_result

def main():
    start_time = time.time()
    print(f"Debate Bot starting with datetime {datetime.now(timezone.utc).isoformat()}")
    
    step = 1
    try:
        # Step 1
        data_block = get_data_block()
        if data_block is None:
            print("Error: data_block is None")
            return
            
        # Step 2
        step = 2
        bull_result, bear_result, risk_result = run_all_debaters(data_block)
        bull_conviction = bull_result.get("conviction", 0) if isinstance(bull_result, dict) else 0
        bear_conviction = bear_result.get("conviction", 0) if isinstance(bear_result, dict) else 0
        risk_uncertainty = risk_result.get("regime_uncertainty", "UNKNOWN") if isinstance(risk_result, dict) else "UNKNOWN"
        print(f"Bull conviction: {bull_conviction}, Bear conviction: {bear_conviction}, Risk uncertainty: {risk_uncertainty}")
        
        # Step 3
        step = 3
        verdict = run_synthesis(
            data_block=data_block,
            bull_result=bull_result,
            bear_result=bear_result,
            risk_result=risk_result,
            all_no_signal=False,
            high_uncertainty=False,
            both_strong=False,
            hard_cancel_present=False
        )
        
        # Step 4
        step = 4
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(base_dir)
        shared_dir = os.path.join(project_root, 'shared')
        os.makedirs(shared_dir, exist_ok=True)

        # -- Build per-asset signals from technicals_data ------------------
        combined_path = os.path.join(shared_dir, 'combined_context.json')
        lock_path = combined_path.replace(".json", ".lock")
        tech_assets = {}
        if os.path.exists(combined_path):
            try:
                try:
                    with FileLock(lock_path, timeout=10):
                        with open(combined_path, 'r', encoding='utf-8') as f:
                            _ctx = json.load(f)
                        tech_assets = _ctx.get('technicals_data', {}).get('assets', {})
                except Timeout:
                    raise TimeoutError("Could not acquire lock on combined_context.json within 10 seconds.")
            except Exception as _e:
                print(f"[run_debate] Warning: could not read combined_context.json — {_e}")

        assets_out = {}
        for asset_name, a_data in tech_assets.items():
            fs    = a_data.get('final_score',   {})
            st    = a_data.get('stops_targets', {})
            et    = a_data.get('entry_timer',   {})
            ez    = et.get('entry_zone')        # list [low, high] or None
            assets_out[asset_name] = {
                'ticker':          a_data.get('ticker',                    'N/A'),
                'signal_strength': fs.get('signal_strength',               'NO_SIGNAL'),
                'direction':       fs.get('direction',                      'NO_SIGNAL'),
                'conviction_score': fs.get('final_score',                  0.0),
                'entry_zone':      f"{ez[0]:.2f}-{ez[1]:.2f}" if ez and len(ez) == 2 else 'N/A',
                'stop_loss':       st.get('stop_loss',                      0.0),
                'target_1':        st.get('target_1',                       0.0),
                'target_2':        st.get('target_2',                       0.0),
            }

        verdict['assets'] = assets_out
        # ------------------------------------------------------------------

        with open(os.path.join(shared_dir, 'final_verdict.json'), 'w', encoding='utf-8') as f:
            json.dump(verdict, f, indent=4)
            
        # Step 5
        step = 5
        outputs_dir = os.path.join(base_dir, 'outputs')
        os.makedirs(outputs_dir, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_json = os.path.join(outputs_dir, f"{date_str}_verdict.json")
        with open(daily_json, 'w', encoding='utf-8') as f:
            json.dump(verdict, f, indent=4)

        # POST to Railway backend (local file save above is kept as backup)
        post_to_backend(verdict)

        # Step 6
        step = 6
        csv_path = os.path.join(outputs_dir, 'verdict_history.csv')
        file_exists = os.path.exists(csv_path)
        
        headers = [
            "date", "final_direction", "overall_conviction", "position_size_recommendation",
            "gold_direction", "gold_conviction", "spx_direction", "spx_conviction",
            "nq_direction", "nq_conviction", "bull_case_score", "bear_case_score",
            "regime_uncertainty", "conflict_warning"
        ]
        
        row = {
            "date": verdict.get("run_timestamp", datetime.now(timezone.utc).isoformat()),
            "final_direction": verdict.get("final_direction", ""),
            "overall_conviction": verdict.get("overall_conviction", ""),
            "position_size_recommendation": verdict.get("position_size_recommendation", ""),
            "gold_direction": verdict.get("gold_direction", ""),
            "gold_conviction": verdict.get("gold_conviction", ""),
            "spx_direction": verdict.get("spx_direction", ""),
            "spx_conviction": verdict.get("spx_conviction", ""),
            "nq_direction": verdict.get("nq_direction", ""),
            "nq_conviction": verdict.get("nq_conviction", ""),
            "bull_case_score": bull_conviction,
            "bear_case_score": bear_conviction,
            "regime_uncertainty": verdict.get("regime_uncertainty", ""),
            "conflict_warning": verdict.get("conflict_warning", "")
        }
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
            
        print("Done saving outputs")
        
        # Step 7
        step = 7
        combined_path = os.path.join(shared_dir, 'combined_context.json')
        lock_path = combined_path.replace(".json", ".lock")
        combined_data = {}
        if os.path.exists(combined_path):
            try:
                with FileLock(lock_path, timeout=10):
                    with open(combined_path, 'r', encoding='utf-8') as f:
                        combined_data = json.load(f)
            except Timeout:
                raise TimeoutError("Could not acquire lock on combined_context.json within 10 seconds.")
                
        tech_data = combined_data.get('technicals_data', {}).get('assets', {})
        
        bull_signals = bull_result.get('top_3_bull_signals', ["N/A", "N/A", "N/A"]) if isinstance(bull_result, dict) else ["N/A", "N/A", "N/A"]
        bear_signals = bear_result.get('top_3_bear_signals', ["N/A", "N/A", "N/A"]) if isinstance(bear_result, dict) else ["N/A", "N/A", "N/A"]
        
        tail_risk = risk_result.get('top_tail_risk', 'None') if isinstance(risk_result, dict) else 'None'
        contradictions = risk_result.get('data_contradictions', ['None']) if isinstance(risk_result, dict) else ['None']
        if not isinstance(contradictions, list):
            contradictions = [contradictions]
            
        regime_unc = verdict.get("regime_uncertainty", "UNKNOWN")
        
        trade_params = []
        # technicals_data is keyed by config.py asset["name"], not ticker symbols
        asset_map = [("Gold", "Gold"), ("SPX", "SPX"), ("NQ", "NQ")]
        for asset_key, asset_label in asset_map:
            a_data = tech_data.get(asset_key, {})
            sig_dir = a_data.get("daily_signal", {}).get("signal", "NO_SIGNAL")
            stops = a_data.get("stops_targets", {})
            sl = stops.get("stop_loss", "N/A")
            t1 = stops.get("target_1", "N/A")
            t2 = stops.get("target_2", "N/A")
            trade_params.append(f"- **{asset_label}**: Signal: {sig_dir} | Stop Loss: {sl} | Target 1: {t1} | Target 2: {t2}")
            
        trade_params_str = "\n".join(trade_params)
        
        md_content = f"""# CIO VERDICT
- **Direction:** {verdict.get('final_direction', 'N/A')}
- **Conviction:** {verdict.get('overall_conviction', 'N/A')}/10
- **Size Recommendation:** {verdict.get('position_size_recommendation', 'N/A')}

## BULL CASE
1. {bull_signals[0] if len(bull_signals) > 0 else 'N/A'}
2. {bull_signals[1] if len(bull_signals) > 1 else 'N/A'}
3. {bull_signals[2] if len(bull_signals) > 2 else 'N/A'}

## BEAR CASE
1. {bear_signals[0] if len(bear_signals) > 0 else 'N/A'}
2. {bear_signals[1] if len(bear_signals) > 1 else 'N/A'}
3. {bear_signals[2] if len(bear_signals) > 2 else 'N/A'}

## RISK FLAGS
- **Top Tail Risk:** {tail_risk}
- **Data Contradictions:**
"""
        for i, c in enumerate(contradictions, 1):
            md_content += f"  {i}. {c}\n"
            
        md_content += f"- **Regime Uncertainty Score:** {regime_unc}\n\n"
        
        md_content += f"""## TRADE PARAMETERS
{trade_params_str}

## INVALIDATION
{verdict.get('invalidation_trigger', 'N/A')}

## CIO NOTE
{verdict.get('cio_note', 'N/A')}
"""
        md_path = os.path.join(outputs_dir, f"{date_str}_brief.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        # Step 8
        step = 8
        print("\n" + "=" * 40)
        print("CIO VERDICT")
        print("=" * 40)
        print(f"Direction:   {verdict.get('final_direction', 'N/A')}")
        print(f"Conviction:  {verdict.get('overall_conviction', 'N/A')}/10")
        print(f"Thesis:      {verdict.get('primary_thesis', 'N/A')}")
        print(f"Invalidate:  {verdict.get('invalidation_trigger', 'N/A')}")
        print("=" * 40)
        
        end_time = time.time()
        print(f"Total runtime: {end_time - start_time:.2f} seconds")
        
    except Exception as e:
        print(f"Failed at step {step}: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
