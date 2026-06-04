"""
News Widget - Live RSS News Feed Display
"""

import logging
import webbrowser
import threading
import subprocess
import sys
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QWidget, QScrollArea, QComboBox, QCheckBox,
    QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

try:
    from src.services.rss_fetcher import RSSNewsFetcher, NewsArticle
except ImportError:
    from services.rss_fetcher import RSSNewsFetcher, NewsArticle

try:
    from config.news_sources import RSS_FEEDS, NEWS_SETTINGS, UI_SETTINGS, get_enabled_feeds
except ImportError:
    import config.news_sources as news_config
    RSS_FEEDS = news_config.RSS_FEEDS
    NEWS_SETTINGS = news_config.NEWS_SETTINGS 
    UI_SETTINGS = news_config.UI_SETTINGS
    get_enabled_feeds = news_config.get_enabled_feeds


class NewsItemWidget(QWidget):
    """Lightweight news item widget - optimized for fast creation"""
    
    def __init__(self, article: NewsArticle):
        super().__init__()
        self.article = article
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # HEADLINE - clickable
        headline = self.article.title.strip()
        if len(headline) > 100:
            headline = headline[:100] + "..."
        
        self.headline_label = QLabel(headline)
        self.headline_label.setWordWrap(True)
        self.headline_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        
        if self.article.link:
            self.headline_label.setStyleSheet("""
                QLabel {
                    color: #ffdd00;
                    padding: 2px 0px;
                }
                QLabel:hover {
                    color: #ff8800;
                    text-decoration: underline;
                }
            """)
            self.headline_label.setCursor(Qt.CursorShape.PointingHandCursor)
            self.headline_label.mousePressEvent = lambda e: self.open_article()
        else:
            self.headline_label.setStyleSheet("color: #ffffff; padding: 2px 0px;")
        
        layout.addWidget(self.headline_label)
        
        # DESCRIPTION
        if self.article.summary and self.article.summary.strip():
            description = self.article.summary.strip()
            if len(description) > 120:
                description = description[:120] + "..."
            
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setFont(QFont("Arial", 9))
            desc_label.setStyleSheet("color: #bbbbbb; padding: 2px 0px;")
            layout.addWidget(desc_label)
        
        # META INFO
        time_ago = self._get_time_ago()
        meta_text = f"{self.article.source} • {time_ago}"
        
        meta_label = QLabel(meta_text)
        meta_label.setFont(QFont("Arial", 8))
        meta_label.setStyleSheet("color: #666666; padding: 2px 0px;")
        layout.addWidget(meta_label)
        
        # Widget styling
        self.setStyleSheet("""
            NewsItemWidget {
                background: #0a0a0a;
                border-bottom: 1px solid #333;
            }
            NewsItemWidget:hover {
                background: #1a1a1a;
            }
        """)
    
    def _get_time_ago(self) -> str:
        """Get time ago string"""
        now = datetime.now()
        diff = now - self.article.published
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "Just now"
    
    def open_article(self):
        """Open article URL in browser"""
        if not self.article.link:
            return
            
        # Rate limit clicks
        current_time = datetime.now()
        if hasattr(self, '_last_click_time'):
            if (current_time - self._last_click_time).total_seconds() < 1.0:
                return
        self._last_click_time = current_time
        
        # Show loading briefly
        original_text = self.headline_label.text()
        self.headline_label.setText("🔗 Opening...")
        self.headline_label.setStyleSheet("color: #2196F3;")
        
        # Open link
        def open_link():
            try:
                import subprocess
                import sys
                url = self.article.link
                
                if sys.platform == "win32":
                    subprocess.Popen(['cmd', '/c', 'start', '', url], 
                                   shell=False, creationflags=subprocess.CREATE_NO_WINDOW)
                elif sys.platform == "darwin":
                    subprocess.Popen(['open', url])
                else:
                    subprocess.Popen(['xdg-open', url])
            except Exception:
                import webbrowser
                webbrowser.open(url)
        
        QTimer.singleShot(1, open_link)
        # Use safe restore to avoid calling methods on deleted widgets
        QTimer.singleShot(800, lambda w=self, t=original_text: NewsItemWidget._safe_restore(w, t))
    
    def _restore(self, text):
        """Restore original appearance"""
        try:
            self.headline_label.setText(text)
            self.headline_label.setStyleSheet("""
                QLabel {
                    color: #ffdd00;
                    padding: 2px 0px;
                }
                QLabel:hover {
                    color: #ff8800;
                    text-decoration: underline;
                }
            """)
        except Exception:
            pass

    @staticmethod
    def _safe_restore(widget, text):
        """Call _restore on widget safely, ignoring if widget has been deleted."""
        try:
            if widget is None:
                return
            widget._restore(text)
        except RuntimeError:
            # Widget already deleted in UI thread
            return
        except Exception as e:
            logger.debug("_safe_restore error: %s", e)


class NewsWidget(QGroupBox):
    """Live RSS News feed widget - simplified streaming"""
    
    # Signals
    symbol_searched = pyqtSignal(str)
    news_updated = pyqtSignal(int)
    new_articles_signal = pyqtSignal(list)
    
    def __init__(self):
        super().__init__("LIVE NEWS FEED")
        self.news_items = []
        self.current_filter = ""
        self.selected_category = "all"
        self.current_symbol = ""  # Track current symbol for sync
        self.article_queue = []  # Queue of articles to display
        self.displayed_guids = set()  # Track what's already shown
        self.all_fetched_articles = []  # Store ALL fetched articles (never clear except on app close)
        self._last_cycle_time = 0  # Track last cycle time to throttle logging
        self._waiting_for_articles = False  # Flag to prevent repeated empty checks
        
        # Initialize RSS fetcher
        try:
            import sys
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(project_root, 'config')
            
            if config_path not in sys.path:
                sys.path.append(config_path)
            
            from config import news_sources as news_config
            from src.services.rss_fetcher import RSSNewsFetcher
            
            self.rss_fetcher = RSSNewsFetcher(
                news_config,
                news_config.NEWS_SETTINGS,
                on_new_articles_callback=self.on_new_articles_from_thread
            )
            logger.info("RSS Fetcher initialized")
        except Exception as e:
            logger.warning("Failed to initialize RSS fetcher: %s", e)
            self.rss_fetcher = None
        
        # Single unified timer for displaying articles (1 per second)
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.display_next_article)
        
        # Connect signal
        self.new_articles_signal.connect(self.add_articles_to_queue)
        
        self.init_ui()
        self.start_news_service()
    
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 15, 0, 0)
        main_layout.setSpacing(5)
        
        # Control bar with category filter and search
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(8, 0, 8, 5)
        control_layout.setSpacing(5)
        
        # Category filter
        cat_label = QLabel("Category:")
        cat_label.setStyleSheet("color: #ff8800; font-size: 9pt; font-weight: bold;")
        cat_label.setFixedWidth(55)
        
        self.category_combo = QComboBox()
        self.category_combo.setFixedHeight(26)
        self.category_combo.addItems(["All", "General Finance", "Business News", "Cryptocurrency", "Technology", "Market Analysis"])
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        self.category_combo.setStyleSheet("""
            QComboBox {
                background: #1a1a1a;
                color: #ffaa00;
                border: 1px solid #ff6600;
                padding: 2px 5px;
                border-radius: 3px;
                font-size: 8pt;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #ff6600;
            }
        """)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search news...")
        self.search_input.setFixedHeight(26)
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #1a1a1a;
                color: #ffaa00;
                border: 1px solid #ff6600;
                padding: 4px;
                border-radius: 3px;
                font-size: 8pt;
            }
        """)
        
        # Refresh button
        refresh_btn = QPushButton("↻")
        refresh_btn.clicked.connect(self.force_refresh)
        refresh_btn.setFixedSize(26, 26)
        refresh_btn.setToolTip("Force refresh news")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #ff6600;
                color: #000000;
                font-weight: bold;
                font-size: 12pt;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #ff8800;
            }
        """)
        
        # Auto-refresh indicator
        self.status_label = QLabel("●")
        self.status_label.setStyleSheet("color: #00ff00; font-size: 8pt;")
        self.status_label.setToolTip("Live feed active")
        self.status_label.setFixedWidth(15)
        
        control_layout.addWidget(cat_label)
        control_layout.addWidget(self.category_combo, 1)
        control_layout.addWidget(self.search_input, 2)
        control_layout.addWidget(refresh_btn)
        control_layout.addWidget(self.status_label)
        
        main_layout.addLayout(control_layout)
        
        # Stats bar with progress indicator
        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(8, 2, 8, 2)
        
        self.stats_label = QLabel("Loading news...")
        self.stats_label.setStyleSheet("color: #888; font-size: 8pt;")
        
        # Compact progress bar for fetching
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(6)  # 6 RSS sources
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                border-radius: 3px;
                background: #1a1a1a;
                text-align: center;
                color: #fff;
                font-size: 7pt;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4CAF50, stop:1 #81C784);
                border-radius: 2px;
            }
        """)
        
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(stats_layout)
        
        # News container
        self.news_container = QWidget()
        self.news_container.setStyleSheet("background: #000000;")
        
        self.news_layout = QVBoxLayout(self.news_container)
        self.news_layout.setContentsMargins(0, 0, 0, 0)
        self.news_layout.setSpacing(0)
        self.news_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Scroll area
        self.news_scroll = QScrollArea()
        self.news_scroll.setWidget(self.news_container)
        self.news_scroll.setWidgetResizable(True)
        self.news_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.news_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.news_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #000000;
            }
            QScrollBar:vertical {
                background: #0a0a0a;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #ff6600;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff8800;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        main_layout.addWidget(self.news_scroll)
        
        self.show_loading_state()
    
    def start_news_service(self):
        """Start RSS fetching and display"""
        if not self.rss_fetcher:
            logger.warning("No RSS fetcher available")
            self.update_status("No RSS fetcher", "#ff0000")
            return

        try:
            logger.info("Starting news service")
            self.rss_fetcher.start_auto_fetch()
            logger.info("RSS auto-fetch started")
            self.display_timer.start(1000)
            logger.info("Display timer started (1 article/second)")
            self.update_status("LIVE", "#00ff00")

        except Exception as e:
            logger.error("Error starting news service: %s", e)
            self.update_status(f"Error: {str(e)}", "#ff0000")
    
    def stop_news_service(self):
        """Stop news service"""
        logger.info("Stopping news service")
        
        if self.rss_fetcher:
            self.rss_fetcher.stop_auto_fetch()
        
        if self.display_timer:
            self.display_timer.stop()
        
        self.update_status("Stopped", "#888888")
    
    def on_new_articles_from_thread(self, new_articles):
        """Callback from RSS fetcher thread - emit signal to main thread"""
        try:
            logger.debug("%d new articles from fetcher", len(new_articles))
            self.new_articles_signal.emit(new_articles)
        except Exception as e:
            logger.warning("Thread callback error: %s", e)
    
    def add_articles_to_queue(self, new_articles):
        """Add new articles to display queue (main thread)"""
        try:
            added_to_storage = 0
            added_to_queue = 0
            
            for article in new_articles:
                # Always add to permanent storage (deduplicate by guid)
                if not any(a.guid == article.guid for a in self.all_fetched_articles):
                    self.all_fetched_articles.append(article)
                    added_to_storage += 1
                    
                    # Only add to display queue if matches current filters
                    if self._article_matches_filters(article) and article.guid not in self.displayed_guids:
                        self.article_queue.append(article)
                        added_to_queue += 1
            
            if added_to_storage > 0:
                self._waiting_for_articles = False
                logger.debug("Stored %d articles (total: %d, queue: %d)",
                             added_to_storage, len(self.all_fetched_articles), len(self.article_queue))
                self.update_status(f"{added_to_storage} new", "#4CAF50")
                QTimer.singleShot(2000, lambda: self.update_status("LIVE", "#00ff00"))

        except Exception as e:
            logger.warning("Error adding articles to queue: %s", e)
    
    def display_next_article(self):
        """Display next article from queue (called every second)"""
        try:
            # Check if we have articles to display in queue
            if not self.article_queue:
                # Skip repeated checks if already waiting for articles
                if self._waiting_for_articles:
                    return
                
                # If queue is empty but we have fetched articles, try to refill from storage
                if self.all_fetched_articles:
                    # Get articles that match current filters but haven't been displayed yet
                    for article in self.all_fetched_articles:
                        if article.guid not in self.displayed_guids and self._article_matches_filters(article):
                            self.article_queue.append(article)
                    
                    # If still empty, allow re-displaying articles (cycling) - but only log once per minute
                    if not self.article_queue:
                        current_time = time.time()
                        if current_time - self._last_cycle_time > 60:
                            logger.debug("Cycling through articles (queue exhausted)")
                            self._last_cycle_time = current_time

                        self.displayed_guids.clear()
                        for article in self.all_fetched_articles:
                            if self._article_matches_filters(article):
                                self.article_queue.append(article)

                        if self.article_queue:
                            logger.debug("Refilled queue with %d articles", len(self.article_queue))
                
                # If still no articles, set waiting flag to prevent repeated checks
                if not self.article_queue:
                    self._waiting_for_articles = True
                    return
            
            # Get next article
            article = self.article_queue.pop(0)
            self.displayed_guids.add(article.guid)
            
            # Create and display widget
            news_item = NewsItemWidget(article)
            self.news_layout.insertWidget(0, news_item)
            self.news_items.insert(0, news_item)
            
            # Highlight briefly
            news_item.setStyleSheet("""
                NewsItemWidget {
                    background: #1a3a1a;
                    border-bottom: 1px solid #4CAF50;
                }
            """)
            # Clear styling safely — widget may be deleted before this fires
            QTimer.singleShot(2000, lambda w=news_item: self._safe_clear_style(w))
            
            # Limit displayed items
            if len(self.news_items) > 30:
                old_item = self.news_items.pop()
                self.news_layout.removeWidget(old_item)
                old_item.deleteLater()
            
            # Update stats
            self.update_stats_display()
            
            logger.debug("Displayed: %s...", article.title[:40])

        except Exception as e:
            logger.warning("Display error: %s", e)
    
    def _article_matches_filters(self, article):
        """Check if article matches current filters"""
        # Category filter
        if self.selected_category != "all":
            if not article.category:
                return False
            
            # Flexible matching: check if filter is substring of article category
            # or if article category is substring of filter (case-insensitive)
            filter_lower = self.selected_category.lower()
            category_lower = article.category.lower()
            
            # Match if either contains the other
            if filter_lower not in category_lower and category_lower not in filter_lower:
                return False
        
        # Search filter  
        if self.current_filter:
            if (self.current_filter.lower() not in article.title.lower() and 
                self.current_filter.lower() not in article.summary.lower()):
                return False
        
        return True
    
    def update_stats_display(self):
        """Update stats display"""
        total_fetched = len(self.all_fetched_articles)
        displayed = len(self.news_items)
        queue_size = len(self.article_queue)
        
        # Count matching articles for current filter
        matching = sum(1 for a in self.all_fetched_articles if self._article_matches_filters(a))
        
        if self.selected_category != "all" or self.current_filter:
            self.stats_label.setText(f"Showing {displayed} • {matching} match • {total_fetched} total • Queue: {queue_size}")
        else:
            self.stats_label.setText(f"Showing {displayed} • {total_fetched} total • Queue: {queue_size}")

    def _safe_clear_style(self, widget):
        """Safely clear widget style if widget still exists.

        Some QTimer callbacks may fire after widgets have been deleted (e.g. when
        filters change). Accessing deleted PyQt objects raises RuntimeError. We
        catch and ignore that case.
        """
        try:
            if widget is None:
                return
            # Attempt to clear style; may raise RuntimeError if deleted
            if hasattr(widget, 'setStyleSheet'):
                widget.setStyleSheet("")
        except RuntimeError:
            # Widget was already deleted by the UI thread — ignore
            return
        except Exception as e:
            logger.debug("_safe_clear_style error: %s", e)
    
    def refresh_news(self):
        """Manual refresh - not needed in continuous mode"""
        pass
    
    def force_refresh(self):
        """Force refresh button"""
        if self.rss_fetcher:
            self.update_status("🔄 Refreshing...", "#ff9800")
            # Clear queue and displayed to force re-fetch
            self.article_queue.clear()
            QTimer.singleShot(1000, lambda: self.update_status("🟢 LIVE", "#00ff00"))
    
    def on_category_changed(self, category: str):
        """Handle category filter change - filter from existing articles, don't re-fetch"""
        self.selected_category = category.lower() if category != "All" else "all"
        logger.debug("Category filter: %s", self.selected_category)
        
        # Re-filter from all fetched articles
        self._reapply_filters()
    
    def on_search_changed(self, text: str):
        """Handle search filter change - filter from existing articles, don't re-fetch"""
        self.current_filter = text.strip()
        logger.debug("Search filter: '%s'", self.current_filter)
        
        # Apply with slight delay to avoid re-filtering on every keystroke
        QTimer.singleShot(300, self._reapply_filters)
    
    def _reapply_filters(self):
        """Re-filter and redisplay from all fetched articles - INSTANT display"""
        try:
            logger.debug("Re-filtering %d articles", len(self.all_fetched_articles))
            
            # Reset waiting flag when filters change
            self._waiting_for_articles = False
            
            # Keep timer running in background
            
            # Rebuild queue from all fetched articles that match current filters
            matching_articles = []
            for article in self.all_fetched_articles:
                if self._article_matches_filters(article):
                    matching_articles.append(article)
            
            logger.debug("%d articles match filters", len(matching_articles))
            
            # Update status
            if matching_articles:
                self.update_status(f"{len(matching_articles)} articles", "#4CAF50")
            else:
                self.update_status("No matches", "#ff9800")
            
            # Fast redisplay: clear and immediately show first batch (no delay)
            self.news_container.setUpdatesEnabled(False)
            self.clear_news()
            
            # Reset tracking
            self.displayed_guids.clear()
            self.article_queue = matching_articles.copy()
            
            # Display first 10 articles IMMEDIATELY (no waiting for timer)
            articles_to_show = min(10, len(self.article_queue))
            for _ in range(articles_to_show):
                if self.article_queue:
                    article = self.article_queue.pop(0)
                    self.displayed_guids.add(article.guid)
                    
                    # Create widget
                    news_item = NewsItemWidget(article)
                    self.news_layout.addWidget(news_item)
                    self.news_items.append(news_item)
            
            self.news_container.setUpdatesEnabled(True)
            self.update_stats_display()
            
            logger.debug("Instantly displayed %d articles", articles_to_show)

        except Exception as e:
            logger.warning("Error reapplying filters: %s", e)
    
    def clear_news(self):
        """Clear all news items"""
        for item in self.news_items:
            self.news_layout.removeWidget(item)
            item.deleteLater()
        self.news_items.clear()
        
        # Clear any labels
        for i in reversed(range(self.news_layout.count())):
            item = self.news_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
    
    def update_status(self, message: str, color: str = "#888888"):
        """Update status indicator"""
        self.status_label.setStyleSheet(f"color: {color}; font-size: 8pt;")
        self.status_label.setToolTip(message)
    
    def show_loading_state(self):
        """Show loading message"""
        loading_label = QLabel("🔄 Loading live news feeds...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet("color: #ffaa00; padding: 30px; font-size: 10pt;")
        self.news_layout.addWidget(loading_label)
    
    def get_latest_articles(self, minutes: int = 60) -> list:
        """Get recent articles"""
        return self.rss_fetcher.get_latest_articles(minutes) if self.rss_fetcher else []
    
    def search_articles(self, query: str) -> list:
        """Search articles"""
        return self.rss_fetcher.search_articles(query) if self.rss_fetcher else []
    
    def update_news(self, news_articles: list):
        """Update news from external source (for compatibility with overview_tab)"""
        # This method exists for compatibility but RSS widget manages its own news
        # Just update the symbol if news is related to a specific symbol
        pass
    
    def closeEvent(self, event):
        """Handle widget close"""
        self.stop_news_service()
        event.accept()