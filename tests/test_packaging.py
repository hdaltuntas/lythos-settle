"""
Tests for the things a green test suite would otherwise miss: the files that
have to travel inside the wheel, the version numbers that have to agree before
a release, and the command line as a user meets it.
"""
import json
import os
import re

import lythossettle
from lythossettle import cli, forms
from lythossettle.web import server

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pyproject() -> str:
    with open(os.path.join(ROOT, "pyproject.toml"), encoding="utf-8") as fh:
        return fh.read()


def test_the_version_is_the_same_in_the_package_and_the_distribution():
    declared = re.search(r'^version\s*=\s*"([^"]+)"', pyproject(), re.MULTILINE)
    assert declared, "pyproject.toml has no version"
    assert declared.group(1) == lythossettle.__version__


def test_the_static_files_are_declared_as_package_data():
    assert '"lythossettle.web" = ["static/*"]' in pyproject()


def test_the_interface_files_the_server_serves_are_present():
    for name in ("index.html", "app.js", "style.css"):
        path = os.path.join(server.STATIC, name)
        assert os.path.isfile(path), f"{name} is missing from the package"
        assert os.path.getsize(path) > 500


def test_the_console_script_points_at_something_that_exists():
    assert 'lythos-settle = "lythossettle.cli:main"' in pyproject()
    assert callable(cli.main)


def test_the_dependencies_are_the_ones_the_program_imports():
    """Nothing in the runtime path may need a package the wheel does not ask for."""
    text = pyproject()
    for required in ("numpy", "matplotlib", "reportlab"):
        assert re.search(rf'"{required}>=', text), f"{required} is not a dependency"
    package = os.path.join(ROOT, "lythossettle")
    for folder, _, files in os.walk(package):
        for name in files:
            if name.endswith(".py"):
                source = open(os.path.join(folder, name), encoding="utf-8").read()
                assert not re.search(r"^\s*(import|from)\s+scipy", source, re.MULTILINE), name


def test_the_optional_formats_are_optional():
    """python-docx and openpyxl are extras: importing the package must not need them."""
    text = pyproject()
    assert 'docx = ["python-docx' in text and 'xlsx = ["openpyxl' in text
    hard = text.split("[project.optional-dependencies]")[0]
    for name in ("python-docx", "openpyxl"):
        assert not re.search(rf'^\s*"{name}>=[^"]*",\s*$', hard, re.MULTILINE)


def test_the_command_line_writes_runs_and_studies_a_project(tmp_path, capsys):
    path = tmp_path / "p.settle"
    assert cli.main(["example", "-o", str(path)]) == 0
    assert json.loads(path.read_text(encoding="utf-8"))["study"]["variables"]
    capsys.readouterr()
    assert cli.main(["run", str(path), "--lang", "tr"]) == 0
    assert "OTURMA ANALİZİ SONUÇLARI" in capsys.readouterr().out
    assert cli.main(["study", str(path), "-o", str(tmp_path / "s.csv")]) == 0
    assert "STUDY RESULTS" in capsys.readouterr().out
    assert (tmp_path / "s.csv").stat().st_size > 1000


def test_the_bare_command_starts_the_interface(monkeypatch):
    """`lythos-settle` with no subcommand is the documented way to start it."""
    started = {}

    def fake_serve(host, port, open_browser, lang):
        started.update(host=host, port=port, open_browser=open_browser, lang=lang)

    import lythossettle.web.server as server_module
    monkeypatch.setattr(server_module, "serve", fake_serve)
    assert cli.main([]) == 0
    assert started == {"host": "127.0.0.1", "port": cli.PORT, "open_browser": True, "lang": "en"}


def test_the_web_subcommand_takes_its_options(monkeypatch):
    started = {}

    def fake_serve(host, port, open_browser, lang):
        started.update(host=host, port=port, open_browser=open_browser, lang=lang)

    import lythossettle.web.server as server_module
    monkeypatch.setattr(server_module, "serve", fake_serve)
    assert cli.main(["web", "--host", "0.0.0.0", "--port", "9000", "--lang", "tr",
                     "--no-browser"]) == 0
    assert started == {"host": "0.0.0.0", "port": 9000, "open_browser": False, "lang": "tr"}


def test_a_refused_analysis_prints_a_message_not_a_traceback(tmp_path, capsys):
    values = forms.defaults()
    values["Df"] = 50.0                            # below the soil profile
    path = tmp_path / "impossible.settle"
    path.write_text(json.dumps(forms.project_file(values)), encoding="utf-8")
    assert cli.main(["run", str(path)]) == 1
    captured = capsys.readouterr()
    assert "Lythos Settle:" in captured.err
    assert "profile" in captured.err
    assert "Traceback" not in captured.err


def test_a_missing_project_file_is_reported_plainly(tmp_path, capsys):
    assert cli.main(["run", str(tmp_path / "nothing.settle")]) == 1
    assert "Traceback" not in capsys.readouterr().err
