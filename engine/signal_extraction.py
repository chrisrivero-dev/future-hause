"""
Signal Extraction for Future Hause

Orchestrates live data ingestion and signal extraction pipeline.
Writes signals into cognition_state.json via state_manager.

Pipeline:
1. Run live ingestion from external sources (Reddit, Twitter, News)
2. Extract and normalize signals
3. Persist to cognition_state.json
"""

import logging
from datetime import datetime, timezone

from engine.state_manager import load_state, save_state_validated
from engine.ingest import run_live_ingest

logger = logging.getLogger(__name__)


def run_signal_extraction() -> dict:
    """
    Run the full signal extraction pipeline.

    1. Runs live ingestion from all available sources
    2. Signals are normalized and deduplicated during ingestion
    3. Returns extraction statistics

    Returns:
        dict with signals_created count and ingestion details.
    """
    logger.info("Running signal extraction pipeline...")

    # Run live ingestion
    ingest_result = run_live_ingest()

    # The ingestion already persists signals, so we just return stats
    signals_created = ingest_result.get("total_new", 0)

    # Load state to get current signals for return
    state = load_state()
    current_signals = state.get("perception", {}).get("signals", [])

    # Get only the newest signals (those just created)
    new_signals = current_signals[-signals_created:] if signals_created > 0 else []

    logger.info(f"Signal extraction complete: {signals_created} new signals")

    return {
        "signals_created": signals_created,
        "signals": new_signals,
        "ingestion_details": {
            "sources": ingest_result.get("sources", {}),
            "total_fetched": ingest_result.get("total_fetched", 0),
            "total_normalized": ingest_result.get("total_normalized", 0),
            "errors": ingest_result.get("errors", []),
        },
    }
