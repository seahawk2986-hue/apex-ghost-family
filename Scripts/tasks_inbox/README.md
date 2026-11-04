# tasks_inbox — the RSEC outsource door

Drop a JSON fitness world; RSEC's next generation evolves against it.
Until then it keeps training on its builtin bench (it never starves).

## File format (strict)

```json
{
  "name": "short-world-name",
  "xs": [0.0, 0.5, ...],      // 8..256 numbers
  "ys": [1.2, 0.9, ...]       // same length, |v| < 1e6
}
```

## Rules
- `.json` only; the NEWEST valid file wins (sorted by name)
- invalid files are skipped blamelessly — never poison the lineage
- files are CONSUMED (read), never mutated by the core
- the world change is stamped on every receipt (`"task"` field) —
  a generation's score is only comparable within one world
