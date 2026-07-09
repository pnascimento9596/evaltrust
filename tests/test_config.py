"""Tests for AuditConfig: one place for a team's statistical policy, loadable
from a config file so it can be checked into a repo."""

import pytest

from evaltrust.config import AuditConfig


def test_defaults_match_the_documented_values():
    c = AuditConfig()
    assert c.alpha == 0.05
    assert c.equivalence_margin == 0.05
    assert c.saturation_fraction == 0.95
    assert c.judge_agreement_threshold == 0.8
    assert c.judge_correlation_threshold == 0.8


def test_from_dict_ignores_unknown_keys():
    c = AuditConfig.from_dict({"alpha": 0.01, "nonsense": 123})
    assert c.alpha == 0.01


def test_correction_defaults_to_bonferroni():
    assert AuditConfig().correction == "bonferroni"


def test_correction_is_loadable_from_a_toml(tmp_path):
    (tmp_path / ".evaltrust.toml").write_text('correction = "holm"\n')
    assert AuditConfig.load(start_dir=str(tmp_path)).correction == "holm"


def test_load_reads_a_dedicated_toml(tmp_path):
    (tmp_path / ".evaltrust.toml").write_text(
        "alpha = 0.01\nequivalence_margin = 0.1\njudge_agreement_threshold = 0.9\n")
    c = AuditConfig.load(start_dir=str(tmp_path))
    assert c.alpha == 0.01
    assert c.equivalence_margin == 0.1
    assert c.judge_agreement_threshold == 0.9


def test_both_judge_thresholds_round_trip_through_dedicated_toml(tmp_path):
    # The agreement floor and the correlation floor are separate keys that both
    # load from a repo's config.
    (tmp_path / ".evaltrust.toml").write_text(
        "judge_agreement_threshold = 0.7\njudge_correlation_threshold = 0.9\n")
    c = AuditConfig.load(start_dir=str(tmp_path))
    assert c.judge_agreement_threshold == 0.7
    assert c.judge_correlation_threshold == 0.9


def test_judge_correlation_threshold_round_trips_through_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[tool.evaltrust]\njudge_correlation_threshold = 0.6\n")
    assert AuditConfig.load(start_dir=str(tmp_path)).judge_correlation_threshold == 0.6


def test_load_reads_pyproject_tool_table(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[tool.evaltrust]\nalpha = 0.02\nsaturation_fraction = 0.9\n")
    c = AuditConfig.load(start_dir=str(tmp_path))
    assert c.alpha == 0.02
    assert c.saturation_fraction == 0.9


def test_dedicated_file_wins_over_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.evaltrust]\nalpha = 0.02\n")
    (tmp_path / ".evaltrust.toml").write_text("alpha = 0.01\n")
    assert AuditConfig.load(start_dir=str(tmp_path)).alpha == 0.01


def test_load_with_no_config_returns_defaults(tmp_path):
    assert AuditConfig.load(start_dir=str(tmp_path)) == AuditConfig()


def test_explicit_path_is_read(tmp_path):
    p = tmp_path / "policy.toml"
    p.write_text("alpha = 0.005\n")
    assert AuditConfig.load(path=str(p)).alpha == 0.005
