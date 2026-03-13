"""
Base connector class for all source connectors.
"""

import hashlib
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Base class for all source connectors."""

    source_name: str = "unknown"

    def __init__(self):
        self.logger = logging.getLogger(f"sources.{self.source_name}")

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the connector has required credentials/config."""
        pass

    @abstractmethod
    def fetch(self) -> list[dict]:
        """Fetch raw items from the source. Returns list of raw items."""
        pass

    def normalize(self, raw_item: dict) -> dict:
        """
        Normalize a raw item into the canonical intel schema.

        Returns a signal dict with:
        - id: Unique signal ID
        - source: Source name
        - source_id: Original ID from the source (for deduplication)
        - source_url: Link to original content
        - category: Classification (support_issue, product_news, firmware_issue, market_news, kb_candidate, discussion)
        - title: Signal title
        - content: Signal content
        - detected_at: ISO timestamp
        - metadata: Additional source-specific data
        """
        return self._normalize_item(raw_item)

    @abstractmethod
    def _normalize_item(self, raw_item: dict) -> dict:
        """Subclass-specific normalization logic."""
        pass

    def generate_dedup_key(self, source: str, external_id: str | None = None, url: str | None = None) -> str:
        """Generate a deduplication key from source + external ID or URL."""
        if external_id:
            key = f"{source}:{external_id}"
        elif url:
            key = f"{source}:{url}"
        else:
            key = f"{source}:{uuid.uuid4()}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def classify_content(self, title: str, content: str) -> str:
        """
        Classify content into categories based on keywords.

        Categories:
        - support_issue: User problems, troubleshooting, bugs
        - product_news: Product announcements, features, releases
        - firmware_issue: Firmware updates, flashing problems
        - market_news: Bitcoin market, mining economics
        - kb_candidate: FAQ patterns, documentation gaps
        - discussion: General discussions
        """
        text = f"{title} {content}".lower()

        # Firmware issues
        firmware_keywords = ["firmware", "update", "flash", "brick", "upgrade", "version"]
        if any(kw in text for kw in firmware_keywords):
            if any(w in text for w in ["issue", "problem", "error", "fail", "stuck", "help"]):
                return "firmware_issue"

        # Support issues
        support_keywords = ["help", "issue", "problem", "error", "not working", "broken", "fix", "troubleshoot"]
        if any(kw in text for kw in support_keywords):
            return "support_issue"

        # Product news
        news_keywords = ["announce", "release", "launch", "new", "introducing", "partnership", "official"]
        if any(kw in text for kw in news_keywords):
            return "product_news"

        # Market/Bitcoin news
        market_keywords = ["bitcoin", "btc", "hashrate", "price", "mining profit", "difficulty", "halving"]
        if any(kw in text for kw in market_keywords):
            return "market_news"

        # KB candidate patterns (questions, how-to)
        kb_patterns = ["how to", "how do", "what is", "where can", "can i", "should i", "best way"]
        if any(p in text for p in kb_patterns):
            return "kb_candidate"

        return "discussion"

    def now_iso(self) -> str:
        """Return current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
