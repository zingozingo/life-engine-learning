"""Annotation API — thin adapter to teaching layer.

This module maintains backward compatibility for server.py imports.
All teaching logic lives in viz/teaching/.

API Contract (do not change signatures):
  get_annotations(level: int) -> dict[str, dict]
  get_annotation_for_event(event_type: str, level: int) -> dict | None
  get_level_info(level: int) -> dict | None
  get_all_levels() -> list[dict]
"""

from viz.teaching import (
    get_annotations,
    get_annotation_for_event,
    get_level_info,
    get_all_levels,
)

__all__ = [
    "get_annotations",
    "get_annotation_for_event",
    "get_level_info",
    "get_all_levels",
]
