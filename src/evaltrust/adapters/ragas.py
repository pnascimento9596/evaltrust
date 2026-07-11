"""Ragas adapter.

Reads a Ragas result export (``EvaluationResult.to_pandas()`` dumped to JSON): one
row per example, with an input column (``user_input``/``question``, ...) alongside
several per-metric score columns (``faithfulness``, ``answer_relevancy``, ...).
One RAG pipeline per run, so the score per row is the mean of its metric columns.
"""

from __future__ import annotations

import numpy as np

from ..core.schema import EvalData
from .common import Record, coerce_score, records_to_evaldata

# Columns Ragas uses for the question/contexts/answer/reference inputs, across
# both the pre- and post-0.2 naming.
_INPUT_KEYS = {
    "question", "user_input", "contexts", "retrieved_contexts", "reference_contexts",
    "answer", "response", "ground_truth", "ground_truths", "reference", "id",
}

# Ragas' built-in metric names (ragas.metrics). A row is only treated as Ragas
# output if it carries at least one of these -- an arbitrary numeric column would
# false-positive on generic wide-format data (e.g. {"question": ..., "gpt": 1}).
_METRIC_NAMES = {
    "faithfulness", "answer_relevancy", "context_precision", "context_recall",
    "context_relevancy", "context_utilization", "context_entity_recall",
    "answer_similarity", "semantic_similarity", "answer_correctness",
    "factual_correctness", "noise_sensitivity_relevant",
    "noise_sensitivity_irrelevant", "summarization_score", "coherence",
    "conciseness", "harmfulness", "maliciousness", "rouge_score", "bleu_score",
    "string_present", "exact_match",
}


def _metric_columns(row: dict) -> list[str]:
    return [k for k in row if k in _METRIC_NAMES]


def _looks_like_ragas(row: dict) -> bool:
    return (
        "model" not in row
        and bool(_INPUT_KEYS & row.keys())
        and bool(_metric_columns(row))
    )


class RagasAdapter:
    source_format = "ragas"

    def detect(self, raw) -> bool:
        return (
            isinstance(raw, list)
            and len(raw) > 0
            and isinstance(raw[0], dict)
            and _looks_like_ragas(raw[0])
        )

    def parse(self, raw) -> EvalData:
        model = "model"

        records: list[Record] = []
        skipped = 0
        for idx, row in enumerate(raw):
            score = _row_score(row)
            if score is None:
                skipped += 1
                continue
            records.append(Record(str(idx), model, score))

        if not records:
            raise ValueError("No usable Ragas metric scores found")
        return records_to_evaldata(
            records, self.source_format, {"skipped_rows": skipped})


def _row_score(row: dict) -> float | None:
    scores = []
    for key in _metric_columns(row):
        try:
            scores.append(coerce_score(row[key]))
        except ValueError:
            continue
    if scores:
        return float(np.mean(scores))
    return None
