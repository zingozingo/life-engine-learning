"""Teaching layer orchestrator.

Maintains backward compatibility with the annotation API contract:
- get_annotations(level) -> dict[str, dict]
- get_annotation_for_event(event_type, level) -> dict | None
- get_level_info(level) -> dict | None
- get_all_levels() -> list[dict]

All teaching content comes from:
- concepts.py (what each level teaches)
- events.py (per-event teaching content)
- insights.py (data-driven insights from measurements)
- comparisons.py (cross-level analysis)
"""

from __future__ import annotations

import re
from typing import Any

from .concepts import LEVEL_CONCEPTS
from .events import EVENT_TEACHING, FUTURE_EVENTS
from .insights import get_insight_data

# Matches unfilled {placeholder} or {placeholder:format_spec} patterns
_UNFILLED_PLACEHOLDER = re.compile(r"\{[a-z_]+(?::[^}]*)?\}")


def get_level_info(level: int) -> dict[str, Any] | None:
    """Return level metadata in the contract-required shape."""
    concept = LEVEL_CONCEPTS.get(level)
    if not concept:
        return None
    return {
        # Contract-required fields
        "number": concept.number,
        "name": concept.name,
        "description": concept.description,
        "implemented": concept.implemented,
        # Enrichment (new fields — dashboard ignores until Phase 4)
        "one_liner": concept.one_liner,
        "who_curates": concept.who_curates,
        "teaches": [c.model_dump() for c in concept.teaches],
        "forces_next": concept.forces_next.model_dump() if concept.forces_next else None,
    }


def get_all_levels() -> list[dict[str, Any]]:
    """Return all level info dicts."""
    return [get_level_info(lvl) for lvl in sorted(LEVEL_CONCEPTS.keys())]


def get_annotation_for_event(
    event_type: str, level: int, session: Any = None
) -> dict[str, Any] | None:
    """Return annotation dict for a specific event at a specific level.

    Args:
        event_type: The event type string (e.g., "prompt_composed")
        level: Engine level (1-4)
        session: Optional QuerySession for data-driven insight generation

    Returns contract-compliant dict or None.
    """
    teaching = EVENT_TEACHING.get((level, event_type))
    if not teaching:
        # Check if this is a future event that doesn't exist at this level
        if event_type in FUTURE_EVENTS:
            return None
        return None

    # Build the level_insight field from template + session measurements
    level_insight = teaching.level_insight_template
    if session:
        try:
            data = get_insight_data(session)
            level_insight = teaching.level_insight_template.format(**data)
        except (KeyError, ValueError):
            pass  # Keep template as-is if data isn't available
        # Strip any surviving {placeholder} patterns so raw templates never show
        level_insight = _UNFILLED_PLACEHOLDER.sub("", level_insight)
        # Clean up double spaces left by stripped placeholders
        level_insight = re.sub(r"  +", " ", level_insight).strip()

    return {
        # Contract-required fields
        "title": teaching.title,
        "what": teaching.what,
        "why": teaching.why,
        "q1_who_decides": teaching.four_questions.q1_who_decides,
        "q2_what_visible": teaching.four_questions.q2_what_visible,
        "q3_blast_radius": teaching.four_questions.q3_blast_radius,
        "q4_human_involved": teaching.four_questions.q4_human_involved,
        "decision_maker": teaching.decision_maker,
        "level_insight": level_insight,
        # Enrichment fields
        "concepts_demonstrated": teaching.concepts_demonstrated,
    }


def get_annotations(level: int) -> dict[str, dict[str, Any]]:
    """Return all annotations for a level, keyed by event_type."""
    result: dict[str, dict[str, Any]] = {}
    for (lvl, event_type), _teaching in EVENT_TEACHING.items():
        if lvl == level:
            annotation = get_annotation_for_event(event_type, level)
            if annotation:
                result[event_type] = annotation
    return result
