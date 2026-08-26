import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from riverside_marketing.generation import ContentType  # noqa: E402
from riverside_marketing.orchestration import (  # noqa: E402
    CatalogGenerationResult,
    load_and_generate_catalog,
    run_catalog_generation,
)
from riverside_marketing.generation.drafts import (  # noqa: E402
    generate_marketing_draft,
)


DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_PATH = DATA_DIR / "books.sample.json"
INVALID_PATH = DATA_DIR / "fixtures" / "books.invalid.json"
MIXED_PATH = DATA_DIR / "fixtures" / "books.mixed.json"


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _valid_records():
    return _load_json(SAMPLE_PATH)


def _invalid_records():
    return [case["record"] for case in _load_json(INVALID_PATH)]


class CatalogOrchestrationTests(unittest.TestCase):
    def test_all_valid_catalog_generates_all_drafts(self) -> None:
        result = load_and_generate_catalog(SAMPLE_PATH)

        self.assertIsInstance(result, CatalogGenerationResult)
        self.assertEqual(result.summary.total_records, 2)
        self.assertEqual(result.summary.valid_records, 2)
        self.assertEqual(result.summary.rejected_records, 0)
        self.assertEqual(result.summary.generated_drafts, 2)
        self.assertEqual(
            [draft.book_id for draft in result.generated_drafts],
            ["RB-001", "RB-002"],
        )
        self.assertTrue(all(item.valid for item in result.validation_diagnostics))

    def test_mixed_catalog_preserves_drafts_rejections_and_diagnostics(self) -> None:
        records = [
            _valid_records()[0],
            _invalid_records()[0],
            _valid_records()[1],
            _invalid_records()[1],
        ]

        result = run_catalog_generation(records)

        self.assertEqual(result.summary.total_records, 4)
        self.assertEqual(result.summary.valid_records, 2)
        self.assertEqual(result.summary.rejected_records, 2)
        self.assertEqual(result.summary.generated_drafts, 2)
        self.assertEqual(
            [draft.book_id for draft in result.generated_drafts],
            ["RB-001", "RB-002"],
        )
        self.assertEqual(
            [record.index for record in result.rejected_records],
            [1, 3],
        )
        self.assertEqual(
            [diagnostic.valid for diagnostic in result.validation_diagnostics],
            [True, False, True, False],
        )

    def test_file_based_mixed_catalog_runs_end_to_end(self) -> None:
        with patch(
            "riverside_marketing.orchestration.generate_marketing_draft",
            wraps=generate_marketing_draft,
        ) as generate_mock:
            result = load_and_generate_catalog(MIXED_PATH, ContentType.SOCIAL_MEDIA)
            repeated_result = load_and_generate_catalog(
                MIXED_PATH,
                ContentType.SOCIAL_MEDIA,
            )

        self.assertEqual(result.as_dict(), repeated_result.as_dict())
        self.assertEqual(result.summary.total_records, 4)
        self.assertEqual(result.summary.valid_records, 2)
        self.assertEqual(result.summary.rejected_records, 2)
        self.assertEqual(result.summary.generated_drafts, 2)
        self.assertEqual(
            [draft.book_id for draft in result.generated_drafts],
            ["RB-001", "RB-002"],
        )
        self.assertTrue(
            all(
                draft.content_type == ContentType.SOCIAL_MEDIA.value
                for draft in result.generated_drafts
            )
        )
        self.assertEqual(
            [record.index for record in result.rejected_records],
            [1, 3],
        )
        self.assertEqual(
            [diagnostic.index for diagnostic in result.validation_diagnostics],
            [0, 1, 2, 3],
        )
        self.assertEqual(
            [diagnostic.valid for diagnostic in result.validation_diagnostics],
            [True, False, True, False],
        )
        self.assertEqual(
            result.validation_diagnostics[1].book_id,
            "RB-MIXED-BAD-STOCK",
        )
        self.assertEqual(
            result.validation_diagnostics[3].book_id,
            "RB-MIXED-BAD-RATING",
        )
        self.assertTrue(result.validation_diagnostics[1].errors)
        self.assertTrue(result.validation_diagnostics[3].errors)
        self.assertEqual(generate_mock.call_count, 4)
        self.assertEqual(
            [call.args[0]["book_id"] for call in generate_mock.call_args_list],
            ["RB-001", "RB-002", "RB-001", "RB-002"],
        )

    def test_all_invalid_catalog_generates_no_drafts(self) -> None:
        result = run_catalog_generation(_invalid_records())

        self.assertEqual(result.summary.total_records, 4)
        self.assertEqual(result.summary.valid_records, 0)
        self.assertEqual(result.summary.rejected_records, 4)
        self.assertEqual(result.summary.generated_drafts, 0)
        self.assertEqual(result.generated_drafts, ())
        self.assertEqual(
            [record.index for record in result.rejected_records],
            [0, 1, 2, 3],
        )
        self.assertTrue(
            all(not diagnostic.valid for diagnostic in result.validation_diagnostics)
        )

    def test_output_is_deterministic_and_preserves_input_order(self) -> None:
        records = [_valid_records()[1], _valid_records()[0]]

        first = run_catalog_generation(records, ContentType.SOCIAL_MEDIA)
        second = run_catalog_generation(records, ContentType.SOCIAL_MEDIA)

        self.assertEqual(first, second)
        self.assertEqual(first.as_dict(), second.as_dict())
        self.assertEqual(
            [draft.book_id for draft in first.generated_drafts],
            ["RB-002", "RB-001"],
        )
        json.dumps(first.as_dict())

    def test_rejected_record_keeps_diagnostic_context(self) -> None:
        invalid_record = _invalid_records()[0]

        result = run_catalog_generation([invalid_record])

        self.assertEqual(result.rejected_records[0].record, invalid_record)
        diagnostic = result.validation_diagnostics[0]
        self.assertEqual(diagnostic.index, 0)
        self.assertEqual(diagnostic.book_id, "RB-INVALID-STOCK")
        self.assertFalse(diagnostic.valid)
        self.assertTrue(
            any("must be one of" in issue.message for issue in diagnostic.errors)
        )

    def test_generation_is_called_only_for_valid_records(self) -> None:
        records = [_valid_records()[0], _invalid_records()[0], _valid_records()[1]]

        with patch(
            "riverside_marketing.orchestration.generate_marketing_draft",
            wraps=generate_marketing_draft,
        ) as generate_mock:
            result = run_catalog_generation(records)

        self.assertEqual(generate_mock.call_count, 2)
        self.assertEqual(
            [call.args[0]["book_id"] for call in generate_mock.call_args_list],
            ["RB-001", "RB-002"],
        )
        self.assertEqual(result.summary.generated_drafts, 2)

    def test_reader_context_adds_one_engagement_message_without_changing_core_drafts(self) -> None:
        result = run_catalog_generation(
            _valid_records(),
            reader_context={
                "reader_id": "reader-7",
                "favorite_genres": ["Science Fiction"],
            },
        )

        self.assertEqual(len(result.generated_drafts), 2)
        self.assertEqual(len(result.engagement_messages), 1)
        self.assertEqual(
            result.engagement_messages[0].message_type,
            "personalized_discovery",
        )
        self.assertIn("engagement_messages", result.as_dict())


if __name__ == "__main__":
    unittest.main()
