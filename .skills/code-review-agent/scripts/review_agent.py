#!/usr/bin/env python3
"""Directory-Based Code Review Skills Generator.

Self-contained script embedded in the code-review-agent skill.
1. Inspects modified files via git (staged, commit, or branch diff).
2. Traverses parent directory tree to discover all inherited SKILL.md files.
3. Merges and unions all active directory skills without duplication.
4. Generates a deterministic markdown review context payload file (.review_context.tmp.md).
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

    skills_dir = directory / ".skills"
    if skills_dir.is_dir():
        for skill_file in sorted(skills_dir.glob("*.md")):
            if skill_file.is_file():
                found.append(skill_file)

    return found


def resolve_skills_for_file(filepath: Path, repo_root: Path) -> list[Path]:
    """Resolve inherited skill files for a given file path from repo root down."""
    try:
        rel_path = filepath.relative_to(repo_root) if filepath.is_absolute() else filepath
    except ValueError:
        rel_path = filepath

    dir_path = rel_path.parent
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


def get_touched_files(
    repo_root: Path,
    base_ref: str | None = None,
    commit_ref: str | None = None,
    staged: bool = False
) -> tuple[list[str], str]:
    """Extract list of touched files and git diff string."""
    if staged:
        name_cmd = ["git", "diff", "--name-only", "--cached"]
        diff_cmd = ["git", "diff", "--cached"]
    elif commit_ref:
        diff_cmd = ["git", "diff", f"{commit_ref}~1", commit_ref]
        name_cmd = ["git", "diff", "--name-only", f"{commit_ref}~1", commit_ref]
    elif base_ref:
        diff_cmd = ["git", "diff", f"{base_ref}...HEAD"]
        name_cmd = ["git", "diff", "--name-only", f"{base_ref}...HEAD"]
    else:
        # 1. Try staged changes first
        try:
            res = subprocess.run(["git", "diff", "--name-only", "--cached"], cwd=repo_root, capture_output=True, text=True, check=True)
            files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
            if files:
                diff_res = subprocess.run(["git", "diff", "--cached"], cwd=repo_root, capture_output=True, text=True, check=True)
                return files, diff_res.stdout
        except subprocess.CalledProcessError:
            pass

        # 2. Try git diff HEAD
        try:
            res = subprocess.run(["git", "diff", "--name-only", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=True)
            files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
            if files:
                diff_res = subprocess.run(["git", "diff", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=True)
                return files, diff_res.stdout
        except subprocess.CalledProcessError:
            pass

        # 3. Fallback to branch comparisons
        for spec in ["origin/main...HEAD", "main...HEAD", "HEAD~1...HEAD"]:
            try:
                res = subprocess.run(["git", "diff", "--name-only", spec], cwd=repo_root, capture_output=True, text=True, check=True)
                files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
                if files:
                    diff_res = subprocess.run(["git", "diff", spec], cwd=repo_root, capture_output=True, text=True, check=True)
                    return files, diff_res.stdout
            except subprocess.CalledProcessError:
                pass
        return [], ""

    try:
        files_res = subprocess.run(name_cmd, cwd=repo_root, capture_output=True, text=True, check=True)
        files = [f.strip() for f in files_res.stdout.splitlines() if f.strip()]
        diff_res = subprocess.run(diff_cmd, cwd=repo_root, capture_output=True, text=True, check=True)
        return files, diff_res.stdout
    except subprocess.CalledProcessError as err:
        print(f"Git diff error: {err}", file=sys.stderr)
        return [], ""


def build_review_context(
    touched_files: list[str],
    diff_text: str,
    repo_root: Path
) -> tuple[str, dict[str, list[Path]], list[Path]]:
    """Build deterministic code review context string."""
    file_to_skills = {}
    all_skills_set = set()
    all_skills_ordered = []

    for file_str in touched_files:
        full_path = repo_root / file_str
        skills = resolve_skills_for_file(full_path, repo_root)
        file_to_skills[file_str] = skills
        for skill in skills:
            if skill not in all_skills_set:
                all_skills_set.add(skill)
                all_skills_ordered.append(skill)

    lines = [
        "# 🤖 DETERMINISTIC CODE REVIEW CONTEXT PAYLOAD",
        "",
        "You are an AI Code Reviewer Agent. Your mission is to strictly review the code changes below ",
        "against the UNION of directory skills collected from every touched file and its parent directories.",
        "",
        "## 📌 TOUCHED FILES & INHERITED SKILL MAPPINGS",
        "",
    ]

    for file_str in sorted(touched_files):
        skills = file_to_skills.get(file_str, [])
        lines.append(f"### File: `{file_str}`")
        if not skills:
            lines.append("- _No specific directory skills found._")
        else:
            for s in skills:
                try:
                    rel_s = s.relative_to(repo_root)
                except ValueError:
                    rel_s = s
                lines.append(f"- Inherits Skill: `{rel_s}`")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 🛠️ UNION OF DIRECTORY SKILLS (REVIEW RULES)",
        "",
    ])

    if not all_skills_ordered:
        lines.append("_No skill files found across touched directories._\n")
    else:
        for s in all_skills_ordered:
            try:
                rel_s = s.relative_to(repo_root)
            except ValueError:
                rel_s = s
            lines.append(f"### Skill File: `{rel_s}`")
            try:
                lines.append(s.read_text(encoding="utf-8"))
            except Exception as e:
                lines.append(f"_Error reading {s}: {e}_")
            lines.append("")

    lines.extend([
        "---",
        "",
        "## 📝 CODE DIFF TO REVIEW",
        "",
        "```diff",
        diff_text if diff_text else "# No diff content available",
        "```",
        "",
        "---",
        "",
        "## 📋 AGENT REVIEW TASK INSTRUCTIONS",
        "1. Evaluate every modified file against all of its inherited directory skills.",
        "2. Identify specific lines or patterns that violate any of the active skill rules.",
        "3. Provide constructive findings categorized by file, line number, severity, and skill source.",
        "4. Conclude with an overall assessment (APPROVED or REVISED_NEEDED).",
    ])

    return "\n".join(lines), file_to_skills, all_skills_ordered


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare deterministic context & run Code Review Agent")
    parser.add_argument("--base", help="Git base branch ref (e.g. main)")
    parser.add_argument("--commit", help="Specific git commit ref (e.g. HEAD or commit hash)")
    parser.add_argument("--staged", action="store_true", help="Compare staged git changes")
    parser.add_argument("--output", default=".review_context.tmp.md", help="Output path for context payload")
    parser.add_argument("--root", default=".", help="Repository root path")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    touched_files, diff_text = get_touched_files(
        repo_root,
        base_ref=args.base,
        commit_ref=args.commit,
        staged=args.staged
    )

    if not touched_files:
        print("No touched files found in git comparison.")
        return 0

    context_payload, file_to_skills, union_skills = build_review_context(touched_files, diff_text, repo_root)

    out_path = repo_root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(context_payload, encoding="utf-8")

    print(f"✅ Generated deterministic review context for {len(touched_files)} files:")
    for f in touched_files:
        skills = []
        for s in file_to_skills.get(f, []):
            try:
                skills.append(str(s.relative_to(repo_root)))
            except ValueError:
                skills.append(str(s))
        print(f"   • {f} -> [{', '.join(skills)}]")
    print(f"\n✅ Total Unioned Skill Files: {len(union_skills)}")
    print(f"✅ Context Payload File Written To: {out_path.relative_to(repo_root)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
