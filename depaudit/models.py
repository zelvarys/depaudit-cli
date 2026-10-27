"""Core data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Dependency:
  name: str
  raw: str
  constraint: str
  source: str
  line: int
  kind: str = "runtime"


@dataclass(frozen=True)
class Import:
  module: str
  source: str
  line: int


@dataclass
class Project:
  root: str
  dependencies: list[Dependency] = field(default_factory=list)
  imports: list[Import] = field(default_factory=list)
  languages: set[str] = field(default_factory=set)

  @property
  def imported_modules(self) -> set[str]:
    return {i.module for i in self.imports}


@dataclass
class SubProject:
  """A manifest and the source files it governs."""

  root: Path
  manifests: list[Path] = field(default_factory=list)
  dependencies: list[Dependency] = field(default_factory=list)
  imports: list[Import] = field(default_factory=list)
  languages: set[str] = field(default_factory=set)

  def to_project(self) -> Project:
    return Project(
      root=str(self.root),
      dependencies=list(self.dependencies),
      imports=list(self.imports),
      languages=set(self.languages),
    )


@dataclass(frozen=True)
class Finding:
  check: str
  severity: str
  message: str
  source: str = ""
  line: int = 0