"""EvalTrust — an auditor for LLM evaluations.

Tells you whether you can trust an evaluation's conclusion, not just what the
score is. Use the CLI (``evaltrust audit``) or this Python API:

    import evaltrust
    report = evaltrust.audit("results.json")
    print(report.verdict.level)
"""

from .api import audit
from .audit.runner import AuditReport, run_audit
from .audit.verdict import Verdict, VerdictLevel
from .core.schema import EvalData, Example, Finding, Status

__all__ = [
    "audit",
    "run_audit",
    "AuditReport",
    "Verdict",
    "VerdictLevel",
    "EvalData",
    "Example",
    "Finding",
    "Status",
]
