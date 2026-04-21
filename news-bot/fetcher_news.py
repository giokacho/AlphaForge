import requests
from datetime import datetime, timedelta
from config import NEWSAPI_KEY, FOCUS_ASSETS

def fetch_newsapi():
    try:
        url = "https://newsapi.org/v2/everything"
        
        # Build query for matching any of the focus assets
        query_terms = []
        for asset in FOCUS_ASSETS:
            if " " in asset:
                query_terms.append(f'"{asset}"')
            else:
                query_terms.append(asset)
        q = "(" + " OR ".join(query_terms) + ")"
        
        # Time constraints - last 24 hours
        from_date = (datetime.now() - timedelta(days=1)).isoformat()
        
        # Allowed domain filter
        domains = (
            "reuters.com,wsj.com,ft.com,bloomberg.com,cnbc.com,"
            "marketwatch.com,apnews.com,foxbusiness.com,thestreet.com"
        )
        
        params = {
            "q": q,
            "domains": domains,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": 30,
            "from": from_date,
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
