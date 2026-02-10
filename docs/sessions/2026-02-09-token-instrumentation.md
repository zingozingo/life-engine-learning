# Session Summary: 2026-02-09

## Token Instrumentation Overhaul

### What Was Done

1. **Replaced all estimated token counting with real API data**
   - `agent.iter()` for per-round instrumentation with real tokens from `ModelResponse.usage`
   - `count_tokens()` API at startup for exact static component measurement
   - Three-tier accuracy model: Measured → Computed → Verified

2. **Rebuilt dashboard from flat event log to narrative timeline**
   - Grouped events into STEPS: Preparation → API Call(s) → Tool Execution(s) → Total Cost
   - "Suitcase" mental model for understanding API call composition
   - Progressive disclosure with expandable breakdowns

3. **Created verification tooling**
   - `verify_tokens.py` validates all token math end-to-end
   - Checks breakdown sums match verified totals
   - Validates conversation grouping (shared conversation_id, sequential sequences)

### Key Measurements (Level 1 Monolith)

| Component | Old Estimate | Real Measured | Error |
|-----------|-------------|---------------|-------|
| System prompt (7 skills) | ~3,051 | 3,687 | -17% |
| Tool definitions (2 tools) | ~50 | 658 | -92% (13x under!) |
| API framing overhead | 0 | 7 | N/A |
| **Total static** | ~3,101 | **4,352** | -29% |

### Files Changed

- `engines/level1_monolith.py` — agent.iter(), count_tokens API, breakdown logic
- `viz/static/app.js` — narrative timeline, suitcase visualization
- `viz/static/styles.css` — token accuracy styling
- `viz/events.py` — API_CALL event type
- `shared/models.py` — round_number, token breakdown fields
- `verify_tokens.py` — new verification script
- `decisions.md` — 3 new architectural decisions

### Decisions Made

1. **Three-Tier Token Accuracy Model** — Every number is measured, computed, or verified
2. **Narrative Timeline** — Educational prose replaces flat event list
3. **Suitcase Mental Model** — Canonical analogy for API call composition

### Test Results

```
4 queries, 6 API rounds, all PASS
- Query 1: seq=1, hist=0, 4,353 tokens (simple, no tools)
- Query 2: seq=2, hist=91, 4,456 tokens (with history)
- Query 3: seq=3, hist=187, 14,791 tokens (3 rounds, weather API)
- Query 4: seq=4, hist=540, 5,498 tokens (accumulated history)

Conversation grouping: 1 conversation, 4 queries
All breakdown math: PASS
```

### Next Steps

- Level 2 implementation with selective skill loading
- Compare token costs between Level 1 and Level 2
- Add comparison view to dashboard
