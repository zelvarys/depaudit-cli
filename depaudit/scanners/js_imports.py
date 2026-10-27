"""Scan JS/TS files for imports (with location), respecting path aliases."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {
  ".git", "node_modules", "dist", "build", "coverage",
  ".next", ".nuxt", ".cache", "out", "target",
}

EXTENSIONS = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}

# Fallback alias prefixes common in Next.js, Vite, CRA, Nuxt
DEFAULT_ALIAS_PREFIXES = ("@/", "~/", "~~/", "@@/")

IMPORT_RE = re.compile(
  r"""(?x)
  (?:
    import \s+ (?:[\w*\s{},]+ \s+ from \s+)? ['"]([^'"]+)['"]
    |
    require \s* \( \s* ['"]([^'"]+)['"] \s* \)
    |
    import \s* \( \s* ['"]([^'"]+)['"] \s* \)
  )
  """
)


def _normalize(spec: str) -> str | None:
  if spec.startswith(".") or spec.startswith("/"):
    return None
  if spec.startswith("@"):
    # scoped npm package: @scope/name
    parts = spec.split("/")
    if len(parts) >= 2:
      return f"{parts[0]}/{parts[1]}".lower()
    return spec.lower()
  return spec.split("/", 1)[0].lower()


def _alias_prefixes(root: Path) -> tuple[str, ...]:
  """Read tsconfig.json / jsconfig.json for path aliases.

  Returns the set of alias prefixes plus the common defaults.
  We only extract the *prefix* (e.g. "@/"), not full path resolution —
  good enough to avoid false positives.
  """
  prefixes = set(DEFAULT_ALIAS_PREFIXES)
  for name in ("tsconfig.json", "jsconfig.json"):
    cfg = root / name
    if not cfg.is_file():
      continue
    try:
      data = json.loads(cfg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
      continue
    opts = (data.get("compilerOptions") or {})
    paths = opts.get("paths") or {}
    for pattern in paths:
      # pattern like "@/*" or "~/*" or "@/components/*"
      if pattern.endswith("/*"):
        prefixes.add(pattern[:-1])
    base = opts.get("baseUrl")
    if isinstance(base, str):
      # baseUrl itself doesn't create a prefix, but many projects use
      # `baseUrl: "."` + paths to alias. Nothing extra to do.
      pass
  return tuple(prefixes)


def _is_alias(spec: str, prefixes: tuple[str, ...]) -> bool:
  for p in prefixes:
    if spec.startswith(p):
      return True
  return False


@dataclass(frozen=True)
class Import:
  module: str
  source: str
  line: int


class JsImportsScanner:
  language = "javascript"

  def scan(self, root: Path) -> list[Import]:
    prefixes = _alias_prefixes(root)
    imports: list[Import] = []
    for path in root.rglob("*"):
      if not path.is_file() or path.suffix not in EXTENSIONS:
        continue
      if any(part in SKIP_DIRS for part in path.parts):
        continue
      try:
        text = path.read_text(encoding="utf-8", errors="replace")
      except OSError:
        continue
      for m in IMPORT_RE.finditer(text):
        spec = m.group(1) or m.group(2) or m.group(3)
        if not spec:
          continue
        if _is_alias(spec, prefixes):
          continue
        norm = _normalize(spec)
        if not norm:
          continue
        line = text.count("\n", 0, m.start()) + 1
        imports.append(Import(norm, str(path), line))
    return imports