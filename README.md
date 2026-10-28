## zelvarys-depaudit

![PyPI total downloads](https://img.shields.io/pepy/dt/zelvarys-depaudit)
![Release version](https://img.shields.io/github/v/release/zelvarys/depaudit-cli)

A dependency auditor for Python and Node projects. Point it at a repo and it tells you what's wrong with your dependency files.

Works on Termux, Linux, macOS. No runtime dependencies outside the standard library.

### What it checks

- **unpinned** — a dependency declared without a version constraint
- **unused** — declared but never imported anywhere in the source
- **stdlib-shadow** — a dependency whose name shadows a Python stdlib module
- **duplicate** — the same package declared more than once with conflicting constraints
- **outdated** — a dependency one or more major versions behind (with `--online`)

Python and JavaScript/TypeScript only. Both `requirements.txt` and `pyproject.toml` are supported for Python; `package.json` for Node.

### Install

```bash
pip install zelvarys-depaudit
```

Or from source:

```bash
git clone https://github.com/zelvarys/depaudit-cli
cd depaudit-cli
pip install -e ".[dev]"
```

### Usage

Run it in the directory you want to check:

```bash
depaudit
```

Or point it at a path:

```bash
depaudit ./myproject
```

Sample output:

```
/home/me/myproject/requirements.txt
  warning  unpinned:2 — `flask` has no version constraint
  warning  unused:2   — `flask` is declared but never imported

Scanned 8 file(s), 4 dependency(ies).
Found 3 issue(s).
```

Exit code is `1` if any issues were found, `0` if clean. Useful in CI.

### Checking for outdated versions

By default, depaudit works offline. Add `--online` to also query PyPI and npm for the latest version of each pinned dependency:

```bash
depaudit --online
```

Only major-version gaps are reported. If you're on `5.2.2` and the latest is `5.2.9`, nothing is printed — that's not worth your attention. If you're on `5.0.8` and the latest is `8.3.4`, you'll see:

```
  warning  outdated — `vite` is on 5.x (latest is 8.x, 3 majors behind)
```

### JSON output

For scripts or CI integrations:

```bash
depaudit --json
```

Returns an array of findings:

```json
[
  {
    "check": "unused",
    "severity": "warning",
    "message": "`pandas` is declared but never imported",
    "source": "/home/me/myproject/requirements.txt",
    "line": 3
  }
]
```

### What it won't do

It doesn't fix anything. It doesn't install or uninstall packages. It doesn't resolve transitive dependencies. It reads your manifest files and your source code, reports what looks wrong, and stops there.

It also doesn't guess whether an import is "missing". If a module isn't in your manifest, it isn't a dependency, so it isn't reported.

### Development

```bash
git clone https://github.com/zelvarys/depaudit-cli
cd depaudit-cli
pip install -e ".[dev]"
pip install ruff
pytest -q
ruff check .
```

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.
