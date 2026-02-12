"""
Canonical Ingestion Object Model (v1)

This defines the normalized object shape that ALL external sources
(Reddit, X, Freshdesk, etc.) must map into before entering cognition_state.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


@dataclass
class IngestionObject:
    id: str
    source: str
    external_id: Optional[str]
    content: str
    content_type: str
    author: Optional[str]
    url: Optional[str]
    tags: list
    created_at: Optional[str]
    ingested_at: str
    metadata: Dict[str, Any]

    def to_dict(self) -> dict:
        return asdict(self)


def create_ingestion_object(
    source: str,
    content: str,
    content_type: str,
    external_id: Optional[str] = None,
    author: Optional[str] = None,
    url: Optional[str] = None,
    created_at: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Create a normalized ingestion object.
    """

    return IngestionObject(
        id=str(uuid.uuid4()),
        source=source,
        external_id=external_id,
        content=content,
        content_type=content_type,
        author=author,
        url=url,
        tags=[],
        created_at=created_at,
        ingested_at=utc_now_iso(),
        metadata=metadata or {},
    ).to_dict()
