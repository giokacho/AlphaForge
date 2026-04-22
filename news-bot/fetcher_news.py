import requests
from config import NEWSAPI_KEY, FOCUS_ASSETS

def fetch_newsapi():
    try:
        url = "https://newsapi.org/v2/everything"

        q = (
            "(\"S&P 500\" OR \"federal reserve\" OR \"interest rates\" OR "
            "\"gold futures\" OR nasdaq OR bitcoin OR inflation OR recession OR "
            "\"stock market\" OR \"crude oil\" OR forex OR GDP OR earnings OR "
            "\"Treasury yields\" OR \"dollar index\")"
        )

        params = {
            "q": q,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 30,
            "apiKey": NEWSAPI_KEY
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            raise Exception(f"NewsAPI error: {data.get('message', 'unknown')}")

        raw_articles = data.get("articles", [])
        
        results = []
        for article in raw_articles:
            results.append({
                "title": article.get("title"),
                "description": article.get("description"),
                "source_name": article.get("source", {}).get("name") if article.get("source") else None,
                "url": article.get("url"),
                "published_date": article.get("publishedAt"),
                "source_tier": "institutional"
            })
            
        return results

    except Exception as e:
        print(f"Warning: NewsAPI fetch failed: {e}")
        return []

if __name__ == "__main__":
    results = fetch_newsapi()
    print(f"\nFetched {len(results)} articles from NewsAPI.")
    for idx, article in enumerate(results, 1):
        print(f"{idx}. {article['title']}")
