"""Marketing and reader-engagement generation boundary for Product D."""
"""Deterministic marketing draft generation for Product D."""

from .drafts import (
    ContentType,
    MarketingDraft,
    generate_marketing_draft,
    generate_marketing_drafts,
)
from ..engagement import (
    EngagementMessage,
    ReaderContext,
    select_engagement_message,
    validate_reader_context,
)

__all__ = [
    "ContentType",
    "MarketingDraft",
    "generate_marketing_draft",
    "generate_marketing_drafts",
    "EngagementMessage",
    "ReaderContext",
    "select_engagement_message",
    "validate_reader_context",
]
