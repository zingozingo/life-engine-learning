"""Level 1: Monolith Engine

All skills hardcoded in one system prompt.
No tool-based skill loading.
LLM decides everything implicitly.

This is the "kitchen sink" approach — simple but wasteful.
Every query pays the token cost for ALL skill instructions.
"""

import time

from pydantic_ai import Agent

from engines.base import BaseEngine
from shared.models import DecisionBy
from shared.skill_loader import build_monolith_prompt, load_all_skills
from shared.tools import http_fetch as _http_fetch
from shared.tools import mock_api_fetch as _mock_api_fetch
from viz.events import EventLogger


class Level1Monolith(BaseEngine):
    """Level 1 engine: everything in one giant prompt."""

    def __init__(self):
        """Initialize the monolith engine with all skills loaded."""
        super().__init__()  # Initialize base engine state
        self.logger = EventLogger(level=1)

        # Build the giant system prompt with all skills
        self.system_prompt = build_monolith_prompt()
        self.skills = load_all_skills()

        # Estimate token count (rough: ~4 chars per token)
        prompt_tokens = len(self.system_prompt) // 4

        # Create the agent with the monolith prompt
        self.agent = Agent(
            "anthropic:claude-sonnet-4-5-20250929",
            system_prompt=self.system_prompt,
        )

        # Register tools on the agent
        self._register_tools()

        # Log that we composed the prompt (once at init)
        # We'll create a dummy query_id for initialization logging
        self._init_prompt_tokens = prompt_tokens
        self._init_skills = list(self.skills.keys())

    def _register_tools(self):
        """Register tools that the LLM can call."""

        @self.agent.tool
        async def http_fetch(ctx, url: str) -> str:
            """Fetch data from a URL via HTTP GET. Use for weather API calls."""
            start = time.time()
            result = await _http_fetch(url)
            duration_ms = int((time.time() - start) * 1000)

            # Log the tool call if we have an active query
            if hasattr(self, "_current_query_id") and self._current_query_id:
                self.logger.log_tool_called(
                    self._current_query_id,
                    "http_fetch",
                    {"url": url[:100]},  # Truncate long URLs
                    result[:200] if len(result) > 200 else result,
                    DecisionBy.LLM,
                    duration_ms,
                )

            return result

        @self.agent.tool
        async def mock_api_fetch(ctx, endpoint: str, params: dict) -> str:
            """Query travel data APIs (flights, hotels, activities, currency, visa)."""
            start = time.time()
            result = _mock_api_fetch(endpoint, params)
            duration_ms = int((time.time() - start) * 1000)

            # Log the tool call if we have an active query
            if hasattr(self, "_current_query_id") and self._current_query_id:
                self.logger.log_tool_called(
                    self._current_query_id,
                    "mock_api_fetch",
                    {"endpoint": endpoint, "params": params},
                    result[:200] if len(result) > 200 else result,
                    DecisionBy.LLM,
                    duration_ms,
                )

            return result

    async def run(self, user_message: str, message_history: list) -> tuple[str, list]:
        """Process a user message and return a response.

        Args:
            user_message: The user's input text
            message_history: Previous messages in the conversation

        Returns:
            Tuple of (response_text, updated_message_history)
        """
        # Increment sequence for this query in the conversation
        self._sequence += 1

        # Estimate conversation history tokens (~4 chars per token)
        history_tokens = len(str(message_history)) // 4 if message_history else 0

        # Start query session with conversation context
        query_id = self.logger.start_query(
            user_message,
            conversation_id=self._conversation_id,
            sequence=self._sequence,
            conversation_history_tokens=history_tokens,
        )
        self._current_query_id = query_id

        try:
            # Log prompt composition (happens every query in L1)
            self.logger.log_prompt_composed(
                query_id,
                self.system_prompt,
                self._init_prompt_tokens,
                self._init_skills,
            )

            # Log tool registrations
            self.logger.log_tool_registered(query_id, "http_fetch", token_count=20)
            self.logger.log_tool_registered(query_id, "mock_api_fetch", token_count=30)

            # Log LLM request
            request_tokens = self._init_prompt_tokens + len(user_message) // 4
            self.logger.log_llm_request(
                query_id,
                "claude-sonnet-4-5-20250929",
                request_tokens,
            )

            # Run the agent
            start = time.time()
            result = await self.agent.run(user_message, message_history=message_history)
            duration_ms = int((time.time() - start) * 1000)

            # Log LLM response
            response_text = result.output
            response_tokens = len(response_text) // 4
            self.logger.log_llm_response(
                query_id,
                response_text,
                response_tokens,
                duration_ms,
            )

            # Return response and updated message history for multi-turn
            return response_text, result.all_messages()

        except Exception as e:
            self.logger.log_error(query_id, str(e), {"type": type(e).__name__})
            raise

        finally:
            self._current_query_id = None
            self.logger.end_query(query_id)

    def get_level(self) -> int:
        """Return the engine level number."""
        return 1

    def get_description(self) -> str:
        """Return a human-readable description."""
        return "Level 1: Monolith - Everything hardcoded in one prompt"

    def get_system_prompt(self) -> str:
        """Return the system prompt for inspection."""
        return self.system_prompt
