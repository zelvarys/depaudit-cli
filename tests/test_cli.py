import json
from pathlib import Path

from depaudit.cli import main


def test_clean_project_exit_zero(tmp_path: Path, capsys):
  (tmp_path / "requirements.txt").write_text("requests==2.31.0\n")
  (tmp_path / "app.py").write_text("import requests\n")
  rc = main([str(tmp_path)])
  out = capsys.readouterr().out
  assert rc == 0
  assert "No issues found" in out


def test_unpinned_exit_one(tmp_path: Path, capsys):
  (tmp_path / "requirements.txt").write_text("requests\n")
  (tmp_path / "app.py").write_text("import requests\n")
  rc = main([str(tmp_path)])
  assert rc == 1
  assert "unpinned" in capsys.readouterr().out


def test_json_output_has_line(tmp_path: Path, capsys):
  (tmp_path / "requirements.txt").write_text("pandas==2.0.0\n")
  (tmp_path / "app.py").write_text("x = 1\n")
  rc = main([str(tmp_path), "--json"])
  out = capsys.readouterr().out
  assert rc == 1
  data = json.loads(out)
  assert any(item["check"] == "unused" for item in data)
  unused = next(item for item in data if item["check"] == "unused")
  assert unused["line"] == 1
  assert unused["source"].endswith("requirements.txt")


def test_online_flag_registered(tmp_path: Path, capsys, monkeypatch):
  (tmp_path / "requirements.txt").write_text("requests==2.0.0\n")
  (tmp_path / "app.py").write_text("import requests\n")

  import depaudit.cli as cli
  monkeypatch.setattr(cli, "latest_pypi", lambda name: "3.0.0")

  rc = cli.main([str(tmp_path), "--online", "--json"])
  out = capsys.readouterr().out
  assert rc == 1
  data = json.loads(out)
  assert any(item["check"] == "outdated" for item in data)


def test_missing_path(capsys):
  rc = main(["/nonexistent/path/xyz"])
  assert rc == 2


def test_no_manifest_reports_nothing(tmp_path: Path, capsys):
  (tmp_path / "app.py").write_text("import pandas\n")
  rc = main([str(tmp_path)])
  out = capsys.readouterr().out
  assert rc == 0
  assert "No dependency manifests found" in out