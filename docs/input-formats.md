# Input formats

You never write an EvalLab-specific format. Point the tool at whatever your eval
framework produced and it detects the shape by structure — not by file name — and
maps it into one internal representation.

```bash
evallab audit results.json
evallab audit results.csv
```

## Supported formats

### Promptfoo

Promptfoo compares several providers across the same test cases, which is exactly
the A-vs-B comparison EvalLab audits. Each provider becomes a model; each test
case becomes an example. Pass the exported results JSON directly.

### Nested JSON

A structured object with a list of examples, each carrying per-model scores:

```json
{
  "models": ["gpt-4", "claude-3"],
  "examples": [
    { "id": "q1", "scores": { "gpt-4": 1, "claude-3": 0 } },
    { "id": "q2", "scores": { "gpt-4": 0, "claude-3": 1 } }
  ]
}
```

Optional per-example `runs` and `judges` unlock the Repeatability and Judge
Reliability checks:

```json
{
  "id": "q3",
  "scores": { "gpt-4": 1, "claude-3": 1 },
  "runs":   { "gpt-4": [1, 1, 0], "claude-3": [1, 0, 1] },
  "judges": { "gpt": { "gpt-4": 1, "claude-3": 0 },
              "human": { "gpt-4": 1, "claude-3": 1 } }
}
```

### Record lists

A flat list of rows, one per (example, model). Column names are matched flexibly
(`model`/`provider`/`system`, `score`/`pass`/`success`, and so on):

```json
[
  { "id": "q1", "model": "gpt-4", "score": 1 },
  { "id": "q1", "model": "claude-3", "score": 0 }
]
```

### CSV

Long format — one row per (example, model):

```csv
id,model,score
q1,gpt-4,1
q1,claude-3,0
```

Wide format — one column per model:

```csv
question,gpt-4,claude-3
q1,1,0
q2,0,1
```

Scores can be numbers, booleans, or words like `pass`/`fail`, `true`/`false`,
`yes`/`no`, `correct`/`incorrect`.

## Single-model tools (two-file comparison)

Some tools — DeepEval, LangSmith, OpenEvals — evaluate one model per run, so a
single export contains only one model. Run each model, then pass both files:

```bash
evallab audit gpt4_run.json claude_run.json
```

EvalLab pairs the two files by example id. Each file must contain exactly one
model; a file that already has several models should be audited on its own. Model
labels default to the models' own names, falling back to the file names if those
collide, and can be overridden with `--model-a` and `--model-b`.

## When a format isn't recognized

Detection fails loudly rather than guessing. If EvalLab can't recognize a file it
tells you what it looked for, so you can reshape the data into one of the formats
above — or, better, [contribute an adapter](adapters.md) for it.
