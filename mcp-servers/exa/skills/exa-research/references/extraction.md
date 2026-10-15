# Extracting Structured Data

Extract from titles, URLs, and snippets before fetching full pages. Fetch with `exa_web_fetch_exa` only when a value is missing, a judgment needs body context, one rich source supplies multiple fields, or the task requires reading beyond the first sentences. Batch 5-10 known URLs when practical.

## Schema Rules

1. Extract literal structured values such as names, dates, URLs, funding, and tickers; mark unavailable values as `not found` rather than guessing.
2. Map categorical values to the closest requested category and note ambiguity.
3. For semantic values, read the evidence, make the judgment, and give a brief rationale.
4. For negation claims, search for the positive case. Report `confirmed absent` only when coverage supports it; otherwise report `not found` with a confidence note.

## Evidence and Gaps

- State whether evidence is `direct`, `inferred`, or `uncertain`.
- Distinguish inaccessible or limited-coverage sources from confirmed absence.
- Explicitly flag paywalls and unreadable pages.

Return compact JSON or a markdown table, for example:

```
[{ "name": "...", "field": "...", "source": "https://...", "confidence": "direct" }]
```

Keep rows compact because they will be merged with other workstreams.
