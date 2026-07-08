"""Tests for embedding EvalTrust inside someone's own eval/test code.

The standalone CLI is one way to use it; the other is calling it in a script or a
pytest test and failing when the evaluation isn't trustworthy enough. `raise_if_below`
is that one-liner.
"""

import pytest

from evaltrust import UntrustworthyError, VerdictLevel, audit, audit_suite
from evaltrust.core.schema import EvalData, Example


def make_data(scores_by_model, n):
    examples = [
        Example(id=str(i), scores={m: float(s[i]) for m, s in scores_by_model.items()})
        for i in range(n)
    ]
    return EvalData(models=list(scores_by_model), examples=examples,
                    source_format="test", metadata={})


def high_report():
    return audit(make_data({"A": [0] * 200, "B": [1] * 180 + [0] * 20}, 200))


def low_report():
    return audit(make_data({"A": [0, 1] * 60, "B": [1, 0] * 60}, 120))


def test_high_confidence_passes_the_guard():
    high_report().raise_if_below("moderate")  # must not raise


def test_low_confidence_trips_the_guard():
    with pytest.raises(UntrustworthyError):
        low_report().raise_if_below("moderate")


def test_default_min_level_blocks_only_low():
    high_report().raise_if_below()          # High >= default, no raise
    with pytest.raises(UntrustworthyError):
        low_report().raise_if_below()


def test_guard_accepts_a_verdict_level_enum():
    with pytest.raises(UntrustworthyError):
        low_report().raise_if_below(VerdictLevel.HIGH)


def test_untrustworthy_error_is_an_assertion_error():
    # So pytest treats it as a clean test failure.
    assert issubclass(UntrustworthyError, AssertionError)


def test_error_message_names_the_level():
    try:
        low_report().raise_if_below("high")
    except UntrustworthyError as e:
        assert "Low Confidence" in str(e)


def test_suite_report_has_the_same_guard():
    suite = audit_suite({
        "good": make_data({"A": [0] * 200, "B": [1] * 180 + [0] * 20}, 200),
        "noise": make_data({"A": [0, 1] * 60, "B": [1, 0] * 60}, 120),
    })
    with pytest.raises(UntrustworthyError):
        suite.raise_if_below("moderate")   # overall is the weakest metric
