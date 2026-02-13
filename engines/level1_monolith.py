"""Level 1: Monolith Engine

All skills hardcoded in one system prompt.
No tool-based skill loading.
LLM decides everything implicitly.

This is the "kitchen sink" approach — simple but wasteful.
Every query pays the token cost for ALL skill instructions.
"""

import time

from anthropic import Anthropic
from pydantic_ai import Agent
from pydantic_ai._agent_graph import CallToolsNode, End
from pydantic_ai.messages import ModelResponse

from engines.base import BaseEngine
from shared.models import DecisionBy
from shared.skill_loader import build_monolith_prompt, load_all_skills
from shared.tools import http_fetch as _http_fetch
from shared.tools import mock_api_fetch as _mock_api_fetch
from shared.tools import get_current_datetime as _get_current_datetime
from viz.events import EventLogger


class Level1Monolith(BaseEngine):
    """Level 1 engine: everything in one giant prompt."""

    def __init__(self):
        """Initialize the monolith engine with all skills loaded."""
        super().__init__()  # Initialize base engine state
        self.logger = EventLogger(level=1)
        self._client = Anthropic()  # For token counting API
        self._model = "claude-sonnet-4-5-20250929"

        # Build the giant system prompt with all skills
        self.system_prompt = build_monolith_prompt()
        self.skills = load_all_skills()

        # Create the agent with the monolith prompt
        self.agent = Agent(
            f"anthropic:{self._model}",
            system_prompt=self.system_prompt,
        )

        # Register tools on the agent
        self._register_tools()

        # Measure REAL token counts for static components (one-time API calls)
        self._prompt_tokens = self._count_real_prompt_tokens()
        self._tool_tokens = self._count_real_tool_tokens()
        self._base_tokens = self._count_real_base_tokens()

        # Store for logging
        self._init_prompt_tokens = self._prompt_tokens
        self._init_tool_tokens = self._tool_tokens
        self._init_base_tokens = self._base_tokens
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
            # Note: result_tokens omitted - real growth computed from consecutive API rounds
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
            # Note: result_tokens omitted - real growth computed from consecutive API rounds
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

        @self.agent.tool
        async def get_current_datetime(ctx, timezone: str = "UTC") -> str:
            """Get current date, time, and day of week for any timezone."""
            start = time.time()
            result = _get_current_datetime(timezone)
            duration_ms = int((time.time() - start) * 1000)

            if hasattr(self, "_current_query_id") and self._current_query_id:
                self.logger.log_tool_called(
                    self._current_query_id,
                    "get_current_datetime",
                    {"timezone": timezone},
                    result[:200] if len(result) > 200 else result,
                    DecisionBy.LLM,
                    duration_ms,
                )

            return result

    def _get_tool_definitions(self) -> list[dict]:
        """Extract tool definitions in Anthropic API format from the agent."""
        tool_defs = []
        for name, tool in self.agent._function_toolset.tools.items():
            tool_defs.append({
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.function_schema.json_schema,
            })
        return tool_defs

    def _count_real_prompt_tokens(self) -> int:
        """Count exact tokens for system prompt using Anthropic API."""
        result = self._client.messages.count_tokens(
            model=self._model,
            system=self.system_prompt,
            messages=[{"role": "user", "content": "x"}],  # Minimal message
        )
        # Subtract 1 for the "x" message
        return result.input_tokens - 1

    def _count_real_tool_tokens(self) -> int:
        """Count exact tokens for tool definitions using Anthropic API."""
        tool_defs = self._get_tool_definitions()
        result = self._client.messages.count_tokens(
            model=self._model,
            system="",  # Empty system prompt
            messages=[{"role": "user", "content": "x"}],
            tools=tool_defs,
        )
        # Subtract 1 for "x" and the base overhead
        base = self._client.messages.count_tokens(
            model=self._model,
            system="",
            messages=[{"role": "user", "content": "x"}],
        )
        return result.input_tokens - base.input_tokens

    def _count_real_base_tokens(self) -> int:
        """Count base overhead tokens (API framing) using Anthropic API."""
        result = self._client.messages.count_tokens(
            model=self._model,
            system="",
            messages=[{"role": "user", "content": "x"}],
        )
        # This includes 1 token for "x" plus base overhead
        return result.input_tokens - 1

    def _count_clean_call_tokens(self, user_message: str) -> int | None:
        """Count exact tokens for this query WITHOUT conversation history.

        Returns the total input tokens if this were a fresh Round 1 call
        with just the system prompt, tools, and this user message.
        One API call (~150ms) per query.

        Returns None if the API call fails (caller must handle gracefully).
        """
        try:
            tool_defs = self._get_tool_definitions()
            result = self._client.messages.count_tokens(
                model=self._model,
                system=self.system_prompt,
                tools=tool_defs if tool_defs else None,
                messages=[{"role": "user", "content": user_message}],
            )
            return result.input_tokens
        except Exception as e:
            print(f"Warning: per-query count_tokens failed: {e}")
            return None  # Caller must handle None — do NOT fall back to estimate

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

        # Initialize per-query state
        self._current_clean_call_tokens = None
        self._current_user_msg_tokens = None
        self._current_history_tokens = 0
        self._first_round_input_tokens = None

        # Count tokens for this query without history (one API call ~150ms)
        # This gives us the exact cost of: prompt + tools + this message
        clean_call_tokens = self._count_clean_call_tokens(user_message)
        self._current_clean_call_tokens = clean_call_tokens

        # Compute user message tokens (includes ~5-7 tokens of message framing)
        if clean_call_tokens is not None:
            self._current_user_msg_tokens = (
                clean_call_tokens - self._init_prompt_tokens - self._init_tool_tokens
            )

        # Start query session with conversation context
        # Note: We'll update conversation_history_tokens after Round 1 with the real value
        query_id = self.logger.start_query(
            user_message,
            conversation_id=self._conversation_id,
            sequence=self._sequence,
            conversation_history_tokens=0,  # Will be updated after Round 1
        )
        self._current_query_id = query_id

        try:
            # Log composition events (what will be packed into the suitcase)
            # These use REAL measured token counts from init
            self.logger.log_prompt_composed(
                query_id,
                self.system_prompt,
                self._init_prompt_tokens,  # Real measured count
                self._init_skills,
            )
            # Log each tool separately (tokens split evenly since API measures combined)
            tool_names = list(self.agent._function_toolset.tools.keys())
            tokens_per_tool = self._init_tool_tokens // len(tool_names)
            remainder = self._init_tool_tokens % len(tool_names)
            for i, tool_name in enumerate(tool_names):
                # Last tool absorbs rounding remainder
                tool_tokens = tokens_per_tool + (remainder if i == len(tool_names) - 1 else 0)
                self.logger.log_tool_registered(query_id, tool_name, token_count=tool_tokens)

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

                        # After Round 1: compute exact history tokens
                        if round_num == 1:
                            self._first_round_input_tokens = round_input
                            if clean_call_tokens is not None:
                                if message_history:
                                    # History = verified_round1 - clean_call (exact)
                                    self._current_history_tokens = round_input - clean_call_tokens
                                else:
                                    self._current_history_tokens = 0

                        # Determine response type and extract tool calls
                        tool_calls = [
                            p.tool_name for p in response.parts
                            if hasattr(p, "tool_name")
                        ]
                        is_tool_call = len(tool_calls) > 0
                        response_type = "tool_call" if is_tool_call else "text"

                        # Build input breakdown with per-query measurements
                        input_breakdown = self._build_input_breakdown(
                            round_num, message_history, round_input, clean_call_tokens
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

            # Update session with REAL history tokens (not the broken sum-of-outputs)
            session = self.logger._active_sessions.get(query_id)
            if session:
                session.conversation_history_tokens = self._current_history_tokens

            # Get the final result
            result = agent_run.result

            return result.output, result.all_messages()

        except Exception as e:
            self.logger.log_error(query_id, str(e), {"type": type(e).__name__})
            raise

        finally:
            self._current_query_id = None
            # Clean up per-query state
            self._current_clean_call_tokens = None
            self._current_user_msg_tokens = None
            self._current_history_tokens = None
            self._first_round_input_tokens = None
            self.logger.end_query(query_id)

    def _build_input_breakdown(
        self, round_number: int, message_history: list, actual_input_tokens: int,
        clean_call_tokens: int | None = None
    ) -> list[dict]:
        """Build breakdown of what's in this round's input.

        Token sources:
        - System prompt: MEASURED at startup via count_tokens API
        - Tool definitions: MEASURED at startup via count_tokens API
        - User message: COMPUTED from per-query count_tokens - prompt - tools
        - Conversation history: COMPUTED from round1_verified - clean_call
        - Tool exchanges (round 2+): COMPUTED from roundN_verified - round1_verified
        - Verified total: VERIFIED from ModelResponse.usage.input_tokens

        Every number traces to a real measurement. No len//4, no hardcoding.
        """
        breakdown = []

        # System prompt — measured at startup
        breakdown.append({
            "label": f"System prompt ({len(self._init_skills)} skills)",
            "tokens": self._init_prompt_tokens,
            "is_measured": True,
            "source": "count_tokens API at startup",
        })

        # Tool definitions — measured at startup
        tool_count = len(self.agent._function_toolset.tools) if hasattr(self.agent, '_function_toolset') else 2
        breakdown.append({
            "label": f"Tool definitions ({tool_count} tools)",
            "tokens": self._init_tool_tokens,
            "is_measured": True,
            "source": "count_tokens API at startup",
        })

        if round_number == 1:
            # ROUND 1: We have clean_call and can split precisely

            if self._current_history_tokens is not None and self._current_history_tokens > 0:
                # Has conversation history
                breakdown.append({
                    "label": "Conversation history",
                    "tokens": self._current_history_tokens,
                    "is_computed": True,
                    "source": "round1_verified - clean_call",
                    "note": "All prior messages, tool calls, and results re-sent",
                })

            if self._current_user_msg_tokens is not None:
                breakdown.append({
                    "label": "Your question",
                    "tokens": self._current_user_msg_tokens,
                    "is_computed": True,
                    "source": "clean_call - prompt - tools",
                    "note": "Includes message framing",
                })
            else:
                # count_tokens failed — compute from what we have
                known = self._init_prompt_tokens + self._init_tool_tokens
                if self._current_history_tokens is not None:
                    known += self._current_history_tokens
                remainder = actual_input_tokens - known
                breakdown.append({
                    "label": "Your question + framing",
                    "tokens": max(remainder, 0),
                    "is_computed": True,
                    "source": "total - known components",
                })

            # Include clean_call_tokens for verification (Round 1 only)
            if clean_call_tokens is not None:
                breakdown.append({
                    "label": "Clean call (verification)",
                    "tokens": clean_call_tokens,
                    "is_metadata": True,
                    "source": "count_tokens(prompt + tools + this_message)",
                })

        else:
            # ROUND 2+: Everything since round 1 is tool exchange growth

            if self._first_round_input_tokens:
                growth = actual_input_tokens - self._first_round_input_tokens

                # Carry forward the round 1 dynamic content split
                if self._current_history_tokens is not None and self._current_history_tokens > 0:
                    breakdown.append({
                        "label": "Conversation history",
                        "tokens": self._current_history_tokens,
                        "is_computed": True,
                        "source": "round1_verified - clean_call",
                    })

                if self._current_user_msg_tokens is not None:
                    breakdown.append({
                        "label": "Your question",
                        "tokens": self._current_user_msg_tokens,
                        "is_computed": True,
                        "source": "clean_call - prompt - tools",
                    })

                breakdown.append({
                    "label": f"Tool exchanges (rounds 1-{round_number - 1})",
                    "tokens": growth,
                    "is_computed": True,
                    "source": f"round{round_number}_verified - round1_verified",
                    "note": "Tool calls sent + results received",
                })
            else:
                # Fallback: lump everything dynamic
                known = self._init_prompt_tokens + self._init_tool_tokens
                remainder = actual_input_tokens - known
                breakdown.append({
                    "label": "Your question + history + tool exchanges",
                    "tokens": max(remainder, 0),
                    "is_computed": True,
                    "source": "total - static components",
                })

        # Verified total — always last
        breakdown.append({
            "label": "TOTAL",
            "tokens": actual_input_tokens,
            "is_real": True,
            "source": "ModelResponse.usage.input_tokens",
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
