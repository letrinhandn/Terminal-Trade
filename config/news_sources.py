"""
RSS News Sources Configuration
Configure news feeds for the Terminal Trade news widget
"""

# Premium Financial News RSS Feeds - High-Quality Active Sources (Nov 2025)
RSS_FEEDS = {
    "crypto_sources": [
        {
            "name": "CoinDesk",
            "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "category": "Cryptocurrency",
            "enabled": True
        },
        {
            "name": "CoinTelegraph",
            "url": "https://cointelegraph.com/rss",
            "category": "Cryptocurrency",
            "enabled": True
        },
        {
            "name": "Decrypt",
            "url": "https://decrypt.co/feed",
            "category": "Cryptocurrency",
            "enabled": True
        }
    ],
    
    "finance_sources": [
        {
            "name": "Reuters Business",
            "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
            "category": "Business News",
            "enabled": True
        },
        {
            "name": "MarketWatch",
            "url": "https://feeds.marketwatch.com/marketwatch/topstories/",
            "category": "Market Analysis",
            "enabled": True
        },
        {
            "name": "Financial Times",
            "url": "https://www.ft.com/?format=rss",
            "category": "Business News",
            "enabled": True
        }
    ],
    
    "tech_sources": [
        {
            "name": "TechCrunch",
            "url": "https://techcrunch.com/feed/",
            "category": "Technology",
            "enabled": True
        },
        {
            "name": "Hacker News",
            "url": "https://hnrss.org/frontpage",
            "category": "Technology",
            "enabled": True
        }
    ],
    
    "general_sources": [
        {
            "name": "BBC Business",
            "url": "http://feeds.bbci.co.uk/news/business/rss.xml",
            "category": "General Finance",
            "enabled": True
        }
    ]
}

# Optimized Settings - Fast and Responsive (Nov 2025)
NEWS_SETTINGS = {
    "refresh_interval_seconds": 30,   # Balanced refresh rate (30 seconds)
    "max_articles_per_feed": 5,       # 5 articles per feed for better content
    "max_total_articles": 50,         # Moderate total for good performance
    "connect_timeout": 5,             # Reasonable timeout
    "read_timeout": 10,               # Sufficient read timeout 
    "article_display_interval": 1,    # Display articles every 1 second
    "show_new_articles_animation": False,  # Disable animations for performance
    "sort_by_published_time": True,   # Sort by newest first
    "filter_old_articles": False,     # Accept all articles
    "latest_only": True,              # Get latest from each feed
    "no_time_filter": True,           # No time filtering
    "batch_size": 2,                  # Process 2 feeds at a time for efficiency
}

# UI Settings
UI_SETTINGS = {
    "show_source_icons": True,      # Show RSS source icons
    "group_by_category": True,      # Group news by category
    "show_timestamps": True,        # Show article timestamps
    "auto_scroll": True,           # Auto-scroll to new articles
    "max_title_length": 120,       # Truncate long titles
    "show_preview": True,          # Show article preview on hover
}

def get_enabled_feeds():
    """Get all enabled RSS feeds as a flat list"""
    enabled_feeds = []
    for category, feeds in RSS_FEEDS.items():
        for feed in feeds:
            if feed.get("enabled", True):
                feed["category_key"] = category
                enabled_feeds.append(feed)
    return enabled_feeds

def get_feeds_by_category(category_key):
    """Get feeds for a specific category"""
    return [feed for feed in RSS_FEEDS.get(category_key, []) if feed.get("enabled", True)]

def add_custom_feed(name, url, category="Custom", enabled=True):
    """Add a custom RSS feed"""
    if "custom" not in RSS_FEEDS:
        RSS_FEEDS["custom"] = []
    
    RSS_FEEDS["custom"].append({
        "name": name,
        "url": url,
        "category": category,
        "enabled": enabled
    })

def disable_feed(feed_name):
    """Disable a specific feed by name"""
    for category, feeds in RSS_FEEDS.items():
        for feed in feeds:
            if feed["name"] == feed_name:
                feed["enabled"] = False
                return True
    return False

def enable_feed(feed_name):
    """Enable a specific feed by name"""
    for category, feeds in RSS_FEEDS.items():
        for feed in feeds:
            if feed["name"] == feed_name:
                feed["enabled"] = True
                return True
    return False