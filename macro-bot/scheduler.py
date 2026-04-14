import schedule
import time
import datetime
from data_fetcher import fetch_macro_data, calculate_net_liquidity
from scorer import score_macro
from report import generate_report

def run_pipeline():
    start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{start_time}] --- Starting Macro-Bot Pipeline ---")
    
    try:
        # 1. Fetch data
        print(f"[{start_time}] Fetching macro data...")
        macro_data = fetch_macro_data()
        macro_data = calculate_net_liquidity(macro_data)
        
        # 2. Score macro data
        print(f"[{start_time}] Calculating scores...")
        result = score_macro(macro_data)
        regime = result.get('regime', 'UNKNOWN')
        
        # 3. Generate report
        print(f"[{start_time}] Initializing report generation...")
        generate_report(macro_data, result)
        
        # Print verdict
        finish_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{finish_time}] Pipeline completed successfully.")
        print(f"[{finish_time}] FINAL REGIME VERDICT: {regime}")
        
    except Exception as e:
        finish_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{finish_time}] [ERROR] Pipeline failed: {e}")

# Schedule the pipeline to run Monday through Friday at 09:30 AM
schedule.every().monday.at("09:30").do(run_pipeline)
schedule.every().tuesday.at("09:30").do(run_pipeline)
schedule.every().wednesday.at("09:30").do(run_pipeline)
schedule.every().thursday.at("09:30").do(run_pipeline)
schedule.every().friday.at("09:30").do(run_pipeline)

if __name__ == "__main__":
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now_str}] Macro-Bot Scheduler Started.")
    
    print("Running initial pipeline test (Immediate Run)...")
    run_pipeline()
    
    print("\nScheduler is active. Waiting for the next scheduled run at 09:30 AM (Weekdays)...")
    while True:
        schedule.run_pending()
        time.sleep(60) # Sleep for a minute to check schedule again to minimize CPU usage
