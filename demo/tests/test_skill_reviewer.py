"""Unit tests for the directory skill review engine."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

# Add skills/code-review-agent/scripts to sys.path for importing review_agent
script_dir = Path(__file__).resolve().parent.parent.parent / "skills" / "code-review-agent" / "scripts"
sys.path.insert(0, str(script_dir))

from review_agent import (
    find_skill_files_in_dir,
    resolve_skills_for_file,
    build_review_context,
)


class TestSkillReviewer(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Create mock directory structure:
        # root/
        #   python/
        #     SKILL.md
        #     api/
        #       SKILL.md
        #       server.py
        #     cli/
        #       SKILL.md
        #       client.py
        self.py_dir = self.root / "python"
        self.api_dir = self.py_dir / "api"
        self.cli_dir = self.py_dir / "cli"

        self.api_dir.mkdir(parents=True)
        self.cli_dir.mkdir(parents=True)

        self.py_skill = self.py_dir / "SKILL.md"
        self.py_skill.write_text("General Python guidelines", encoding="utf-8")

        self.api_skill = self.api_dir / "SKILL.md"
        self.api_skill.write_text("API specific guidelines", encoding="utf-8")

        self.cli_skill = self.cli_dir / "SKILL.md"
        self.cli_skill.write_text("CLI specific guidelines", encoding="utf-8")

        self.api_file = self.api_dir / "server.py"
        self.api_file.write_text("# server code", encoding="utf-8")

        self.cli_file = self.cli_dir / "client.py"
        self.cli_file.write_text("# cli code", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_find_skill_files_in_dir(self) -> None:
        skills = find_skill_files_in_dir(self.py_dir)
        self.assertEqual(skills, [self.py_skill])

    def test_resolve_skills_for_api_file(self) -> None:
        skills = resolve_skills_for_file(self.api_file, self.root)
        # Should include python/SKILL.md AND python/api/SKILL.md in order
        self.assertEqual(skills, [self.py_skill, self.api_skill])

    def test_resolve_skills_for_cli_file(self) -> None:
        skills = resolve_skills_for_file(self.cli_file, self.root)
        # Should include python/SKILL.md AND python/cli/SKILL.md
        self.assertEqual(skills, [self.py_skill, self.cli_skill])

    def test_build_review_context_union(self) -> None:
        changed_files = ["python/api/server.py", "python/cli/client.py"]
        context, file_to_skills, union_skills = build_review_context(changed_files, "mock diff", self.root)

        # file_to_skills mapping
        self.assertEqual(file_to_skills["python/api/server.py"], [self.py_skill, self.api_skill])
        self.assertEqual(file_to_skills["python/cli/client.py"], [self.py_skill, self.cli_skill])

        # Union should contain all 3 unique skills without duplicates
        self.assertEqual(len(union_skills), 3)
        self.assertEqual(union_skills, [self.py_skill, self.api_skill, self.cli_skill])

        self.assertIn("DETERMINISTIC CODE REVIEW CONTEXT PAYLOAD", context)
        self.assertIn("General Python guidelines", context)
        self.assertIn("API specific guidelines", context)
        self.assertIn("CLI specific guidelines", context)


if __name__ == "__main__":
    unittest.main()
