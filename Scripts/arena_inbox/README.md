# arena_inbox — the RREASON strategy door

Drop a reasoning arena; RREASON evolves its inference strategies
(debate / synth / refine / styles) against YOUR gold answers.
Empty depot = the builtin bench (deterministic, gold computed in-file).

## File format (strict)

```json
{
  "name": "short-arena-name",
  "items": [
    {"q": "What is 17 * 3 + 8?", "a": "59"},
    {"q": "How many letter 'e' in 'telescope'?", "a": "3"}
  ]
}
```

## Rules
- minimum 2 items; the newest valid file wins
- gold answers are yours to own: plain strings or numbers
- grading is honest-normalized (exact match, numeric equality, or
  high token overlap on the extracted 'ANSWER:' line)
- difficulty is what-evolves: too easy and cheap strategies win on
  cost; hard arenas force the swarm to buy its accuracy with seats
- invalid files are skipped blamelessly; nothing is ever minted
