"""LangSmith adapter.

LangSmith evaluates one experiment (one model/variant) per run export, so a
single export contains one model — you compare two experiments with
``evaltrust audit expA.json expB.json``. This adapter reads a LangSmith run
list (one dict per run, as returned by ``Client.list_runs`` or the runs query
API): each run is grouped by ``reference_example_id`` and scored from its
``feedback_stats``.

Per run the score is the mean across whatever feedback metrics are present —
LangSmith has no single dominant pass/fail field the way DeepEval has
``success``. Runs with no ``reference_example_id`` (not part of the evaluated
dataset) are skipped. The raw schema carries no experiment/session name, so
the model is left generic; the file name supplies the label when pairing two
runs.
"""

from __future__ import annotations

import numpy as np

from ..core.schema import EvalData
from .common import Record, coerce_score, records_to_evaldata


class LangSmithAdapter:
    source_format = "langsmith"

    def detect(self, raw) -> bool:
        return (
            isinstance(raw, list)
            and len(raw) > 0
            and isinstance(raw[0], dict)
            and "reference_example_id" in raw[0]
            and "feedback_stats" in raw[0]
        )

    def parse(self, raw) -> EvalData:
        model = "model"

        records: list[Record] = []
        for run in raw:
            ref_id = run.get("reference_example_id")
            if ref_id is None:
                continue
            records.append(Record(str(ref_id), model, _run_score(run)))

        if not records:
            raise ValueError(
                "No LangSmith runs with a reference_example_id found")
        return records_to_evaldata(records, self.source_format)


def _run_score(run: dict) -> float:
    stats = run.get("feedback_stats") or {}
    scores = [coerce_score(s["avg"]) for s in stats.values() if s.get("avg") is not None]
    if scores:
        return float(np.mean(scores))
    raise ValueError(f"LangSmith run {run.get('id', '?')} has no feedback scores")
