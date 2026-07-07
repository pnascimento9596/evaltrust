# EvalLab — Design Spec (V1)

**Date:** 2026-07-06
**Status:** Approved for implementation

## Mission

Prevent AI engineers from making model decisions based on misleading evaluation
results. EvalLab is not another eval framework, benchmark, or judge — it is an
**evaluation auditor**. It sits *after* your existing eval tool and answers one
question:

> **Is the evidence from my evaluation strong enough to justify the decision I'm about to make?**

Concretely: when someone sees "Model A: 84.7, Model B: 86.2 → ship B," EvalLab
tells them whether that conclusion is trustworthy — and if not, why, how we know,
and how to fix it.

## Scope of V1

- **Pure offline auditor.** No API keys, no network, no config. Install and run.
- **Setup:** `pip install evallab` → `evallab audit results.json`. Under a minute.
- **Terminal-only report.** Colored, readable, screenshot-able. (HTML deferred.)
- **Primary case:** comparing two models, A vs B ("should I ship B over A?").
  Single-model-vs-threshold is a subset that falls out for free.
- **Deterministic.** The auditor must itself be reproducible: all resampling uses
  a fixed seed so the same input always yields the same report. (An auditor that
  isn't reproducible has no standing to demand reproducibility.)

### The Golden Rule (every finding)

Every finding answers exactly three questions:

1. **Why is this a problem?**
2. **How did we detect it?**
3. **How do I fix it?**

No arbitrary aggregate score. The report ends in a plain-language confidence
verdict: **High / Moderate / Low**.

## Ingestion — "works with everything"

The user never writes an EvalLab schema. There is no user-facing format. EvalLab
sniffs the file, detects which tool produced it, and maps it into one **internal
canonical representation** that the audit engine consumes.

```
DeepEval  ─┐
Promptfoo ─┤
LangSmith ─┼─▶ [auto-detect + adapter] ─▶ canonical model ─▶ audit ─▶ terminal report
OpenEvals ─┤
CSV/JSON  ─┘
```

Day-one adapters (all named in the vision): **DeepEval, Promptfoo, LangSmith,
OpenEvals, and generic CSV/JSON**. Auto-detection is by structural fingerprint
(distinctive keys/columns), not file extension. Unknown formats fail loudly with
a helpful message listing what was recognized. More adapters are added over time —
that is the V3 "reliability layer" roadmap.

### Canonical model

```python
@dataclass(frozen=True)
class Example:
    id: str
    scores: dict[str, float]                       # model -> final score
    runs: dict[str, list[float]] | None = None     # model -> repeated-run scores
    judges: dict[str, dict[str, float]] | None = None  # judge -> {model -> score}

@dataclass(frozen=True)
class EvalData:
    models: list[str]
    examples: list[Example]
    source_format: str
    metadata: dict
```

`scores` is always present. `runs` and `judges` are optional — their presence
*unlocks* extra checks; their absence produces a SKIP finding that tells the user
how to generate that evidence.

## The audit engine

Each check is a pure function `EvalData -> Finding`. A `Finding` is:

```python
@dataclass(frozen=True)
class Finding:
    pillar: str
    title: str
    status: Status              # PASS | WARN | FAIL | SKIP
    why: str                    # why this matters for trusting the eval
    how_detected: str           # what we computed and observed
    how_to_fix: str             # concrete, actionable recommendation
    details: dict               # numbers backing the finding (for transparency)
```

### V1 checks (pure math on the file — no keys)

**1. Statistical Validity** — the core differentiator. Given paired per-example
scores for A and B:
- **Significance:** paired permutation test on per-example differences
  (sign-flip / label permutation). Assumption-light, exact in the limit, works
  for binary or continuous scores. Reports a p-value.
- **Confidence interval:** paired bootstrap (resample examples with replacement,
  recompute the mean difference), percentile 95% CI on B−A. If the CI straddles
  0, the two models are statistically indistinguishable.
- **Effect size:** Cohen's d on paired differences (mean diff / sd of diffs),
  with a plain-language magnitude label (negligible/small/medium/large).
- **Power / sample size:** achieved power to detect the observed effect at
  α=0.05, and the n needed for 80% power. Drives "collect ~N more examples."

**2. Benchmark Health** — from the score distribution:
- **Saturation:** scores bunched near the ceiling (both models ≈ perfect) → the
  benchmark can no longer discriminate.
- **No discrimination:** near-zero variance, or (near-)identical per-example
  scores across models → the benchmark can't tell them apart regardless of stats.

**3. Repeatability** — *only if `runs` present.* Variance across repeated runs per
model; does the A-vs-B ranking flip across reruns? Reports a stability figure.
If absent: SKIP with "add repeated runs to enable this check."

**4. Judge Reliability** — *only if `judges` present.* Inter-judge agreement
(percent agreement; Cohen's κ for two judges, Fleiss' κ for more), outlier-judge
flag, and whether the A-vs-B conclusion survives under each judge. If absent:
SKIP with "evaluate with an additional judge to enable this check."

### Deferred (need orchestration / API keys — NOT in V1)

- **Robustness** (perturb prompt wording / answer order / seed) — requires
  *re-running* the eval; impossible from a static file.
- **Reproducibility auditing** (judge/prompt/dataset/version provenance) —
  requires provenance metadata most files don't yet carry.

Theme: **V1 audits whatever evidence is in the file; where evidence is missing it
tells you how to generate it.** A SKIP is itself a useful recommendation.

## Verdict logic

Findings combine into one verdict via explicit, documented rules (not a weighted
mystery score):

- **Low confidence** — the headline claim fails: difference not significant, or
  the bootstrap CI straddles 0, or the ranking flips across reruns/judges.
- **Moderate confidence** — claim holds but with material warnings (small effect,
  underpowered sample, mild saturation, one dissenting judge).
- **High confidence** — significant, CI clear of 0, adequate power, healthy
  benchmark, and (where present) stable across reruns and judges.

The verdict names the specific findings that produced it. Nothing is a black box.

## Architecture / module layout

```
evallab/
  cli.py                  # Typer app: `evallab audit <file> [flags]`
  core/
    schema.py             # Example, EvalData, Finding, Status
    ingest.py             # detect() + load() -> EvalData
  adapters/
    base.py               # Adapter protocol: detect(raw) -> bool, parse(raw) -> EvalData
    deepeval.py  promptfoo.py  langsmith.py  openevals.py  csv_generic.py
    registry.py           # ordered adapter list + auto-detect
  audit/
    statistical.py        # significance, bootstrap CI, effect size, power
    benchmark_health.py
    repeatability.py
    judge_reliability.py
    verdict.py            # findings -> High/Moderate/Low
    runner.py             # run all applicable checks -> list[Finding]
  stats/
    resampling.py         # bootstrap_ci, permutation_test (numpy, seeded)
    effect.py             # cohens_d, magnitude label
    power.py              # achieved power, required n
    agreement.py          # percent agreement, cohen_kappa, fleiss_kappa
  report/
    terminal.py           # rich rendering of findings + verdict
```

Each module has one job and a small, testable interface. `stats/` is pure numeric
code with zero knowledge of findings or formatting — it's where correctness lives
and where the heaviest tests point.

## Dependencies (minimal, all justified)

- **numpy** — array math / resampling.
- **scipy** — reference-grade distributions for power analysis and to cross-check
  our resampling in tests. (Universal in this audience.)
- **rich** — the standard beautiful-terminal library.
- **typer** — clean single-command CLI.

Python 3.10+.

## Correctness strategy (this is the point of the project)

Test-driven, against **known-correct reference values**:

- Permutation test: symmetric/identical data → p ≈ 1; strongly separated data →
  p small. Cross-checked against `scipy.stats.wilcoxon` / paired-t for sanity.
- Bootstrap CI: identical A and B → CI contains 0; large clean separation → CI
  excludes 0. Coverage sanity via seeded synthetic data.
- Cohen's d: matches hand calculation on fixtures.
- Power / required-n: matches `statsmodels`/`scipy` reference numbers within
  tolerance.
- Agreement: κ matches textbook worked examples.
- Determinism: same input → byte-identical report (fixed seed).
- Adapters: golden fixture file per platform → expected `EvalData`.
- Graceful degradation: minimal file (scores only) → SKIP findings, never a crash.

Every public function gets a test before its implementation. The stats layer is
the non-negotiable core.

## Explicitly out of scope for V1 (YAGNI)

HTML/PDF reports, Python API, framework plugins, dashboard, org features, any
model-calling or eval-orchestration. All are later roadmap items with their own
specs.
