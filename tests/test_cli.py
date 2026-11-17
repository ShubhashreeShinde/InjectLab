from typer.testing import CliRunner

from injectlab import __version__
from injectlab.cli import app

runner = CliRunner()


def test_help_lists_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "version" in result.output
    assert "run" in result.output


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_run_placeholder_exits_nonzero():
    result = runner.invoke(app, ["run", "configs/example.yaml"])
    assert result.exit_code == 1
