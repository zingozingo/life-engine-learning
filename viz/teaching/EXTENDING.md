---
name: teaching
version: 1.0.0
description: How the Life Engine Learner's educational layer works and how to extend it
triggers:
  - add teaching content
  - add educational content
  - extend teaching layer
  - new level teaching
  - new overlay teaching
---

# Teaching Layer — Extension Guide

## Architecture

The teaching layer has four components in `viz/teaching/`:

| Component | File | Purpose |
|-----------|------|---------|
| Models | `models.py` | Pydantic models for all teaching data |
| Concepts | `concepts.py` | What each level teaches (structured metadata) |
| Events | `events.py` | Per-event teaching content keyed by `(level, event_type)` |
| Insights | `insights.py` | Functions that take measurements -> narrative |
| Comparisons | `comparisons.py` | Cross-level analysis (activates when data exists) |
| Adapter | `__init__.py` | Maintains API contract for dashboard |

## Adding Teaching for a New Level

When you implement Level N:

### 1. Concept Registry (`concepts.py`)
The level's entry should already exist (all 4 are pre-populated). Update `implemented=True`.

### 2. Event Teaching (`events.py`)
Add entries for each event type the level produces:
```python
(N, "event_type"): EventTeaching(
    title="...",
    what="...",
    why="...",
    four_questions=FourQuestions(...),
    decision_maker="code" | "llm" | "human",
    level_insight_template="... {placeholder} ...",
    concepts_demonstrated=["concept_id", ...],
)
```

### 3. Insight Generators (`insights.py`)
Add generator functions for level-specific measurements:
```python
@insight(level=N, concept="concept_id")
def ln_specific_insight(session: QuerySession) -> Insight | None:
    # Extract measurements from session
    # Return Insight with text, measurements, accuracy tiers
```

### 4. Comparisons (`comparisons.py`)
Add comparison functions for the new level against existing ones:
```python
@comparison(1, N)
def monolith_vs_level_n(sessions: dict[int, QuerySession]) -> ComparisonInsight | None:
    # Compare measurements between levels
```

## Adding Teaching for an Overlay

Overlays use the same event teaching system. If an overlay introduces new event types:

1. Add the event type to `shared/models.py` EventType enum
2. Add event teaching entries in `events.py` keyed by `(level, event_type)`
3. Add insight generators for overlay-specific measurements
4. Add comparison functions for "with overlay" vs "without overlay"

## Template Placeholders

The `level_insight_template` field supports these placeholders, filled from real session data:

| Placeholder | Source | Accuracy Tier |
|------------|--------|---------------|
| `{system_tokens}` | count_tokens API on system prompt | MEASURED |
| `{tool_tokens}` | count_tokens API on tool definitions | MEASURED |
| `{total_input}` | API response usage.input_tokens | VERIFIED |
| `{total_output}` | API response usage.output_tokens | VERIFIED |
| `{input_pct}` | Computed from input/(input+output) | COMPUTED |
| `{skill_count}` | Count of skill_loaded events | MEASURED |

New placeholders can be added in `insights.py:get_insight_data()`.

## The Accuracy Contract

Every number in a teaching insight must trace to one of:
- **MEASURED**: From count_tokens API or direct instrumentation
- **VERIFIED**: From Claude's API response (usage field)
- **COMPUTED**: Arithmetic from measured/verified values

Never estimate. Never hardcode. If you can't measure it, don't show a number.

## Dashboard API Contract

The adapter in `__init__.py` returns these exact dict shapes (field names cannot change):

**Level Info:** `{number, name, description, implemented}`
**Annotation:** `{title, what, why, q1_who_decides, q2_what_visible, q3_blast_radius, q4_human_involved, decision_maker, level_insight}`

Additional fields can be added (dashboard ignores unknown keys).
