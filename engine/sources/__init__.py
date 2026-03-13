"""
Future Hause — Source Connectors

Provides live data ingestion from external sources:
- Reddit: FutureBit mentions and relevant subreddit posts
- Reddit RSS: FutureBit subreddit posts via public RSS feeds (no API required)
- Twitter/X: FutureBit official posts (feature-flagged)
- News: Bitcoin news feeds

All connectors normalize data into the canonical intel schema.
"""

from engine.sources.reddit import RedditConnector
from engine.sources.reddit_rss import RedditRSSConnector
from engine.sources.twitter import TwitterConnector
from engine.sources.news import NewsConnector

__all__ = ["RedditConnector", "RedditRSSConnector", "TwitterConnector", "NewsConnector"]
