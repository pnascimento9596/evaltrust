# EvalLab

**An auditor for LLM evaluations.** It doesn't tell you how good your model is —
it tells you whether you can *trust* the evaluation you used to decide.

Every day teams look at "Model A: 84.7, Model B: 86.2" and ship Model B. That
number hides a dozen assumptions: maybe the difference isn't significant, maybe
the sample is too small, maybe another judge disagrees, maybe the benchmark is
saturated. Existing tools tell you *what* your score is. EvalLab tells you
**whether you should believe it.**

Think of it like a financial audit. Bookkeeping answers "what are the numbers?"
An audit answers "can you trust these numbers?" EvalLab is the audit for evals.

## Install & run (about a minute)

```bash
pip install evallab
evallab audit results.json
```

No API keys. No config. No cloud. Point it at the output of your existing eval
run and read the verdict.

```bash
evallab audit results.json          # a file that already compares 2+ models
evallab audit gpt4.json claude.json # two single-model runs (e.g. two DeepEval runs)
evallab audit results.csv --strict  # exit non-zero on Low Confidence (for CI)
evallab audit run.json --model-a gpt-4 --model-b claude   # choose the pair
```

Tools like Promptfoo compare several models in one run — audit that file directly.
Tools like DeepEval evaluate one model per run — point EvalLab at **two** files and
it pairs them by example id into an A-vs-B comparison.

## What it checks

EvalLab audits four pillars of trust and ends in one plain-language verdict —
**High / Moderate / Low Confidence** — never an arbitrary score.

| Pillar | The question it answers |
|--------|-------------------------|
| **Statistical Validity** | Is the gap real, big enough to matter, and was the sample large enough? (paired permutation test, bootstrap CI, Cohen's d, power analysis) |
| **Benchmark Health** | Can this benchmark even tell the models apart, or is it saturated / flat? |
| **Repeatability** | If you reran it, would the winner stay the winner? *(uses repeated-run data when present)* |
| **Judge Reliability** | Would a different judge reach the same verdict? *(uses multi-judge data when present)* |

Every finding follows one rule — it tells you **why it matters**, **how we
detected it**, and **how to fix it**:

```
⚠ Sample size may be too small
  Why it matters  An underpowered evaluation can miss a real difference entirely.
  How we detected With 90 examples and the observed small effect, the paired test
                  had 66% power to detect it (80% is the usual target).
  How to fix      Collect about 36 more comparable examples (~126 total) to reach
                  80% power.
```

Repeatability and Judge Reliability only need extra data (repeated runs, multiple
judges). If it isn't in your file, EvalLab doesn't guess — it tells you how to
generate that evidence.

## Input formats

EvalLab reads what your eval tool already produced — you never write a special
format. It auto-detects the shape of the file:

- **Promptfoo** results (multiple providers compared across test cases)
- **Native nested JSON** — `{"models": [...], "examples": [{"id", "scores": {...}}]}`
- **Generic record lists** — JSON like `[{"id", "model", "score"}, ...]`
- **CSV** — long (`id,model,score`) or wide (`id,gpt,claude`)

Optional per-example `runs` and `judges` unlock the repeatability and judge
checks automatically.

## Why trust the statistics

Every statistical claim EvalLab makes is validated in the test suite against an
independent reference implementation (`scipy` and `statsmodels`), and all
resampling is seeded — so the auditor is itself reproducible: the same input
always yields the same report.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT.
