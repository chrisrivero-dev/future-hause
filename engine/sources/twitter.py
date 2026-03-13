"""
Twitter/X Source Connector

Fetches FutureBit official posts from Twitter/X.
Feature-flagged: gracefully fails if credentials are not available.

Required env vars:
- TWITTER_BEARER_TOKEN
- TWITTER_ENABLED (optional, defaults to 'false')

Note: Twitter API v2 requires elevated access for search endpoints.
This connector is designed to work with basic/elevated access levels.
"""

import logging
import os
from typing import Any

from engine.sources.base import BaseConnector

logger = logging.getLogger(__name__)


class TwitterConnector(BaseConnector):
    """Connector for Twitter/X FutureBit posts."""

    source_name = "twitter"

    # Accounts to monitor
    ACCOUNTS = [
        "FutureBitIO",  # Official FutureBit account
    ]

    # Search terms
    SEARCH_TERMS = [
        "futurebit",
        "apollo btc miner",
    ]

    def __init__(self):
        super().__init__()
        self.bearer_token = os.environ.get("TWITTER_BEARER_TOKEN", "")
        self.enabled = os.environ.get("TWITTER_ENABLED", "false").lower() == "true"
        self._client = None

    def is_available(self) -> bool:
        """Check if Twitter connector is enabled and configured."""
        if not self.enabled:
            self.logger.info("Twitter connector disabled (set TWITTER_ENABLED=true to enable)")
            return False

        if not self.bearer_token:
            self.logger.warning("Twitter credentials not configured (TWITTER_BEARER_TOKEN)")
            return False

        return True

    def _get_client(self):
        """Get or create Twitter client."""
        if self._client is not None:
            return self._client

        try:
            import tweepy
        except ImportError:
            self.logger.error("tweepy package not installed. Run: pip install tweepy")
            return None

        try:
            self._client = tweepy.Client(bearer_token=self.bearer_token)
            return self._client
        except Exception as e:
            self.logger.error(f"Failed to create Twitter client: {e}")
            return None

    def fetch(self) -> list[dict]:
        """Fetch tweets from monitored accounts and search for mentions."""
        if not self.is_available():
            self.logger.info("Twitter connector not available, skipping")
            return []

        client = self._get_client()
        if not client:
            return []

        tweets = []
        seen_ids = set()

        try:
            # Fetch from monitored accounts
            for username in self.ACCOUNTS:
                try:
                    # Get user ID first
                    user = client.get_user(username=username)
                    if user.data:
                        user_id = user.data.id
                        # Get recent tweets
                        response = client.get_users_tweets(
                            user_id,
                            max_results=20,
                            tweet_fields=["created_at", "public_metrics", "context_annotations"],
                        )
                        if response.data:
                            for tweet in response.data:
                                if tweet.id not in seen_ids:
                                    seen_ids.add(tweet.id)
                                    tweets.append(self._tweet_to_dict(tweet, username))
                except Exception as e:
                    self.logger.warning(f"Error fetching tweets from @{username}: {e}")
                    continue

            # Search for FutureBit mentions (requires elevated access)
            for term in self.SEARCH_TERMS:
                try:
                    response = client.search_recent_tweets(
                        query=f"{term} -is:retweet",
                        max_results=20,
                        tweet_fields=["created_at", "public_metrics", "author_id"],
                    )
                    if response.data:
                        for tweet in response.data:
                            if tweet.id not in seen_ids:
                                seen_ids.add(tweet.id)
                                tweets.append(self._tweet_to_dict(tweet))
                except Exception as e:
                    self.logger.warning(f"Error searching Twitter for '{term}': {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Twitter fetch error: {e}")

        self.logger.info(f"Fetched {len(tweets)} tweets from Twitter")
        return tweets

    def _tweet_to_dict(self, tweet, username: str = "") -> dict:
        """Convert a tweepy Tweet to a dictionary."""
        metrics = tweet.public_metrics or {}
        return {
            "id": str(tweet.id),
            "text": tweet.text,
            "url": f"https://twitter.com/{username or 'i'}/status/{tweet.id}",
            "author": username or str(getattr(tweet, "author_id", "")),
            "created_at": str(tweet.created_at) if tweet.created_at else "",
            "retweet_count": metrics.get("retweet_count", 0),
            "like_count": metrics.get("like_count", 0),
            "reply_count": metrics.get("reply_count", 0),
        }

    def _normalize_item(self, raw_item: dict) -> dict:
        """Normalize a Twitter post into the canonical intel schema."""
        text = raw_item.get("text", "")
        external_id = raw_item.get("id", "")
        url = raw_item.get("url", "")

        # For Twitter, use first line or first 100 chars as title
        title = text.split("\n")[0][:100]
        if len(title) < len(text.split("\n")[0]):
            title += "..."

        category = self.classify_content(title, text)

        # Generate priority based on engagement
        likes = raw_item.get("like_count", 0)
        retweets = raw_item.get("retweet_count", 0)
        if likes > 100 or retweets > 50:
            priority = "high"
        elif likes > 20 or retweets > 10:
            priority = "medium"
        else:
            priority = "low"

        return {
            "id": self.generate_dedup_key("twitter", external_id),
            "source": "twitter",
            "source_id": external_id,
            "source_url": url,
            "category": category,
            "title": title,
            "content": text,
            "priority": priority,
            "detected_at": self.now_iso(),
            "metadata": {
                "author": raw_item.get("author", ""),
                "like_count": likes,
                "retweet_count": retweets,
                "reply_count": raw_item.get("reply_count", 0),
            },
        }
