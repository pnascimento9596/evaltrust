"""Paired hypothesis tests for binary (pass/fail) outcomes.

For paired binary data — the same examples scored pass/fail by two models —
McNemar's test is the textbook choice. It looks only at the *discordant* pairs
(examples where the two models disagree) and asks whether the disagreements split
evenly. That is exactly the right question, and it is what a reviewer will expect
to see for accuracy comparisons.
"""

from __future__ import annotations

from scipy import stats as _sp


def mcnemar_exact(b_only: int, a_only: int) -> float:
    """Two-sided exact McNemar p-value from the two discordant-pair counts.

    ``b_only`` is the number of examples the second model got right and the first
    got wrong; ``a_only`` is the reverse. Concordant pairs (both right or both
    wrong) carry no information and are ignored. With no discordant pairs there is
    nothing to test, so the p-value is 1.

    The exact test is a two-sided binomial test of the discordant split against
    an even 50/50 chance.
    """
    n = b_only + a_only
    if n == 0:
        return 1.0
    result = _sp.binomtest(min(b_only, a_only), n, 0.5, alternative="two-sided")
    return float(result.pvalue)
