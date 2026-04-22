import os
import json
import warnings
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai

load_dotenv()

def parse_json_response(text):
    """Cleanly parse markdown-wrapped JSON responses from generative models."""
    try:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except json.JSONDecodeError as e:
        return {"error": "JSON parse error", "raw": text, "exception": str(e)}

def score_assets_and_narrative(articles):
    """
    Takes classified and weighted articles, and uses Gemini to produce structured
    sentiment scores, risk metrics, and top narrative extraction for trading context.
    """
    if not articles:
        return {"error": "No articles provided to analyze"}
        
    system_prompt = (
        "You are a senior portfolio analyst at a global macro hedge fund. "
        "Analyze the provided news articles and return only valid JSON with these exact keys: "
        "gold_score (float -1.0 to 1.0 sentiment for Gold), "
        "spx_score (float -1.0 to 1.0 sentiment for S&P 500), "
        "nq_score (float -1.0 to 1.0 sentiment for Nasdaq 100), "
        "dow_score (float -1.0 to 1.0 sentiment for Dow Jones), "
        "btc_score (float -1.0 to 1.0 sentiment for Bitcoin), "
        "eth_score (float -1.0 to 1.0 sentiment for Ethereum), "
        "oil_score (float -1.0 to 1.0 sentiment for Crude Oil), "
        "eurusd_score (float -1.0 to 1.0 sentiment for EUR/USD, positive=bullish EUR), "
        "usdjpy_score (float -1.0 to 1.0 sentiment for USD/JPY, positive=bullish USD), "
        "usdcad_score (float -1.0 to 1.0 sentiment for USD/CAD, positive=bullish USD), "
        "geopolitical_risk (float 0 to 1.0), "
        "earnings_tone (float -1.0 to 1.0 based only on earnings and guidance articles), "
        "dominant_narrative (string, maximum 6 words describing the single dominant market theme today), "
        "narrative_confidence (float 0 to 1.0), "
        "top_3_headlines (list of the 3 most market-moving headlines with one sentence explanation each). "
        "Weight each article by its weight field when forming your view. Be precise and direct."
    )
    
    payload = "Articles for Analysis:\n\n"
    for idx, article in enumerate(articles, 1):
        payload += (
            f"[Article {idx}]\n"
            f"Title: {article.get('title', 'N/A')}\n"
            f"Description: {article.get('description', 'N/A')}\n"
            f"Event Type: {article.get('event_type', 'N/A')}\n"
            f"Weight: {article.get('weight', 0.5)}\n"
            f"Asset Mentions: {', '.join(article.get('asset_mentions', []))}\n\n"
        )
        
    api_key_env = os.getenv("GEMINI_API_KEY", "")
    genai.configure(api_key=api_key_env)
    
    try:
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction=system_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content(payload)
        return parse_json_response(response.text)
        
    except Exception as e:
        return {"error": f"API Call Failed: {str(e)}"}

if __name__ == "__main__":
    # Test dataset passing title, description, event_type, weights, and asset_mentions.
    test_articles_input = [
        {
            "title": "Gold rallies to all-time highs as geopolitical tension spikes", 
            "description": "Investors flee to safety among middle east conflict.",
            "event_type": "GEOPOLITICAL",
            "weight": 0.9,
            "asset_mentions": ["Gold"]
        },
        {
            "title": "Major Tech Company absolutely crushes earnings targets", 
            "description": "Nasdaq surges on incredible AI revenue guidance and forward EPS.",
            "event_type": "EARNINGS_GUIDANCE",
            "weight": 0.8,
            "asset_mentions": ["Nasdaq", "NQ"]
        },
        {
            "title": "S&P 500 trading sideways following mixed jobs report yesterday", 
            "description": "NFP numbers meet expectations precisely.",
            "event_type": "MACRO_DATA_RELEASE",
            "weight": 0.8,
            "asset_mentions": ["S&P500", "SPX"]
        }
    ]
    
    print("Executing asset and narrative scoring...")
    result = score_assets_and_narrative(test_articles_input)
    print("\n[Result JSON]:")
    print(json.dumps(result, indent=2))
