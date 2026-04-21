import datetime
import os
import requests
from dotenv import load_dotenv
from data_fetcher import fetch_macro_data, calculate_net_liquidity
from scorer import score_macro
from report import generate_report

load_dotenv()

def post_to_backend(payload: dict) -> None:
    backend_url = os.getenv("ALPHAFORGE_BACKEND_URL", "http://localhost:8000")
    secret = os.getenv("INTERNAL_SECRET", "")
    try:
        resp = requests.post(
            f"{backend_url}/internal/update/macro",
            json=payload,
            headers={"x-internal-key": secret},
            timeout=10
        )
        resp.raise_for_status()
        print(f"--> Backend POST /internal/update/macro → {resp.status_code}")
    except Exception as e:
        print(f"--> Backend POST failed (non-fatal): {e}")

def main():
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Macro Bot starting — {now_str}\n")

    # 1. Fetch data
    print("--> Fetching macro data from API sources...")
    macro_data = fetch_macro_data()
    macro_data = calculate_net_liquidity(macro_data)

    # 2. Score indicators
    print("--> Scoring compiled indicators...")
    result = score_macro(macro_data)

    # 3. Generate report (local markdown backup)
    print("--> Calling report generator module...\n")
    generate_report(macro_data, result)

    today_str = datetime.date.today().strftime('%Y-%m-%d')
    report_filename = f"{today_str}.md"
    print(f"\nDone — report saved to reports/{report_filename}")

    # 4. POST to Railway backend (keeps local file save above as backup)
    post_payload = {
        **result,
        "indicators": macro_data,
        "run_date": today_str,
    }
    post_to_backend(post_payload)

    # Master Readout
    print("\n" + "=" * 50)
    print(" MACRO BOT FINAL VERDICT ".center(50, "="))
    print("=" * 50)
    print(f"   REGIME: {result['regime']}   ".center(50))
    print(f"   TOTAL SCORE: {result['total_score']} ".center(50))
    print("=" * 50 + "\n")

if __name__ == "__main__":
    main()
