"""Flag imports that aren't declared as dependencies."""

from __future__ import annotations

import sys
from pathlib import Path

from ..models import Finding, Project
from .base import Check

STDLIB = set(getattr(sys, "stdlib_module_names", set()))

IMPORT_TO_PACKAGE = {
  "pil": "pillow",
  "cv2": "opencv-python",
  "sklearn": "scikit-learn",
  "yaml": "pyyaml",
  "bs4": "beautifulsoup4",
  "dotenv": "python-dotenv",
  "jwt": "pyjwt",
  "dateutil": "python-dateutil",
  "serial": "pyserial",
  "git": "gitpython",
  "attr": "attrs",
}

IGNORE_MISSING = {"tests", "test"}

# Defensive: alias-like module names should never reach this check,
# but skip them if they do.
ALIAS_PREFIXES = ("@/", "~/", "~~/", "@@/")


def _local_packages(root: Path) -> set[str]:
  names: set[str] = set()
  if not root.is_dir():
    return names
  for entry in root.iterdir():
    if entry.is_dir() and (entry / "__init__.py").exists():
      names.add(entry.name.replace("_", "-").lower())
    elif entry.is_file() and entry.suffix == ".py":
      names.add(entry.stem.replace("_", "-").lower())
  return names


class MissingCheck(Check):
  name = "missing"

  def run(self, project: Project) -> list[Finding]:
    declared = {d.name for d in project.dependencies}
    local = _local_packages(Path(project.root))
    findings: list[Finding] = []
    reported: set[tuple[str, str]] = set()

    for imp in project.imports:
      mod = imp.module
      if mod in STDLIB or mod in IGNORE_MISSING or mod.startswith("_"):
        continue
      if any(mod.startswith(p) for p in ALIAS_PREFIXES):
        continue
      if mod in local:
        continue
      pkg = IMPORT_TO_PACKAGE.get(mod, mod)
      if pkg in declared or mod in declared:
        continue
      key = (mod, imp.source)
      if key in reported:
        continue
      reported.add(key)
      findings.append(
        Finding(
          check=self.name,
          severity="error",
          message=f"`{mod}` is imported but not declared",
          source=imp.source,
          line=imp.line,
        )
      )
    return findings