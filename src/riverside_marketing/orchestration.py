"""Coordinate catalog loading, validation, and deterministic draft generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping, Sequence
from typing import Any

from .data import (
    BookDataValidator,
    DataLoadError,
    ValidationIssue,
)
from .generation import (
    ContentType,
    MarketingDraft,
    generate_marketing_draft,
)
from .engagement import (
    EngagementMessage,
    ReaderContext,
    select_engagement_message,
    validate_reader_context,
)


@dataclass(frozen=True)
class ValidationDiagnostic:
    """Validation outcome for one catalog entry, retained in input order."""

    index: int
    book_id: str | None
    valid: bool
    errors: tuple[ValidationIssue, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "book_id": self.book_id,
            "valid": self.valid,
            "errors": [
                {"path": issue.path, "message": issue.message}
                for issue in self.errors
            ],
        }


@dataclass(frozen=True)
class RejectedRecord:
    """Raw catalog entry rejected before it can reach generation."""

    index: int
    record: Any

    def as_dict(self) -> dict[str, Any]:
        return {"index": self.index, "record": self.record}


@dataclass(frozen=True)
class OrchestrationSummary:
    """Counts for one catalog-to-drafts run."""

    total_records: int
    valid_records: int
    rejected_records: int
    generated_drafts: int

    def as_dict(self) -> dict[str, int]:
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "rejected_records": self.rejected_records,
            "generated_drafts": self.generated_drafts,
        }


@dataclass(frozen=True)
class CatalogGenerationResult:
    """Structured result of validating a catalog and generating its drafts."""

    generated_drafts: tuple[MarketingDraft, ...]
    engagement_messages: tuple[EngagementMessage, ...]
    rejected_records: tuple[RejectedRecord, ...]
    validation_diagnostics: tuple[ValidationDiagnostic, ...]
    summary: OrchestrationSummary

    @property
    def drafts(self) -> tuple[MarketingDraft, ...]:
        """Short alias for consumers that refer to generated drafts as drafts."""

        return self.generated_drafts

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly review artifact."""

        return {
            "generated_drafts": [
                draft.as_dict() for draft in self.generated_drafts
            ],
            "engagement_messages": [
                message.as_dict() for message in self.engagement_messages
            ],
            "rejected_records": [
                record.as_dict() for record in self.rejected_records
            ],
            "validation_diagnostics": [
                diagnostic.as_dict()
                for diagnostic in self.validation_diagnostics
            ],
            "summary": self.summary.as_dict(),
        }


def run_catalog_generation(
    records: Sequence[Any],
    content_type: ContentType | str = ContentType.PROMOTIONAL_DESCRIPTION,
    validator: BookDataValidator | None = None,
    reader_context: Mapping[str, Any] | ReaderContext | None = None,
) -> CatalogGenerationResult:
    """Validate records and generate drafts only for valid entries.

    Validation diagnostics, rejected records, and generated drafts all retain
    their original input order. The generator receives only
    ``ValidationResult.record`` values from successful validation calls.
    """

    if not isinstance(records, (list, tuple)):
        raise DataLoadError("Expected a sequence of book records")

    active_validator = validator or BookDataValidator()
    if isinstance(reader_context, ReaderContext):
        context = reader_context
    elif reader_context is None:
        context = None
    else:
        context = validate_reader_context(reader_context)
    generated_drafts: list[MarketingDraft] = []
    valid_books: list[dict[str, Any]] = []
    rejected_records: list[RejectedRecord] = []
    validation_diagnostics: list[ValidationDiagnostic] = []

    for index, record in enumerate(records):
        validation_result = active_validator.validate_record(record)
        book_id = _book_id_for_diagnostic(record)
        validation_diagnostics.append(
            ValidationDiagnostic(
                index=index,
                book_id=book_id,
                valid=validation_result.valid,
                errors=validation_result.errors,
            )
        )

        if not validation_result.valid:
            rejected_records.append(RejectedRecord(index=index, record=record))
            continue

        # The validator guarantees a record is present when valid is true.
        valid_books.append(validation_result.record)  # type: ignore[arg-type]
        generated_drafts.append(
            generate_marketing_draft(
                validation_result.record,  # type: ignore[arg-type]
                content_type=content_type,
            )
        )

    engagement_messages: tuple[EngagementMessage, ...] = ()
    if context is not None:
        engagement_messages = (
            select_engagement_message(tuple(valid_books), context),
        )

    summary = OrchestrationSummary(
        total_records=len(records),
        valid_records=len(generated_drafts),
        rejected_records=len(rejected_records),
        generated_drafts=len(generated_drafts),
    )
    return CatalogGenerationResult(
        generated_drafts=tuple(generated_drafts),
        engagement_messages=engagement_messages,
        rejected_records=tuple(rejected_records),
        validation_diagnostics=tuple(validation_diagnostics),
        summary=summary,
    )


def load_and_generate_catalog(
    path: str | Path,
    content_type: ContentType | str = ContentType.PROMOTIONAL_DESCRIPTION,
    validator: BookDataValidator | None = None,
    reader_context: Mapping[str, Any] | ReaderContext | None = None,
) -> CatalogGenerationResult:
    """Load a JSON catalog and run the validation-to-generation workflow."""

    records = _load_catalog(path)
    return run_catalog_generation(
        records,
        content_type=content_type,
        validator=validator,
        reader_context=reader_context,
    )


def _load_catalog(path: str | Path) -> list[Any]:
    source_path = Path(path)
    try:
        payload = json.loads(source_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DataLoadError(f"Book data file does not exist: {source_path}") from exc
    except OSError as exc:
        raise DataLoadError(f"Could not read book data file: {source_path}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DataLoadError(
            f"Book data file is not valid UTF-8 JSON: {source_path}"
        ) from exc

    if not isinstance(payload, list):
        raise DataLoadError("Expected a JSON array of book records")
    return payload


def _book_id_for_diagnostic(record: Any) -> str | None:
    if isinstance(record, Mapping) and isinstance(record.get("book_id"), str):
        return record["book_id"]
    return None
