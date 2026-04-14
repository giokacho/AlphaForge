import pandas as pd
import numpy as np
import ta
import logging
from config import EMA_FAST, EMA_SLOW, MACD_FAST, MACD_SLOW, MACD_SIGNAL, ADX_PERIOD, ATR_PERIOD

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    @staticmethod
    def calculate_all(df):
        """
        Applies all core technical indicators to the dataframe.
        Expects columns to be MultiIndex from yf or standard ['Open', 'High', 'Low', 'Close', 'Volume']
        """
        if df is None or df.empty:
            return df
            
        # Clean columns if multi-level from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        try:
            # Ensure index is datetime
            
            # Trend: EMAs
            df[f'EMA_{EMA_FAST}'] = ta.trend.ema_indicator(df['Close'], window=EMA_FAST)
            df[f'EMA_{EMA_SLOW}'] = ta.trend.ema_indicator(df['Close'], window=EMA_SLOW)
            
            # Trend: EMA Crossover state
            df['EMA_Crossover'] = np.where(df[f'EMA_{EMA_FAST}'] > df[f'EMA_{EMA_SLOW}'], 1, -1)
            
            # Momentum: MACD
            df['MACD'] = ta.trend.macd(df['Close'], window_slow=MACD_SLOW, window_fast=MACD_FAST)
            df['MACD_Signal'] = ta.trend.macd_signal(df['Close'], window_slow=MACD_SLOW, window_fast=MACD_FAST, window_sign=MACD_SIGNAL)
            df['MACD_Hist'] = ta.trend.macd_diff(df['Close'], window_slow=MACD_SLOW, window_fast=MACD_FAST, window_sign=MACD_SIGNAL)
            
            # Trend Strength: ADX
            adx_indicator = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=ADX_PERIOD)
            df['ADX'] = adx_indicator.adx()
            df['DI_Plus'] = adx_indicator.adx_pos()
            df['DI_Minus'] = adx_indicator.adx_neg()

            # Volatility: ATR
            df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=ATR_PERIOD)
            
            # Regimes: Volatility regime (ATR normalization)
            df['ATR_Pct'] = df['ATR'] / df['Close']
            
            # Clean NaNs efficiently
            return df.fillna(method='bfill')
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df
