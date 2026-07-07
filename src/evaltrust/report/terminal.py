"""Render an audit report to the terminal.

The default view is built to be read in a glance: the verdict and one line, the
checks grouped by pillar, then a short list of what to do. The full reasoning for
each flag (why it matters, how we measured it) is one `--explain` away, so the
common case stays clean and the detail is there when you want it.
"""

from __future__ import annotations

import io
from collections import OrderedDict

from rich.console import Console
from rich.text import Text

from ..audit.runner import AuditReport
from ..audit.verdict import VerdictLevel
from ..core.schema import Finding, Status

_SYMBOL = {
    Status.PASS: ("✓", "green"),
    Status.WARN: ("!", "yellow"),
    Status.FAIL: ("✗", "red"),
    Status.SKIP: ("–", "dim"),
}
_PLAIN_MARK = {Status.PASS: "ok  ", Status.WARN: "warn",
               Status.FAIL: "fail", Status.SKIP: "--  "}
_DOT = {VerdictLevel.HIGH: "green", VerdictLevel.MODERATE: "yellow",
        VerdictLevel.LOW: "red"}


def _grouped(findings) -> "OrderedDict[str, list[Finding]]":
    groups: OrderedDict[str, list[Finding]] = OrderedDict()
    for f in findings:
        groups.setdefault(f.pillar, []).append(f)
    return groups


def _subtitle(report: AuditReport) -> str:
    return (f"{report.model_a} vs {report.model_b} · "
            f"{report.n_examples} examples · {report.source_format}")


def _others(report: AuditReport) -> list[str]:
    return [m for m in report.models_available
            if m not in (report.model_a, report.model_b)]


# --------------------------------------------------------------------------- #
# Rich (colour) rendering
# --------------------------------------------------------------------------- #

def _renderable(report: AuditReport, explain: bool = False) -> Text:
    v = report.verdict
    t = Text()

    t.append("EvalTrust  ", style="bold")
    t.append(_subtitle(report) + "\n", style="dim")
    others = _others(report)
    if others:
        t.append(f"comparing the two strongest of {len(report.models_available)}; "
                 f"others: {', '.join(others)}\n", style="dim")

    t.append("\n")
    t.append("● ", style=_DOT[v.level])
    t.append(f"{v.level.value}\n", style=f"bold {_DOT[v.level]}")
    t.append(v.summary + "\n")

    for pillar, items in _grouped(report.findings).items():
        t.append(f"\n{pillar}\n", style="bold")
        for f in items:
            sym, color = _SYMBOL[f.status]
            t.append(f"  {sym} ", style=color)
            t.append(f.title, style=("dim" if f.status is Status.SKIP else ""))
            t.append("\n")

    todo = [f.how_to_fix for f in report.findings
            if f.status in (Status.WARN, Status.FAIL)]
    _bullets(t, "What to do", todo)

    optional = [f.how_to_fix for f in report.findings if f.status is Status.SKIP]
    _bullets(t, "To check more", optional, style="dim")

    if explain:
        flagged = [f for f in report.findings if f.status is not Status.PASS]
        if flagged:
            t.append("\nDetail\n", style="bold")
            for f in flagged:
                sym, color = _SYMBOL[f.status]
                t.append(f"\n  {sym} ", style=color)
                t.append(f"{f.title}\n", style="bold")
                t.append(f"    {f.why}\n", style="dim")
                t.append(f"    {f.how_detected}\n", style="dim")
    return t


def _bullets(t: Text, heading: str, items: list[str], style: str = "") -> None:
    if not items:
        return
    t.append(f"\n{heading}\n", style=(f"bold {style}" if style else "bold"))
    for item in items:
        t.append("  • ", style=style or None)
        t.append(item + "\n", style=style or None)


def render_report(report: AuditReport, explain: bool = False, width: int = 90) -> str:
    """Render the report to a plain string (used for tests and piping)."""
    console = Console(record=True, width=width, file=io.StringIO())
    console.print(_renderable(report, explain=explain))
    return console.export_text()


def print_report(report: AuditReport, explain: bool = False) -> None:
    """Print the report to the real terminal with colour."""
    Console().print(_renderable(report, explain=explain))


# --------------------------------------------------------------------------- #
# Plain ASCII rendering
# --------------------------------------------------------------------------- #

_ASCII = str.maketrans({
    "·": "-", "–": "-", "—": "-", "•": "*", "●": "*",
    "’": "'", "‘": "'", "“": '"', "”": '"', "×": "x",
})


def render_plain(report: AuditReport, explain: bool = False) -> str:
    """Render the report as plain ASCII — safe for Windows, CI logs, and pipes."""
    v = report.verdict
    lines = ["EvalTrust  " + _subtitle(report)]
    others = _others(report)
    if others:
        lines.append(f"comparing the two strongest of "
                     f"{len(report.models_available)}; others: {', '.join(others)}")
    lines += ["", f"{v.level.value.upper()}", v.summary]

    for pillar, items in _grouped(report.findings).items():
        lines.append("")
        lines.append(pillar)
        for f in items:
            lines.append(f"  [{_PLAIN_MARK[f.status]}] {f.title}")

    todo = [f.how_to_fix for f in report.findings
            if f.status in (Status.WARN, Status.FAIL)]
    if todo:
        lines += ["", "What to do"] + [f"  - {x}" for x in todo]

    optional = [f.how_to_fix for f in report.findings if f.status is Status.SKIP]
    if optional:
        lines += ["", "To check more"] + [f"  - {x}" for x in optional]

    if explain:
        flagged = [f for f in report.findings if f.status is not Status.PASS]
        if flagged:
            lines += ["", "Detail"]
            for f in flagged:
                lines += [f"  [{_PLAIN_MARK[f.status]}] {f.title}",
                          f"    {f.why}", f"    {f.how_detected}"]

    return ("\n".join(lines).rstrip() + "\n").translate(_ASCII)
