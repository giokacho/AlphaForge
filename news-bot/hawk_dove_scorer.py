import os
import json
import warnings
from dotenv import load_dotenv

# Suppress deprecation warnings from legacy genai package outputs
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai

# Load external environments
load_dotenv()

def score_fed_language(articles):
    """
    Filters articles to pick out CENTRAL_BANK items, then invokes Gemini 
    using the dedicated financial analyst persona prompt to rate Hawkish vs Dovish tone.
    """
    # Isolate fed news via the event_type explicitly mapped earlier
    fed_articles = [a for a in articles if a.get('event_type') == 'CENTRAL_BANK']
    
    if not fed_articles:
        return {"hawkishness_score": 0.0, "key_phrase": None}
        
    system_prompt = (
        "You are a Federal Reserve language analyst at a macro hedge fund. "
        "Your only job is to detect hawkish versus dovish language shifts in Fed communications. "
        "Hawkish signals include: higher for longer, further tightening, inflation not defeated, "
        "restrictive policy, rate hike, above target. "
        "Dovish signals include: pivot, cut, pause, easing, inflation cooling, "
        "labor market softening, accommodative. "
        "Score the overall Fed tone as a single float from -1.0 meaning extremely dovish "
        "to +1.0 meaning extremely hawkish. "
        "Also identify the single most important Fed quote or phrase from all articles provided. "
        "Return only valid JSON with keys: hawkishness_score, key_phrase, confidence, reasoning."
    )
    
    payload = "Analyze these Fed-focused articles:\n"
    for idx, a in enumerate(fed_articles, 1):
        payload += f"Article {idx}:\nTitle: {a.get('title')}\nDescription: {a.get('description')}\n\n"
        
    # Get config (API Key). Fallback string added natively so the script cleanly errors
    # with the structured format if the user hasn't set their key yet rather than natively crashing program
    api_key_env = os.getenv("GEMINI_API_KEY", "")
    genai.configure(api_key=api_key_env if api_key_env else "MISSING_KEY")
    
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        response = model.generate_content(payload)
        
        # Output clean up for edge case markdown JSON bounds
        res_text = response.text.replace('```json', '').replace('```', '').strip()
        
        return json.loads(res_text)
        
    except Exception as e:
        # Fallback dictionary schema safety matching the format if an API failure occurs
        return {
            "hawkishness_score": 0.0,
            "key_phrase": None,
            "confidence": 0.0,
            "reasoning": f"Exception occurred during API calling: {str(e)}"
        }

if __name__ == "__main__":
    test_articles = [
        {"title": "Fed Chairman Powell hints at the next policy rate decision", "description": "FOMC sets out strategy to hike again.", "event_type": "CENTRAL_BANK"},
        {"title": "Inflation comes in softer than expected", "description": "Markets wait for more.", "event_type": "MACRO_DATA_RELEASE"},
        {"title": "Federal Reserve explicitly states inflation not defeated", "description": "Higher for longer will be the ongoing mantra.", "event_type": "CENTRAL_BANK"}
    ]
    
    print("Testing score_fed_language with dummy articles... (May fail if GEMINI_API_KEY is not active)")
    score_result = score_fed_language(test_articles)
    print("\n[Result Object]:")
    print(json.dumps(score_result, indent=2))
    
    empty_result = score_fed_language([])
    print("\n[Result Object (Empty List Test)]:")
    print(json.dumps(empty_result, indent=2))
