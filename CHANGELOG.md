# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-07-07

Initial release.

### Added

- `evallab audit` command: reads an evaluation results file and prints a
  High/Moderate/Low confidence verdict.
- Four audit pillars:
  - **Statistical Validity** — paired permutation test, bootstrap confidence
    interval, Cohen's *d*, and power analysis.
  - **Benchmark Health** — saturation and discrimination checks.
  - **Repeatability** — rerun stability and measurement noise (when the file
    contains repeated runs).
  - **Judge Reliability** — inter-judge consensus, agreement, and outlier
    detection (when the file contains multiple judges).
- Format auto-detection with adapters for Promptfoo, nested JSON, generic record
  lists, and CSV (long and wide).
- Two-file comparison for single-model tools (e.g. two DeepEval runs), paired by
  example id.
- `--strict` flag to fail CI on a Low-Confidence verdict.
- Deterministic, seeded resampling so audits are reproducible.

[Unreleased]: https://github.com/quantkyled/evallab/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/quantkyled/evallab/releases/tag/v0.1.0
