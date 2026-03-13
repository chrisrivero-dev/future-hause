"""
Future Hause — Live Intel Ingestion

Orchestrates real-time data collection from external sources:
- Reddit RSS: FutureBit subreddit posts via public RSS feeds (no API required)
- Reddit API: FutureBit mentions via PRAW (requires credentials)
- Twitter/X: FutureBit official posts (feature-flagged)
- News: Bitcoin news feeds

All items are normalized into the canonical intel schema and
persisted to cognition_state.json under perception.signals.

After ingestion, triggers the signal extraction pipeline.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from engine.state_manager import load_state, save_state_validated
from engine.sources.reddit import RedditConnector
from engine.sources.reddit_rss import RedditRSSConnector
from engine.sources.twitter import TwitterConnector
from engine.sources.news import NewsConnector

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)


def run_live_ingest() -> dict:
    """
    Run live ingestion from all available sources.

    1. Fetches data from each source connector
    2. Normalizes items into canonical intel schema
    3. Deduplicates against existing signals
    4. Persists new signals to cognition_state.json
    5. Returns ingestion statistics

    Returns:
        dict with counts per source and total signals ingested.
    """
    logger.info("Starting live intel ingestion...")

    # Initialize connectors
    # RedditRSSConnector is preferred as it requires no API credentials
    connectors = [
        RedditRSSConnector(),
        RedditConnector(),
        TwitterConnector(),
        NewsConnector(),
    ]

    # Collect results from each source
    results = {
        "sources": {},
        "total_fetched": 0,
        "total_normalized": 0,
        "total_new": 0,
        "errors": [],
    }

    all_normalized_signals = []

    for connector in connectors:
        source_name = connector.source_name
        source_result = {
            "available": False,
            "fetched": 0,
            "normalized": 0,
            "error": None,
        }

        try:
            # Check if connector is available
            if not connector.is_available():
                source_result["error"] = "Not configured or disabled"
                results["sources"][source_name] = source_result
                continue

            source_result["available"] = True

            # Fetch raw items
            raw_items = connector.fetch()
            source_result["fetched"] = len(raw_items)
            results["total_fetched"] += len(raw_items)

            # Normalize each item
            for raw_item in raw_items:
                try:
                    normalized = connector.normalize(raw_item)
                    all_normalized_signals.append(normalized)
                    source_result["normalized"] += 1
                except Exception as e:
                    logger.warning(f"Failed to normalize item from {source_name}: {e}")
                    continue

            results["total_normalized"] += source_result["normalized"]

        except Exception as e:
            error_msg = f"Source {source_name} failed: {e}"
            logger.error(error_msg)
            source_result["error"] = str(e)
            results["errors"].append(error_msg)

        results["sources"][source_name] = source_result

    # Deduplicate and persist
    new_signals = _deduplicate_and_persist(all_normalized_signals)
    results["total_new"] = len(new_signals)

    logger.info(
        f"Ingestion complete: {results['total_fetched']} fetched, "
        f"{results['total_normalized']} normalized, "
        f"{results['total_new']} new signals persisted"
    )

    return results


def _deduplicate_and_persist(signals: list[dict]) -> list[dict]:
    """
    Deduplicate signals against existing state and persist new ones.

    Deduplication is based on:
    1. Signal ID (hash of source + external_id or URL)
    2. Source + source_id combination

    Returns:
        list of newly persisted signals.
    """
    state = load_state()
    existing_signals = state.get("perception", {}).get("signals", [])

    # Build set of existing dedup keys
    existing_keys = set()
    for sig in existing_signals:
        existing_keys.add(sig.get("id", ""))
        # Also track source + source_id
        source = sig.get("source", "")
        source_id = sig.get("source_id", "")
        if source and source_id:
            existing_keys.add(f"{source}:{source_id}")

    # Filter to new signals only
    new_signals = []
    for sig in signals:
        sig_id = sig.get("id", "")
        source = sig.get("source", "")
        source_id = sig.get("source_id", "")
        source_key = f"{source}:{source_id}" if source and source_id else ""

        if sig_id not in existing_keys and source_key not in existing_keys:
            new_signals.append(sig)
            # Add to existing keys to handle duplicates within batch
            existing_keys.add(sig_id)
            if source_key:
                existing_keys.add(source_key)

    if new_signals:
        # Append to perception.signals
        state["perception"]["signals"].extend(new_signals)

        # Update meta timestamp
        state["meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()

        # Track sources
        sources_seen = set(state.get("perception", {}).get("sources", []))
        for sig in new_signals:
            sources_seen.add(sig.get("source", ""))
        state["perception"]["sources"] = sorted(sources_seen)

        save_state_validated(state)
        logger.info(f"Persisted {len(new_signals)} new signals to cognition_state.json")

    return new_signals


def get_ingestion_status() -> dict:
    """
    Get current ingestion status and source availability.

    Returns:
        dict with source availability and last ingestion stats.
    """
    connectors = [
        RedditRSSConnector(),
        RedditConnector(),
        TwitterConnector(),
        NewsConnector(),
    ]

    status = {
        "sources": {},
        "state_signals_count": 0,
    }

    for connector in connectors:
        status["sources"][connector.source_name] = {
            "available": connector.is_available(),
        }

    # Get current signal count
    try:
        state = load_state()
        status["state_signals_count"] = len(state.get("perception", {}).get("signals", []))
    except Exception:
        status["state_signals_count"] = 0

    return status
