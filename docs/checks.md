# Checks and methods

EvalLab groups its checks into four pillars. Each check returns a finding with a
status — **PASS**, **WARN**, **FAIL**, or **SKIP** — and the reasoning behind it.
This page documents the method and thresholds for each.

All comparisons are **paired**: the same examples are scored by both models, so
EvalLab works with per-example differences rather than comparing two noisy
averages.

## Statistical Validity

The core question: is the reported gap real evidence, or noise? Four complementary
views, each a separate finding.

### Significance — paired permutation test

Under the null hypothesis the two models are exchangeable on each example, so the
sign of every per-example difference could equally have been flipped. EvalLab
compares the observed mean against the distribution of means under random sign
flips and reports a two-sided p-value (with the standard `(count + 1) / (N + 1)`
correction, so it never reports exactly zero). This makes no normality assumption.

- **PASS** when `p < alpha` (default `0.05`).
- **FAIL** otherwise.

### Confidence interval — paired bootstrap

Resamples examples with replacement, recomputes the mean difference each time, and
takes the percentile interval (default 95%). If the interval excludes zero, the
direction of the gap is solid.

- **PASS** when the interval excludes zero.
- **WARN** when it overlaps zero (the models are statistically indistinguishable).

### Effect size — Cohen's *d*

`mean(differences) / sd(differences)`, reported with a plain-language magnitude
using conventional thresholds: negligible (`< 0.2`), small (`< 0.5`), medium
(`< 0.8`), large (`>= 0.8`). Significance says a gap is real; effect size says
whether it is big enough to matter.

- **PASS** when the effect is medium or large.
- **WARN** when it is small or negligible.

### Power / sample size

Using the observed effect and an exact noncentral-*t* model, EvalLab computes the
power the test had to detect that effect, and the number of examples needed for
80% power.

- **PASS** when achieved power is at least 80%.
- **WARN** otherwise, with a recommendation for how many more examples to collect.

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

For each rerun, EvalLab computes the mean gap between the models and checks whether
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
