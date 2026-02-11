"""Cross-level comparison engine.

Comparison generators activate only when real data from multiple levels
exists. Each generator is registered with the levels it compares.
"""

from __future__ import annotations

from typing import Callable

from shared.models import QuerySession
from .models import ComparisonInsight

# Registry of comparison generators
_comparisons: list[Callable] = []


def comparison(*levels: int):
    """Decorator to register a comparison generator for specific level pairs."""

    def decorator(func: Callable) -> Callable:
        func._levels = levels  # type: ignore[attr-defined]
        _comparisons.append(func)
        return func

    return decorator


def get_comparisons(
    sessions: dict[int, QuerySession],
) -> list[ComparisonInsight]:
    """Run all applicable comparisons given available session data."""
    results = []
    available_levels = set(sessions.keys())
    for comp_func in _comparisons:
        required = set(comp_func._levels)  # type: ignore[attr-defined]
        if required.issubset(available_levels):
            try:
                result = comp_func(sessions)
                if result:
                    results.append(result)
            except Exception:
                pass
    return results


@comparison(1, 2)
def monolith_vs_skills(
    sessions: dict[int, QuerySession],
) -> ComparisonInsight | None:
    l1, l2 = sessions[1], sessions[2]
    if l1.total_input_tokens == 0:
        return None
    delta = l1.total_input_tokens - l2.total_input_tokens
    pct = (delta / l1.total_input_tokens) * 100
    return ComparisonInsight(
        levels=(1, 2),
        text=(
            f"Same query. L1: {l1.total_input_tokens:,} tokens. "
            f"L2: {l2.total_input_tokens:,} tokens. "
            f"Progressive disclosure saved {delta:,} tokens ({pct:.0f}%)."
        ),
        what_changed="L2 loaded only the relevant skill details instead of all skills",
        measurements={
            "l1_input": l1.total_input_tokens,
            "l2_input": l2.total_input_tokens,
        },
    )


# More comparisons added as levels are built:
# @comparison(1, 3) — monolith vs classifier
# @comparison(2, 3) — implicit vs explicit routing
# @comparison(1, 4) — monolith vs adaptive (the full journey)
