<h1 align="center">EvalLab</h1>

<p align="center">
  <strong>An auditor for LLM evaluations.</strong><br>
  It doesn't tell you how good your model is — it tells you whether you can trust the evaluation you used to decide.
</p>

<p align="center">
  <a href="#installation">Install</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="#what-it-checks">What it checks</a> ·
  <a href="docs/">Docs</a> ·
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

<p align="center">
  <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-blue.svg">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-blue.svg">
  <img alt="CI" src="https://github.com/quantkyled/evallab/actions/workflows/ci.yml/badge.svg">
</p>

---

Teams spend real money evaluating models, then look at two numbers:

```
Model A: 84.7
Model B: 86.2   ->  ship B
```

That single comparison hides a dozen assumptions. Maybe the difference isn't
statistically significant. Maybe the sample is too small. Maybe another judge
disagrees, or the benchmark is already saturated. Most eval tools tell you *what*
your score is. **EvalLab tells you whether you should believe it.**

It works like a financial audit: bookkeeping answers "what are the numbers?"; an
audit answers "can you trust them?" EvalLab is the audit for evaluations. It runs
*after* your existing eval tool — it doesn't replace it.

## Example

```console
$ evallab audit gpt4_run.json claude_run.json
```

```
EvalLab Audit
Comparing claude-3 vs gpt-4  · 150 examples · source: deepeval+deepeval
╭─ Verdict ────────────────────────────────────────────────────────────────────╮
│ Low Confidence                                                               │
│ The evidence does not support the conclusion. Do not ship on this result     │
│ as-is — resolve the issues below first.                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
 ✗ Improvement is not statistically significant   Statistical Validity
 ⚠ 95% confidence interval overlaps zero          Statistical Validity
 ⚠ Effect size is negligible                      Statistical Validity
 ✓ Benchmark has headroom                         Benchmark Health

  ✗ Improvement is not statistically significant
    Why it matters   A raw gap means nothing until you rule out chance.
    How we detected  A paired permutation test over 150 examples gave p = 0.41.
    How to fix       Do not claim a winner yet. Collect more examples first.
```

Two runs at 71% and 74% — a three-point "win" that is actually noise. EvalLab
catches it before it becomes a shipping decision.

## Installation

> **Note:** EvalLab is not yet published to PyPI. Once it is, installation will be
> a single command:
>
> ```bash
> pip install evallab
> ```

Until then, install from source:

```bash
git clone https://github.com/quantkyled/evallab
cd evallab
pip install -e .
```

## Quick start

<!-- TODO: expand once the packaged release and hosted docs are live. -->

1. Run your evaluation with whatever tool you already use (DeepEval, Promptfoo,
   LangSmith, OpenEvals, or a plain CSV).
2. Point EvalLab at the output:

   ```bash
   # A file that already compares two or more models:
   evallab audit results.json

   # Two single-model runs (e.g. two DeepEval runs), paired by example id:
   evallab audit gpt4_run.json claude_run.json
   ```

3. Read the verdict. Fix what it flags. Re-run.

Useful flags:

| Flag | Effect |
|------|--------|
| `--strict` | Exit with a non-zero status on a Low-Confidence verdict (use it to gate CI). |
| `--model-a`, `--model-b` | Choose which two models to compare, or label the two files. |
| `--alpha` | Significance level (default `0.05`). |
| `--seed` | Seed for the resampling (results are deterministic; change only to stress-test). |

## What it checks

EvalLab audits four pillars of trust and ends in one plain-language verdict —
**High**, **Moderate**, or **Low Confidence**. There is no arbitrary aggregate
score.

| Pillar | The question it answers |
|--------|-------------------------|
| **Statistical Validity** | Is the gap real, large enough to matter, and was the sample big enough to detect it? Paired permutation test, bootstrap confidence interval, Cohen's *d*, and power analysis. |
| **Benchmark Health** | Can the benchmark even separate these models, or is it saturated / flat? |
| **Repeatability** | If you reran the evaluation, would the winner stay the winner? Uses repeated-run data when the file contains it. |
| **Judge Reliability** | Would a different judge reach the same verdict? Uses multi-judge data when the file contains it. |

Every finding follows the same rule — **why it matters**, **how we detected it**,
and **how to fix it**. Checks that need extra data (repeated runs, multiple
judges) don't guess when it's missing; they tell you how to generate it.

See [`docs/checks.md`](docs/checks.md) for the methods and thresholds behind each
one.

## Supported inputs

You never write an EvalLab-specific format. It reads what your tool already
produced and auto-detects the shape:

- **Promptfoo** results (several providers compared across test cases)
- **Nested JSON** — `{"models": [...], "examples": [{"id", "scores": {...}}]}`
- **Record lists** — JSON like `[{"id", "model", "score"}, ...]`
- **CSV** — long (`id,model,score`) or wide (`id,gpt,claude`)

Single-model tools (DeepEval, LangSmith, OpenEvals) evaluate one model per run,
so you pass two files and EvalLab pairs them. Details in
[`docs/input-formats.md`](docs/input-formats.md).

## How it works

```
your eval output ──▶ auto-detect + adapter ──▶ canonical model ──▶ audit ──▶ verdict
```

Adapters map every format into one internal representation, so the statistics are
written once and work everywhere. Every statistical method is validated in the
test suite against an independent reference (`scipy` and `statsmodels`), and all
resampling is seeded, so the auditor is itself reproducible. See
[`docs/architecture.md`](docs/architecture.md).

## Roadmap

- **Now:** offline CLI, four pillars, terminal report.
- **Next:** dedicated adapters for more tools, a Python API (`evallab.audit(...)`),
  and an optional HTML report.
- **Later:** opt-in orchestration for the pillars that need to generate evidence
  (robustness perturbations, extra judges) and a provenance/reproducibility check.

## Contributing

Contributions are welcome — new format adapters and additional checks especially.
Start with [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

[MIT](LICENSE).
