import json
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

def run_bull_bot(data_block):
    """
    Acts as the 'Bull' in the debate, constructing the strongest possible bullish argument
    based on the provided market data block. Returns parsed JSON results.
    """
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
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Generation config to ensure JSON output
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=system_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        response = model.generate_content(
            f"Here is the market data block:\n{data_block}\n\nReturn only valid JSON based on your instructions."
        )
        
        # Clean and parse response text for valid JSON
        text = response.text.strip()
        print(f"\n[BULL BOT RAW RESPONSE]\n{text}\n[END BULL BOT RAW RESPONSE]\n")
        
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
            
        if text.endswith("```"):
            text = text[:-3]
            
        try:
            parsed_response = json.loads(text.strip())
        except json.JSONDecodeError as e:
            print(f"\n[BULL BOT JSON PARSE ERROR]\nError Details: {e}\nFailed string:\n{text.strip()}\n[END ERROR]\n")
            raise
        
        # Enforce that case_direction is always BULL as requested.
        parsed_response["case_direction"] = "BULL"
        return parsed_response
        
    except Exception as e:
        return {
            "case_direction": "BULL",
            "conviction": 0,
            "error": str(e)
        }

def run_bear_bot(data_block):
    """
    Acts as the 'Bear' in the debate, constructing the strongest possible bearish argument
    based on the provided market data block. Returns parsed JSON results.
    """
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
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Generation config to ensure JSON output
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=system_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        response = model.generate_content(
            f"Here is the market data block:\n{data_block}\n\nReturn only valid JSON based on your instructions."
        )
        
        # Clean and parse response text for valid JSON
        text = response.text.strip()
        print(f"\n[BEAR BOT RAW RESPONSE]\n{text}\n[END BEAR BOT RAW RESPONSE]\n")
        
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
            
        if text.endswith("```"):
            text = text[:-3]
            
        try:
            parsed_response = json.loads(text.strip())
        except json.JSONDecodeError as e:
            print(f"\n[BEAR BOT JSON PARSE ERROR]\nError Details: {e}\nFailed string:\n{text.strip()}\n[END ERROR]\n")
            raise
        
        # Enforce that case_direction is always BEAR as requested.
        parsed_response["case_direction"] = "BEAR"
        return parsed_response
        
    except Exception as e:
        return {
            "case_direction": "BEAR",
            "conviction": 0,
            "error": str(e)
        }

if __name__ == "__main__":
    # Test block fetching
    from data_assembler import get_data_block
    
    test_block = get_data_block()
    if test_block:
        print("Running Bull Bot on data block...")
        bull_result = run_bull_bot(test_block)
        print(json.dumps(bull_result, indent=4))
        
        print("\nRunning Bear Bot on data block...")
        bear_result = run_bear_bot(test_block)
        print(json.dumps(bear_result, indent=4))
    else:
        print("No valid data block generated. Please check combined_context.json.")
