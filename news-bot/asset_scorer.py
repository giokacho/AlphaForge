import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

_OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
_MODEL = "google/gemini-2.0-flash-001"
_HEADERS = {
    "Authorization": f"Bearer {_OPENROUTER_KEY}",
    "Content-Type": "application/json",
}

def parse_json_response(text):
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
        "eurusd_score (float -1.0 to 1.0 for EUR/USD, positive=bullish EUR), "
        "usdjpy_score (float -1.0 to 1.0 for USD/JPY, positive=bullish USD), "
        "usdcad_score (float -1.0 to 1.0 for USD/CAD, positive=bullish USD), "
        "geopolitical_risk (float 0 to 1.0), "
        "earnings_tone (float -1.0 to 1.0 based only on earnings/guidance articles), "
        "inflation_score (float -1.0 to 1.0 from CPI/PPI/inflation articles, positive=inflationary), "
        "gdp_score (float -1.0 to 1.0 from GDP/growth/recession articles, positive=strong growth), "
        "employment_score (float -1.0 to 1.0 from jobs/NFP/unemployment articles, positive=strong labor market), "
        "dominant_narrative (string, max 6 words describing the dominant market theme today), "
        "narrative_confidence (float 0 to 1.0), "
        "top_3_headlines (list of 3 strings, each the most market-moving headline with one sentence explanation), "
        "top_headlines (object with keys macro, tech_earnings, commodity_fx — each a list of up to 3 objects "
        "with keys headline string and impact string one sentence). "
        "Weight each article by its weight field. Be precise and direct."
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

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=_HEADERS,
            json={
                "model": _MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": payload},
                ],
                "response_format": {"type": "json_object"},
            },
            timeout=60,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
        return parse_json_response(text)
    except Exception as e:
        return {"error": f"API Call Failed: {str(e)}"}


if __name__ == "__main__":
    test_articles = [
        {
            "title": "Gold rallies to all-time highs as geopolitical tension spikes",
            "description": "Investors flee to safety amid Middle East conflict.",
            "event_type": "GEOPOLITICAL", "weight": 0.9, "asset_mentions": ["Gold"]
        },
        {
            "title": "Major Tech Company crushes earnings targets",
            "description": "Nasdaq surges on AI revenue guidance.",
            "event_type": "EARNINGS_GUIDANCE", "weight": 0.8, "asset_mentions": ["Nasdaq", "NQ"]
        },
    ]
    print(json.dumps(score_assets_and_narrative(test_articles), indent=2))
