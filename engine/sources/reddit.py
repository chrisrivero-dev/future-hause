"""
Reddit Source Connector

Fetches FutureBit mentions and posts from relevant subreddits.
Uses Reddit API via PRAW (Python Reddit API Wrapper).

Required env vars:
- REDDIT_CLIENT_ID
- REDDIT_CLIENT_SECRET
- REDDIT_USER_AGENT (optional, defaults to 'FutureHause/0.1')
"""

import logging
import os
from typing import Any

from engine.sources.base import BaseConnector

logger = logging.getLogger(__name__)


class RedditConnector(BaseConnector):
    """Connector for Reddit FutureBit mentions and subreddit posts."""

    source_name = "reddit"

    # Subreddits to monitor
    SUBREDDITS = [
        "FutureBit",
        "BitcoinMining",
        "CryptoCurrency",
    ]

    # Search terms for FutureBit mentions
    SEARCH_TERMS = [
        "futurebit",
        "apollo btc",
        "apollo miner",
    ]

    def __init__(self):
        super().__init__()
        self.client_id = os.environ.get("REDDIT_CLIENT_ID", "")
        self.client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
        self.user_agent = os.environ.get("REDDIT_USER_AGENT", "FutureHause/0.1")
        self._reddit = None

    def is_available(self) -> bool:
        """Check if Reddit credentials are configured."""
        if not self.client_id or not self.client_secret:
            self.logger.warning("Reddit credentials not configured (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)")
            return False
        return True

    def _get_client(self):
        """Get or create Reddit client."""
        if self._reddit is not None:
            return self._reddit

        try:
            import praw
        except ImportError:
            self.logger.error("praw package not installed. Run: pip install praw")
            return None

        try:
            self._reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
            )
            # Test connection
            self._reddit.read_only = True
            return self._reddit
        except Exception as e:
            self.logger.error(f"Failed to create Reddit client: {e}")
            return None

    def fetch(self) -> list[dict]:
        """Fetch posts from monitored subreddits and search for mentions."""
        if not self.is_available():
            self.logger.info("Reddit connector not available, skipping")
            return []

        reddit = self._get_client()
        if not reddit:
            return []

        posts = []
        seen_ids = set()

        try:
            # Fetch from monitored subreddits
            for subreddit_name in self.SUBREDDITS:
                try:
                    subreddit = reddit.subreddit(subreddit_name)
                    for post in subreddit.new(limit=25):
                        if post.id not in seen_ids:
                            seen_ids.add(post.id)
                            posts.append(self._submission_to_dict(post))
                except Exception as e:
                    self.logger.warning(f"Error fetching from r/{subreddit_name}: {e}")
                    continue

            # Search for FutureBit mentions across Reddit
            for term in self.SEARCH_TERMS:
                try:
                    for post in reddit.subreddit("all").search(term, sort="new", limit=10):
                        if post.id not in seen_ids:
                            seen_ids.add(post.id)
                            posts.append(self._submission_to_dict(post))
                except Exception as e:
                    self.logger.warning(f"Error searching for '{term}': {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Reddit fetch error: {e}")

        self.logger.info(f"Fetched {len(posts)} posts from Reddit")
        return posts

    def _submission_to_dict(self, submission) -> dict:
        """Convert a PRAW submission to a dictionary."""
        return {
            "id": submission.id,
            "title": submission.title,
            "selftext": submission.selftext or "",
            "url": f"https://reddit.com{submission.permalink}",
            "subreddit": str(submission.subreddit),
            "author": str(submission.author) if submission.author else "[deleted]",
            "score": submission.score,
            "num_comments": submission.num_comments,
            "created_utc": submission.created_utc,
            "link_flair_text": submission.link_flair_text,
        }

    def _normalize_item(self, raw_item: dict) -> dict:
        """Normalize a Reddit post into the canonical intel schema."""
        title = raw_item.get("title", "")
        content = raw_item.get("selftext", "")
        external_id = raw_item.get("id", "")
        url = raw_item.get("url", "")

        category = self.classify_content(title, content)

        # Generate priority based on engagement
        score = raw_item.get("score", 0)
        comments = raw_item.get("num_comments", 0)
        if score > 50 or comments > 20:
            priority = "high"
        elif score > 10 or comments > 5:
            priority = "medium"
        else:
            priority = "low"

        return {
            "id": self.generate_dedup_key("reddit", external_id),
            "source": "reddit",
            "source_id": external_id,
            "source_url": url,
            "category": category,
            "title": title,
            "content": content if content else f"[Link post from r/{raw_item.get('subreddit', 'unknown')}]",
            "priority": priority,
            "detected_at": self.now_iso(),
            "metadata": {
                "subreddit": raw_item.get("subreddit", ""),
                "author": raw_item.get("author", ""),
                "score": score,
                "num_comments": comments,
                "flair": raw_item.get("link_flair_text", ""),
            },
        }
