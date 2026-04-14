import re
from collections import Counter

# Core classification keyword mappings matching prompt exact specifications
EVENT_KEYWORDS = {
    'CENTRAL_BANK': ['fed', 'federal reserve', 'powell', 'fomc', 'rate decision', 'basis points', 'monetary policy'],
    'MACRO_DATA_RELEASE': ['cpi', 'inflation', 'nfp', 'payrolls', 'gdp', 'unemployment', 'pmi', 'retail sales', 'jobs report'],
    'GEOPOLITICAL': ['war', 'sanctions', 'conflict', 'geopolitical', 'tariff', 'trade war', 'china', 'russia'],
    'EARNINGS_GUIDANCE': ['earnings', 'guidance', 'revenue', 'eps', 'beat', 'miss', 'outlook', 'raised guidance', 'lowered guidance'],
    'CREDIT_LIQUIDITY': ['credit', 'spread', 'default', 'liquidity', 'bank stress', 'contagion', 'svb', 'debt ceiling']
}

# Supported assets specified by prompt
ASSETS_TO_TRACK = [
    'Gold', 'SPX', 'S&P500', 'Nasdaq', 'NQ', 'bonds', 'Treasury', 'dollar', 'DXY', 'oil'
]

def _build_event_patterns():
    """Compiles regex patterns with word boundaries around keywords to avoid false positive sub-word matches."""
    patterns = {}
    for event, keywords in EVENT_KEYWORDS.items():
        escaped = [re.escape(k.lower()) for k in keywords]
        pattern_str = r'\b(?:' + '|'.join(escaped) + r')\b'
        patterns[event] = re.compile(pattern_str, re.IGNORECASE)
    return patterns

EVENT_PATTERNS = _build_event_patterns()

def _check_asset_mentions(text):
    """Checks the text for exact occurrences of the tracked assets."""
    mentions = set()
    text_lower = text.lower()
    
    for asset in ASSETS_TO_TRACK:
        asset_lower = asset.lower()
        if asset_lower == 's&p500':
            # Handle special characters and potential spacing edge cases for S&P 500
            if 's&p500' in text_lower or 's&p 500' in text_lower:
                mentions.add(asset)
        else:
            # Match using word boundaries to ensure 'gold' isolated matches, omitting e.g. 'golden'
            if re.search(r'\b' + re.escape(asset_lower) + r'\b', text_lower):
                mentions.add(asset)
                
    return list(mentions)

def classify_articles(articles):
    """
    Takes weighted article list, assigns event_type and asset_mentions.
    Rules cascade sequentially through the pre-defined groupings.
    """
    for article in articles:
        title = article.get('title', '')
        desc = article.get('description', '')
        # Analyze both title and description combined
        combined_text = f"{title} {desc}"
        
        assigned_event = 'GENERAL_COMMENTARY'
        
        # 1. Iteratively match words for specific event types
        for event, pattern in EVENT_PATTERNS.items():
            if pattern.search(combined_text):
                assigned_event = event
                break  # Stops searching after first match block
                
        # 2. Extract ASSET mentions
        mentions = _check_asset_mentions(combined_text)
        article['asset_mentions'] = mentions
        
        # 3. Fallbacks to cover missing classification tiers based on mention presence
        if assigned_event == 'GENERAL_COMMENTARY':
            if mentions:
                assigned_event = 'ASSET_SPECIFIC'
            
        article['event_type'] = assigned_event
        
    return articles

if __name__ == "__main__":
    # Test dataset mapping perfectly directly to user instructions
    test_articles_input = [
        {"title": "Fed Chairman Powell hints at the next policy rate decision", "description": "FOMC sets out strategy."},
        {"title": "Latest CPI and inflation numbers shake markets", "description": "Payrolls surge unexpectedly."},
        {"title": "Russia imposes new sanctions amid global geopolitical friction", "description": "Trade war with China intensifies."},
        {"title": "Company X posted monster earnings, beat EPS and raised guidance", "description": "A big revenue outlook."},
        {"title": "Bank stress rises amidst liquidity crunch following SVB defaults", "description": "Credit spread widens."},
        {"title": "Gold and SPX break out as DXY falls", "description": "Traders rotate out of Nasdaq and Treasury bonds into oil."},
        {"title": "Regulators propose general comment rule update", "description": "An opaque story without specific keywords."}
    ]
    
    print("Running classification engine on test subset...\n")
    classified = classify_articles(test_articles_input)
    
    # Generate breakdown
    event_counts = Counter(a.get('event_type') for a in classified)
    
    print("=== BREAKDOWN BY EVENT_TYPE ===")
    for etype, count in event_counts.items():
        print(f"{etype}: {count}")
    
    print("\n=== CLASSIFIED RESULT PREVIEW ===")
    for article in classified:
        print(f"Title: {article['title']}")
        print(f"Event: {article['event_type']}")
        print(f"Mentions: {article['asset_mentions']}\n")
