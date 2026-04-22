import requests
from config import ALPHAVANTAGE_KEY

def fetch_alphavantage():
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "topics": "financial_markets,economy_macro,commodity_markets,forex",
            "limit": 25,
            "apikey": ALPHAVANTAGE_KEY
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Alpha Vantage often returns 200 OK along with an error message in JSON
        if "feed" not in data:
            error_msg = data.get("Information") or data.get("Error Message") or "Unknown API response format or rate limit reached."
            raise Exception(error_msg)
            
        articles = data.get("feed", [])
        
        results = []
        for article in articles:
            # Extract ticker specific sentiments for SPY, GLD, QQQ
            ticker_scores = {}
            for ts in article.get("ticker_sentiment", []):
                ticker = ts.get("ticker")
                if ticker in ["SPY", "GLD", "QQQ"]:
                    score = ts.get("ticker_sentiment_score")
                    ticker_scores[f"{ticker}_sentiment_score"] = float(score) if score else None
                    ticker_scores[f"{ticker}_sentiment_label"] = ts.get("ticker_sentiment_label")
                    
            score = article.get("overall_sentiment_score")
            item = {
                "title": article.get("title"),
                "summary": article.get("summary"),
                "source": article.get("source"),
                "url": article.get("url"),
                "time_published": article.get("time_published"),
                "overall_sentiment_label": article.get("overall_sentiment_label"),
                "overall_sentiment_score": float(score) if score else None,
                "source_tier": "financial_press"
            }
            item.update(ticker_scores)
            results.append(item)
            
        return results

    except Exception as e:
        print(f"Warning: Alpha Vantage fetch failed: {e}")
        return []

if __name__ == "__main__":
    results = fetch_alphavantage()
    print(f"\nFetched {len(results)} articles from Alpha Vantage.")
    for idx, article in enumerate(results, 1):
        print(f"{idx}. {article['title']}")
