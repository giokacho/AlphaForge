import yfinance as yf
import pandas as pd
from config import ASSETS, LOOKBACK_DAYS

def fetch_asset_data(ticker: str, lookback_days: int = LOOKBACK_DAYS):
    """
    Downloads OHLCV data and returns weekly, daily, and 4-hour DataFrames.
    """
    tkr = yf.Ticker(ticker)
    
    # Weekly candles using interval 1wk
    df_weekly = tkr.history(period="1y", interval="1wk")
    
    # Daily candles using interval 1d
    df_daily = tkr.history(period="1y", interval="1d")
    
    # Flatten multi-index if yfinance returned them
    for df in [df_weekly, df_daily]:
        if not df.empty and isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
    # 4-hour candles using interval 1h
    df_1h = tkr.history(period="60d", interval="1h")
    
    if not df_1h.empty:
        # Resample to 4H
        # yfinance columns might be MultiIndex if not careful, we will parse them cleanly
        if isinstance(df_1h.columns, pd.MultiIndex):
            df_1h.columns = df_1h.columns.droplevel(1)
            
        df_4h = df_1h.resample('4h').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
    else:
        df_4h = pd.DataFrame()
        
    return df_weekly, df_daily, df_4h

def fetch_all_assets():
    """
    Loops through all assets in config.py, calls fetch_asset_data for each, 
    and returns a dictionary mapping asset names to their dataframes.
    """
    all_data = {}
    for asset in ASSETS:
        name = asset["name"]
        ticker = asset["ticker"]
        
        # We catch potential errors gracefully
        try:
            df_weekly, df_daily, df_4h = fetch_asset_data(ticker, LOOKBACK_DAYS)
            all_data[name] = {
                "weekly": df_weekly,
                "daily": df_daily,
                "4h": df_4h
            }
        except Exception as e:
            print(f"Error fetching data for {name} ({ticker}): {e}")
            
    return all_data

if __name__ == "__main__":
    print("Fetching data for all assets to verify shapes and prices...\n")
    data = fetch_all_assets()
    for name, dfs in data.items():
        if name != "Gold":
            continue
        print(f"Asset: {name}")
        for timeframe, df in dfs.items():
            if not df.empty:
                print(f"  {timeframe.capitalize()} shape: {df.shape}")
            else:
                print(f"  {timeframe.capitalize()} DataFrame is Empty")
                
        if "daily" in dfs and not dfs["daily"].empty:
            last_idx = dfs["daily"].index[-1]
            date_str = last_idx.strftime('%Y-%m-%d') if hasattr(last_idx, 'strftime') else str(last_idx)[:10]
            closing_price = dfs["daily"]["Close"].iloc[-1]
            print(f"  Today's Date: {date_str}")
            print(f"  Current Close Price: {closing_price:.2f}")
            
        print("-" * 30)
