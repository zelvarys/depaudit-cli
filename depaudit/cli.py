"""depaudit CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .checks.base import Check
from .checks.duplicate import DuplicateCheck
from .checks.missing import MissingCheck
from .checks.outdated import OutdatedCheck
from .checks.stdlib_shadow import StdlibShadowCheck
from .checks.unpinned import UnpinnedCheck
from .checks.unused import UnusedCheck
from .models import SubProject
from .online import latest_npm, latest_pypi
from .parsers.package_json import PackageJsonParser
from .parsers.pyproject import PyprojectParser
from .parsers.requirements import RequirementsParser
from .report import human_report, json_report
from .scanners.js_imports import JsImportsScanner
from .scanners.py_imports import PyImportsScanner

SKIP_DIRS = {
  ".git", ".hg", ".svn", "node_modules", "venv", ".venv",
  "__pycache__", "dist", "build", ".pytest_cache",
  ".mypy_cache", ".ruff_cache", "target", "vendor",
  ".tox", ".eggs", ".next", ".nuxt", ".cache", "out",
}

# filenames that declare dependencies
MANIFEST_FILENAMES = {"requirements.txt", "pyproject.toml", "package.json"}


def _iter_files(root: Path):
  for path in root.rglob("*"):
    if not path.is_file():
      continue
    if any(part in SKIP_DIRS for part in path.parts):
      continue
    yield path


def _manifest_root(manifest: Path) -> Path:
  """Return the directory that a manifest governs.

  requirements.txt inside a 'requirements/' folder → one level up.
  Everything else → the manifest's own directory.
  """
  if manifest.name == "requirements.txt" and manifest.parent.name == "requirements":
    return manifest.parent.parent
  return manifest.parent


def _find_manifests(root: Path) -> list[Path]:
  return [p for p in _iter_files(root) if p.name in MANIFEST_FILENAMES]


def _build_subprojects(root: Path) -> list[SubProject]:
  manifests = _find_manifests(root)

  # group manifests by the root they govern
  by_root: dict[Path, list[Path]] = {}
  for m in manifests:
    r = _manifest_root(m).resolve()
    by_root.setdefault(r, []).append(m)

  subprojects: list[SubProject] = []

  for sub_root, subs_manifests in by_root.items():
    sp = SubProject(root=sub_root, manifests=subs_manifests)

    # parse deps from every manifest that governs this root
    for m in subs_manifests:
      if m.name == "requirements.txt":
        sp.dependencies.extend(RequirementsParser().parse(m))
      elif m.name == "pyproject.toml":
        sp.dependencies.extend(PyprojectParser().parse(m))
      elif m.name == "package.json":
        sp.dependencies.extend(PackageJsonParser().parse(m))

    # scan imports under this root only
    sp.imports.extend(PyImportsScanner().scan(sub_root))
    sp.imports.extend(JsImportsScanner().scan(sub_root))

    # figure out which languages this subproject speaks
    if any(m.name in ("requirements.txt", "pyproject.toml") for m in subs_manifests):
      sp.languages.add("python")
    if any(m.name == "package.json" for m in subs_manifests):
      sp.languages.add("javascript")
    # also infer from imports (e.g. a package.json project with .py files)
    if any(i.source.endswith(".py") for i in sp.imports):
      sp.languages.add("python")
    if any(i.source.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")) for i in sp.imports):
      sp.languages.add("javascript")

    subprojects.append(sp)

  return subprojects


def _lookup_latest(dep):
  if dep.source.endswith("package.json"):
    return latest_npm(dep.name)
  return latest_pypi(dep.name)


def _run_checks(subprojects: list[SubProject], online: bool) -> list:
  findings = []
  for sp in subprojects:
    project = sp.to_project()
    checks: list[Check] = [
      UnpinnedCheck(),
      UnusedCheck(),
      MissingCheck(),
      StdlibShadowCheck(),
      DuplicateCheck(),
    ]
    if online:
      checks.append(OutdatedCheck(_lookup_latest))
    for check in checks:
      if "*" in check.languages or (set(check.languages) & sp.languages):
        try:
          findings.extend(check.run(project))
        except Exception as e:  # noqa: BLE001
          print(f"warning: check {check.name} failed on {sp.root}: {e}",
              file=sys.stderr)
  return findings


def run(path: str, as_json: bool, online: bool) -> int:
  root = Path(path).resolve()
  if not root.exists():
    print(f"error: path not found: {path}", file=sys.stderr)
    return 2

  files_scanned = sum(1 for _ in _iter_files(root))
  subprojects = _build_subprojects(root)

  if not subprojects:
    if as_json:
      print(json_report([]))
    else:
      print(f"Scanned {files_scanned} file(s).")
      print("No dependency manifests found (requirements.txt, pyproject.toml, package.json).")
    return 0

  total_deps = sum(len(sp.dependencies) for sp in subprojects)
  findings = _run_checks(subprojects, online)

  color = sys.stdout.isatty()
  if as_json:
    print(json_report(findings))
  else:
    print(human_report(findings, files_scanned, total_deps, color=color))

  return 1 if findings else 0


def main(argv: list[str] | None = None) -> int:
  p = argparse.ArgumentParser(prog="depaudit", description="Audit dependencies.")
  p.add_argument("-v", "--version", action="version",
           version=f"depaudit {__version__}")
  p.add_argument("path", nargs="?", default=".", help="Project directory")
  p.add_argument("--json", action="store_true", help="JSON output")
  p.add_argument("--online", action="store_true",
           help="Also check for outdated versions (network)")
  args = p.parse_args(argv)

  return run(args.path, as_json=args.json, online=args.online)


if __name__ == "__main__":
  raise SystemExit(main())