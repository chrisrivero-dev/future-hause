"""
Future Hause — Source Connectors

Provides live data ingestion from external sources:
- Reddit: FutureBit mentions and relevant subreddit posts
- Twitter/X: FutureBit official posts (feature-flagged)
- News: Bitcoin news feeds

All connectors normalize data into the canonical intel schema.
"""

from engine.sources.reddit import RedditConnector
from engine.sources.twitter import TwitterConnector
from engine.sources.news import NewsConnector

__all__ = ["RedditConnector", "TwitterConnector", "NewsConnector"]
