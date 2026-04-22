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

def score_fed_language(articles):
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

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=_HEADERS,
            json={
                "model": _MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": payload},
                ],
                "response_format": {"type": "json_object"},
            },
            timeout=60,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        return {
            "hawkishness_score": 0.0,
            "key_phrase": None,
            "confidence": 0.0,
            "reasoning": f"API call failed: {str(e)}"
        }


if __name__ == "__main__":
    test_articles = [
        {"title": "Fed Chairman Powell hints at the next policy rate decision", "description": "FOMC sets out strategy to hike again.", "event_type": "CENTRAL_BANK"},
        {"title": "Inflation comes in softer than expected", "description": "Markets wait for more.", "event_type": "MACRO_DATA_RELEASE"},
        {"title": "Federal Reserve explicitly states inflation not defeated", "description": "Higher for longer will be the ongoing mantra.", "event_type": "CENTRAL_BANK"}
    ]
    print(json.dumps(score_fed_language(test_articles), indent=2))
