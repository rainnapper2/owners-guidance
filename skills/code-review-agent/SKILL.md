---
name: code-review-agent
description: Automated Directory-Based Code Review Agent Skill. Resolves parent directory SKILL.md rules for touched files in git, unions them, and executes an AI code review.
---

# Code Review Agent Skill

This skill encodes the pattern for **Directory-Based Code Review Skills**. It dynamically discovers modified files in git, resolves parent directory skills (`SKILL.md`), unions them across touched files, and conducts a strict AI code review.

## 🚀 How to Execute This Skill

When asked to **"run code review agent"** or **"review code against directory skills"**, follow these exact steps:

### Step 1: Generate Deterministic Context Payload
Run the self-contained Python script embedded in this skill:

```bash
python3 skills/code-review-agent/scripts/review_agent.py
```

*Options supported:*
- `--staged`: Review staged git changes (`git diff --cached`).
- `--commit <ref>`: Review a specific git commit (e.g. `HEAD` or commit SHA).
- `--base <ref>`: Review branch diff against base (e.g. `main`).
- `--output <path>`: Custom output file path (default: `.review_context.tmp.md`).

This script will:
1. Detect touched files using `git`.
2. Walk up parent directory paths to resolve all inherited `SKILL.md` files.
3. Union all unique directory skills.
4. Output the deterministic context payload to `.review_context.tmp.md`.

### Step 2: Read the Context Payload
Read the generated `.review_context.tmp.md` file using `view_file` or your harness file reader tool. The payload contains:
- List of touched files and their exact inherited directory skill mappings.
- Complete text of all unioned `SKILL.md` guidelines.
- Full `git diff` content.

### Step 3: Perform AI Code Review
Invoke a specialized `code_reviewer` subagent or perform a line-by-line evaluation against the unioned skills:

1. **Verify Type Annotations & PEP 8**: Check functions against global Python standards (`python/SKILL.md`).
2. **Verify Subdirectory Guidelines**: Check API endpoints (`python/api/SKILL.md`), CLI interfaces (`python/cli/SKILL.md`), or domain-specific directory rules.
3. **Verify Test Coverage**: Check that modified/new functions have unit tests.

### Step 4: Output Code Review Report
Produce a structured review report containing:
- **Touched Files & Inherited Skill Mappings**
- **Line-by-Line Findings Table** (File, Line, Severity, Skill Source, Description)
- **Union Skill Compliance Checklist**
- **Suggested Code Diffs**
- **Overall Verdict**: `APPROVED` or `REVISED_NEEDED`
