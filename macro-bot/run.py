import datetime
from data_fetcher import fetch_macro_data, calculate_net_liquidity
from scorer import score_macro
from report import generate_report

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
    
    # 3. Generate report
    print("--> Calling report generator module...\n")
    generate_report(macro_data, result)
    
    # End outputs
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    report_filename = f"{today_str}.md"
    
    print(f"\nDone — report saved to reports/{report_filename}")
    
    # Master Readout in BIG Text
    print("\n" + "=" * 50)
    print(" MACRO BOT FINAL VERDICT ".center(50, "="))
    print("=" * 50)
    print(f"   REGIME: {result['regime']}   ".center(50))
    print(f"   TOTAL SCORE: {result['total_score']} ".center(50))
    print("=" * 50 + "\n")

if __name__ == "__main__":
    main()
