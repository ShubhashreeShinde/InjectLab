"""Command-line entry point.

What this does: defines the `injectlab` command with placeholder subcommands.
Real commands (run, summary, report, ...) are added in later components.
"""

import typer

from injectlab import __version__

app = typer.Typer(help="InjectLab: measure how well defenses stop prompt injection.")


@app.callback()
def main() -> None:
    """InjectLab command group (keeps subcommands listed even with only one)."""


@app.command()
def version() -> None:
    """Print the installed InjectLab version."""
    typer.echo(f"injectlab {__version__}")


@app.command()
def run(config: str = typer.Argument(..., help="Path to a YAML config (added in C6).")) -> None:
    """Placeholder: run an experiment from a YAML config."""
    typer.echo(f"Not implemented yet (C6). Would run: {config}")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
