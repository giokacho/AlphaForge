import yfinance as yf
import pandas as pd
import logging
from config import TICKERS, TIMEFRAMES

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self, tickers=TICKERS, timeframes=TIMEFRAMES):
        self.tickers = tickers
        self.timeframes = timeframes

    def fetch_data(self, ticker, interval="1d", period="1y"):
        """
        Fetches historical data for a given ticker and interval.
        Using yfinance for multi-timeframe data.
        """
        try:
            logger.info(f"Fetching data for {ticker} at {interval} interval...")
            # Note: yfinance 4h interval only supports max 60 days of data.
            if interval == "4h":
                period = "60d"
                
            data = yf.download(ticker, period=period, interval=interval, progress=False)
            if data.empty:
                logger.warning(f"No data returned for {ticker} at {interval}")
                return None
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None

    def fetch_multi_timeframe(self, ticker):
        """
        Returns a dictionary of dataframes for multiple timeframes.
        """
        market_data = {}
        for tf in self.timeframes:
            # map config timeframes to yf parameters
            # yfinance periods/intervals map: 1d -> 1y length, 1wk -> 2y, 4h -> 60d
            period_map = {"1wk": "2y", "1d": "1y", "4h": "60d"}
            interval_map = {"1wk": "1wk", "1d": "1d", "4h": "1h"} # 4h not supported cleanly without calculation, using 1h or specific interval logic

            actual_interval = tf
            if tf == "4h":
                # sometimes yfinance doesn't like 4h directly depending on version, fallback to 1h
                pass
                
            df = self.fetch_data(ticker, interval=actual_interval, period=period_map.get(tf, "1y"))
            market_data[tf] = df
            
        return market_data

if __name__ == "__main__":
    fetcher = DataFetcher(tickers=["SPY"], timeframes=["1d"])
    data = fetcher.fetch_multi_timeframe("SPY")
    print(data["1d"].tail())
