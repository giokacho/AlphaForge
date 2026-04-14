import datetime
import yfinance as yf
from fredapi import Fred
from config import FRED_API_KEY

def fetch_macro_data():
    macro_data = {}
    
    # 1. Fetch from Yahoo Finance
    # VIX
    try:
        vix_data = yf.Ticker("^VIX").history(period="5d")
        macro_data['VIX'] = float(vix_data['Close'].dropna().iloc[-1]) if not vix_data.empty else None
    except Exception as e:
        macro_data['VIX'] = None
        print(f"Warning: Failed to fetch VIX from Yahoo Finance: {e}")
        
    # DXY (US Dollar Index)
    try:
        dxy_data = yf.Ticker("DX-Y.NYB").history(period="5d")
        macro_data['DXY'] = float(dxy_data['Close'].dropna().iloc[-1]) if not dxy_data.empty else None
    except Exception as e:
        macro_data['DXY'] = None
        print(f"Warning: Failed to fetch DXY from Yahoo Finance: {e}")

    # MOVE Index
    try:
        move_data = yf.Ticker("^MOVE").history(period="5d")
        if not move_data.empty:
            macro_data['MOVE'] = float(move_data['Close'].dropna().iloc[-1])
        else:
            macro_data['MOVE'] = 110.0
            print("Warning: MOVE data empty from yfinance, using fallback.")
    except Exception as e:
        macro_data['MOVE'] = 110.0 # manual fallback 
        print(f"Warning: Failed to fetch MOVE from Yahoo Finance, using fallback: {e}")
        
    # NYA Breadth Proxy (% of days above 200 SMA in the last 200 days)
    try:
        nya_data = yf.Ticker("^NYA").history(period="410d")['Close']
        if not nya_data.empty and len(nya_data) >= 200:
            sma200 = nya_data.rolling(window=200).mean()
            past_200_days = nya_data.iloc[-200:]
            past_200_sma = sma200.iloc[-200:]
            pct_above = (past_200_days > past_200_sma).sum() / 200.0 * 100.0
            macro_data['Breadth'] = float(pct_above)
        else:
            macro_data['Breadth'] = 50.0
            print("Warning: Insufficient NYA data to calculate Breadth, using fallback 50.0")
    except Exception as e:
        macro_data['Breadth'] = 50.0 # manual fallback
        print(f"Warning: Failed to fetch NYA Breadth from Yahoo Finance, using fallback: {e}")

    # 2. Fetch from FRED
    try:
        fred = Fred(api_key=FRED_API_KEY)
        fred_series = {
            'US10Y': 'DGS10',
            'US2Y': 'DGS2',
            'HY_Spread': 'BAMLH0A0HYM2',
            'Fed_Balance_Sheet': 'WALCL',
            'TGA_Balance': 'WTREGEN',
            'Overnight_RRP': 'RRPONTSYD',
            'TIPS_10Y': 'DFII10'
        }
        
        for key, series_id in fred_series.items():
            try:
                # get_series returns a pandas Series indexed by date.
                data = fred.get_series(series_id)
                macro_data[key] = float(data.dropna().iloc[-1])
            except Exception as e:
                macro_data[key] = None
                print(f"Warning: Failed to fetch {key} ({series_id}): {e}")
                
    except ValueError as ve:
        print(f"Warning: FRED API Initialization Error - {ve}. Please ensure your FRED_API_KEY is correct.")
        fred_keys = ['US10Y', 'US2Y', 'HY_Spread', 'Fed_Balance_Sheet', 'TGA_Balance', 'Overnight_RRP', 'TIPS_10Y']
        for key in fred_keys:
            macro_data[key] = None
    except Exception as e:
        print(f"Warning: Unexpected error calling FRED API: {e}")
        fred_keys = ['US10Y', 'US2Y', 'HY_Spread', 'Fed_Balance_Sheet', 'TGA_Balance', 'Overnight_RRP', 'TIPS_10Y']
        for key in fred_keys:
            macro_data[key] = None

    return macro_data

def calculate_net_liquidity(macro_data):
    """
    Computes Net Liquidity: WALCL - WTREGEN - RRPONTSYD
    WALCL and WTREGEN are in Millions of USD, so we convert them to Billions
    to match RRPONTSYD (which is in Billions of USD).
    """
    walcl = macro_data.get('Fed_Balance_Sheet')
    wtregen = macro_data.get('TGA_Balance')
    rrp = macro_data.get('Overnight_RRP')

    if None not in (walcl, wtregen, rrp):
        # Convert Millions to Billions
        walcl_b = walcl / 1000
        wtregen_b = wtregen / 1000
        current_nl = walcl_b - wtregen_b - rrp
        macro_data['net_liquidity'] = current_nl
        
        try:
            fred = Fred(api_key=FRED_API_KEY)
            
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=60)
            
            walcl_series = fred.get_series('WALCL', observation_start=start_date)
            wtregen_series = fred.get_series('WTREGEN', observation_start=start_date)
            rrp_series = fred.get_series('RRPONTSYD', observation_start=start_date)
            
            # Go back 28 days from the most recent WALCL observation
            latest_idx = walcl_series.dropna().index[-1]
            target_date = latest_idx - datetime.timedelta(days=28)
            
            past_walcl = walcl_series.loc[:target_date].dropna().iloc[-1]
            past_wtregen = wtregen_series.loc[:target_date].dropna().iloc[-1]
            past_rrp = rrp_series.loc[:target_date].dropna().iloc[-1]
            
            past_nl = (past_walcl / 1000) - (past_wtregen / 1000) - past_rrp
            macro_data['net_liquidity_4w_change'] = current_nl - past_nl
        except Exception as e:
            print(f"Warning: Failed to calculate 4-week change for Net Liquidity: {e}")
            macro_data['net_liquidity_4w_change'] = None
    else:
        macro_data['net_liquidity'] = None
        macro_data['net_liquidity_4w_change'] = None

    return macro_data

if __name__ == "__main__":
    import pprint
    print("Fetching macro data...")
    data = fetch_macro_data()
    data = calculate_net_liquidity(data)
    print("\n--- Latest Macro Data ---")
    pprint.pprint(data)
