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
