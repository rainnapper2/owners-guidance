"""Unit tests for the directory CODE_REVIEW.md review engine."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

# Add skills/code-review-agent/scripts to sys.path for importing review_agent
script_dir = Path(__file__).resolve().parent.parent.parent / "skills" / "code-review-agent" / "scripts"
sys.path.insert(0, str(script_dir))

from review_agent import (
    find_review_files_in_dir,
    resolve_reviews_for_file,
    build_review_context,
)


class TestSkillReviewer(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Create mock directory structure:
        # root/
        #   python/
        #     CODE_REVIEW.md
        #     api/
        #       CODE_REVIEW.md
        #       server.py
        #     cli/
        #       CODE_REVIEW.md
        #       client.py
        self.py_dir = self.root / "python"
        self.api_dir = self.py_dir / "api"
        self.cli_dir = self.py_dir / "cli"

        self.api_dir.mkdir(parents=True)
        self.cli_dir.mkdir(parents=True)

        self.py_review = self.py_dir / "CODE_REVIEW.md"
        self.py_review.write_text("General Python guidelines", encoding="utf-8")

        self.api_review = self.api_dir / "CODE_REVIEW.md"
        self.api_review.write_text("API specific guidelines", encoding="utf-8")

        self.cli_review = self.cli_dir / "CODE_REVIEW.md"
        self.cli_review.write_text("CLI specific guidelines", encoding="utf-8")

        self.api_file = self.api_dir / "server.py"
        self.api_file.write_text("# server code", encoding="utf-8")

        self.cli_file = self.cli_dir / "client.py"
        self.cli_file.write_text("# cli code", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_find_review_files_in_dir(self) -> None:
        reviews = find_review_files_in_dir(self.py_dir)
        self.assertEqual(reviews, [self.py_review])

    def test_resolve_reviews_for_api_file(self) -> None:
        reviews = resolve_reviews_for_file(self.api_file, self.root)
        # Should include python/CODE_REVIEW.md AND python/api/CODE_REVIEW.md in order
        self.assertEqual(reviews, [self.py_review, self.api_review])

    def test_resolve_reviews_for_cli_file(self) -> None:
        reviews = resolve_reviews_for_file(self.cli_file, self.root)
        # Should include python/CODE_REVIEW.md AND python/cli/CODE_REVIEW.md
        self.assertEqual(reviews, [self.py_review, self.cli_review])

    def test_build_review_context_union(self) -> None:
        changed_files = ["python/api/server.py", "python/cli/client.py"]
        context, file_to_reviews, union_reviews = build_review_context(changed_files, "mock diff", self.root)

        # file_to_reviews mapping
        self.assertEqual(file_to_reviews["python/api/server.py"], [self.py_review, self.api_review])
        self.assertEqual(file_to_reviews["python/cli/client.py"], [self.py_review, self.cli_review])

        # Union should contain all 3 unique reviews without duplicates
        self.assertEqual(len(union_reviews), 3)
        self.assertEqual(union_reviews, [self.py_review, self.api_review, self.cli_review])

        self.assertIn("DETERMINISTIC CODE REVIEW CONTEXT PAYLOAD", context)
        self.assertIn("General Python guidelines", context)
        self.assertIn("API specific guidelines", context)
        self.assertIn("CLI specific guidelines", context)


if __name__ == "__main__":
    unittest.main()
