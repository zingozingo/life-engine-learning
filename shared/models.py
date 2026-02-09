"""Pydantic models for events, query sessions, and configuration.

These models are the foundation for event logging and visualization.
All engines (L1-L5) emit events using these types, and the dashboard reads them.
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
    LLM_REQUEST = "llm_request"  # Request sent to LLM
    LLM_RESPONSE = "llm_response"  # Response received from LLM
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
    level: int = Field(ge=1, le=5, description="Engine level (1-5)")
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
    level: int = Field(ge=1, le=5, description="Engine level used")
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

        Composition events (prompt_composed, tool_registered) describe what goes
        INTO the API call. Actual events (llm_request, llm_response) represent
        real API usage. Only actual events count toward the total.
        """
        return sum(
            e.token_count or 0 for e in self.events if e.token_role == "actual"
        )


class SkillMetadata(BaseModel):
    """Metadata from a skill's YAML frontmatter.

    Used by the skill loader to discover and describe available skills.
    """

    name: str = Field(description="Skill identifier")
    description: str = Field(description="What this skill does")
    status: str = Field(
        default="active", description="active, planned, or archived"
    )
