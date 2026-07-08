"""Judge calibration — does the AI judge agree with the humans?

Most eval untrustworthiness comes from the judge, not the arithmetic. If the file
includes a human/gold judge alongside the AI judge(s), we treat it as ground truth
and measure how often each AI judge matches it. A judge that agrees with humans
only 70% of the time can't be trusted to rank models on its own.

Include your human labels as a judge named ``gold``/``human``/``reference`` (etc.),
or name the reference judge explicitly.
"""

from __future__ import annotations

from ..core.schema import EvalData, Finding, Status
from .judge_reliability import _judge_names

PILLAR = "Judge Reliability"
REFERENCE_NAMES = {"gold", "human", "humans", "reference", "ground_truth",
                   "groundtruth", "expert", "label", "truth"}


def audit_judge_calibration(
    data: EvalData,
    model_a: str,
    model_b: str,
    threshold: float = 0.8,
    reference_judge: str | None = None,
) -> list[Finding]:
    """Return a calibration finding, or [] when there's nothing to calibrate.

    Silent (returns []) when there are no judges or no reference judge — the
    general Judge Reliability check already covers the multi-judge case.
    """
    if not data.has_judges:
        return []
    judges = _judge_names(data)
    ref = reference_judge or next(
        (j for j in judges if j.lower() in REFERENCE_NAMES), None)
    if ref is None or ref not in judges:
        return []

    others = [j for j in judges if j != ref]
    accuracies: dict[str, float] = {}
    for j in others:
        matches = total = 0
        for ex in data.examples:
            if not ex.judges:
                continue
            j_scores, ref_scores = ex.judges.get(j), ex.judges.get(ref)
            if not j_scores or not ref_scores:
                continue
            for m in (model_a, model_b):
                if m in j_scores and m in ref_scores:
                    total += 1
                    matches += int(j_scores[m] == ref_scores[m])
        if total:
            accuracies[j] = matches / total

    if not accuracies:
        return []

    worst_judge = min(accuracies, key=accuracies.get)
    worst = accuracies[worst_judge]
    good = worst >= threshold
    per_judge = ", ".join(f"{j} {a:.0%}" for j, a in accuracies.items())

    return [Finding(
        pillar=PILLAR,
        title=(f"Judges track {ref}" if good
               else f"A judge disagrees with {ref}"),
        status=Status.PASS if good else Status.WARN,
        why=(
            "A judge is only trustworthy if it agrees with people. If it often "
            "disagrees with the human labels, its scores — and any ranking built "
            "on them — carry that error."
        ),
        how_detected=(
            f"Agreement with {ref} (treated as ground truth): {per_judge}."),
        how_to_fix=(
            f"The judge(s) track {ref} closely." if good else
            f"Recalibrate or replace {worst_judge}; it matches {ref} only "
            f"{worst:.0%} of the time."
        ),
        details={"check": "judge_calibration", "reference": ref,
                 "accuracies": accuracies, "worst_judge": worst_judge,
                 "worst_accuracy": worst},
    )]
