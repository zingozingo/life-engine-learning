"""Event logging for engine visualization.

Provides a simple API for engines to record what happens at each step.
Events are stored as JSON files in logs/ for the dashboard to read.

Usage:
    logger = EventLogger(level=1)
    query_id = logger.start_query("What's the weather in Tokyo?")
    logger.log_prompt_composed(query_id, prompt, token_count=500, skills_included=["weather"])
    logger.log_tool_called(query_id, "http_fetch", {"url": "..."}, "sunny, 22C", DecisionBy.LLM, 150)
    logger.log_llm_response(query_id, "The weather in Tokyo is...", token_count=50, duration_ms=800)
    logger.end_query(query_id)
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from shared.models import (
    DecisionBy,
    EngineEvent,
    EventType,
    QuerySession,
)


class EventLogger:
    """Logs events during query processing for visualization.

    Each engine level creates one EventLogger instance.
    Events are collected per-query, then written to disk when the query ends.
    """

    def __init__(self, level: int, log_dir: str = "logs"):
        """Initialize the logger for a specific engine level.

        Args:
            level: Engine level (1-5)
            log_dir: Directory to write session files
        """
        self.level = level
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self._active_sessions: dict[str, QuerySession] = {}
        self._current_conversation_id: str | None = None

    def start_conversation(self) -> str:
        """Begin a new conversation that will group multiple queries.

        Returns:
            conversation_id (UUID string) to pass to start_query()
        """
        self._current_conversation_id = str(uuid.uuid4())
        return self._current_conversation_id

    def start_query(
        self,
        query_text: str,
        conversation_id: str | None = None,
        sequence: int = 1,
        conversation_history_tokens: int | None = None,
    ) -> str:
        """Begin a new query session.

        Args:
            query_text: The user's input query
            conversation_id: UUID grouping queries in same chat (defaults to query_id)
            sequence: Order within conversation (1, 2, 3...)
            conversation_history_tokens: Tokens of prior history sent with this query

        Returns:
            query_id (UUID string) for use in subsequent log calls
        """
        query_id = str(uuid.uuid4())
        # Use provided conversation_id, or fall back to query_id (single-query conversation)
        effective_conversation_id = conversation_id or query_id
        session = QuerySession(
            query_id=query_id,
            level=self.level,
            query_text=query_text,
            started_at=datetime.now(timezone.utc),
            conversation_id=effective_conversation_id,
            sequence=sequence,
            conversation_history_tokens=conversation_history_tokens,
        )
        self._active_sessions[query_id] = session
        return query_id

    def end_query(self, query_id: str) -> QuerySession:
        """Complete a query session and write to disk.

        Args:
            query_id: The session to complete

        Returns:
            The completed QuerySession

        Raises:
            KeyError: If query_id is not an active session
        """
        session = self._active_sessions.pop(query_id)
        session.ended_at = datetime.now(timezone.utc)
        session.total_tokens = session.compute_total_tokens()

        # Write to disk
        filepath = self.log_dir / f"session_{query_id}.json"
        filepath.write_text(session.model_dump_json(indent=2))

        return session

    def _log(
        self,
        query_id: str,
        event_type: EventType,
        decision_by: DecisionBy,
        data: dict,
        token_count: int | None = None,
        token_role: str = "actual",
        duration_ms: int | None = None,
    ) -> EngineEvent:
        """Internal method to create and record an event.

        Args:
            query_id: Which session this event belongs to
            event_type: What kind of event
            decision_by: Who made the decision (code or llm)
            data: Event-specific payload
            token_count: Optional token count
            token_role: 'composition', 'actual', or 'info'
            duration_ms: Optional timing

        Returns:
            The created EngineEvent

        Raises:
            KeyError: If query_id is not an active session
        """
        event = EngineEvent(
            query_id=query_id,
            level=self.level,
            event_type=event_type,
            decision_by=decision_by,
            data=data,
            token_count=token_count,
            token_role=token_role,
            duration_ms=duration_ms,
        )
        self._active_sessions[query_id].events.append(event)
        return event

    # --- Convenience methods ---

    def log_prompt_composed(
        self,
        query_id: str,
        prompt_text: str,
        token_count: int,
        skills_included: list[str],
    ) -> EngineEvent:
        """Log that the system prompt was built.

        Token role is 'composition' because the prompt is part of what gets
        sent to the LLM, not a separate API cost.
        """
        return self._log(
            query_id,
            EventType.PROMPT_COMPOSED,
            DecisionBy.CODE,
            {
                "prompt_preview": prompt_text[:200] + "..."
                if len(prompt_text) > 200
                else prompt_text,
                "prompt_length": len(prompt_text),
                "skills_included": skills_included,
            },
            token_count=token_count,
            token_role="composition",
        )

    def log_classifier_decision(
        self,
        query_id: str,
        classification: str,
        confidence: float | None,
        duration_ms: int,
    ) -> EngineEvent:
        """Log a query classification decision (L3+ only).

        Token role is 'info' - classifier runs locally, no API token cost.
        """
        return self._log(
            query_id,
            EventType.CLASSIFIER_DECISION,
            DecisionBy.CODE,
            {"classification": classification, "confidence": confidence},
            token_role="info",
            duration_ms=duration_ms,
        )

    def log_skill_loaded(
        self,
        query_id: str,
        skill_name: str,
        decision_by: DecisionBy,
        token_count: int,
    ) -> EngineEvent:
        """Log that a skill's instructions were loaded.

        Token role is 'composition' - skill content becomes part of the prompt.
        """
        return self._log(
            query_id,
            EventType.SKILL_LOADED,
            decision_by,
            {"skill_name": skill_name},
            token_count=token_count,
            token_role="composition",
        )

    def log_tool_registered(
        self, query_id: str, tool_name: str, token_count: int
    ) -> EngineEvent:
        """Log that a tool was made available to the LLM.

        Token role is 'composition' - tool definitions are sent as part of the
        API call, included in llm_request input tokens.
        """
        return self._log(
            query_id,
            EventType.TOOL_REGISTERED,
            DecisionBy.CODE,
            {"tool_name": tool_name},
            token_count=token_count,
            token_role="composition",
        )

    def log_proactive_fetch(
        self,
        query_id: str,
        source: str,
        data_summary: str,
        token_count: int,
        duration_ms: int,
    ) -> EngineEvent:
        """Log a proactive data fetch before LLM runs (L4+ only).

        Token role is 'composition' - fetched data is injected into context
        before the LLM call.
        """
        return self._log(
            query_id,
            EventType.PROACTIVE_FETCH,
            DecisionBy.CODE,
            {"source": source, "data_summary": data_summary},
            token_count=token_count,
            token_role="composition",
            duration_ms=duration_ms,
        )

    def log_tool_called(
        self,
        query_id: str,
        tool_name: str,
        parameters: dict,
        result_summary: str,
        decision_by: DecisionBy,
        duration_ms: int,
    ) -> EngineEvent:
        """Log a tool invocation during generation.

        Token role is 'info' - tool execution time is logged but the token
        cost is already accounted for in llm_request/response.
        """
        return self._log(
            query_id,
            EventType.TOOL_CALLED,
            decision_by,
            {
                "tool_name": tool_name,
                "parameters": parameters,
                "result_summary": result_summary[:200]
                if len(result_summary) > 200
                else result_summary,
            },
            token_role="info",
            duration_ms=duration_ms,
        )

    def log_llm_request(
        self, query_id: str, model: str, token_count: int
    ) -> EngineEvent:
        """Log that a request was sent to the LLM.

        Token role is 'actual' - this represents real API input token usage.
        """
        return self._log(
            query_id,
            EventType.LLM_REQUEST,
            DecisionBy.CODE,
            {"model": model},
            token_count=token_count,
            token_role="actual",
        )

    def log_llm_response(
        self,
        query_id: str,
        response_text: str,
        token_count: int,
        duration_ms: int,
    ) -> EngineEvent:
        """Log that a response was received from the LLM.

        Token role is 'actual' - this represents real API output token usage.
        """
        return self._log(
            query_id,
            EventType.LLM_RESPONSE,
            DecisionBy.CODE,
            {
                "response_preview": response_text[:200] + "..."
                if len(response_text) > 200
                else response_text,
                "response_length": len(response_text),
            },
            token_count=token_count,
            token_role="actual",
            duration_ms=duration_ms,
        )

    def log_error(
        self, query_id: str, error_message: str, detail: dict | None = None
    ) -> EngineEvent:
        """Log an error that occurred during processing.

        Token role is 'info' - errors have no token cost.
        """
        return self._log(
            query_id,
            EventType.ERROR,
            DecisionBy.CODE,
            {"error_message": error_message, "detail": detail or {}},
            token_role="info",
        )

    # --- Session loading for dashboard ---

    @classmethod
    def load_session(cls, filepath: str | Path) -> QuerySession:
        """Load a query session from a JSON file.

        Args:
            filepath: Path to session JSON file

        Returns:
            Parsed QuerySession
        """
        content = Path(filepath).read_text()
        return QuerySession.model_validate_json(content)

    @classmethod
    def load_all_sessions(cls, log_dir: str = "logs") -> list[QuerySession]:
        """Load all session files from the log directory.

        Args:
            log_dir: Directory containing session files

        Returns:
            List of QuerySessions sorted by started_at (oldest first)
        """
        log_path = Path(log_dir)
        if not log_path.exists():
            return []

        sessions = []
        for filepath in log_path.glob("session_*.json"):
            try:
                sessions.append(cls.load_session(filepath))
            except (json.JSONDecodeError, ValueError) as e:
                # Skip corrupted files, log could be added here
                print(f"Warning: Could not load {filepath}: {e}")

        return sorted(sessions, key=lambda s: s.started_at)

    @classmethod
    def load_conversations(cls, log_dir: str = "logs") -> dict[str, list[QuerySession]]:
        """Load all sessions grouped by conversation.

        Args:
            log_dir: Directory containing session files

        Returns:
            Dict mapping conversation_id to list of QuerySessions sorted by sequence
        """
        sessions = cls.load_all_sessions(log_dir)
        conversations: dict[str, list[QuerySession]] = {}

        for session in sessions:
            # For legacy sessions without conversation_id, use query_id
            conv_id = session.conversation_id or session.query_id
            if conv_id not in conversations:
                conversations[conv_id] = []
            conversations[conv_id].append(session)

        # Sort each conversation's queries by sequence number
        for conv_id in conversations:
            conversations[conv_id].sort(key=lambda s: s.sequence)

        return conversations
