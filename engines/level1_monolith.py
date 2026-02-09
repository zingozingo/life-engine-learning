"""Level 1: Monolith Engine

All skills hardcoded in one system prompt.
No tool-based skill loading.
LLM decides everything implicitly.

This is the "kitchen sink" approach — simple but wasteful.
Every query pays the token cost for ALL skill instructions.
"""

import time

from pydantic_ai import Agent
from pydantic_ai._agent_graph import CallToolsNode, End
from pydantic_ai.messages import ModelResponse

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

            # Estimate how many tokens this result adds to the next round's input
            result_tokens = len(result) // 4

            # Log the tool call if we have an active query
            if hasattr(self, "_current_query_id") and self._current_query_id:
                self.logger.log_tool_called(
                    self._current_query_id,
                    "http_fetch",
                    {"url": url[:100]},  # Truncate long URLs
                    result[:200] if len(result) > 200 else result,
                    DecisionBy.LLM,
                    duration_ms,
                    result_tokens=result_tokens,
                )

            return result

        @self.agent.tool
        async def mock_api_fetch(ctx, endpoint: str, params: dict) -> str:
            """Query travel data APIs (flights, hotels, activities, currency, visa)."""
            start = time.time()
            result = _mock_api_fetch(endpoint, params)
            duration_ms = int((time.time() - start) * 1000)

            # Estimate how many tokens this result adds to the next round's input
            result_tokens = len(result) // 4

            # Log the tool call if we have an active query
            if hasattr(self, "_current_query_id") and self._current_query_id:
                self.logger.log_tool_called(
                    self._current_query_id,
                    "mock_api_fetch",
                    {"endpoint": endpoint, "params": params},
                    result[:200] if len(result) > 200 else result,
                    DecisionBy.LLM,
                    duration_ms,
                    result_tokens=result_tokens,
                )

            return result

    async def run(self, user_message: str, message_history: list) -> tuple[str, list]:
        """Process a user message and return a response.

        Uses agent.iter() for per-round instrumentation with REAL token counts
        from the API instead of len/4 estimates.

        Args:
            user_message: The user's input text
            message_history: Previous messages in the conversation

        Returns:
            Tuple of (response_text, updated_message_history)
        """
        # Increment sequence for this query in the conversation
        self._sequence += 1

        # Compute real conversation history tokens from previous responses
        history_tokens = self._compute_history_tokens(message_history)

        # Start query session with conversation context
        query_id = self.logger.start_query(
            user_message,
            conversation_id=self._conversation_id,
            sequence=self._sequence,
            conversation_history_tokens=history_tokens,
        )
        self._current_query_id = query_id

        try:
            # Log composition events (what will be packed into the suitcase)
            self.logger.log_prompt_composed(
                query_id,
                self.system_prompt,
                self._init_prompt_tokens,  # Structural estimate for display
                self._init_skills,
            )
            self.logger.log_tool_registered(query_id, "http_fetch", token_count=20)
            self.logger.log_tool_registered(query_id, "mock_api_fetch", token_count=30)

            # Run with per-round instrumentation using agent.iter()
            round_num = 0
            start = time.time()
            round_start = start

            async with self.agent.iter(user_message, message_history=message_history) as agent_run:
                async for node in agent_run:
                    if isinstance(node, CallToolsNode):
                        round_num += 1
                        response = node.model_response

                        # Get REAL token counts from the API
                        round_input = response.usage.input_tokens
                        round_output = response.usage.output_tokens

                        # Determine response type and extract tool calls
                        tool_calls = [
                            p.tool_name for p in response.parts
                            if hasattr(p, "tool_name")
                        ]
                        is_tool_call = len(tool_calls) > 0
                        response_type = "tool_call" if is_tool_call else "text"

                        # Build input breakdown (structural estimates for the suitcase view)
                        input_breakdown = self._build_input_breakdown(
                            round_num, message_history, round_input
                        )

                        # Get response preview
                        response_preview = self._get_response_preview(response)

                        round_duration = int((time.time() - round_start) * 1000)
                        round_start = time.time()  # Reset for next round

                        self.logger.log_api_call(
                            query_id,
                            round_number=round_num,
                            model="claude-sonnet-4-5-20250929",
                            input_tokens=round_input,
                            output_tokens=round_output,
                            response_type=response_type,
                            response_preview=response_preview,
                            input_breakdown=input_breakdown,
                            tool_calls=tool_calls if is_tool_call else None,
                            duration_ms=round_duration,
                        )

            # Backfill total_rounds on all API_CALL events now that we know the total
            self.logger.backfill_total_rounds(query_id, round_num)

            # Get the final result
            result = agent_run.result

            return result.output, result.all_messages()

        except Exception as e:
            self.logger.log_error(query_id, str(e), {"type": type(e).__name__})
            raise

        finally:
            self._current_query_id = None
            self.logger.end_query(query_id)

    def _build_input_breakdown(
        self, round_number: int, message_history: list, actual_input_tokens: int
    ) -> list[dict]:
        """Build structural breakdown of what's in this round's input (the suitcase contents).

        These are estimates for understanding — the actual_input_tokens from the API is the truth.
        """
        breakdown = []

        # System prompt is always included
        breakdown.append({
            "label": f"System prompt ({len(self._init_skills)} skills)",
            "tokens_est": self._init_prompt_tokens,
            "note": "All skills loaded — monolith tax",
        })

        # Tool definitions always included
        breakdown.append({
            "label": "Tool definitions (2 tools)",
            "tokens_est": 50,
        })

        # Conversation history from previous queries
        if message_history:
            history_est = self._compute_history_tokens(message_history)
            breakdown.append({
                "label": "Conversation history (prior queries)",
                "tokens_est": history_est,
                "note": "Re-sent every round",
            })

        # User message (rough estimate)
        breakdown.append({
            "label": "User message",
            "tokens_est": 30,
        })

        # For round 2+, previous rounds' tool calls and results accumulate
        if round_number > 1:
            breakdown.append({
                "label": f"Tool calls + results (rounds 1-{round_number - 1})",
                "tokens_est": None,  # Hard to estimate precisely
                "note": "Previous tool interactions re-sent",
            })

        # Always include the real total as ground truth
        breakdown.append({
            "label": "ACTUAL TOTAL (from API)",
            "tokens": actual_input_tokens,
            "is_real": True,
        })

        return breakdown

    def _compute_history_tokens(self, message_history: list) -> int:
        """Compute conversation history tokens from previous ModelResponse usage data.

        For ModelResponse messages, we use the real output_tokens from the API.
        This gives us accurate history cost for multi-turn conversations.
        """
        if not message_history:
            return 0

        total = 0
        for msg in message_history:
            if isinstance(msg, ModelResponse):
                # Use real output tokens from the API
                total += msg.usage.output_tokens
            # ModelRequest content is harder to measure accurately,
            # but it's captured in the next ModelResponse.input_tokens
        return total

    def _get_response_preview(self, response: ModelResponse) -> str:
        """Extract a preview of the response content for display."""
        if not response.parts:
            return ""

        # Try to get text content first
        for part in response.parts:
            if hasattr(part, "content") and isinstance(part.content, str):
                return part.content[:300]

        # Fall back to string representation of first part
        return str(response.parts[0])[:300]

    def get_level(self) -> int:
        """Return the engine level number."""
        return 1

    def get_description(self) -> str:
        """Return a human-readable description."""
        return "Level 1: Monolith - Everything hardcoded in one prompt"

    def get_system_prompt(self) -> str:
        """Return the system prompt for inspection."""
        return self.system_prompt
