import json
import requests
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL

_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
}

def _call_openrouter(system_prompt: str, user_content: str) -> str:
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content},
        ],
        "response_format": {"type": "json_object"},
    }
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=_HEADERS,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def run_bull_bot(data_block):
    system_prompt = (
        "You are the bull case analyst at a global macro hedge fund. "
        "Build the strongest possible case for being long Gold, S&P 500, and Nasdaq 100. "
        "Do not hedge. Do not present the bear case. Use specific numbers from the data. "
        "If data is mostly bearish find exceptions and argue why they signal a turn. "
        "Return only valid JSON with these exact keys: case_direction always BULL, "
        "conviction integer 1 to 10, top_3_bull_signals list of 3 strings each with a "
        "specific data point and number, preferred_assets list of up to 3 from Gold SPX NQ "
        "in preference order, suggested_timeframe SHORT_TERM or MEDIUM_TERM, "
        "key_risk_to_bull_case one sentence, bull_summary maximum 3 sentences."
    )
    try:
        text = _call_openrouter(
            system_prompt,
            f"Here is the market data block:\n{data_block}\n\nReturn only valid JSON based on your instructions."
        )
        parsed = json.loads(text.strip())
        parsed["case_direction"] = "BULL"
        return parsed
    except Exception as e:
        return {"case_direction": "BULL", "conviction": 0, "error": str(e)}


def run_bear_bot(data_block):
    system_prompt = (
        "You are the bear case analyst at a global macro hedge fund. "
        "Build the strongest possible case for being short or risk-off on Gold S&P 500 and Nasdaq 100. "
        "Do not hedge. Do not present the bull case. Use specific numbers from the data. "
        "If data is mostly bullish find warning signs arguing why the rally is fragile or exhausted. "
        "Return only valid JSON with these exact keys: case_direction always BEAR, "
        "conviction integer 1 to 10, top_3_bear_signals list of 3 strings each with specific data point and number, "
        "assets_at_risk list of up to 3 assets, suggested_action one of REDUCE_LONGS or SHORT or CASH or HEDGE, "
        "key_risk_to_bear_case one sentence, bear_summary maximum 3 sentences."
    )
    try:
        text = _call_openrouter(
            system_prompt,
            f"Here is the market data block:\n{data_block}\n\nReturn only valid JSON based on your instructions."
        )
        parsed = json.loads(text.strip())
        parsed["case_direction"] = "BEAR"
        return parsed
    except Exception as e:
        return {"case_direction": "BEAR", "conviction": 0, "error": str(e)}


if __name__ == "__main__":
    from data_assembler import get_data_block
    test_block = get_data_block()
    if test_block:
        print("Running Bull Bot...")
        print(json.dumps(run_bull_bot(test_block), indent=4))
        print("\nRunning Bear Bot...")
        print(json.dumps(run_bear_bot(test_block), indent=4))
    else:
        print("No valid data block. Check combined_context.json.")
