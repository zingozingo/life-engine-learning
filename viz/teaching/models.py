"""Pydantic models for the teaching layer.

These models define the structured metadata that drives all educational
content in the dashboard — concept definitions, event annotations,
data-driven insights, and cross-level comparisons.
"""

from __future__ import annotations

from pydantic import BaseModel


class Concept(BaseModel):
    """A single thing a level teaches."""

    id: str  # e.g. "monolith_tax", "progressive_disclosure"
    label: str  # Human-readable name
    description: str  # One sentence explanation


class ForcingFunction(BaseModel):
    """What forces you to the next level."""

    trigger: str  # The problem that emerges
    observable: str  # How you notice it


class FourQuestions(BaseModel):
    """The Four Questions answered for a specific context."""

    q1_who_decides: str
    q2_what_visible: str
    q3_blast_radius: str
    q4_human_involved: str


class LevelConcept(BaseModel):
    """Complete teaching metadata for one level."""

    number: int
    name: str
    one_liner: str
    who_curates: str
    description: str  # For backward compat with LEVEL_INFO
    implemented: bool
    teaches: list[Concept]
    forces_next: ForcingFunction | None  # None for L4 (ceiling)
    four_questions: FourQuestions


class EventTeaching(BaseModel):
    """Teaching content for one event type at one level."""

    title: str
    what: str  # Plain English description
    why: str  # Why this happens at this level
    four_questions: FourQuestions
    decision_maker: str  # "code" | "llm" | "human"
    level_insight_template: str  # Template with {placeholders} for dynamic data
    # New enrichment fields (app.js will ignore these until Phase 4 wires them)
    concepts_demonstrated: list[str]  # concept IDs this event demonstrates


class Insight(BaseModel):
    """A data-driven insight generated from real measurements."""

    text: str
    measurements: dict[str, int | float]  # Named values used
    accuracy: dict[str, str]  # "measured" | "computed" | "verified" per value


class ComparisonInsight(BaseModel):
    """Cross-level comparison from real data."""

    levels: tuple[int, int]
    text: str
    what_changed: str
    measurements: dict[str, int | float]
