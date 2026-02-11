"""Pydantic models for events, query sessions, and configuration.

These models are the foundation for event logging and visualization.
All engines (L1-L4) emit events using these types, and the dashboard reads them.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events that can occur during query processing."""

    PROMPT_COMPOSED = "prompt_composed"  # System prompt was built
    CLASSIFIER_DECISION = "classifier_decision"  # Query was classified (L3+)
    SKILL_LOADED = "skill_loaded"  # Skill instructions loaded into context
    TOOL_REGISTERED = "tool_registered"  # Tool made available to LLM
    PROACTIVE_FETCH = "proactive_fetch"  # Data fetched before LLM runs (L4+)
    TOOL_CALLED = "tool_called"  # Tool was invoked during generation
    API_CALL = "api_call"  # One complete API round-trip with real token counts
    LLM_REQUEST = "llm_request"  # DEPRECATED: kept for backward compat with old logs
    LLM_RESPONSE = "llm_response"  # DEPRECATED: kept for backward compat with old logs
    ERROR = "error"  # Something went wrong


class DecisionBy(str, Enum):
    """Who made the decision: deterministic code or the LLM."""

    CODE = "code"
    LLM = "llm"


class EngineEvent(BaseModel):
    """A single event in the query processing timeline.

    Events are immutable records of what happened at each step.
    The dashboard uses these to visualize the flow and compare levels.
    """

    query_id: str = Field(description="UUID grouping events for one query")
    level: int = Field(ge=1, le=4, description="Engine level (1-4)")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this event occurred (UTC)",
    )
    event_type: EventType = Field(description="What kind of event this is")
    decision_by: DecisionBy = Field(description="Who made this decision")
    data: dict[str, Any] = Field(
        default_factory=dict, description="Event-specific payload"
    )
    token_count: int | None = Field(
        default=None, description="Tokens involved in this event"
    )
    token_role: str = Field(
        default="actual",
        description="Token classification: 'composition' (part of future API call), 'actual' (real API usage), 'info' (no token cost)",
    )
    round_number: int | None = Field(
        default=None,
        description="Which API round within this query (1-indexed). Only set for API_CALL events.",
    )
    duration_ms: int | None = Field(
        default=None, description="How long this step took in milliseconds"
    )


class QuerySession(BaseModel):
    """A complete query from start to finish with all events.

    Each query the user submits creates one QuerySession.
    Multiple QuerySessions share a conversation_id if they're in the same chat.
    The session is written to logs/ when the query completes.
    """

    query_id: str = Field(description="UUID for this session")
    level: int = Field(ge=1, le=4, description="Engine level used")
    query_text: str = Field(description="The user's input query")
    started_at: datetime = Field(description="When processing began (UTC)")
    ended_at: datetime | None = Field(
        default=None, description="When processing completed (UTC)"
    )
    events: list[EngineEvent] = Field(
        default_factory=list, description="All events in order"
    )
    total_tokens: int = Field(
        default=0, description="Sum of tokens across all events"
    )
    # Real token metrics (from API_CALL events)
    total_api_calls: int = Field(
        default=0, description="Number of API round-trips in this query"
    )
    total_input_tokens: int = Field(
        default=0, description="Real input tokens across all rounds (from API)"
    )
    total_output_tokens: int = Field(
        default=0, description="Real output tokens across all rounds (from API)"
    )
    # Conversation grouping fields (with defaults for backward compatibility)
    conversation_id: str | None = Field(
        default=None,
        description="UUID grouping queries in the same chat session. Defaults to query_id for legacy sessions.",
    )
    sequence: int = Field(
        default=1,
        description="Order of this query within the conversation (1, 2, 3...)",
    )
    conversation_history_tokens: int | None = Field(
        default=None,
        description="Tokens of prior conversation history sent with this query",
    )

    def compute_total_tokens(self) -> int:
        """Sum token_count from events with token_role='actual' only.

        Prefers API_CALL events (new format with real tokens).
        Falls back to LLM_REQUEST/LLM_RESPONSE for backward compat with old logs.
        """
        # Check for new API_CALL events first
        api_call_events = [e for e in self.events if e.event_type == EventType.API_CALL]
        if api_call_events:
            # Sum input_tokens + output_tokens from each API_CALL's data dict
            total = 0
            for e in api_call_events:
                total += e.data.get("input_tokens", 0)
                total += e.data.get("output_tokens", 0)
            return total

        # Fallback for old logs: sum token_count from actual events
        return sum(
            e.token_count or 0 for e in self.events if e.token_role == "actual"
        )

    def compute_token_breakdown(self) -> tuple[int, int, int]:
        """Compute (total_api_calls, total_input_tokens, total_output_tokens).

        Returns real values from API_CALL events, or (0, 0, 0) for old logs.
        """
        api_call_events = [e for e in self.events if e.event_type == EventType.API_CALL]
        if not api_call_events:
            return (0, 0, 0)

        total_input = sum(e.data.get("input_tokens", 0) for e in api_call_events)
        total_output = sum(e.data.get("output_tokens", 0) for e in api_call_events)
        return (len(api_call_events), total_input, total_output)


class SkillMetadata(BaseModel):
    """Metadata from a skill's YAML frontmatter.

    Used by the skill loader to discover and describe available skills.
    """

    name: str = Field(description="Skill identifier")
    description: str = Field(description="What this skill does")
    status: str = Field(
        default="active", description="active, planned, or archived"
    )
