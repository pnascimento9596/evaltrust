"""Tests for comparing two audits to catch regressions between runs."""

import pytest

from evaltrust.diff import compare


def report(level, outcome):
    return {
        "verdict": {"level": level},
        "findings": [{"pillar": "Statistical Validity", "title": "t",
                      "details": {"check": "decision", "outcome": outcome}}],
    }


def suite(overall, metrics):
    return {"overall_level": overall,
            "metrics": {m: report(lvl, out) for m, (lvl, out) in metrics.items()}}


def test_no_change_is_reported_when_identical():
    d = compare(report("HIGH", "significant"), report("HIGH", "significant"))
    assert d.changes == []
    assert d.has_regression is False


def test_confidence_drop_is_a_regression():
    d = compare(report("HIGH", "significant"), report("LOW", "inconclusive"))
    assert d.has_regression is True
    regs = [c for c in d.changes if c.regression]
    assert any(c.field == "confidence" for c in regs)


def test_confidence_improvement_is_not_a_regression():
    d = compare(report("LOW", "inconclusive"), report("HIGH", "significant"))
    assert d.has_regression is False
    assert any(c.improvement for c in d.changes)


def test_losing_a_significant_win_is_a_regression():
    d = compare(report("MODERATE", "significant"), report("MODERATE", "equivalent"))
    assert any(c.field == "decision" and c.regression for c in d.changes)


def test_suite_compares_per_metric():
    old = suite("HIGH", {"correctness": ("HIGH", "significant"),
                         "safety": ("HIGH", "significant")})
    new = suite("LOW", {"correctness": ("HIGH", "significant"),
                        "safety": ("LOW", "inconclusive")})
    d = compare(old, new)
    assert d.has_regression is True
    assert any(c.scope == "safety" and c.regression for c in d.changes)
    assert not any(c.scope == "correctness" for c in d.changes)


def test_mismatched_shapes_error():
    with pytest.raises(ValueError):
        compare(report("HIGH", "significant"),
                suite("HIGH", {"m": ("HIGH", "significant")}))
