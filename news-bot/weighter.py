import string

def get_5_grams(text):
    """
    Returns a set of 5-grams (5 consecutive words) from the input text.
    Ignores punctuation and case.
    """
    if not text:
        return set()
    
    # Remove punctuation and lowercase
    translator = str.maketrans('', '', string.punctuation)
    clean_text = str(text).translate(translator).lower()
    words = clean_text.split()
    
    # A sequence of 5 words means they 'share more than 4 consecutive words'
    return set(tuple(words[i:i+5]) for i in range(len(words) - 4))

def are_titles_similar(title1, title2):
    """
    Checks if two titles share more than 4 consecutive words.
    For short titles (< 5 words), falls back to exact match (case-insensitive).
    """
    grams1 = get_5_grams(title1)
    grams2 = get_5_grams(title2)
    
    # If either title is too short to have 5-grams, just compare them directly
    if not grams1 or not grams2:
        return str(title1).lower().strip() == str(title2).lower().strip()
        
    return bool(grams1.intersection(grams2))

def apply_source_weights(articles):
    """
    Adds a 'weight' field to each article based on its 'source_tier'.
    Returns the list of articles.
    """
    weights = {
        'central_bank': 1.0,
        'wire_service': 0.9,
        'institutional': 0.8,
        'financial_press': 0.8,
        'fred_release': 0.9
    }
    
    for item in articles:
        tier = item.get('source_tier')
        # Default weight of 0.5 for unspecified tiers
        item['weight'] = weights.get(tier, 0.5)
        
    return articles

def deduplicate_articles(articles):
    """
    Removes duplicate stories comparing titles (sharing > 4 consecutive words).
    Keeps the one with the higher weight.
    Returns the cleaned weighted list sorted by weight descending.
    """
    unique_articles = []
    
    for article in articles:
        is_dup_of = None
        for existing in unique_articles:
            if are_titles_similar(article.get('title', ''), existing.get('title', '')):
                is_dup_of = existing
                break
                
        if is_dup_of:
            # Overwrite if current article has a higher weight
            if article.get('weight', 0.0) > is_dup_of.get('weight', 0.0):
                unique_articles.remove(is_dup_of)
                unique_articles.append(article)
        else:
            unique_articles.append(article)
            
    # Sort descending by weight
    return sorted(unique_articles, key=lambda x: x.get('weight', 0.0), reverse=True)

if __name__ == "__main__":
    # Test data representing combined list of articles from fetchers
    test_articles = [
        {"title": "The Federal Reserve announces a new interest rate hike today", "source_tier": "wire_service"},
        # This one shares "Federal Reserve announces a new interest" with the previous title
        {"title": " Federal Reserve announces a new interest rate hike today", "source_tier": "central_bank"},
        {"title": "Markets rally on the latest tech earnings reports from Silicon Valley", "source_tier": "financial_press"},
        {"title": "Employment situation summary released for this month", "source_tier": "fred_release"},
        # A short title exact match
        {"title": "Gold breaks out", "source_tier": "institutional"},
        {"title": "Gold breaks out", "source_tier": "financial_press"},
        # Unknown source tier
        {"title": "Random blog post about investing tips", "source_tier": "unknown_blog"}
    ]
    
    print(f"Total article count before deduplication: {len(test_articles)}")
    
    # 1. Apply weights
    weighted_articles = apply_source_weights(test_articles)
    
    # 2. Deduplicate and sort
    cleaned_and_sorted_articles = deduplicate_articles(weighted_articles)
    
    print(f"Total article count after deduplication: {len(cleaned_and_sorted_articles)}\n")
    
    print("Final Articles List (Sorted by Weight):")
    for a in cleaned_and_sorted_articles:
        print(f"[Weight: {a.get('weight', 0.0)}] {a.get('title')} (Source Tier: {a.get('source_tier')})")
