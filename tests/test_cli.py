"""Tests for the `evallab audit` command."""

import json

from typer.testing import CliRunner

from evallab.cli import app

runner = CliRunner()


def write(tmp_path, name, obj):
    p = tmp_path / name
    p.write_text(json.dumps(obj))
    return str(p)


def clean_win_file(tmp_path):
    raw = {"models": ["A", "B"], "examples": [
        {"id": str(i), "scores": {"A": 0, "B": 1 if i < 180 else 0}}
        for i in range(200)]}
    return write(tmp_path, "win.json", raw)


def noise_file(tmp_path):
    raw = {"models": ["A", "B"], "examples": [
        {"id": str(i), "scores": {"A": i % 2, "B": (i + 1) % 2}}
        for i in range(120)]}
    return write(tmp_path, "noise.json", raw)


def test_audit_prints_report_and_exits_zero(tmp_path):
    result = runner.invoke(app, ["audit", clean_win_file(tmp_path)])
    assert result.exit_code == 0
    assert "EvalLab Audit" in result.stdout
    assert "High Confidence" in result.stdout


def test_missing_file_exits_nonzero_with_message(tmp_path):
    result = runner.invoke(app, ["audit", str(tmp_path / "nope.json")])
    assert result.exit_code != 0
    assert "No such" in result.stdout or "not" in result.stdout.lower()


def test_unknown_format_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["audit", write(tmp_path, "x.json", {"nope": 1})])
    assert result.exit_code != 0


def test_single_model_exits_with_helpful_message(tmp_path):
    raw = {"models": ["A"], "examples": [{"id": "1", "scores": {"A": 1}}]}
    result = runner.invoke(app, ["audit", write(tmp_path, "one.json", raw)])
    assert result.exit_code != 0
    assert "two models" in result.stdout.lower()


def test_strict_flag_fails_on_low_confidence(tmp_path):
    result = runner.invoke(app, ["audit", noise_file(tmp_path), "--strict"])
    assert result.exit_code == 1


def test_no_strict_still_exits_zero_on_low_confidence(tmp_path):
    result = runner.invoke(app, ["audit", noise_file(tmp_path)])
    assert result.exit_code == 0
    assert "Low Confidence" in result.stdout


def test_explicit_model_selection(tmp_path):
    raw = {"models": ["A", "B", "C"], "examples": [
        {"id": str(i), "scores": {"A": 0, "B": 1, "C": 0}} for i in range(30)]}
    result = runner.invoke(
        app, ["audit", write(tmp_path, "m.json", raw), "--model-a", "A", "--model-b", "C"])
    assert result.exit_code == 0
    assert "A vs C" in result.stdout or "C vs A" in result.stdout
