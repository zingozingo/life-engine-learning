# Architectural Decisions Log

This file tracks key architectural decisions for the Life Engine Learning project.
Format: Date, decision title, and brief explanation of the choice and rationale.

---

## 2025-02-07: Initial Architecture

**Decision**: Pydantic AI agent with progressive disclosure skill system, MCP integration via `call_mcp_tool` bridge pattern, Logfire for observability.

**Details**:
- Skills use YAML frontmatter + Markdown body for metadata and instructions
- Agent sees only skill names/descriptions initially, calls `load_skill()` for details
- MCP servers wrapped behind a single generic `call_mcp_tool()` rather than exposing raw MCP tools
- Logfire auto-instrumentation for tracing all agent runs and tool calls

---

## 2025-02-07: Skill Status Cleanup

**Decision**: Math and database skills marked as `status: planned`. Only filesystem, time, and weather skills are currently active.

**Details**:
- Math skill references an MCP server that was built for learning but is now archived
- Database skill was defined aspirationally but never implemented
- Adding `status` field to frontmatter allows skill_loader to potentially filter in future
- Active skills: filesystem (MCP), time (native tool), weather (http_request)

---

## 2025-02-07: Pivot to Travel Concierge Theme

**Decision**: Restructured project around 5 engine levels (monolith → skills → classifier → adaptive → MCP) sharing common skills and tools.

**Details**:
- Custom event logging with FastAPI dashboard for visualization
- Old chatbot code archived to archive/v1_original/
- Goal: master implicit vs explicit routing and proactive vs reactive data fetching through visual comparison
- New skills: weather, flights, hotels, activities, currency, visa, packing
- See docs/SPEC.md for full architecture specification

---

## 2025-02-08: Developer Experience

**Decision**: Makefile for project commands (chat, dashboard, start, stop). FastAPI + uvicorn for dashboard server. Process management via PID files.

**Details**:
- `make dashboard` starts dashboard as a persistent background service
- `make chat` runs chatbot independently of dashboard
- `make start` ensures dashboard is running, then starts chat
- `make stop` is the only way to kill the dashboard
- FastAPI serves dashboard UI and session API endpoints
- Session data accessed via EventLogger.load_all_sessions()

---

## 2025-02-08: Dashboard Design

**Decision**: Four Questions framework (Who Decides, What Does It See, What Can Go Wrong, Where's the Human) as the annotation backbone for every event in the timeline.

**Details**:
- Dynamic annotation engine generates per-level explanations (viz/annotations.py)
- No hardcoded frontend content — all annotations served via API
- Color coding: blue = code decision, orange = LLM decision, green = human decision
- Session timeline view with expandable event details
- Vanilla HTML + CSS + JS, no frameworks — keeps it simple for a learning project
- This scales automatically as new levels are added

---

## 2025-02-08: Conversation Grouping

**Decision**: Added conversation_id and sequence to QuerySession model. Dashboard shows conversations (grouped queries) instead of individual messages.

**Details**:
- EventLogger.start_conversation() generates a conversation_id shared across all queries in a chat session
- QuerySession now tracks: conversation_id, sequence (order within conversation), conversation_history_tokens (accumulating context cost)
- Dashboard sidebar shows conversations with first query as title, query count, and total tokens
- Main area shows all queries in a conversation sequentially, each with its own collapsible event timeline
- Legacy sessions without conversation_id are treated as single-query conversations (backward compatible)
- No emoji in UI — clean text and CSS only

---

## 2025-02-08: Dashboard Lifecycle

**Decision**: Dashboard runs as a persistent background service, independent of chat sessions.

**Details**:
- `make dashboard` starts it (idempotent — safe to call multiple times)
- `make stop` is the only way to kill it
- `make chat` starts/stops chat sessions without affecting dashboard
- `make start` is a convenience: ensures dashboard running, then starts chat
- This allows running multiple chat sessions while keeping dashboard open for continuous observation
- Tool events now show specific tool names (http_fetch, mock_api_fetch) instead of generic titles

---

## 2026-02-08: Three Decision Makers Framework

**Decision**: Expanded decision_by from code|llm to code|llm|human as the attribution model for all events.

**Context**: During dashboard design, realized the human is a third decision maker (chooses query, selects level, approves actions in future). Two decision makers was incomplete.

**Rationale**: Every event in the system should be attributable to one of exactly three entities. This maps to the Four Questions framework Q1 ("Who Decides?") and enables color-coded visualization (blue=code, orange=LLM, green=human).

**Impact**: Affects shared/models.py DecisionBy enum, viz/annotations.py, dashboard color coding. All future engine levels must tag events with the correct decision maker.

---

## 2026-02-08: Two-Level Event Expansion UX

**Decision**: Dashboard events expand in three tiers — Data first, Education second, Raw debug third.

**Context**: Initial dashboard showed educational Four Questions content immediately on expand, drowning out the operational data (parameters, response text, tool results).

**Rationale**: Users need to see WHAT happened before learning WHY. The educational content is still one click away but doesn't block visibility of actual event data.

**Impact**: Sets the UX pattern for all future dashboard views. app.js renders collapsed → data panel → "Learn" toggle → "Raw Data" toggle.

---

## 2026-02-08: Generic Tools Pattern

**Decision**: Tools are generic verbs (http_fetch, mock_api_fetch), skills provide specific nouns (URLs, parameters, when/why to use). Multiple skills share the same tools with different configurations.

**Context**: Needed a tool architecture that works across all 5 levels without linear tool definition growth.

**Rationale**: At Level 1, both tools are always registered. At Level 3, tools can be scoped per route. The tools themselves don't change — only which skills provide instructions for using them. This enables progressive disclosure without changing tool definitions.

**Impact**: shared/tools.py contains generic tools. Skills contain the specific invocation instructions. This pattern scales to 50+ capabilities without proportional growth in tool definitions.

---

## 2026-02-08: LLM Statelessness and Conversation Memory Pattern

**Decision**: Engine.run() returns (response_text, message_history) tuple. Application code passes full message_history on every call.

**Context**: Discovered during Level 1 testing that LLMs are completely stateless — follow-up questions had no context from previous turns.

**Rationale**: Pydantic AI's .all_messages() captures the full conversation including tool calls. This must be passed back as message_history parameter on subsequent calls. The engine returns the updated history so the chat loop can track it.

**Impact**: engines/base.py return type is tuple[str, list]. All future engine levels must implement this pattern. Conversation history token count is now tracked in events for cost visibility.

---

## 2026-02-08: Token Role Classification

**Decision**: Added `token_role` field to EngineEvent with three values: 'composition', 'actual', 'info'. Running totals only sum 'actual' events.

**Context**: Dashboard was incorrectly summing all token counts (~6,312) when the real API cost was much lower (~3,211). Events like prompt_composed and tool_registered describe what goes INTO the LLM request, not separate API calls.

**Rationale**:
- **composition**: Tokens that become part of the LLM input (prompt, tools, skills). Already counted in llm_request.
- **actual**: Real API usage (llm_request = input tokens, llm_response = output tokens). Sum these for cost.
- **info**: Events with no token cost (tool_called execution, errors, classifier decisions).

**Impact**:
- shared/models.py: EngineEvent has token_role field, compute_total_tokens() filters by role
- viz/events.py: Each log method sets appropriate token_role
- viz/static/app.js: Running total (Σ) only sums 'actual' events, composition events styled dimmer
- Backward compatible: legacy sessions without token_role default to 'actual'

---

## 2026-02-09: Token Role Display Refinement

**Decision**: Composition events display NO badges and NO running totals. Token counts appear only in the description text (e.g., "~3,051 tokens of LLM input"). Only actual events (llm_request, llm_response) show +N badges and Σ running totals.

**Context**: Initial implementation still showed +N badges on composition events, which looked additive and confused users. Showing "+3,051" on prompt_composed and "+3,073" on llm_request side-by-side implied they should sum to ~6,124 when the real cost was ~3,073.

**Rationale**: The fix isn't about styling — it's about removing visual elements that imply addition. Composition events are context/preparation; actual events are the real cost. The llm_request one-liner now includes a breakdown: "(prompt: 3,051 + tools: 50 + message: ~22)" to show where input tokens come from.

**Impact**: viz/static/app.js completely restructured token display. Dashboard now shows ~3,362 tokens per query instead of ~6,447.

---

## 2026-02-09: Server Restart After Code Changes

**Decision**: Always run `make restart` (or `make stop && make dashboard`) after modifying backend Python files.

**Context**: Spent debugging time when token_role was correctly saved to disk but missing from API responses. Root cause: the persistent uvicorn server kept old code in memory.

**Rationale**: The dashboard runs as a persistent background service for good UX (survives chat session restarts). But Python doesn't hot-reload like JavaScript. Changes to models.py, events.py, server.py, or annotations.py require a server restart.

**Symptom**: Data on disk is correct but API response is missing new fields or has old behavior.

**Impact**: Added to mental checklist: after editing backend files, restart server before testing.

---

## 2026-02-09: Per-Round Token Instrumentation (Option B)

**Decision**: Use Pydantic AI's `agent.iter()` API to capture real token counts per API round, replacing len/4 estimates.

**Context**: Token counts were estimated using `len(text) // 4` which significantly underestimated actual API costs. Multi-round tool loops were invisible — only one llm_request/llm_response pair was logged regardless of how many tool calls occurred.

**Solution**:
- Iterate through the agent run using `async for node in agent.iter()`
- On each `CallToolsNode`, extract `node.model_response.usage.input_tokens` and `output_tokens`
- Log a new `API_CALL` event per round with real token data
- Backfill `total_rounds` on all events after the loop completes

**Data Model Changes**:
- `EventType.API_CALL` added (LLM_REQUEST/LLM_RESPONSE deprecated for backward compat)
- `EngineEvent.round_number` tracks which round within query
- `QuerySession` gains `total_api_calls`, `total_input_tokens`, `total_output_tokens`
- `compute_token_breakdown()` returns (calls, input, output) tuple

**Verification**: Weather query now shows 3 rounds (4,355 → 4,558 → 5,027 input tokens) with visible accumulation as tool results add to context.

**Impact**: Dashboard can now show per-round breakdowns, input accumulation, and real API costs. Old logs remain readable via backward compatibility.

---

## 2026-02-09: Real Token Counting via count_tokens API

**Decision**: Replace all `len(text) // 4` token estimates with exact measurements from Anthropic's `client.messages.count_tokens()` API.

**Context**: Token estimates were significantly wrong. System prompt estimated at 3,051 tokens was actually 3,687 (17% under). Tool definitions estimated at 50 tokens were actually 658 (92% under, 13x error!).

**Solution**:
- At engine init, call `count_tokens()` to measure static components once:
  - `_count_real_prompt_tokens()` — system prompt alone
  - `_count_real_tool_tokens()` — tool definitions alone (extracted via `agent._function_toolset.tools`)
  - `_count_real_base_tokens()` — API framing overhead
- In `_build_input_breakdown()`, use arithmetic: `dynamic = actual_total - known_static`
- Each breakdown item now has one of three flags:
  - `is_measured: true` — exact count from count_tokens API
  - `is_computed: true` — derived as total minus known static
  - `is_real: true` — the actual API total (verification)

**Measured Values**:
- System prompt (7 skills): 3,687 tokens
- Tool definitions (2 tools): 658 tokens
- API framing overhead: 7 tokens
- **Total static**: 4,352 tokens per API call

**Impact**:
- engines/level1_monolith.py: Anthropic client, counting methods, new breakdown format
- viz/static/app.js: Handle is_measured/is_computed/is_real flags, new CSS classes
- viz/static/styles.css: token-measured, token-computed, token-real styling
- Backward compatible: legacy sessions with tokens_est still render correctly

---

## 2026-02-09: User Message Token Display in Preparation Step

**Decision**: Show user message token count in the narrative Preparation step, extracted from the first API call's breakdown.

**Context**: The Preparation step listed skills, tools, and conversation history with token counts, but "Your question" showed no count. The data was available in the API call breakdown but not displayed.

**Solution**:
- In `groupEventsIntoSteps()`, pass `firstApiCall` reference to the preparation step
- In `renderPreparationStep()`, extract user message tokens from the breakdown by finding the `is_computed` entry labeled "Your question" or similar
- Display the token count next to the question preview

**Breakdown Label Updates** (for consistency):
- Round 1 with no history: "Your question"
- Round 1 with history: "Conversation history + your question"
- Round 2+: "Your question + tool exchanges (rounds 1-N)"

**Verification Script**: Created `verify_tokens.py` to validate token math across all sessions:
- For each query, for each API round, verifies breakdown items sum to verified total
- Checks session aggregate totals match sum of round totals
- Reports PASS/FAIL per round with detailed breakdown

**Test Results**: 4 queries, 6 total API rounds, all PASS:
- Simple query (no tools): 1 round, 4,353 tokens
- Query with history (no tools): 1 round, 4,494 tokens
- Weather API query: 3 rounds (4,613 → 4,804 → 5,272)
- Follow-up with accumulated history: 1 round, 5,436 tokens

**Conversation Grouping Verification** (added to verify_tokens.py):
- Checks all sessions in a chat share one conversation_id
- Validates sequence numbers are sequential (1, 2, 3, 4)
- Confirms history_tokens=0 for seq=1, >0 for seq>1
- Detects broken grouping when conversation_id == query_id

---

## 2026-02-09: Three-Tier Token Accuracy Model

**Decision**: Every token number in the system must fall into exactly one of three categories: MEASURED (from count_tokens API, exact for static components), COMPUTED (derived by subtracting measured values from verified totals, exact by arithmetic), or VERIFIED (real input_tokens/output_tokens from Claude API response). No len//4 estimates. No hardcoded values. No guessing.

**Context**: The session began with all numbers estimated via character counting. Each fix revealed deeper problems. The only acceptable standard for an educational system about token costs is that every number traces to a real measurement.

**Rationale**: Measured gives exact values for things that don't change (prompt, tools). Verified gives exact totals per round (from API). Computed fills the gap via subtraction: dynamic_content = verified_total - measured_static. The sum of measured + computed always equals verified exactly, by construction.

**Impact**: Dashboard visually distinguishes tiers via is_measured/is_computed/is_real flags. Breakdown items always sum to the verified total. Known limitation: the dynamic bucket (user message + conversation history) can't be further split without an additional per-query API call (~150ms). Within that bucket, ~1-9 tokens may shift between sub-components due to tokenizer interaction effects, but the total is always exact.

---

## 2026-02-09: Narrative Timeline Replaces Flat Event List

**Decision**: Group raw events into narrative STEPs with explanatory prose: Preparation ("Your code packed a suitcase") → Sent to Claude (per round, with input growth explanation) → Your code ran the tool (with parameters and results) → Total Cost (with percentage insights). Progressive disclosure via expandable "View suitcase contents breakdown."

**Context**: The flat event timeline (prompt_composed → tool_registered → api_call → tool_called) showed accurate data but didn't teach. Users could see numbers but couldn't follow the story of what happened and why. The dashboard's purpose is education, not just monitoring.

**Rationale**: "Claude received the suitcase (4,564 tokens), read everything, and decided it needs more data" teaches more than "api_call: input_tokens=4564, output_tokens=90". Composition events merge into one Preparation step. Each API round gets context about what changed since the last round. Tool executions make clear that code, not Claude, runs tools.

**Impact**: New rendering pipeline in app.js: groupEventsIntoSteps() → renderNarrativeStep(). Legacy renderTimeline() preserved for old log files without API_CALL events. Each step type has its own renderer. Future levels will add new step types (e.g., classifier_decision for Level 3, routing_choice for Level 4).

---

## 2026-02-09: Suitcase Mental Model as Canonical API Call Analogy

**Decision**: "Packing a suitcase" is the canonical mental model for understanding what happens in each API call. Every call packs everything (system prompt, tool definitions, user message, conversation history, previous tool call/result pairs) into one payload. Rounds 2+ repack everything from before PLUS new tool results — the suitcase gets heavier.

**Context**: The project creator couldn't intuitively understand why input tokens grew between rounds or why the system prompt cost was paid multiple times per query. The suitcase analogy made it click immediately and maps perfectly to the technical reality.

**Rationale**: Unlike "context window" or "prompt," "suitcase" implies physical weight, repacking, and the cost of carrying everything. It drives both architecture decisions (what data to log in the breakdown) and visualization (how to display input composition). Level comparisons become "lighter suitcases" vs "heavier suitcases."

**Impact**: All dashboard copy uses suitcase language. Breakdown sections labeled "View suitcase contents breakdown." The analogy extends to all levels: Level 2 packs fewer skills (lighter suitcase), Level 3 routes to avoid unnecessary packing, Level 5 distributes the load across multiple smaller suitcases.

---

## 2026-02-10: API_CALL Event Type (Combined Request+Response)

**Decision**: New API_CALL event type where one event = one complete API round-trip, carrying real input_tokens, output_tokens, input_breakdown[], response_type, tool_calls[], response_preview.

**Context**: Old model logged separate LLM_REQUEST and LLM_RESPONSE events but tool queries have 2-3 round-trips. The natural unit of cost is one complete send+receive cycle.

**Rationale**: One suitcase = one event = one visual card. Simpler data model, maps directly to suitcase mental model.

**Impact**: New EventType value. Old types kept for backward compat. Dashboard handles both formats. input_breakdown array enables detailed visualization of what's packed in each call.

---

## 2026-02-10: Per-Query count_tokens for History/Question Split

**Decision**: Add one count_tokens API call per query (~150ms) measuring prompt + tools + just this message (no history). Enables exact split: user_msg = clean_call - prompt - tools, history = round1_verified - clean_call.

**Context**: Without this, "Your question" and "Conversation history" were lumped in one bucket. The logged conversation_history_tokens was wrong — only summed output_tokens, missing user messages and tool exchanges (540 logged vs 1,147 actual, a 53% undercount).

**Rationale**: Diagnostic proved clean_call matches actual Round 1 exactly for seq=1 queries (0 difference). History computation uses two real numbers. Cost is one API call per query, not per round.

**Impact**: Exact history tracking enables accurate conversation growth visualization. Fixes the broken history_tokens field. Preparation step now shows separate "Conversation history" and "Your question" items with exact token counts.

---

## 2026-02-10: Combined Tool Growth from Verified Round Deltas

**Decision**: Replace per-tool result token estimates (len//4) with combined growth computed from consecutive verified API round totals: growth = roundN+1_input - roundN_input.

**Context**: The last remaining len//4 in the system. Tool result estimates showed ~15 tokens when actual growth was 253 (17x undercount). Per-tool splitting impossible without additional API calls when multiple tools run between rounds.

**Rationale**: When 2+ tools run between rounds, we can't split per-tool without more API calls. Combined total from two verified numbers is exact and honest. Better to show "These 2 tool calls added 531 tokens" (accurate) than "~7 tokens" + "~8 tokens" (wrong).

**Impact**: Eliminates the last estimate in the system. Dashboard shows combined growth on tool execution steps. groupEventsIntoSteps() links tool steps with adjacent API calls to compute realGrowthTokens.

---

## 2026-02-10: API Framing Overhead as Measured Constant

**Decision**: Measure framing overhead at startup: framing = count_tokens(empty_prompt + "x") - 1. Typically ~7 tokens for message structure encoding by the API.

**Context**: Even with measured prompt and tools, sum didn't match base total. The gap was API encoding overhead — the token cost of message structure itself.

**Rationale**: Constant per session (property of message structure, not content). Closes breakdown math gap. Without this, breakdown items wouldn't sum to verified total.

**Impact**: Enables the guarantee that breakdown items sum to verified total exactly. Stored as self._base_tokens on engine instance.

---

## 2026-02-10: No Emojis in Dashboard — CSS Indicators Only

**Decision**: Remove all emojis from dashboard UI. Use CSS left-border color coding for visual distinction: purple for skills, teal for tools, blue for history, green for question.

**Context**: Dashboard is an educational engineering tool, not a chat interface. Emojis (📚🔧💬📜📦) were used initially for visual scannability but felt unprofessional.

**Rationale**: Professional aesthetic. Emojis render inconsistently across platforms. CSS is reliable and maintainable. Color coding provides visual hierarchy without character rendering issues.

**Impact**: Clean, consistent visual language. pack-item-skills, pack-item-tools, pack-item-history, pack-item-question CSS classes. Color coding can extend to Level 2+ step types.

---

## 2026-02-10: Migration from 5-Level to 4+3 Model

**Decision**: Restructure architecture from 5 discrete levels to 4 core levels + 3 orthogonal overlays.

**Context**: The original 5-level model (Monolith → Skills → Classifier → Adaptive → MCP) treated MCP as a separate "level" when it's really an infrastructure choice orthogonal to the routing/loading strategy. Additionally, capabilities like execution orchestration, context persistence, and human-in-the-loop cut across all levels.

**New Model**:
- **4 Levels**: Monolith, Selective Loading, Explicit Routing, Adaptive Context
- **3 Overlays**: Execution Orchestration, Context Persistence, Human-in-the-Loop

**Rationale**: Overlays are capabilities that can be enabled on any level. MCP becomes an implementation detail of tool execution, not a level. This creates a cleaner conceptual model: levels define HOW queries are processed, overlays define WHAT additional capabilities are available.

**Impact**:
- `engines/level5_mcp.py` deleted
- `shared/models.py` level constraint changed from `le=5` to `le=4`
- `viz/server.py` validation updated
- `main.py` LEVELS dict reduced to 4 entries
- New spec: `docs/ARCHITECTURE_SPEC.md` supersedes `docs/SPEC.md`
- Teaching layer (annotations, dashboard) to be updated in Phase 3
