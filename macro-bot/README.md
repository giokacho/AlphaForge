# Macro-Bot

Macro-Bot is an automated, AI-driven quantitative macro hedge fund analytics tool. It fetches live data for critical financial indicators, standardizes their scores to determine the overall market regime (RISK ON / RISK OFF / TRANSITION), and generates sharp, hedge-fund style daily briefings using Google's Gemini LLM.

## Files Structure

- **`config.py`**: Configuration file storing your API keys (`FRED_API_KEY`, `GEMINI_API_KEY`) and the master scoring thresholds (`THRESHOLDS`).
- **`data_fetcher.py`**: Interacts with Yahoo Finance (`yfinance`) and FRED (`fredapi`) to pull real-time data for indicators (VIX, DXY, US10Y, HY Spreads, Net Liquidity metrics, etc.). 
- **`scorer.py`**: Analyzes the raw data pulled by the fetcher against your defined thresholds, converting them into a binary Bullish/Bearish mathematical matrix to establish a total market regime verdict.
- **`report.py`**: Organizes the mathematical findings and prompts the Gemini LLM to synthesize an actionable daily macro analyst brief. Automatically handles fallbacks and writes the final Markdown document to the `reports/` directory.
- **`run.py`**: The master on-demand entry point. Running this executes the entire pipeline sequentially and outputs the final result to the terminal.
- **`scheduler.py`**: The automated daemon script. Runs continuously in the background and triggers the entire pipeline autonomously every weekday at 09:30 AM.
- **`requirements.txt`**: Standard Python required libraries.

## How to use

Ensure all libraries are installed:
```bash
pip install -r requirements.txt
```
*Note: Ensure to provide your valid keys under `FRED_API_KEY` and `GEMINI_API_KEY` inside `config.py`!*

### Run On-Demand
Whenever you want to pull a fresh report instantly, simply execute:
```bash
python run.py
```

### Run the Daily Scheduler
To set the bot to automatically generate these reports continuously at 09:30 AM (Monday through Friday), launch the scheduler:
```bash
python scheduler.py
```
