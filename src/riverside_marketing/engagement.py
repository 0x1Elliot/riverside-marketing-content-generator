"""Deterministic reader-engagement message selection for Product D."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Mapping

from .data.validation import ValidationIssue


class ReaderContextError(ValueError):
    """Raised when reader context cannot be used by the engagement engine."""

    def __init__(self, errors: tuple[ValidationIssue, ...]) -> None:
        self.errors = errors
        detail = "; ".join(str(error) for error in errors)
        super().__init__(detail or "Reader context is invalid")


@dataclass(frozen=True)
class ReaderContext:
    """Optional reader and community signals used for one engagement decision."""

    reader_id: str | None = None
    favorite_genres: tuple[str, ...] = ()
    books_read: tuple[str, ...] = ()
    active_challenge: str | None = None
    challenge_progress: float | None = None
    last_visit: str | None = None
    community_progress: float | None = None
    community_goal: str = "the Riverside reading goal"


@dataclass(frozen=True)
class EngagementMessage:
    """Structured, reviewable message selected for a reader or segment."""

    message_type: str
    reader_or_segment: str
    recommended_book: dict[str, Any] | None
    reason_selected: str
    headline: str
    body_copy: str
    call_to_action: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type,
            "reader_or_segment": self.reader_or_segment,
            "recommended_book": self.recommended_book,
            "reason_selected": self.reason_selected,
            "headline": self.headline,
            "body_copy": self.body_copy,
            "call_to_action": self.call_to_action,
        }


_CONTEXT_FIELDS = {
    "reader_id",
    "favorite_genres",
    "books_read",
    "active_challenge",
    "challenge_progress",
    "last_visit",
    "community_progress",
    "community_goal",
}


def validate_reader_context(value: Any) -> ReaderContext:
    """Validate an optional JSON reader context without changing book validation."""

    if not isinstance(value, Mapping):
        raise ReaderContextError(
            (ValidationIssue("$.reader_context", "expected type 'object'"),)
        )

    errors: list[ValidationIssue] = []
    for field_name in sorted(set(value) - _CONTEXT_FIELDS):
        errors.append(
            ValidationIssue(
                f"$.reader_context.{field_name}",
                "additional field is not allowed",
            )
        )

    reader_id = _optional_non_empty_string(value, "reader_id", errors)
    favorite_genres = _string_list(value, "favorite_genres", errors)
    books_read = _string_list(value, "books_read", errors)
    active_challenge = _optional_non_empty_string(
        value, "active_challenge", errors
    )
    community_goal = _optional_non_empty_string(value, "community_goal", errors)
    if community_goal is None:
        community_goal = "the Riverside reading goal"

    challenge_progress = _percentage(value, "challenge_progress", errors)
    community_progress = _percentage(value, "community_progress", errors)

    last_visit = value.get("last_visit")
    if last_visit is not None:
        if not isinstance(last_visit, str) or not last_visit.strip():
            errors.append(
                ValidationIssue(
                    "$.reader_context.last_visit",
                    "must be a non-empty ISO date or datetime string",
                )
            )
        else:
            try:
                _parse_date(last_visit)
            except ValueError:
                errors.append(
                    ValidationIssue(
                        "$.reader_context.last_visit",
                        "must be a valid ISO date or datetime string",
                    )
                )

    if errors:
        raise ReaderContextError(tuple(errors))

    return ReaderContext(
        reader_id=reader_id,
        favorite_genres=tuple(favorite_genres),
        books_read=tuple(books_read),
        active_challenge=active_challenge,
        challenge_progress=challenge_progress,
        last_visit=last_visit,
        community_progress=community_progress,
        community_goal=community_goal,
    )


def select_engagement_message(
    books: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]],
    context: ReaderContext,
    *,
    today: date | None = None,
) -> EngagementMessage:
    """Select one deterministic engagement message from validated books.

    Decision priority is: challenge completion, comeback, community progress,
    genre exploration, and personalized discovery. The order makes the most
    time-sensitive individual signal win while keeping fallback behavior useful.
    """

    books_in_order = list(books)
    reader_label = _reader_label(context)
    favorite_genres = {genre.casefold() for genre in context.favorite_genres}
    read_ids = set(context.books_read)
    candidates = [
        book
        for book in books_in_order
        if book.get("stock_status") != "out_of_stock"
        and str(book.get("book_id")) not in read_ids
    ]
    if not candidates:
        candidates = [
            book for book in books_in_order if book.get("stock_status") != "out_of_stock"
        ]
    if not candidates:
        candidates = books_in_order

    favorite_candidates = [
        book
        for book in candidates
        if str(book.get("genre", "")).casefold() in favorite_genres
    ]

    if (
        context.active_challenge
        and context.challenge_progress is not None
        and context.challenge_progress >= 80
    ):
        book = (favorite_candidates or candidates or [None])[0]
        remaining = max(0, 100 - context.challenge_progress)
        return EngagementMessage(
            message_type="challenge_completion_nudge",
            reader_or_segment=reader_label,
            recommended_book=_book_summary(book),
            reason_selected=(
                f"The reader is {context.challenge_progress:g}% through the active "
                f"{context.active_challenge} challenge, so a completion nudge is timely."
            ),
            headline=f"You’re almost there on {context.active_challenge}",
            body_copy=(
                f"You’re {remaining:g}% away from completing {context.active_challenge}. "
                + _book_sentence(book, "A strong next pick is")
            ),
            call_to_action="Finish the challenge",
        )

    if context.last_visit and _is_comeback(context.last_visit, today=today):
        book = (favorite_candidates or candidates or [None])[0]
        return EngagementMessage(
            message_type="comeback_challenge",
            reader_or_segment=reader_label,
            recommended_book=_book_summary(book),
            reason_selected=(
                "The reader has been away for at least 30 days, so a low-friction "
                "return challenge is more useful than a generic promotion."
            ),
            headline="A small reading challenge for your return",
            body_copy=(
                "It’s good to have you back. "
                + _book_sentence(book, "Start with")
                + " and make it your first Riverside read this week."
            ),
            call_to_action="Take the comeback challenge",
        )

    if context.community_progress is not None:
        progress = context.community_progress
        return EngagementMessage(
            message_type="community_progress",
            reader_or_segment=reader_label,
            recommended_book=_book_summary((candidates or [None])[0]),
            reason_selected=(
                "Community progress was supplied, so the message invites the reader "
                "into a shared goal rather than treating them as an isolated buyer."
            ),
            headline=f"Riverside readers are {progress:g}% to {context.community_goal}",
            body_copy=(
                f"The community is {progress:g}% of the way to {context.community_goal}. "
                "Add one more read and help unlock the next milestone."
            ),
            call_to_action="Join the community goal",
        )

    read_genres = {
        str(book.get("genre", "")).casefold()
        for book in books_in_order
        if str(book.get("book_id")) in read_ids
    }
    exploration_candidates = [
        book
        for book in candidates
        if str(book.get("genre", "")).casefold() not in favorite_genres
    ]
    if favorite_genres and read_genres and read_genres <= favorite_genres and exploration_candidates:
        book = exploration_candidates[0]
        favorites = ", ".join(context.favorite_genres)
        return EngagementMessage(
            message_type="genre_exploration_quest",
            reader_or_segment=reader_label,
            recommended_book=_book_summary(book),
            reason_selected=(
                f"The reader’s recorded reads stay within favorite genres ({favorites}), "
                "and the catalog has an unread title outside that comfort zone."
            ),
            headline="Try one chapter outside your usual shelf",
            body_copy=(
                f"You’ve been enjoying {favorites}. "
                + _book_sentence(book, "Your next quest is")
                + "—a chance to discover a new favorite."
            ),
            call_to_action="Start the exploration quest",
        )

    book = (favorite_candidates or candidates or [None])[0]
    genre = str(book.get("genre", "book")) if book else "book"
    return EngagementMessage(
        message_type="personalized_discovery",
        reader_or_segment=reader_label,
        recommended_book=_book_summary(book),
        reason_selected=(
            "An unread catalog title matches the reader’s favorite genres, so the "
            "message focuses on relevant discovery."
            if favorite_candidates
            else "No higher-priority engagement signal applied; the best available catalog title is used for discovery."
        ),
        headline=f"A {genre} pick for you",
        body_copy=_book_sentence(book, "Based on your reading interests, try"),
        call_to_action="Discover this book",
    )


def _optional_non_empty_string(
    value: Mapping[str, Any], field_name: str, errors: list[ValidationIssue]
) -> str | None:
    field = value.get(field_name)
    if field is None:
        return None
    if not isinstance(field, str) or not field.strip():
        errors.append(
            ValidationIssue(
                f"$.reader_context.{field_name}",
                "must be a non-empty string",
            )
        )
        return None
    return field.strip()


def _string_list(
    value: Mapping[str, Any], field_name: str, errors: list[ValidationIssue]
) -> list[str]:
    field = value.get(field_name, [])
    if not isinstance(field, list):
        errors.append(
            ValidationIssue(
                f"$.reader_context.{field_name}",
                "must be an array of non-empty strings",
            )
        )
        return []
    result: list[str] = []
    for index, item in enumerate(field):
        if not isinstance(item, str) or not item.strip():
            errors.append(
                ValidationIssue(
                    f"$.reader_context.{field_name}[{index}]",
                    "must be a non-empty string",
                )
            )
        else:
            result.append(item.strip())
    return result


def _percentage(
    value: Mapping[str, Any], field_name: str, errors: list[ValidationIssue]
) -> float | None:
    field = value.get(field_name)
    if field is None:
        return None
    if isinstance(field, bool) or not isinstance(field, (int, float)):
        errors.append(
            ValidationIssue(
                f"$.reader_context.{field_name}",
                "must be a number from 0 to 100",
            )
        )
        return None
    if not 0 <= field <= 100:
        errors.append(
            ValidationIssue(
                f"$.reader_context.{field_name}",
                "must be a number from 0 to 100",
            )
        )
        return None
    return float(field)


def _parse_date(value: str) -> date:
    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        return date.fromisoformat(normalized)


def _is_comeback(value: str, *, today: date | None) -> bool:
    reference_date = today or date.today()
    return reference_date - _parse_date(value) >= timedelta(days=30)


def _reader_label(context: ReaderContext) -> str:
    if context.reader_id:
        return context.reader_id
    if context.favorite_genres:
        return f"Readers who enjoy {', '.join(context.favorite_genres)}"
    return "Riverside readers"


def _book_summary(book: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if book is None:
        return None
    return {
        "book_id": book.get("book_id"),
        "title": book.get("title"),
        "author": book.get("author"),
        "genre": book.get("genre"),
    }


def _book_sentence(book: Mapping[str, Any] | None, prefix: str) -> str:
    if book is None:
        return f"{prefix} a book from the Riverside catalog."
    return f"{prefix} {book['title']} by {book['author']}."
