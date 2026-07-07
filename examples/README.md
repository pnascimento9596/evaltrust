# Example results files

Sample inputs you can run EvalTrust against to see each kind of verdict.

| File | What it shows |
|------|---------------|
| `clean_win.json` | A large, unambiguous improvement → **High Confidence**. |
| `borderline.json` | A small, noisy improvement with repeated runs and multiple judges → **Moderate Confidence**. |
| `deepeval_gpt4.json`, `deepeval_claude.json` | Two single-model runs to compare as a pair. |

Try them:

```bash
evaltrust audit examples/clean_win.json
evaltrust audit examples/borderline.json
evaltrust audit examples/deepeval_gpt4.json examples/deepeval_claude.json
```
