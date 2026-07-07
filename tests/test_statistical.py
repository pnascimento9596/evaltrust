"""Tests for the Statistical Validity audit — EvalTrust's flagship check.

The audit produces three findings:
  - decision:   is there a real, meaningful improvement? (significant /
                equivalent / inconclusive) — never a blunt "not significant = fail"
  - effect_size: how big is it, in interpretable terms (Cohen's d, or a proportion
                effect size for binary data)
  - precision:  was the sample large enough, framed prospectively (minimum
                detectable effect), not as post-hoc power
"""

import numpy as np

from evaltrust.audit.statistical import audit_statistical_validity
from evaltrust.core.schema import EvalData, Example, Status


def make_data(a_scores, b_scores):
    examples = [
        Example(id=str(i), scores={"A": float(a), "B": float(b)})
        for i, (a, b) in enumerate(zip(a_scores, b_scores))
    ]
    return EvalData(models=["A", "B"], examples=examples,
                    source_format="test", metadata={})


def by_check(findings, check):
    (f,) = [f for f in findings if f.details.get("check") == check]
    return f


def test_produces_three_checks():
    findings = audit_statistical_validity(make_data([0] * 50, [1] * 50), "A", "B")
    assert {f.details["check"] for f in findings} == {
        "decision", "effect_size", "precision"}


def test_clean_win_is_a_significant_improvement():
    a, b = [0] * 200, [1] * 180 + [0] * 20
    findings = audit_statistical_validity(make_data(a, b), "A", "B", seed=0)
    decision = by_check(findings, "decision")
    assert decision.status is Status.PASS
    assert decision.details["outcome"] == "significant"
    assert by_check(findings, "effect_size").status is Status.PASS
    assert by_check(findings, "precision").status is Status.PASS


def test_binary_data_uses_mcnemar():
    a, b = [0] * 100, [1] * 90 + [0] * 10
    decision = by_check(
        audit_statistical_validity(make_data(a, b), "A", "B"), "decision")
    assert "McNemar" in decision.how_detected


def test_binary_effect_size_reports_proportion_difference():
    a, b = [0] * 100, [1] * 80 + [0] * 20
    effect = by_check(
        audit_statistical_validity(make_data(a, b), "A", "B"), "effect_size")
    # 80% vs 0% -> risk difference of 0.8, reported in percentage points.
    assert effect.details["risk_difference"] == 0.8
    assert "cohens_h" in effect.details


def test_tiny_symmetric_difference_is_equivalent_not_a_failure():
    # Continuous scores essentially identical (well within a 0.05 margin).
    rng = np.random.default_rng(0)
    a = rng.normal(0.5, 0.1, size=400)
    b = a + rng.normal(0.0, 0.001, size=400)
    decision = by_check(
        audit_statistical_validity(make_data(a, b), "A", "B",
                                   equivalence_margin=0.05, seed=0), "decision")
    assert decision.details["outcome"] == "equivalent"
    assert decision.status is Status.WARN


def test_underpowered_noise_is_inconclusive_not_equivalent():
    # A handful of noisy examples: can't call it a win, can't call it equivalent.
    rng = np.random.default_rng(1)
    a = rng.normal(0.5, 1.0, size=8)
    b = a + rng.normal(0.3, 1.0, size=8)
    decision = by_check(
        audit_statistical_validity(make_data(a, b), "A", "B",
                                   equivalence_margin=0.05, seed=0), "decision")
    assert decision.details["outcome"] == "inconclusive"
    assert decision.status is Status.FAIL


def test_precision_reports_minimum_detectable_effect():
    findings = audit_statistical_validity(make_data([0] * 40, [1] * 30 + [0] * 10),
                                          "A", "B")
    precision = by_check(findings, "precision")
    assert "minimum_detectable_effect" in precision.details
    assert precision.details["minimum_detectable_effect"] > 0


def test_underpowered_precision_recommends_more_examples():
    rng = np.random.default_rng(2)
    a = rng.normal(0.5, 1.0, size=8)
    b = a + rng.normal(0.2, 1.0, size=8)
    precision = by_check(
        audit_statistical_validity(make_data(a, b), "A", "B", seed=0), "precision")
    assert precision.status is Status.WARN
    assert "example" in precision.how_to_fix.lower()


def test_every_finding_obeys_the_golden_rule():
    findings = audit_statistical_validity(make_data([0] * 40, [1] * 40), "A", "B")
    for f in findings:
        assert f.why.strip() and f.how_detected.strip() and f.how_to_fix.strip()
        assert f.pillar == "Statistical Validity"


def test_is_deterministic():
    data = make_data([0] * 100, [1] * 90 + [0] * 10)
    f1 = audit_statistical_validity(data, "A", "B", seed=1)
    f2 = audit_statistical_validity(data, "A", "B", seed=1)
    assert [f.details for f in f1] == [f.details for f in f2]
