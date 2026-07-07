# Contributing to EvalLab

Thanks for your interest in improving EvalLab. This project has one job — helping
people tell trustworthy evaluations from untrustworthy ones — and contributions
that sharpen that are very welcome. The two highest-value areas are **new format
adapters** (so EvalLab reads more tools out of the box) and **new audit checks**
(so it catches more ways an evaluation can mislead).

## Development setup

EvalLab targets Python 3.10+.

```bash
git clone https://github.com/quantkyled/evallab
cd evallab
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest
```

The suite is fast (under a second) and should be green before and after your
change.

## How the codebase is organized

```
src/evallab/
  cli.py            Command-line entry point
  core/             Canonical data model, file loading, two-file pairing
  adapters/         Format detection and mapping into the canonical model
  stats/            Pure statistical primitives (resampling, effect size, power, agreement)
  audit/            The checks, the verdict logic, and the runner
  report/           Terminal rendering
```

The dependency direction is one-way: `adapters` and `audit` depend on `core` and
`stats`, never the reverse. `stats` knows nothing about findings or formatting —
it is pure numbers, and it is where correctness matters most. See
[`docs/architecture.md`](docs/architecture.md) for the full picture.

## Ground rules

**Everything is test-driven.** Write the test first, watch it fail, then write the
code to pass it. For statistical code, validate against a known-correct reference
(we use `scipy` and `statsmodels` in tests) rather than against your own
implementation.

**The auditor must be reproducible.** Any resampling takes a `seed` and produces
deterministic output. A tool that demands reproducibility has to be reproducible
itself.

**Every finding follows the Golden Rule.** A check that raises a concern must
answer three things: *why it matters*, *how we detected it*, and *how to fix it*.
Findings without all three won't be merged.

**Keep it focused.** Prefer small modules with a single responsibility. Don't add
configuration or abstraction for cases that don't exist yet.

## Adding a format adapter

This is the most common contribution. The full walkthrough is in
[`docs/adapters.md`](docs/adapters.md). In short: implement `detect()` and
`parse()`, map the format into the shared `(example, model, score)` record
pipeline, register it, and add a test with a small fixture representing the real
format.

## Adding a check

A check is a pure function from `EvalData` to a list of `Finding`s. Put the math
in `stats/` (tested against a reference), keep the interpretation in `audit/`, and
make sure the check degrades gracefully — emit a `SKIP` finding that explains how
to generate the missing data rather than crashing when the data isn't there.

## Pull requests

- Keep each PR focused on one change.
- Include tests. New behavior without a failing-first test won't be merged.
- Make sure `pytest` is green.
- Describe *what* changed and *why* in the PR description.

## Reporting bugs and requesting features

Open an issue using the templates. For bugs, a minimal results file that
reproduces the problem is worth a thousand words.
