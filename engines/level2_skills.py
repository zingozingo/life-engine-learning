"""Level 2: Skills + Generic Tools Engine

Progressive disclosure via load_skill tool.
LLM sees skill summaries, loads details on demand.
All generic tools always available.

This is where the LLM starts curating its own context.
Instead of paying for ALL skill instructions on every query,
it loads only the skills it needs — when it decides it needs them.
"""

import time

from anthropic import Anthropic
from pydantic_ai import Agent
from pydantic_ai._agent_graph import CallToolsNode, End
from pydantic_ai.messages import ModelResponse

from engines.base import BaseEngine
from shared.models import DecisionBy, EventType
from shared.skill_loader import (
    build_skill_menu,
    list_skill_files as _list_skill_files,
    load_all_skills,
    load_skill_detail,
    read_skill_file as _read_skill_file,
)
from shared.tools import get_current_datetime as _get_current_datetime
from shared.tools import http_fetch as _http_fetch
from shared.tools import mock_api_fetch as _mock_api_fetch
from viz.events import EventLogger


class Level2SkillsEngine(BaseEngine):
    """Level 2 engine: LLM loads skills on demand via tools."""

    def __init__(self):
        """Initialize the skills engine with skill menu and 6 tools."""
        super().__init__()
        self.logger = EventLogger(level=2)
        self._client = Anthropic()
        self._model = "claude-sonnet-4-5-20250929"

        # Build the lighter system prompt (menu, not full instructions)
        self.skills = load_all_skills()
        skill_menu = build_skill_menu()
        self.system_prompt = self._build_system_prompt(skill_menu)

        # Create the agent with the skill menu prompt
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

    def _build_system_prompt(self, skill_menu: str) -> str:
        """Build the L2 system prompt with skill menu and tool instructions."""
        return "\n".join([
            "# Travel Concierge Assistant",
            "",
            "You are an expert travel concierge assistant. You help users plan trips, "
            "find flights and hotels, check weather, convert currencies, understand visa "
            "requirements, and create packing lists.",
            "",
            "## Available Tools",
            "",
            "- `http_fetch(url)`: Fetch data from any URL (used for weather API)",
            "- `mock_api_fetch(endpoint, params)`: Query travel data APIs (flights, hotels, etc.)",
            "- `get_current_datetime(timezone)`: Get current date, time, and day of week",
            "",
            "## Skills",
            "",
            skill_menu,
            "",
            "## How to Use Skills",
            "",
            "When a user asks about a topic, ALWAYS call `load_skill(skill_name)` to read "
            "the full instructions for the relevant skill BEFORE answering. The skill menu "
            "above only shows summaries — the full instructions contain critical details "
            "about tool usage, parameters, and response formatting.",
            "",
            "If you need even more detail (API references, formatting guides), call "
            "`list_skill_files(skill_name)` to see what reference files are available, "
            "then `read_skill_file(skill_name, file_path)` to load them.",
        ])

    def _register_tools(self):
        """Register the 6 tools that the LLM can call."""

        # --- Skill discovery tools (L2-specific) ---

        @self.agent.tool
        async def load_skill(ctx, skill_name: str) -> str:
            """Load full instructions for a skill. Call this BEFORE using any skill."""
            start = time.time()
            result = load_skill_detail(skill_name)
            duration_ms = int((time.time() - start) * 1000)

            # Log as SKILL_LOADED with disclosure_level=2 (SKILL.md body)
            # Uses _log() directly for richer data dict and token_role="info"
            if hasattr(self, "_current_query_id") and self._current_query_id:
                self.logger._log(
                    self._current_query_id,
                    EventType.SKILL_LOADED,
                    DecisionBy.LLM,
                    {
                        "skill_name": skill_name,
                        "disclosure_level": 2,
                        "content_preview": result[:200] if len(result) > 200 else result,
                    },
                    token_count=0,
                    token_role="info",
                    duration_ms=duration_ms,
                )

            return result

        @self.agent.tool
        async def list_skill_files(ctx, skill_name: str) -> str:
            """List reference files available for a skill."""
            start = time.time()
            files = _list_skill_files("skills", skill_name)
            duration_ms = int((time.time() - start) * 1000)

            result = "\n".join(files) if files else "No reference files available."

            # Log as TOOL_CALLED (not SKILL_LOADED — this is just listing, not loading)
            if hasattr(self, "_current_query_id") and self._current_query_id:
                self.logger.log_tool_called(
                    self._current_query_id,
                    "list_skill_files",
                    {"skill_name": skill_name},
                    result,
                    DecisionBy.LLM,
                    duration_ms,
                )

            return result

        @self.agent.tool
        async def read_skill_file(ctx, skill_name: str, file_path: str) -> str:
            """Read a reference file from a skill directory for detailed information."""
            start = time.time()
            result = _read_skill_file("skills", skill_name, file_path)
            duration_ms = int((time.time() - start) * 1000)

            # Log as SKILL_LOADED with disclosure_level=3 (reference file)
            # Uses _log() directly for richer data dict and token_role="info"
            if hasattr(self, "_current_query_id") and self._current_query_id:
                self.logger._log(
                    self._current_query_id,
                    EventType.SKILL_LOADED,
                    DecisionBy.LLM,
                    {
                        "skill_name": skill_name,
                        "disclosure_level": 3,
                        "file_path": file_path,
                        "content_preview": result[:200] if len(result) > 200 else result,
                    },
                    token_count=0,
                    token_role="info",
                    duration_ms=duration_ms,
                )

            return result

        # --- Generic tools (same as L1) ---

        @self.agent.tool
        async def http_fetch(ctx, url: str) -> str:
            """Fetch data from a URL via HTTP GET. Use for weather API calls."""
            start = time.time()
            result = await _http_fetch(url)
            duration_ms = int((time.time() - start) * 1000)

            if hasattr(self, "_current_query_id") and self._current_query_id:
                self.logger.log_tool_called(
                    self._current_query_id,
                    "http_fetch",
                    {"url": url[:100]},
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
            messages=[{"role": "user", "content": "x"}],
        )
        return result.input_tokens - 1

    def _count_real_tool_tokens(self) -> int:
        """Count exact tokens for tool definitions using Anthropic API."""
        tool_defs = self._get_tool_definitions()
        result = self._client.messages.count_tokens(
            model=self._model,
            system="",
            messages=[{"role": "user", "content": "x"}],
            tools=tool_defs,
        )
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
            return None

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
        clean_call_tokens = self._count_clean_call_tokens(user_message)
        self._current_clean_call_tokens = clean_call_tokens

        # Compute user message tokens (includes ~5-7 tokens of message framing)
        if clean_call_tokens is not None:
            self._current_user_msg_tokens = (
                clean_call_tokens - self._init_prompt_tokens - self._init_tool_tokens
            )

        # Start query session with conversation context
        query_id = self.logger.start_query(
            user_message,
            conversation_id=self._conversation_id,
            sequence=self._sequence,
            conversation_history_tokens=0,
        )
        self._current_query_id = query_id

        try:
            # Log composition events (what will be packed into the suitcase)
            self.logger.log_prompt_composed(
                query_id,
                self.system_prompt,
                self._init_prompt_tokens,
                self._init_skills,
            )
            # Log each tool separately (tokens split evenly since API measures combined)
            tool_names = list(self.agent._function_toolset.tools.keys())
            tokens_per_tool = self._init_tool_tokens // len(tool_names)
            remainder = self._init_tool_tokens % len(tool_names)
            for i, tool_name in enumerate(tool_names):
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
                        round_start = time.time()

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

            # Update session with REAL history tokens
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
        """
        breakdown = []

        # System prompt — measured at startup
        breakdown.append({
            "label": f"System prompt (skill menu, {len(self._init_skills)} skills)",
            "tokens": self._init_prompt_tokens,
            "is_measured": True,
            "source": "count_tokens API at startup",
        })

        # Tool definitions — measured at startup
        tool_count = len(self.agent._function_toolset.tools) if hasattr(self.agent, '_function_toolset') else 6
        breakdown.append({
            "label": f"Tool definitions ({tool_count} tools)",
            "tokens": self._init_tool_tokens,
            "is_measured": True,
            "source": "count_tokens API at startup",
        })

        if round_number == 1:
            if self._current_history_tokens is not None and self._current_history_tokens > 0:
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

            if clean_call_tokens is not None:
                breakdown.append({
                    "label": "Clean call (verification)",
                    "tokens": clean_call_tokens,
                    "is_metadata": True,
                    "source": "count_tokens(prompt + tools + this_message)",
                })

        else:
            if self._first_round_input_tokens:
                growth = actual_input_tokens - self._first_round_input_tokens

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

    def _get_response_preview(self, response: ModelResponse) -> str:
        """Extract a preview of the response content for display."""
        if not response.parts:
            return ""

        for part in response.parts:
            if hasattr(part, "content") and isinstance(part.content, str):
                return part.content[:300]

        return str(response.parts[0])[:300]

    def get_level(self) -> int:
        """Return the engine level number."""
        return 2

    def get_description(self) -> str:
        """Return a human-readable description."""
        return "Skills + Generic Tools (Progressive Disclosure)"

    def get_system_prompt(self) -> str:
        """Return the system prompt for inspection."""
        return self.system_prompt
