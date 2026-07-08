"""Tests for judge calibration: when the file contains a human/gold judge, measure
how well each AI judge agrees with it (treated as ground truth)."""

from evaltrust.audit.judge_calibration import audit_judge_calibration
from evaltrust.core.schema import EvalData, Example, Status


def make(judge_examples):
    examples = []
    for i, judges in enumerate(judge_examples):
        first = next(iter(judges.values()))
        examples.append(Example(id=str(i), scores=dict(first), judges=judges))
    return EvalData(models=["A", "B"], examples=examples,
                    source_format="test", metadata={})


def by_check(findings, check="judge_calibration"):
    return [f for f in findings if f.details.get("check") == check]


def test_no_finding_without_judges():
    data = EvalData(models=["A", "B"],
                    examples=[Example("q1", {"A": 1, "B": 0})],
                    source_format="t", metadata={})
    assert audit_judge_calibration(data, "A", "B") == []


def test_no_finding_without_a_gold_judge():
    ex = [{"gpt": {"A": 1, "B": 0}, "claude": {"A": 1, "B": 0}} for _ in range(10)]
    assert audit_judge_calibration(make(ex), "A", "B") == []


def test_well_calibrated_judge_passes():
    ex = [{"gpt": {"A": 1, "B": 0}, "gold": {"A": 1, "B": 0}} for _ in range(20)]
    f = by_check(audit_judge_calibration(make(ex), "A", "B"))[0]
    assert f.status is Status.PASS
    assert f.details["accuracies"]["gpt"] == 1.0


def test_poorly_calibrated_judge_warns_and_is_named():
    ex = []
    for i in range(20):
        gold = {"A": 1, "B": 0}
        claude = gold if i % 2 == 0 else {"A": 0, "B": 1}   # disagrees half the time
        ex.append({"gold": gold, "gpt": {"A": 1, "B": 0}, "claude": claude})
    f = by_check(audit_judge_calibration(make(ex), "A", "B"))[0]
    assert f.status is Status.WARN
    assert f.details["worst_judge"] == "claude"
    assert f.pillar == "Judge Reliability"


def test_reference_judge_can_be_named_explicitly():
    ex = [{"gpt": {"A": 1, "B": 0}, "human_expert": {"A": 1, "B": 0}} for _ in range(10)]
    # 'human_expert' isn't in the default alias set, so pass it explicitly.
    findings = audit_judge_calibration(make(ex), "A", "B",
                                       reference_judge="human_expert")
    assert by_check(findings)[0].details["reference"] == "human_expert"
