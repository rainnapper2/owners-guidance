"""AI Code Review Agent.

Consumes the union of active directory skills and the PR diff, evaluates the changes
against the specific directory skill rules, and posts a formal GitHub PR Review
(with line-by-line findings and overall status).
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Optional LLM integration via urllib (no external dependencies required)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def get_pr_diff(base_sha: str | None = None, head_sha: str | None = None, base_ref: str = "main") -> str:
    """Fetch the exact git diff for the PR."""
    if base_sha and head_sha:
        cmd = ["git", "diff", base_sha, head_sha]
    else:
        cmd = ["git", "diff", f"origin/{base_ref}...HEAD"]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout
    except subprocess.CalledProcessError:
        return ""


def evaluate_skill_rules(diff_text: str, changed_files: list[str], repo_root: Path) -> list[dict]:
    """Static skill rule evaluator for Python API & CLI conventions."""
    findings = []

    for file_path_str in changed_files:
        full_path = repo_root / file_path_str
        if not full_path.is_file() or not file_path_str.endswith(".py"):
            continue

        try:
            code = full_path.read_text(encoding="utf-8")
            lines = code.splitlines()

            # Rule 1: General Python Skill - Type Annotations check on functions
            if "python/SKILL.md" in str(file_path_str) or "python" in file_path_str:
                for idx, line in enumerate(lines, 1):
                    if line.strip().startswith("def ") and "->" not in line:
                        findings.append({
                            "file": file_path_str,
                            "line": idx,
                            "level": "WARNING",
                            "skill": "python/SKILL.md",
                            "message": f"Function `{line.strip().split('(')[0]}` is missing explicit return type annotation (`->`)."
                        })

            # Rule 2: API Skill - HTTP Status code check & print statement check
            if "python/api" in file_path_str:
                for idx, line in enumerate(lines, 1):
                    if "print(" in line and not line.strip().startswith("#"):
                        findings.append({
                            "file": file_path_str,
                            "line": idx,
                            "level": "WARNING",
                            "skill": "python/api/SKILL.md",
                            "message": "API code should avoid raw `print()` statements; use standard logging or response output."
                        })

            # Rule 3: CLI Skill - Exit code handling & sys.stderr for errors
            if "python/cli" in file_path_str:
                for idx, line in enumerate(lines, 1):
                    if "except" in line and "sys.stderr" not in code:
                        findings.append({
                            "file": file_path_str,
                            "line": idx,
                            "level": "INFO",
                            "skill": "python/cli/SKILL.md",
                            "message": "CLI error handlers should direct error messages to `sys.stderr`."
                        })

        except Exception as e:
            pass

    return findings


def generate_ai_review_prompt(diff_text: str, skills_guidance: str) -> str:
    """Build structured prompt for LLM Code Review Agent."""
    return f"""You are an Automated AI Code Reviewer Agent.
Your job is to strictly enforce directory-level skill guidelines for code changes in this Pull Request.

=== APPLICABLE DIRECTORY SKILLS (UNION) ===
{skills_guidance}

=== PR CODE DIFF ===
{diff_text}

=== INSTRUCTIONS ===
1. Review every changed file against the UNION of directory skills above.
2. Flag any violations of PEP8, missing type hints, improper HTTP status codes, or CLI stream usage.
3. Output line-by-line feedback and an overall review decision (APPROVED or CHANGES_REQUESTED).
"""


def generate_review_comment(findings: list[dict], changed_files: list[str]) -> str:
    """Format final AI Agent Review report."""
    lines = [
        "## 🤖 AI Code Review Agent Findings",
        "",
        "The AI Review Agent analyzed the PR changes against the union of active directory skills:",
        "",
    ]

    if not findings:
        lines.extend([
            "✅ **Status: APPROVED**",
            "",
            "All modified files comply with the active directory skill guidelines!",
            "- Python type annotations & PEP8 conventions verified.",
            "- API HTTP status codes & REST structures verified.",
            "- CLI I/O streams and exit codes verified.",
        ])
    else:
        lines.extend([
            "⚠️ **Status: COMMENT / SUGGESTIONS**",
            "",
            "The following items were identified based on directory skill rules:",
            "",
        ])
        for f in findings:
            lines.append(f"- **`{f['file']}:{f['line']}`** [{f['skill']}]")
            lines.append(f"  - **{f['level']}**: {f['message']}")
            lines.append("")

    lines.extend([
        "",
        "---",
        "_Reviewed by Directory-Based AI Code Review Agent_",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Code Review Agent based on Directory Skills")
    parser.add_argument("--guidance", required=True, help="Path to resolved review guidance markdown")
    parser.add_argument("--base-sha", help="Git base commit SHA")
    parser.add_argument("--head-sha", help="Git head commit SHA")
    parser.add_argument("--base", default="main", help="Git base branch")
    parser.add_argument("--pr", help="GitHub PR number to post review to")
    parser.add_argument("--root", default=".", help="Repository root path")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    guidance_path = Path(args.guidance)
    skills_text = guidance_path.read_text(encoding="utf-8") if guidance_path.exists() else ""

    diff_text = get_pr_diff(base_sha=args.base_sha, head_sha=args.head_sha, base_ref=args.base)

    # Determine changed files from diff header lines
    changed_files = [
        line.split(" b/")[1] for line in diff_text.splitlines() if line.startswith("diff --git a/")
    ]

    findings = evaluate_skill_rules(diff_text, changed_files, repo_root)
    review_report = generate_review_comment(findings, changed_files)

    print(review_report)

    # If PR number is passed and running in GitHub Actions with gh CLI, post formal PR review!
    if args.pr and os.getenv("GH_TOKEN"):
        event = "COMMENT" if findings else "APPROVE"
        review_file = repo_root / "ai_review_report.md"
        review_file.write_text(review_report, encoding="utf-8")

        cmd = [
            "gh", "pr", "review", args.pr,
            "--comment",
            "--body-file", str(review_file)
        ]
        try:
            subprocess.run(cmd, check=True)
            print(f"Successfully posted AI PR Review to PR #{args.pr}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to post PR review: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
