"""
Reddit RSS Source Connector

Fetches FutureBit mentions and posts from relevant subreddits via RSS feeds.
No Reddit API credentials required - uses public RSS endpoints.

RSS Feeds:
- https://www.reddit.com/r/FutureBit/.rss
- https://www.reddit.com/r/BitcoinMining/.rss
"""

import html
import logging
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

from engine.sources.base import BaseConnector

logger = logging.getLogger(__name__)

# RSS feed URLs to monitor
RSS_FEEDS = [
    "https://www.reddit.com/r/FutureBit/.rss",
    "https://www.reddit.com/r/BitcoinMining/.rss",
]

# Request timeout in seconds
REQUEST_TIMEOUT = 30

# User agent for Reddit RSS requests
USER_AGENT = "FutureHause/0.1 (RSS Reader)"

# Atom namespace
ATOM_NS = "{http://www.w3.org/2005/Atom}"


def strip_html_tags(text: str) -> str:
    """Strip all HTML tags from text content."""
    if not text:
        return ""
    # Decode HTML entities
    text = html.unescape(text)
    # Remove HTML tags
    clean = re.sub(r"<[^>]+>", "", text)
    # Normalize whitespace
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def parse_reddit_timestamp(timestamp_str: str) -> str:
    """
    Parse Reddit RSS timestamp into ISO format.

    Reddit uses format like: 2026-03-08T11:51:45+00:00
    """
    if not timestamp_str:
        return datetime.now(timezone.utc).isoformat()

    try:
        # Handle timezone suffix variations
        timestamp_str = timestamp_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(timestamp_str)
        return dt.isoformat()
    except (ValueError, TypeError):
        return datetime.now(timezone.utc).isoformat()


def extract_subreddit_from_url(url: str) -> str:
    """Extract subreddit name from a Reddit URL."""
    match = re.search(r"/r/([^/]+)", url)
    return match.group(1) if match else ""


def extract_author_from_entry(entry: ET.Element) -> str:
    """Extract author name from RSS entry."""
    # Try atom:author/atom:name
    author_elem = entry.find(f"{ATOM_NS}author")
    if author_elem is not None:
        name_elem = author_elem.find(f"{ATOM_NS}name")
        if name_elem is not None and name_elem.text:
            # Reddit format: /u/username
            author = name_elem.text
            if author.startswith("/u/"):
                return author[3:]
            return author
    return "[unknown]"


def fetch_rss_feed(url: str) -> list[dict]:
    """
    Fetch and parse an RSS/Atom feed.

    Args:
        url: RSS feed URL

    Returns:
        List of raw entry dictionaries
    """
    entries = []

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT}
        )

        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            content = response.read()
            root = ET.fromstring(content)

            # Find all entries (Atom feeds use <entry>)
            for entry in root.findall(f"{ATOM_NS}entry"):
                try:
                    # Extract entry ID
                    id_elem = entry.find(f"{ATOM_NS}id")
                    entry_id = id_elem.text if id_elem is not None else ""

                    # Extract external_id from Reddit ID format (t3_xxxxx)
                    external_id = ""
                    if entry_id:
                        # Reddit IDs look like: t3_1ro2z1y
                        match = re.search(r"(t[0-9]_[a-zA-Z0-9]+)", entry_id)
                        if match:
                            external_id = match.group(1)
                        else:
                            # Fallback to using the full ID
                            external_id = entry_id.split("/")[-1] if "/" in entry_id else entry_id

                    # Extract title
                    title_elem = entry.find(f"{ATOM_NS}title")
                    title = title_elem.text if title_elem is not None else ""

                    # Extract link
                    link_elem = entry.find(f"{ATOM_NS}link")
                    url_href = ""
                    if link_elem is not None:
                        url_href = link_elem.get("href", "")

                    # Extract content (prefer content over summary)
                    content_elem = entry.find(f"{ATOM_NS}content")
                    summary_elem = entry.find(f"{ATOM_NS}summary")

                    raw_content = ""
                    if content_elem is not None and content_elem.text:
                        raw_content = content_elem.text
                    elif summary_elem is not None and summary_elem.text:
                        raw_content = summary_elem.text

                    # Strip HTML from content
                    clean_content = strip_html_tags(raw_content)

                    # Extract published/updated timestamp
                    published_elem = entry.find(f"{ATOM_NS}published")
                    updated_elem = entry.find(f"{ATOM_NS}updated")

                    timestamp_str = ""
                    if published_elem is not None and published_elem.text:
                        timestamp_str = published_elem.text
                    elif updated_elem is not None and updated_elem.text:
                        timestamp_str = updated_elem.text

                    # Extract author
                    author = extract_author_from_entry(entry)

                    # Extract subreddit from URL
                    subreddit = extract_subreddit_from_url(url_href or url)

                    entries.append({
                        "id": external_id,
                        "title": title or "",
                        "url": url_href,
                        "author": author,
                        "published_at": parse_reddit_timestamp(timestamp_str),
                        "content": clean_content,
                        "subreddit": subreddit,
                        "raw_id": entry_id,
                    })

                except Exception as e:
                    logger.warning(f"Failed to parse RSS entry: {e}")
                    continue

    except urllib.error.URLError as e:
        logger.error(f"Failed to fetch RSS feed {url}: {e}")
    except ET.ParseError as e:
        logger.error(f"Failed to parse RSS feed {url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching RSS feed {url}: {e}")

    return entries


class RedditRSSConnector(BaseConnector):
    """Connector for Reddit posts via public RSS feeds."""

    source_name = "reddit_rss"

    # Product announcement keywords for signal detection
    PRODUCT_ANNOUNCEMENT_PATTERNS = [
        r"apollo\s*(iii|3|III)",
        r"is\s+here",
        r"announcement",
        r"launch",
        r"introducing",
        r"now\s+available",
        r"new\s+release",
        r"official",
    ]

    def __init__(self, feeds: list[str] | None = None):
        super().__init__()
        self.feeds = feeds or RSS_FEEDS

    def is_available(self) -> bool:
        """RSS feeds are always available (no credentials required)."""
        return True

    def fetch(self) -> list[dict]:
        """
        Fetch posts from all configured RSS feeds.

        Continues processing if one feed fails.
        """
        all_entries = []
        seen_ids = set()

        for feed_url in self.feeds:
            try:
                self.logger.info(f"Fetching RSS feed: {feed_url}")
                entries = fetch_rss_feed(feed_url)

                for entry in entries:
                    entry_id = entry.get("id", "")
                    if entry_id and entry_id not in seen_ids:
                        seen_ids.add(entry_id)
                        all_entries.append(entry)

                self.logger.info(f"Fetched {len(entries)} entries from {feed_url}")

            except Exception as e:
                self.logger.error(f"Feed {feed_url} failed: {e}")
                # Continue with other feeds
                continue

        self.logger.info(f"Total RSS entries fetched: {len(all_entries)}")
        return all_entries

    def _detect_product_announcement(self, title: str, content: str) -> bool:
        """
        Detect if post is a product announcement.

        Returns True if title or content matches announcement patterns.
        """
        text = f"{title} {content}".lower()

        for pattern in self.PRODUCT_ANNOUNCEMENT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def _normalize_item(self, raw_item: dict) -> dict:
        """
        Normalize a Reddit RSS entry into the canonical intel schema.

        Maps RSS fields as follows:
        - source: "reddit_rss"
        - external_id: entry.id (e.g., t3_1ro2z1y)
        - title: entry.title
        - url: entry.link
        - author: entry.author or parsed username
        - published_at: entry.published or entry.updated
        - content: Stripped HTML from entry.content or entry.summary
        """
        title = raw_item.get("title", "")
        content = raw_item.get("content", "")
        external_id = raw_item.get("id", "")
        url = raw_item.get("url", "")
        subreddit = raw_item.get("subreddit", "")

        # Determine category based on content analysis
        is_announcement = self._detect_product_announcement(title, content)

        if is_announcement:
            category = "announcement"
        else:
            category = self.classify_content(title, content)

        # Generate tags based on subreddit
        tags = []
        if subreddit:
            tags.append(subreddit)

        # Add support tag if it looks like a support request
        if category in ("support_issue", "firmware_issue", "kb_candidate"):
            tags.append("support")

        # Add announcement tag if detected
        if is_announcement:
            tags.append("product_announcement")

        return {
            "id": self.generate_dedup_key("reddit_rss", external_id),
            "source": "reddit_rss",
            "source_id": external_id,
            "external_id": external_id,
            "source_url": url,
            "category": category,
            "title": title,
            "url": url,
            "author": raw_item.get("author", "[unknown]"),
            "published_at": raw_item.get("published_at", self.now_iso()),
            "content": content if content else f"[Post from r/{subreddit}]",
            "detected_at": self.now_iso(),
            "tags": tags,
            "metadata": {
                "subreddit": subreddit,
                "author": raw_item.get("author", ""),
                "raw_id": raw_item.get("raw_id", ""),
            },
        }
