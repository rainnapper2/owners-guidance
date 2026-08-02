"""Skill Reviewer Script for GitHub Code Review.

Traverses directory hierarchy for changed files in a PR, resolves all inherited
skills from parent directories to target directories, unions them across all touched
files, and generates structured code review context and guidance.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

SKILL_FILENAMES = ["SKILL.md", ".skill.md", "SKILL.txt", ".skills.md"]


def find_skill_files_in_dir(directory: Path) -> list[Path]:
    """Find skill files in a given directory."""
    found = []
    for filename in SKILL_FILENAMES:
        skill_path = directory / filename
        if skill_path.is_file():
            found.append(skill_path)

    # Also check if there is a .skills/ directory with markdown files
    skills_dir = directory / ".skills"
    if skills_dir.is_dir():
        for skill_file in sorted(skills_dir.glob("*.md")):
            if skill_file.is_file():
                found.append(skill_file)

    return found


def resolve_skills_for_file(filepath: str | Path, repo_root: Path) -> list[Path]:
    """Resolve all inherited skill files for a file, from repo root down to file directory."""
    filepath = Path(filepath)
    if filepath.is_absolute():
        try:
            rel_path = filepath.relative_to(repo_root)
        except ValueError:
            rel_path = filepath
    else:
        rel_path = filepath

    dir_path = rel_path.parent
    # Build list of directory ancestors from root to dir_path
    parts = dir_path.parts if dir_path.parts != (".",) else ()
    ancestor_dirs = [repo_root]
    current = repo_root
    for part in parts:
        current = current / part
        ancestor_dirs.append(current)

    skill_files = []
    for ancestor in ancestor_dirs:
        if ancestor.exists():
            skill_files.extend(find_skill_files_in_dir(ancestor))

    return skill_files


def get_changed_files_from_git(base_ref: str = "main", repo_root: Path | None = None) -> list[str]:
    """Get list of changed files in git relative to base ref."""
    cwd = repo_root or Path.cwd()
    # Try various ref specs to handle both local and CI PR checkouts
    ref_specs = [f"origin/{base_ref}...HEAD", f"{base_ref}...HEAD", "HEAD~1...HEAD", "HEAD"]
    for ref_spec in ref_specs:
        cmd = ["git", "diff", "--name-only", ref_spec]
        try:
            res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
            files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
            if files:
                return files
        except subprocess.CalledProcessError:
            pass

    return []


def build_review_summary(changed_files: list[str], repo_root: Path) -> tuple[dict[str, list[Path]], list[Path]]:
    """Build mapping of file -> skills and return union of all unique skill files."""
    file_to_skills = {}
    all_skills_set = set()
    all_skills_ordered = []

    for file_path in changed_files:
        full_path = repo_root / file_path
        skills = resolve_skills_for_file(full_path, repo_root)
        file_to_skills[file_path] = skills
        for skill in skills:
            if skill not in all_skills_set:
                all_skills_set.add(skill)
                all_skills_ordered.append(skill)

    return file_to_skills, all_skills_ordered


def generate_markdown_report(changed_files: list[str], repo_root: Path) -> str:
    """Generate Markdown report of directory-based skills for code review."""
    file_to_skills, union_skills = build_review_summary(changed_files, repo_root)

    report_lines = [
        "# 🔍 Code Review Guidance & Skill Context",
        "",
        "This code review automatically resolves and unions directory-level skills across all touched files.",
        "",
        "## 📁 Modified Files & Inherited Directory Skills",
        "",
    ]

    if not changed_files:
        report_lines.append("_No modified files detected._\n")
    else:
        for file_path in sorted(changed_files):
            skills = file_to_skills.get(file_path, [])
            report_lines.append(f"### `{file_path}`")
            if not skills:
                report_lines.append("- _No specific directory skills found._")
            else:
                for skill_path in skills:
                    try:
                        rel_skill = skill_path.relative_to(repo_root)
                    except ValueError:
                        rel_skill = skill_path
                    report_lines.append(f"- Includes skill: `{rel_skill}`")
            report_lines.append("")

    report_lines.extend([
        "---",
        "",
        "## 🛠️ Union of Applicable Review Skills",
        "",
    ])

    if not union_skills:
        report_lines.append("_No skill files applied to this Pull Request._\n")
    else:
        for skill_path in union_skills:
            try:
                rel_skill = skill_path.relative_to(repo_root)
            except ValueError:
                rel_skill = skill_path

            report_lines.append(f"### 📋 Skill: `{rel_skill}`")
            report_lines.append("")
            try:
                content = skill_path.read_text(encoding="utf-8")
                report_lines.append(content)
            except Exception as err:
                report_lines.append(f"_Error reading skill content: {err}_")
            report_lines.append("")

    report_lines.extend([
        "---",
        "*Generated by GitHub Code Review Skills Resolver*",
    ])

    return "\n".join(report_lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve & Union Directory Skills for GitHub Code Review")
    parser.add_argument("--files", nargs="*", help="List of changed file paths")
    parser.add_argument("--base", default="main", help="Git base branch ref for diff comparison")
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument("--output", help="Path to write output markdown report")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()

    if args.files:
        changed_files = args.files
    else:
        changed_files = get_changed_files_from_git(base_ref=args.base, repo_root=repo_root)

    report = generate_markdown_report(changed_files, repo_root)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
