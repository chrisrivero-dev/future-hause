"""
Bitcoin News Source Connector

Fetches Bitcoin and cryptocurrency news from public RSS feeds.
No API keys required - uses public RSS feeds.

Monitored sources:
- Bitcoin Magazine
- CoinDesk
- Decrypt
- The Block
"""

import logging
import os
import hashlib
from datetime import datetime, timezone
from typing import Any
from xml.etree import ElementTree

from engine.sources.base import BaseConnector

logger = logging.getLogger(__name__)


class NewsConnector(BaseConnector):
    """Connector for Bitcoin/crypto news feeds."""

    source_name = "news"

    # RSS feeds to monitor
    RSS_FEEDS = [
        {
            "name": "Bitcoin Magazine",
            "url": "https://bitcoinmagazine.com/feed",
            "category": "bitcoin",
        },
        {
            "name": "CoinDesk",
            "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "category": "crypto",
        },
        {
            "name": "Decrypt",
            "url": "https://decrypt.co/feed",
            "category": "crypto",
        },
    ]

    # Keywords to filter relevant articles
    RELEVANCE_KEYWORDS = [
        "bitcoin", "btc", "mining", "miner", "hashrate",
        "difficulty", "halving", "asic", "home mining",
        "futurebit", "apollo",
    ]

    def __init__(self):
        super().__init__()
        self.timeout = int(os.environ.get("NEWS_FETCH_TIMEOUT", "10"))

    def is_available(self) -> bool:
        """News connector is always available (uses public RSS feeds)."""
        return True

    def fetch(self) -> list[dict]:
        """Fetch articles from RSS feeds."""
        try:
            import requests
        except ImportError:
            self.logger.error("requests package not installed. Run: pip install requests")
            return []

        articles = []
        seen_urls = set()

        for feed_config in self.RSS_FEEDS:
            feed_name = feed_config["name"]
            feed_url = feed_config["url"]
            feed_category = feed_config["category"]

            try:
                self.logger.debug(f"Fetching RSS feed: {feed_name}")
                response = requests.get(feed_url, timeout=self.timeout)
                response.raise_for_status()

                # Parse RSS XML
                root = ElementTree.fromstring(response.content)

                # Handle both RSS 2.0 and Atom feeds
                items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

                for item in items[:20]:  # Limit to 20 items per feed
                    article = self._parse_rss_item(item, feed_name, feed_category)
                    if article and article.get("url") not in seen_urls:
                        # Filter for relevance
                        if self._is_relevant(article):
                            seen_urls.add(article["url"])
                            articles.append(article)

            except requests.RequestException as e:
                self.logger.warning(f"Error fetching feed '{feed_name}': {e}")
                continue
            except ElementTree.ParseError as e:
                self.logger.warning(f"Error parsing feed '{feed_name}': {e}")
                continue
            except Exception as e:
                self.logger.warning(f"Unexpected error with feed '{feed_name}': {e}")
                continue

        self.logger.info(f"Fetched {len(articles)} relevant news articles")
        return articles

    def _parse_rss_item(self, item, feed_name: str, feed_category: str) -> dict | None:
        """Parse an RSS item element into a dictionary."""
        try:
            # Try RSS 2.0 format first
            title = self._get_text(item, "title")
            link = self._get_text(item, "link")
            description = self._get_text(item, "description")
            pub_date = self._get_text(item, "pubDate")

            # Fall back to Atom format
            if not title:
                title = self._get_text(item, "{http://www.w3.org/2005/Atom}title")
            if not link:
                link_elem = item.find("{http://www.w3.org/2005/Atom}link")
                if link_elem is not None:
                    link = link_elem.get("href", "")
            if not description:
                description = self._get_text(item, "{http://www.w3.org/2005/Atom}summary")
            if not pub_date:
                pub_date = self._get_text(item, "{http://www.w3.org/2005/Atom}published")

            if not title or not link:
                return None

            return {
                "title": title,
                "url": link,
                "description": description or "",
                "pub_date": pub_date or "",
                "feed_name": feed_name,
                "feed_category": feed_category,
            }
        except Exception as e:
            self.logger.debug(f"Error parsing RSS item: {e}")
            return None

    def _get_text(self, element, tag: str) -> str:
        """Safely get text content from an XML element."""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return ""

    def _is_relevant(self, article: dict) -> bool:
        """Check if an article is relevant to FutureBit/Bitcoin mining."""
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()
        return any(kw in text for kw in self.RELEVANCE_KEYWORDS)

    def _normalize_item(self, raw_item: dict) -> dict:
        """Normalize a news article into the canonical intel schema."""
        title = raw_item.get("title", "")
        description = raw_item.get("description", "")
        url = raw_item.get("url", "")

        # Generate external ID from URL hash
        external_id = hashlib.sha256(url.encode()).hexdigest()[:16]

        category = self.classify_content(title, description)

        # News articles default to medium priority
        priority = "medium"

        # Check for high-priority keywords
        text = f"{title} {description}".lower()
        high_priority_keywords = ["breaking", "urgent", "futurebit", "apollo"]
        if any(kw in text for kw in high_priority_keywords):
            priority = "high"

        return {
            "id": self.generate_dedup_key("news", external_id, url),
            "source": "news",
            "source_id": external_id,
            "source_url": url,
            "category": category,
            "title": title,
            "content": description,
            "priority": priority,
            "detected_at": self.now_iso(),
            "metadata": {
                "feed_name": raw_item.get("feed_name", ""),
                "feed_category": raw_item.get("feed_category", ""),
                "pub_date": raw_item.get("pub_date", ""),
            },
        }
