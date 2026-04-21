import os
import json
import requests
from datetime import datetime, timezone
from filelock import FileLock, Timeout
from dotenv import load_dotenv

load_dotenv()

def post_to_backend(payload: dict) -> None:
    backend_url = os.getenv("ALPHAFORGE_BACKEND_URL", "http://localhost:8000")
    secret = os.getenv("INTERNAL_SECRET", "")
    try:
        resp = requests.post(
            f"{backend_url}/internal/update/cot",
            json=payload,
            headers={"x-internal-key": secret},
            timeout=10
        )
        resp.raise_for_status()
        print(f"--> Backend POST /internal/update/cot → {resp.status_code}")
    except Exception as e:
        print(f"--> Backend POST failed (non-fatal): {e}")

from config import ASSETS, CFTC_MAPPING, DATA_DIR
from fetcher import fetch_cot_data
from analyzer import (
    calculate_net_positions,
    get_institutional_bias,
    get_positioning_extreme,
    get_crowding_risk
)

def export_for_orchestrator(cot_output: dict):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    ctx_path = os.path.join(project_root, "shared", "combined_context.json")
    lock_path = ctx_path.replace(".json", ".lock")
    
    if os.path.exists(ctx_path):
        try:
            with FileLock(lock_path, timeout=10):
                with open(ctx_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = {}
        except Timeout:
            raise TimeoutError("Could not acquire lock on combined_context.json within 10 seconds.")
    else:
        data = {}
        
    data["cot_data"] = cot_output
    
    os.makedirs(os.path.dirname(ctx_path), exist_ok=True)
    try:
        with FileLock(lock_path, timeout=10):
            with open(ctx_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
    except Timeout:
        raise TimeoutError("Could not acquire lock on combined_context.json within 10 seconds.")
        
    print("COT context exported successfully")

def run_cot_pipeline():
    """
    Master pipeline for the COT bot.
    Fetches data, calculates net positions, and generates metrics for 
    institutional bias, extremes, and crowding risk.
    """
    run_timestamp = datetime.now(timezone.utc).isoformat()
    
    cot_output = {
        "run_timestamp": run_timestamp,
        "assets": {}
    }
    
    # Ensure outputs directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print("=" * 60)
    print("                COT-BOT PIPELINE START")
    print("=" * 60)
    
    for asset in ASSETS:
        print(f"\nProcessing {asset}...")
        cftc_code = CFTC_MAPPING.get(asset)
        
        try:
            # Step 1: Fetch data
            df = fetch_cot_data(cftc_code)
            
            # Step 2: Calculate net positions
            df = calculate_net_positions(df)
            
            # Step 3: Get institutional bias
            bias = get_institutional_bias(df)
            
            # Step 4: Get positioning extreme
            extreme_data = get_positioning_extreme(df)
            
            # Step 5: Get crowding risk
            crowding_data = get_crowding_risk(df)
            
            # Record results
            cot_output["assets"][asset] = {
                "institutional_bias": bias,
                "positioning_extreme": extreme_data['extreme'],
                "positioning_percentile": extreme_data['percentile'],
                "crowding_risk": crowding_data['risk']
            }
            
            # Print asset summary
            print(f"  [+] Success")
            print(f"      Bias       : {bias}")
            print(f"      Extreme?   : {extreme_data['extreme']} (Pct: {extreme_data['percentile']})")
            print(f"      Crowding   : {crowding_data['risk']}")
            
        except Exception as e:
            print(f"  [-] Failed processing for {asset}: {e}")
            cot_output["assets"][asset] = {
                "error": str(e)
            }
            
    print("\n" + "=" * 60)
    print("                PIPELINE COMPLETE")
    print("=" * 60)
    
    # Save output to JSON
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_path = os.path.join(DATA_DIR, f"{date_str}_cot.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cot_output, f, indent=4)
        
    print(f"\nSaved COT report to: {output_path}")
    export_for_orchestrator(cot_output)

    # POST to Railway backend (local file save above is kept as backup)
    post_to_backend(cot_output)

if __name__ == "__main__":
    run_cot_pipeline()
