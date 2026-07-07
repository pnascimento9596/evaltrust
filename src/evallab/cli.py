"""The `evallab` command-line interface.

One command, no configuration:

    evallab audit results.json

Reads your existing eval output, audits whether its conclusion is trustworthy,
and prints the verdict. ``--strict`` makes a Low-Confidence verdict fail the
process, so an audit can gate CI the way tests do.
"""

from __future__ import annotations

import typer
from rich.console import Console

from .adapters.registry import UnknownFormatError
from .audit.runner import run_audit
from .audit.verdict import VerdictLevel
from .core.ingest import load
from .report.terminal import print_report

app = typer.Typer(add_completion=False, help="Audit whether you can trust an LLM evaluation.")
_err = Console(stderr=False)  # keep errors on stdout so they're easy to capture


@app.callback()
def main() -> None:
    """EvalLab — an auditor for LLM evaluations."""


@app.command()
def audit(
    results: str = typer.Argument(..., help="Path to your eval results (JSON or CSV)."),
    model_a: str = typer.Option(None, "--model-a", help="First model to compare."),
    model_b: str = typer.Option(None, "--model-b", help="Second model to compare."),
    alpha: float = typer.Option(0.05, "--alpha", help="Significance level."),
    seed: int = typer.Option(0, "--seed", help="Seed for reproducible resampling."),
    strict: bool = typer.Option(
        False, "--strict", help="Exit non-zero if confidence is Low."),
) -> None:
    """Audit an evaluation results file and print a confidence verdict."""
    try:
        data = load(results)
    except FileNotFoundError as e:
        _err.print(f"[red]{e}[/red]")
        raise typer.Exit(code=2)
    except UnknownFormatError as e:
        _err.print(f"[red]Unrecognised evaluation format.[/red]\n{e}")
        raise typer.Exit(code=2)

    try:
        report = run_audit(data, model_a=model_a, model_b=model_b,
                           alpha=alpha, seed=seed)
    except ValueError as e:
        _err.print(f"[red]{e}[/red]")
        raise typer.Exit(code=2)

    print_report(report)

    if strict and report.verdict.level is VerdictLevel.LOW:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
