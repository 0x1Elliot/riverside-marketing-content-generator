import json
import sys
import unittest
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from riverside_marketing.engagement import (  # noqa: E402
    EngagementMessage,
    ReaderContextError,
    select_engagement_message,
    validate_reader_context,
)


SAMPLE_PATH = PROJECT_ROOT / "data" / "books.sample.json"


def _books():
    return json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))


class ReaderContextValidationTests(unittest.TestCase):
    def test_context_normalizes_optional_fields(self) -> None:
        context = validate_reader_context(
            {
                "reader_id": " reader-7 ",
                "favorite_genres": [" Historical Fiction "],
                "books_read": ["RB-001"],
                "active_challenge": "Detective Trail",
                "challenge_progress": 82,
                "last_visit": "2026-01-01",
            }
        )

        self.assertEqual(context.reader_id, "reader-7")
        self.assertEqual(context.favorite_genres, ("Historical Fiction",))
        self.assertEqual(context.books_read, ("RB-001",))
        self.assertEqual(context.challenge_progress, 82)

    def test_context_rejects_unknown_fields_and_invalid_percentages(self) -> None:
        with self.assertRaises(ReaderContextError) as raised:
            validate_reader_context(
                {"challenge_progress": 101, "unexpected": True}
            )

        self.assertEqual(len(raised.exception.errors), 2)
        self.assertTrue(
            any(
                "additional field is not allowed" in str(error)
                for error in raised.exception.errors
            )
        )


class ReaderEngagementSelectionTests(unittest.TestCase):
    def test_challenge_completion_nudge_has_the_contract_fields(self) -> None:
        context = validate_reader_context(
            {
                "reader_id": "reader-7",
                "favorite_genres": ["Historical Fiction"],
                "active_challenge": "Detective Trail",
                "challenge_progress": 82,
            }
        )

        message = select_engagement_message(_books(), context)

        self.assertIsInstance(message, EngagementMessage)
        self.assertEqual(message.message_type, "challenge_completion_nudge")
        self.assertEqual(message.reader_or_segment, "reader-7")
        self.assertEqual(message.recommended_book["book_id"], "RB-001")
        self.assertTrue(message.reason_selected)
        self.assertTrue(message.headline)
        self.assertTrue(message.body_copy)
        self.assertTrue(message.call_to_action)

    def test_personalized_discovery_avoids_books_already_read(self) -> None:
        context = validate_reader_context(
            {"reader_id": "reader-8", "favorite_genres": ["Science Fiction"]}
        )

        message = select_engagement_message(_books(), context)

        self.assertEqual(message.message_type, "personalized_discovery")
        self.assertEqual(message.recommended_book["book_id"], "RB-002")

    def test_genre_exploration_quest_uses_an_unread_outside_genre(self) -> None:
        context = validate_reader_context(
            {
                "reader_id": "reader-9",
                "favorite_genres": ["Historical Fiction"],
                "books_read": ["RB-001"],
            }
        )

        message = select_engagement_message(_books(), context)

        self.assertEqual(message.message_type, "genre_exploration_quest")
        self.assertEqual(message.recommended_book["book_id"], "RB-002")

    def test_comeback_and_community_signals_are_supported(self) -> None:
        comeback = select_engagement_message(
            _books(),
            validate_reader_context(
                {"reader_id": "reader-10", "last_visit": "2025-01-01"}
            ),
            today=date(2026, 2, 15),
        )
        community = select_engagement_message(
            _books(),
            validate_reader_context(
                {
                    "favorite_genres": ["Science Fiction"],
                    "community_progress": 78,
                    "community_goal": "the Spring Reading Quest",
                }
            ),
        )

        self.assertEqual(comeback.message_type, "comeback_challenge")
        self.assertEqual(community.message_type, "community_progress")
        self.assertIn("Spring Reading Quest", community.headline)
        json.dumps(community.as_dict())


if __name__ == "__main__":
    unittest.main()
