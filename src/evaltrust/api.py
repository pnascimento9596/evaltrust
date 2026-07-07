"""The public Python API.

    import evaltrust

    report = evaltrust.audit("results.json")
    if report.verdict.level is evaltrust.VerdictLevel.LOW:
        raise SystemExit("Evaluation is not trustworthy enough to ship on.")

    report.to_dict()   # machine-readable, JSON-serializable

``audit`` accepts whatever you have: a path to a results file, two paths to pair
single-model files, or an already-loaded ``EvalData``.
"""

from __future__ import annotations

from .audit.runner import AuditReport, run_audit
from .core.ingest import load, load_comparison
from .core.schema import EvalData


def audit(
    source: "str | list[str] | tuple[str, ...] | EvalData",
    *,
    model_a: str | None = None,
    model_b: str | None = None,
    alpha: float = 0.05,
    seed: int = 0,
) -> AuditReport:
    """Audit an evaluation and return an :class:`AuditReport`.

    ``source`` may be:
      - a path to a results file (JSON or CSV),
      - a list/tuple of two paths to single-model files, paired by example id,
      - an :class:`EvalData` you built yourself.

    ``model_a`` / ``model_b`` choose which two models to compare (or, for the
    two-file form, label the two files).
    """
    if isinstance(source, EvalData):
        return run_audit(source, model_a=model_a, model_b=model_b,
                         alpha=alpha, seed=seed)

    if isinstance(source, (list, tuple)):
        paths = list(source)
        if len(paths) == 1:
            data = load(paths[0])
            return run_audit(data, model_a=model_a, model_b=model_b,
                             alpha=alpha, seed=seed)
        data = load_comparison(paths, label_a=model_a, label_b=model_b)
        return run_audit(data, alpha=alpha, seed=seed)

    data = load(source)
    return run_audit(data, model_a=model_a, model_b=model_b, alpha=alpha, seed=seed)
