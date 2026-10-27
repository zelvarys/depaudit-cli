from depaudit.checks.duplicate import DuplicateCheck
from depaudit.checks.stdlib_shadow import StdlibShadowCheck
from depaudit.checks.unpinned import UnpinnedCheck
from depaudit.checks.unused import UnusedCheck
from depaudit.models import Dependency, Import, Project


def make_project(deps=(), imports=(), languages=("python",)):
  return Project(
    root=".",
    dependencies=list(deps),
    imports=list(imports),
    languages=set(languages),
  )


def dep(name, constraint="", kind="runtime", line=1):
  return Dependency(
    name=name, raw=name, constraint=constraint,
    source="requirements.txt", line=line, kind=kind,
  )


def imp(name, source="app.py", line=1):
  return Import(module=name, source=source, line=line)


def test_unpinned():
  p = make_project(deps=[dep("requests")])
  assert len(UnpinnedCheck().run(p)) == 1


def test_pinned_ok():
  p = make_project(deps=[dep("requests", "==2.31.0")])
  assert UnpinnedCheck().run(p) == []


def test_unused():
  p = make_project(deps=[dep("requests", "==2.31.0")], imports=[])
  assert len(UnusedCheck().run(p)) == 1


def test_used_ok():
  p = make_project(
    deps=[dep("requests", "==2.31.0")],
    imports=[imp("requests")],
  )
  assert UnusedCheck().run(p) == []


def test_dev_deps_not_flagged_unused():
  p = make_project(deps=[dep("pytest", "==7", kind="dev")], imports=[])
  assert UnusedCheck().run(p) == []


def test_stdlib_shadow():
  p = make_project(deps=[dep("json", "==1")])
  assert len(StdlibShadowCheck().run(p)) == 1


def test_duplicate_different_constraints():
  p = make_project(deps=[dep("requests", "==2.0"), dep("requests", "==2.1")])
  assert len(DuplicateCheck().run(p)) == 1


def test_duplicate_same_constraint_ok():
  p = make_project(deps=[dep("requests", "==2.0"), dep("requests", "==2.0")])
  assert DuplicateCheck().run(p) == []