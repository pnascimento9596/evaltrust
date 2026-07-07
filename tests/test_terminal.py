"""Tests for the terminal report rendering."""

from evaltrust.audit.runner import run_audit
from evaltrust.core.schema import EvalData, Example
from evaltrust.report.terminal import render_report


def make_data(scores_by_model, n):
    examples = [
        Example(id=str(i), scores={m: float(s[i]) for m, s in scores_by_model.items()})
        for i in range(n)
    ]
    return EvalData(models=list(scores_by_model), examples=examples,
                    source_format="test", metadata={})


def test_report_shows_header_and_models():
    report = run_audit(make_data({"A": [0] * 50, "B": [1] * 50}, 50))
    out = render_report(report)
    assert "EvalTrust" in out
    assert "A" in out and "B" in out


def test_clean_win_report_shows_high_confidence():
    report = run_audit(make_data({"A": [0] * 200, "B": [1] * 180 + [0] * 20}, 200))
    out = render_report(report)
    assert "High Confidence" in out


def test_noise_report_shows_low_confidence_and_the_failing_title():
    report = run_audit(make_data({"A": [0, 1] * 60, "B": [1, 0] * 60}, 120))
    out = render_report(report)
    assert "Low Confidence" in out
    assert "not statistically significant" in out.lower()


def test_report_lists_every_pillar():
    report = run_audit(make_data({"A": [0] * 40, "B": [1] * 40}, 40))
    out = render_report(report)
    for pillar in ("Statistical Validity", "Benchmark Health",
                   "Repeatability", "Judge Reliability"):
        assert pillar in out


def test_report_explains_how_to_fix_problems():
    # Missing runs/judges produce SKIPs whose fixes should be surfaced.
    report = run_audit(make_data({"A": [0] * 40, "B": [1] * 40}, 40))
    out = render_report(report).lower()
    assert "how to fix" in out or "fix" in out
