# Checks and methods

EvalTrust groups its checks into four pillars. Each check returns a finding with a
status — **PASS**, **WARN**, **FAIL**, or **SKIP** — and the reasoning behind it.
This page documents the method and thresholds for each.

All comparisons are **paired**: the same examples are scored by both models, so
EvalTrust works with per-example differences rather than comparing two noisy
averages.

## Statistical Validity

The core question: is the reported gap real evidence you can act on? Three
findings.

### Decision — significant, equivalent, or inconclusive

This deliberately avoids the trap of treating "not significant" as a failure
(that would confuse *absence of evidence* with *evidence of absence*). It returns
one of three honest outcomes:

- **Significant** (**PASS**) — the leader really is ahead. Detected with
  **McNemar's exact test** for paired pass/fail data, or a **paired permutation
  test** (sign-flip, two-sided, `(count + 1) / (N + 1)` correction, no normality
  assumption) for continuous scores. Triggered when `p < alpha` (default `0.05`).
- **Equivalent** (**WARN**) — a genuine conclusion that the models are the *same*
  within a margin you set. Established by a two-one-sided-tests (TOST) style check:
  the `(1 − 2·alpha)` bootstrap interval for the gap lies entirely within
  ±`equivalence_margin`. This is what lets you answer "is my cheaper model as good
  as the expensive one?".
- **Inconclusive** (**FAIL**) — not significant *and* not equivalent: there simply
  isn't enough evidence to decide. The fix is more data, not a different claim.

A bootstrap confidence interval for the gap is reported alongside all three.

### Effect size — how big, in interpretable terms

- Continuous scores: **Cohen's *d*** on the paired differences, with a magnitude
  label (negligible `< 0.2`, small `< 0.5`, medium `< 0.8`, large `≥ 0.8`).
- Pass/fail scores: the **risk difference** in percentage points plus **Cohen's
  *h***, the effect size appropriate for proportions (Cohen's *d* assumes roughly
  continuous data and is not used for 0/1 outcomes).

**PASS** when the effect is medium or large; **WARN** when small or negligible —
because a real gap can still be too small to matter in production.

### Precision — minimum detectable effect (not post-hoc power)

Rather than the widely-criticised *observed-effect* (post-hoc) power, EvalTrust
reports the **minimum detectable effect**: the smallest true effect this sample
size could reliably detect at 80% power, computed from the exact noncentral-*t*
distribution. This is a property of the design, not of the observed result.

- **PASS** when the comparison reached a conclusion (significant or equivalent) —
  the sample was adequate.
- **WARN** when inconclusive, with a prospective recommendation for how many
  examples would be needed to detect even a small effect.

## Benchmark Health

Even a flawless comparison is worthless on a broken benchmark.

### Saturation

If the strongest model already averages within 95% of the benchmark's ceiling,
there is little headroom left to demonstrate an improvement.

- **PASS** when there is headroom.
- **WARN** when the benchmark is saturated.

### Discrimination

If the pooled standard deviation of scores is below `0.01`, the benchmark assigns
nearly the same score to everything and cannot separate any two models.

- **PASS** when scores show a healthy spread.
- **WARN** when there is almost no variation.

## Repeatability

*Requires repeated-run data (`runs`). If absent, the pillar returns a single SKIP
explaining how to add it.*

### Rerun stability

For each rerun, EvalTrust computes the mean gap between the models and checks whether
the winner is consistent.

- **PASS** when the winner never changes across reruns.
- **WARN** when it changes on a minority of reruns.
- **FAIL** when it changes on half or more (the winner is effectively a coin flip).

### Measurement noise

Compares the run-to-run standard deviation of the gap against the gap itself.

- **PASS** when the gap is stable relative to its noise.
- **WARN** when the noise is as large as the gap.

## Judge Reliability

*Requires multi-judge data (`judges`). If absent, the pillar returns a single SKIP
explaining how to add it.*

### Consensus on the winner

Each judge's preferred model is computed from its mean scores.

- **PASS** when every judge prefers the same model.
- **FAIL** when judges disagree on the winner (the ranking depends on the judge).

### Inter-judge agreement

Mean pairwise agreement across judges, plus Fleiss' kappa when the scores are
categorical, and the identity of the judge that agrees least with the rest.

- **PASS** when mean agreement is at least 80%.
- **WARN** otherwise, naming the likely outlier judge.

## The verdict

The overall verdict follows simple, documented rules rather than a weighted score:

- **Low Confidence** — any check FAILs (a load-bearing part of the conclusion is
  unsupported).
- **Moderate Confidence** — no failures, but at least one WARN.
- **High Confidence** — every applicable check passes.

SKIP findings never raise confidence; they represent evidence you don't yet have.

## Assumptions and limitations

We would rather you trust EvalTrust for the right reasons than oversell it. The
current release assumes:

- **Paired data.** Both models are scored on the *same* examples, matched by id.
  Unpaired comparisons (different test sets) are out of scope.
- **One scalar score per example per model.** Multi-metric suites (several
  metrics per example) and pairwise-preference judgments (A-beats-B votes) are not
  yet modelled — audit each metric's scores separately for now.
- **A two-model comparison.** When a file has more than two models, the two
  strongest by mean are compared; there is no all-pairs sweep yet, and therefore
  no multiple-comparison correction across pairs.
- **Opinionated thresholds.** `alpha` and the equivalence margin are configurable;
  the effect-size, saturation, spread, and agreement cutoffs use conventional
  defaults that may not fit every domain.
- **Monte-Carlo methods are seeded.** Results are reproducible for a given seed,
  but a p-value or interval sitting exactly on a threshold can move slightly if
  you change the seed.

These are the honest edges of the tool. Several are on the roadmap; none are
hidden.
