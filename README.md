# Monorepo: Python API & CLI with Directory-Based Code Review Skills

A lightweight Python monorepo showcasing **Directory-Based Code Review Skills** in GitHub Actions.

## 📁 Repository Structure

```
.
├── .github/
│   ├── scripts/
│   │   ├── ai_reviewer.py         # AI Code Review Agent logic
│   │   └── skill_reviewer.py      # Resolves parent directory skills and unions them for PR review
│   └── workflows/
│       ├── ci.yml                  # Continuous Integration test runner
│       └── code-review.yml         # PR Code Review workflow using directory skills
├── scripts/
│   └── run_code_review_agent.py   # Harness-agnostic local review payload generator
├── python/
│   ├── SKILL.md                    # Core Python standards (Type hints, PEP8, testing)
│   ├── api/
│   │   ├── SKILL.md                # API specific standards (REST, status codes, JSON format)
│   │   ├── server.py               # REST API HTTP server (Python standard library)
│   │   └── test_api.py             # Integration & unit tests for API
│   └── cli/
│       ├── SKILL.md                # CLI specific standards (argparse, stdio streams, exit codes)
│       ├── client.py               # CLI client tool
│       └── test_cli.py             # Integration & unit tests for CLI
└── tests/
    └── test_skill_reviewer.py      # Unit tests for directory skill inheritance & unioning engine
```

---

## 🎯 How Directory-Based Code Review Skills Work

When a Pull Request is opened or code is modified, the review engine (`scripts/run_code_review_agent.py` / `skill_reviewer.py`) evaluates all changed files:

1. **Hierarchy Resolution**: For every touched file, it walks up the directory path from the file's directory to the repository root, gathering all applicable `SKILL.md` files along the path.
2. **Multi-Directory Union**: If a change touches files across multiple directories (e.g. `python/api/server.py` and `python/cli/client.py`), the reviewer engine unions the skills from all affected directories and parent paths without duplication.
3. **Deterministic Context Payload**: Generates a self-contained `.review_context.tmp.md` file containing the union of skills, file mappings, git diff, and review instructions.
4. **Harness-Agnostic Agent Execution**: The payload file is fed into any AI Code Reviewer Agent (Antigravity subagents, LLM API, Claude Code, Cursor, Aider, GitHub Actions) to produce a strict compliance review.

### Skill Resolution Matrix

| Modified File(s) | Applicable Skill Files (Union of Parents) |
|---|---|
| `python/api/server.py` | `python/SKILL.md` + `python/api/SKILL.md` |
| `python/cli/client.py` | `python/SKILL.md` + `python/cli/SKILL.md` |
| `python/api/server.py` **AND** `python/cli/client.py` | `python/SKILL.md` + `python/api/SKILL.md` + `python/cli/SKILL.md` |

---

## 🤖 Local Agent Execution & Example Review Output

### 1. Stage a change & generate review context payload
```bash
# Stage changes
git add python/api/server.py

# Generate deterministic review payload
python3 scripts/run_code_review_agent.py
```

**Terminal Output:**
```text
✅ Generated deterministic review context for 1 files:
   • python/api/server.py -> [python/SKILL.md, python/api/SKILL.md]

✅ Total Unioned Skill Files: 2
✅ Context Payload File Written To: .review_context.tmp.md
```

### 2. Example AI Code Reviewer Report Output

> # Code Review Report
> **Overall Verdict**: **`REVISED_NEEDED`**
> 
> ---
> 
> ## 🚨 Line-by-Line Findings
> 
> | File | Line(s) | Severity | Skill Source | Description |
> | --- | --- | --- | --- | --- |
> | `python/api/server.py` | 16 | **High** | `python/SKILL.md` | Function signature `def format_item_response(item):` missing explicit type annotations for parameter `item` and return type. |
> | `python/api/server.py` | 15–16 | **Medium** | `python/SKILL.md` | `format_item_response` uses an inline comment instead of a formal function docstring explaining purpose and return value. |
> | `python/api/test_api.py` | N/A | **High** | `python/SKILL.md` | Missing unit tests for the newly introduced `format_item_response` function. |
> | `python/api/server.py` | 17 | **Low** | Code Quality | Residual debug `print(f"DEBUG...")` statement pollutes standard output. |
> 
> ---
> 
> ## 🛠️ Suggested Code Changes
> 
> ```diff
> -# Helper to format item responses for API consumers
> -def format_item_response(item):
> -    print(f"DEBUG: Formatting response for item {item}")
> -    return {"data": item, "version": "v1"}
> +def format_item_response(item: dict) -> dict:
> +    """Format item dictionary response payload for API consumers.
> +
> +    Args:
> +        item: Dictionary containing item attributes.
> +
> +    Returns:
> +        Formatted dictionary with payload data and version metadata.
> +    """
> +    return {"data": item, "version": "v1"}
> ```

---

## 🚀 Quickstart & Testing

### Running API Server & CLI Client
```bash
# Start API server
python3 python/api/server.py

# In another terminal, run CLI client commands
python3 python/cli/client.py health
python3 python/cli/client.py list
python3 python/cli/client.py create --name "Demo Item"
python3 python/cli/client.py get --id 1
```

### Running All Unit Tests (Zero External Dependencies)
```bash
python3 -m unittest discover -s python -p "test_*.py"
python3 -m unittest discover -s tests -p "test_*.py"
```

---

## 🐙 Publishing to GitHub with `gh` CLI

To connect this local repo to a new GitHub repository:

```bash
# 1. Authenticate gh CLI (if needed)
gh auth login

# 2. Create remote repository and push
gh repo create owners-guidance --public --source=. --remote=origin --push
```
