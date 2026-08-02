# Monorepo: Python API & CLI with Directory-Based Code Review Skills

A lightweight Python monorepo showcasing **Directory-Based Code Review Skills** in GitHub Actions.

## 📁 Repository Structure

```
.
├── .github/
│   ├── scripts/
│   │   └── skill_reviewer.py      # Resolves parent directory skills and unions them for PR review
│   └── workflows/
│       ├── ci.yml                  # Continuous Integration test runner
│       └── code-review.yml         # PR Code Review workflow using directory skills
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

When a Pull Request is opened or updated, `.github/scripts/skill_reviewer.py` evaluates all changed files:

1. **Hierarchy Resolution**: For every touched file, it walks up the directory path from the file's directory to the repository root, gathering all applicable `SKILL.md` files along the path.
2. **Multi-Directory Union**: If a PR touches files across multiple directories (e.g. `python/api/server.py` and `python/cli/client.py`), the reviewer engine unions the skills from all affected directories and parent paths without duplication.
3. **Automated Review Guidance**: Generates a unified Markdown review guide attached to the PR summary and PR comments.

### Skill Resolution Matrix

| Modified File(s) | Applicable Skill Files (Union of Parents) |
|---|---|
| `python/api/server.py` | `python/SKILL.md` + `python/api/SKILL.md` |
| `python/cli/client.py` | `python/SKILL.md` + `python/cli/SKILL.md` |
| `python/api/server.py` **AND** `python/cli/client.py` | `python/SKILL.md` + `python/api/SKILL.md` + `python/cli/SKILL.md` |

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

### Testing the Skill Reviewer Locally
```bash
# Simulating a PR touching both API and CLI files
python3 .github/scripts/skill_reviewer.py --files python/api/server.py python/cli/client.py
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
