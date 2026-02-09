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
