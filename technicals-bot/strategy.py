import logging
from config import EMA_FAST, EMA_SLOW, ATR_STOP_MULTIPLIER, ATR_TARGET_MULTIPLIER

logger = logging.getLogger(__name__)

class StrategyEngine:
    """
    Evaluates market structure, volume intent, and generates actionable 
    trade signals with dynamic risk management (stop-loss and target placement).
    """
    
    @staticmethod
    def generate_signal(df_daily, df_4h, df_weekly):
        """
        Evaluates multi-timeframe gating to output a combined trade signal.
        """
        # Ensure we have data
        if df_daily is None or df_daily.empty:
            return None
            
        latest_daily = df_daily.iloc[-1]
        
        # 1. Macro Context Gating (Weekly Trend)
        weekly_trend = "BULLISH"
        if df_weekly is not None and not df_weekly.empty:
            weekly_ema_fast = df_weekly[f'EMA_{EMA_FAST}'].iloc[-1]
            weekly_ema_slow = df_weekly[f'EMA_{EMA_SLOW}'].iloc[-1]
            if weekly_ema_fast < weekly_ema_slow:
                weekly_trend = "BEARISH"
                
        # 2. Daily Setup (MACD + ADX Strength)
        is_strong_trend = latest_daily['ADX'] > 25
        macd_bullish = latest_daily['MACD'] > latest_daily['MACD_Signal']
        
        # 3. Execution alignment (4H pullback / trigger)
        # Simplified for template purposes
        
        # Logic: If Weekly Bullish, Daily ADX Strong + MACD Bullish -> LONG
        signal = "NEUTRAL"
        if weekly_trend == "BULLISH" and is_strong_trend and macd_bullish:
            signal = "LONG"
        elif weekly_trend == "BEARISH" and is_strong_trend and not macd_bullish:
            signal = "SHORT"
            
        # Risk Management Math
        current_price = latest_daily['Close']
        current_atr = latest_daily['ATR']
        
        stop_loss = 0.0
        target = 0.0
        
        if signal == "LONG":
            stop_loss = current_price - (current_atr * ATR_STOP_MULTIPLIER)
            target = current_price + (current_atr * ATR_TARGET_MULTIPLIER)
        elif signal == "SHORT":
            stop_loss = current_price + (current_atr * ATR_STOP_MULTIPLIER)
            target = current_price - (current_atr * ATR_TARGET_MULTIPLIER)
            
        risk_management = {
            "entry_price": current_price,
            "stop_loss": stop_loss,
            "take_profit_target": target,
            "atr_at_entry": current_atr,
            "risk_reward_ratio": ATR_TARGET_MULTIPLIER / ATR_STOP_MULTIPLIER
        }

        return {
            "signal": signal,
            "conviction": "HIGH" if is_strong_trend else "LOW",
            "weekly_context": weekly_trend,
            "risk_management": risk_management if signal != "NEUTRAL" else None
        }
