"""Insight generators — functions that take measurements and produce narrative.

Each generator is registered with a decorator specifying the level and concept
it applies to. The get_insight_data function extracts template placeholders
from session data for filling level_insight_template strings.
"""

from __future__ import annotations

from typing import Any, Callable

from shared.models import QuerySession
from .models import Insight

# Registry of insight generators
_generators: dict[tuple[int, str], Callable] = {}


def insight(level: int, concept: str):
    """Decorator to register an insight generator."""

    def decorator(func: Callable) -> Callable:
        _generators[(level, concept)] = func
        return func

    return decorator


def get_insights_for_session(session: QuerySession) -> list[Insight]:
    """Run all applicable insight generators for a session."""
    results = []
    for (lvl, _concept), generator in _generators.items():
        if lvl == session.level:
            try:
                result = generator(session)
                if result:
                    results.append(result)
            except Exception:
                pass  # Don't let insight generation break the dashboard
    return results


def get_insight_data(session: QuerySession) -> dict[str, Any]:
    """Extract measurement data from a session for template filling.

    Returns dict of {placeholder_name: value} for level_insight_template.
    """
    # All template keys get defaults so .format() never raises KeyError
    data: dict[str, Any] = {
        "total_input": 0,
        "total_output": 0,
        "input_pct": 0,
        "system_tokens": 0,
        "tool_tokens": 0,
        "skill_count": 0,
    }

    # From session totals (VERIFIED — from API response)
    data["total_input"] = session.total_input_tokens
    data["total_output"] = session.total_output_tokens
    total = session.total_input_tokens + session.total_output_tokens
    if total > 0:
        data["input_pct"] = (session.total_input_tokens / total) * 100

    # From events (MEASURED — from count_tokens API or engine instrumentation)
    system_events = [
        e for e in session.events if e.event_type == "prompt_composed"
    ]
    if system_events:
        data["system_tokens"] = system_events[0].token_count or 0

    tool_events = [
        e for e in session.events if e.event_type == "tool_registered"
    ]
    if tool_events:
        data["tool_tokens"] = sum(e.token_count or 0 for e in tool_events)

    skill_events = [
        e for e in session.events if e.event_type == "skill_loaded"
    ]
    if skill_events:
        data["skill_count"] = len(skill_events)

    return data


# --- Level 1 Insight Generators ---


@insight(level=1, concept="monolith_tax")
def l1_monolith_tax(session: QuerySession) -> Insight | None:
    system_events = [
        e for e in session.events if e.event_type == "prompt_composed"
    ]
    if not system_events or not system_events[0].token_count:
        return None
    system_tokens = system_events[0].token_count
    total_input = session.total_input_tokens
    if total_input == 0:
        return None
    pct = (system_tokens / total_input) * 100
    return Insight(
        text=(
            f"System prompt consumes {system_tokens:,} tokens ({pct:.0f}% of input). "
            f"This is the monolith tax — the fixed cost paid on every query, every round."
        ),
        measurements={"system_tokens": system_tokens, "total_input": total_input},
        accuracy={
            "system_tokens": "measured",
            "total_input": "verified",
            "pct": "computed",
        },
    )


@insight(level=1, concept="input_dominance")
def l1_input_dominance(session: QuerySession) -> Insight | None:
    inp = session.total_input_tokens
    out = session.total_output_tokens
    if inp + out == 0:
        return None
    pct = (inp / (inp + out)) * 100
    return Insight(
        text=(
            f"Input: {inp:,} tokens. Output: {out:,} tokens. "
            f"Input is {pct:.0f}% of total cost — the suitcase weighs far more than the postcard back."
        ),
        measurements={"input_tokens": inp, "output_tokens": out},
        accuracy={
            "input_tokens": "verified",
            "output_tokens": "verified",
            "pct": "computed",
        },
    )


@insight(level=1, concept="suitcase_model")
def l1_suitcase_growth(session: QuerySession) -> Insight | None:
    api_events = [e for e in session.events if e.event_type == "api_call"]
    if len(api_events) < 2:
        return None  # Need multiple rounds to show growth
    first_input = api_events[0].data.get("input_tokens", 0)
    last_input = api_events[-1].data.get("input_tokens", 0)
    if first_input == 0:
        return None
    growth = last_input - first_input
    return Insight(
        text=(
            f"Suitcase grew from {first_input:,} to {last_input:,} tokens across "
            f"{len(api_events)} rounds (+{growth:,}). Each round adds tool results "
            f"to the context that gets re-sent next round."
        ),
        measurements={
            "first_input": first_input,
            "last_input": last_input,
            "rounds": len(api_events),
        },
        accuracy={
            "first_input": "verified",
            "last_input": "verified",
            "rounds": "measured",
            "growth": "computed",
        },
    )
