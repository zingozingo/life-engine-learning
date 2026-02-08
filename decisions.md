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
- `make start` runs dashboard in background, opens browser, starts chat in foreground
- Dashboard auto-stops when chat exits (no orphan processes)
- `make stop` cleans up any running dashboard processes
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
