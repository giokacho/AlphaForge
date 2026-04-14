import feedparser

def fetch_fed_and_wires():
    feeds = [
        {
            "url": "https://www.federalreserve.gov/feeds/press_all.xml",
            "tier": "central_bank",
            "source": "Federal Reserve"
        },
        {
            "url": "https://feeds.reuters.com/reuters/businessNews",
            "tier": "wire_service",
            "source": "Reuters"
        },
        {
            "url": "https://feeds.reuters.com/reuters/topNews",
            "tier": "wire_service",
            "source": "Reuters"
        }
    ]
    
    all_entries = []
    seen_titles = set()
    
    for feed_info in feeds:
        try:
            parsed = feedparser.parse(feed_info["url"])
            if parsed.get('bozo_exception'):
             print(f"Notice: Issue parsing {feed_info['url']} - {parsed.bozo_exception}")
             
            for entry in parsed.entries[:15]:
                title = entry.get("title", "").strip()
                if not title or title in seen_titles:
                    continue
                    
                seen_titles.add(title)
                
                extracted = {
                    "title": title,
                    "summary": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "published_date": entry.get("published", ""),
                    "source_name": feed_info["source"],
                    "source_tier": feed_info["tier"]
                }
                
                all_entries.append(extracted)
        except Exception as e:
            print(f"Warning: Failed to fetch RSS feed {feed_info['url']}: {e}")
            
    return all_entries

if __name__ == "__main__":
    results = fetch_fed_and_wires()
    print(f"\nFetched {len(results)} articles from Fed and Wires.")
    for idx, article in enumerate(results, 1):
        print(f"{idx}. {article['title']}")
