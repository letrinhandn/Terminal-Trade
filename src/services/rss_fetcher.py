"""
RSS News Fetcher Service - Simplified for smooth continuous fetching
"""

import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import time
from dataclasses import dataclass
import logging

@dataclass
class NewsArticle:
    """News article data structure"""
    title: str
    summary: str
    link: str
    published: datetime
    source: str
    category: str
    guid: str = ""
    
    def __post_init__(self):
        # Generate GUID if not provided
        if not self.guid:
            self.guid = f"{self.source}_{hash(self.title + self.link)}"

class RSSNewsFetcher:
    """Ultra-simple RSS fetcher - continuous smooth fetching"""
    
    def __init__(self, feeds_config, settings_config, on_new_articles_callback=None):
        self.feeds_config = feeds_config
        self.settings = settings_config
        self.articles = []
        self.is_running = False
        self.fetch_thread = None
        self.lock = threading.Lock()
        self.on_new_articles_callback = on_new_articles_callback
        self.feed_index = 0  # Current feed being fetched
        self.feed_last_fetch = {}  # Track last fetch time per feed
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start_auto_fetch(self):
        """Start continuous RSS fetching"""
        if self.is_running:
            return
        
        self.is_running = True
        self.fetch_thread = threading.Thread(target=self._continuous_fetch_loop, daemon=True)
        self.fetch_thread.start()
        self.logger.info("✅ RSS continuous fetch started")
    
    def stop_auto_fetch(self):
        """Stop RSS fetching"""
        self.is_running = False
        if self.fetch_thread and self.fetch_thread.is_alive():
            self.fetch_thread.join(timeout=1)
        self.logger.info("❌ RSS fetch stopped")
    
    def _continuous_fetch_loop(self):
        """Robust diverse fetch - parallel initial load then fast rotation"""
        enabled_feeds = self.feeds_config.get_enabled_feeds()
        
        if not enabled_feeds:
            self.logger.error("No enabled feeds!")
            return
        
        # PHASE 1: Initial parallel fetch from ALL feeds for diversity
        self.logger.info(f"🚀 Initial parallel fetch from {len(enabled_feeds)} feeds...")
        self._parallel_fetch_all_feeds(enabled_feeds)
        
        # PHASE 2: Continuous rotation with fast cycle
        while self.is_running:
            try:
                # Get current feed (rotate through all feeds)
                feed = enabled_feeds[self.feed_index % len(enabled_feeds)]
                
                # Fetch single feed
                articles = self._fetch_single_feed(feed)
                
                if articles:
                    # Add new articles
                    newly_added = []
                    with self.lock:
                        for article in articles:
                            if not any(ex.guid == article.guid for ex in self.articles):
                                self.articles.append(article)
                                newly_added.append(article)
                        
                        # Sort and limit
                        self.articles.sort(key=lambda x: x.published, reverse=True)
                        self.articles = self.articles[:100]
                    
                    # Notify UI immediately
                    if newly_added and self.on_new_articles_callback:
                        try:
                            self.on_new_articles_callback(newly_added)
                            self.logger.info(f"✅ {len(newly_added)} new from {feed['name']}")
                        except Exception as e:
                            self.logger.error(f"Callback error: {e}")
                
                # Move to next feed
                self.feed_index += 1
                
                # Sleep 3 seconds (faster than before for more diversity)
                time.sleep(3)
                
            except Exception as e:
                self.logger.error(f"Fetch error: {e}")
                time.sleep(3)
    
    def _parallel_fetch_all_feeds(self, feeds):
        """Fetch all feeds in parallel for initial diversity"""
        import concurrent.futures
        
        def fetch_feed_wrapper(feed):
            try:
                return self._fetch_single_feed(feed)
            except Exception as e:
                self.logger.error(f"Parallel fetch {feed['name']} failed: {e}")
                return []
        
        # Use ThreadPoolExecutor for parallel fetching (more workers for faster load)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_feed = {executor.submit(fetch_feed_wrapper, feed): feed for feed in feeds}
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_feed, timeout=20):
                feed = future_to_feed[future]
                try:
                    articles = future.result()
                    completed += 1
                    
                    if articles:
                        # Add new articles
                        newly_added = []
                        with self.lock:
                            for article in articles:
                                if not any(ex.guid == article.guid for ex in self.articles):
                                    self.articles.append(article)
                                    newly_added.append(article)
                            
                            # Sort and limit
                            self.articles.sort(key=lambda x: x.published, reverse=True)
                            self.articles = self.articles[:100]
                        
                        # Notify UI immediately
                        if newly_added and self.on_new_articles_callback:
                            try:
                                self.on_new_articles_callback(newly_added)
                                self.logger.info(f"✅ {len(newly_added)} new from {feed['name']} (parallel {completed}/{len(feeds)})")
                            except Exception as e:
                                self.logger.error(f"Callback error: {e}")
                    else:
                        self.logger.warning(f"⚠️ No articles from {feed['name']}")
                        
                except concurrent.futures.TimeoutError:
                    self.logger.error(f"⏱️ Timeout fetching {feed['name']}")
                except Exception as e:
                    self.logger.error(f"❌ Parallel fetch result error for {feed['name']}: {e}")
        
        self.logger.info(f"🎉 Initial parallel fetch completed - {len(self.articles)} articles loaded from {completed}/{len(feeds)} feeds")
    
    def fetch_all_feeds(self) -> List[NewsArticle]:
        """Get all current articles"""
        with self.lock:
            return self.articles.copy()
    
    def _fetch_single_feed(self, feed_config: Dict) -> List[NewsArticle]:
        """Simple RSS feed fetch - returns top 5 articles for more diversity"""
        url = feed_config["url"]
        source_name = feed_config["name"]
        category = feed_config["category"]
        
        try:
            # Parse feed with timeout
            feed = feedparser.parse(url)
            
            if not feed.entries:
                return []
            
            articles = []
            
            # Get top 5 articles for more diversity (was 3)
            for entry in feed.entries[:5]:
                try:
                    # Parse date
                    published = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            published = datetime(*entry.published_parsed[:6])
                        except:
                            pass
                    
                    # Extract content
                    title = entry.get('title', 'No Title')[:150]
                    summary = entry.get('summary', entry.get('description', ''))[:250]
                    link = entry.get('link', '')
                    
                    # Clean HTML
                    import re
                    summary = re.sub('<[^<]+?>', '', summary)
                    
                    # Create article
                    article = NewsArticle(
                        title=title,
                        summary=summary,
                        link=link,
                        published=published,
                        source=source_name,
                        category=category,
                        guid=entry.get('id', entry.get('guid', link))
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    continue
            
            return articles
        
        except Exception as e:
            self.logger.error(f"Fetch {source_name} failed: {e}")
            return []
    
    def get_articles(self, category: Optional[str] = None, limit: Optional[int] = None) -> List[NewsArticle]:
        """Get articles, optionally filtered"""
        with self.lock:
            articles = self.articles.copy()
        
        if category and category != "all":
            articles = [a for a in articles if category.lower() in a.category.lower()]
        
        if limit:
            articles = articles[:limit]
        
        return articles
    
    def get_latest_articles(self, minutes: int = 60) -> List[NewsArticle]:
        """Get recent articles"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        with self.lock:
            return [a for a in self.articles if a.published > cutoff]
    
    def search_articles(self, query: str) -> List[NewsArticle]:
        """Search articles"""
        query = query.lower()
        with self.lock:
            return [a for a in self.articles 
                   if query in a.title.lower() or query in a.summary.lower()]
    
    def get_sources(self) -> List[str]:
        """Get all sources"""
        with self.lock:
            return list(set(a.source for a in self.articles))
    
    def get_categories(self) -> List[str]:
        """Get all categories"""
        with self.lock:
            return list(set(a.category for a in self.articles))
    
    def force_refresh(self):
        """Force refresh - does nothing in continuous mode"""
        pass