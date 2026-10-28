# Contributing

Thanks for taking the time to improve zelvarys-depaudit. This guide covers the
local workflow and what to expect when opening a pull request.

## Requirements

- Python 3.10 or newer
- git

## Setup

```bash
git clone https://github.com/zelvarys/depaudit-cli.git
cd depaudit-cli
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pip install ruff
```

## Checks

Run the tests:

```bash
pytest -q
```

Run the linter:

```bash
ruff check .
```

Fix issues automatically where possible:

```bash
ruff check --fix .
```

This project uses Ruff because it is a Python project. ESLint does not apply to
Python source files.

## Pull requests

- Keep changes focused and describe the behavior that changed.
- Add or update tests for bug fixes and new checks.
- Update the README when user-facing behavior changes.
- Do not bump the package version in a pull request. Releases are handled
  separately.
- Do not commit caches, virtual environments, or generated package metadata.

## Commit messages

Short, conventional commit subjects are preferred:

```text
feat: add a new dependency check
fix: handle empty manifest files
docs: clarify online mode
test: cover duplicate constraints
chore: update tooling
```

## Reporting bugs

Open an issue with a minimal reproduction, the expected result, the actual
result, your Python version, and your operating system.

For security issues, use
[GitHub Security Advisories](https://github.com/zelvarys/depaudit-cli/security/advisories/new)
instead of opening a public issue.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
