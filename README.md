# Code Review Agent Skill & Monorepo Demo

A reusable AI Agent Skill (`code-review-agent`) that automatically resolves, inherits, and unions parent directory skills (`SKILL.md`) across modified files in Git, generating a deterministic context payload for AI code review.

Includes a demo monorepo codebase in `demo/`.

---

## 📁 Repository Structure

```
.
├── skills/
│   └── code-review-agent/           # Reusable Code Review Agent Skill
│       ├── SKILL.md                 # Agent instructions for "run code review agent"
│       └── scripts/
│           └── review_agent.py      # Self-contained Python script to build review payload
├── .skills/                         # Symlinked/Mirrored skill folder for auto-discovery
│   └── code-review-agent/
├── demo/                            # Sample Monorepo Codebase
│   ├── python/
│   │   ├── SKILL.md                 # General Python guidelines & standards
│   │   ├── api/
│   │   │   ├── SKILL.md             # API specific standards (REST, status codes, JSON errors)
│   │   │   ├── server.py            # REST API HTTP server
│   │   │   └── test_api.py          # API unit tests
│   │   └── cli/
│   │       ├── SKILL.md             # CLI specific standards (argparse, stdio streams)
│   │       ├── client.py            # CLI client tool
│   │       └── test_cli.py          # CLI unit tests
│   └── tests/
│       └── test_skill_reviewer.py   # Unit tests for the skill resolution engine
├── .github/
│   └── workflows/
│       ├── ci.yml                   # CI pipeline runner
│       └── code-review.yml          # GitHub Actions workflow for PR code review
└── README.md
```

---

## 💡 How to Use the Skill

Include this repository or copy `skills/code-review-agent` into your project. An AI assistant or developer can trigger code review by simply asking:

> **"run code review agent"** or **"review my code against directory skills"**

The agent will execute:

```bash
python3 skills/code-review-agent/scripts/review_agent.py
```

### Script Execution Options
- **Staged Git Changes**: `python3 skills/code-review-agent/scripts/review_agent.py --staged`
- **Specific Commit**: `python3 skills/code-review-agent/scripts/review_agent.py --commit HEAD`
- **Branch Diff vs Main**: `python3 skills/code-review-agent/scripts/review_agent.py --base main`

---

## 🎯 Skill Resolution Matrix (Demo Codebase)

When files in `demo/` are modified, the skill engine resolves and unions all parent directory skills from the root down to each file's directory:

| Modified File(s) in `demo/` | Union of Inherited Skill Guidelines |
|---|---|
| `demo/python/api/server.py` | `demo/python/SKILL.md` + `demo/python/api/SKILL.md` |
| `demo/python/cli/client.py` | `demo/python/SKILL.md` + `demo/python/cli/SKILL.md` |
| `demo/python/api/server.py` **AND** `demo/python/cli/client.py` | `demo/python/SKILL.md` + `demo/python/api/SKILL.md` + `demo/python/cli/SKILL.md` |

---

## 🚀 Quickstart & Running Tests

### Running Demo Monorepo Unit Tests
```bash
python3 -m unittest discover -s demo -p "test_*.py"
```

### Running Local Skill Review Payload Generator
```bash
# Stage any change in demo/
git add demo/python/api/server.py

# Run the review agent script
python3 skills/code-review-agent/scripts/review_agent.py
```

---

## 🤖 Example AI Code Review Output

> # Code Review Report
> **Overall Verdict**: **`REVISED_NEEDED`**
> 
> ---
> 
> ## 🚨 Line-by-Line Findings
> 
> | File | Line(s) | Severity | Skill Source | Description |
> | --- | --- | --- | --- | --- |
> | `demo/python/api/server.py` | 16 | **High** | `demo/python/SKILL.md` | Function signature `def format_item_response(item):` missing explicit type annotations for parameter `item` and return type. |
> | `demo/python/api/server.py` | 15–16 | **Medium** | `demo/python/SKILL.md` | `format_item_response` uses an inline comment instead of a formal function docstring. |
> | `demo/python/api/test_api.py` | N/A | **High** | `demo/python/SKILL.md` | Missing unit tests for newly introduced `format_item_response` function. |
> | `demo/python/api/server.py` | 17 | **Low** | Code Quality | Residual debug `print(f"DEBUG...")` statement. |
