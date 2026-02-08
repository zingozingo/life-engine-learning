# Travel Concierge — Multi-Level Agent Architecture Spec

**Created:** 2025-02-07
**Project:** Life Engine Learning

---

## Overview

A Travel Concierge AI assistant built five different ways, from monolith to fully adaptive with MCP. Same skills, same tools, same queries — different wiring. A visualization dashboard shows exactly what happens at each level so we can see the architectural tradeoffs in real time.

---

## Skills

| Skill | Description | Tools It Uses | Demonstrates |
|-------|------------|---------------|-------------|
| `weather` | Forecasts, current conditions, packing weather advice | `http_fetch` (Open-Meteo API) | Simple lookup, proactive fetch candidate |
| `flights` | Flight search, price comparison, booking info | `http_fetch` (mock/real API) | Multi-param tool calls |
| `hotels` | Accommodation search, ratings, availability | `http_fetch` | Similar to flights, routing distinction |
| `activities` | Local attractions, tours, restaurants | `http_fetch` | Broad/ambiguous queries |
| `currency` | Exchange rates, conversion, budget estimation | `http_fetch` | Simple factual, proactive candidate |
| `visa` | Visa requirements, travel documents, entry rules | `http_fetch` | Conditional need |
| `packing` | Packing lists based on destination/weather/duration | None (LLM reasoning) | No-tool skill, pure instruction |

---

## Generic Tools

| Tool | Description | Levels |
|------|------------|--------|
| `http_fetch` | GET/POST to any URL. Skills provide the URLs. | All |
| `load_skill` | Load detailed instructions for a skill | L2 only |
| `call_mcp_tool` | Bridge to MCP servers | L5 only |

---

## Test Queries

| Query | Expected Routing | Why It's Interesting |
|-------|-----------------|---------------------|
| "What's the weather in Tokyo in April?" | weather | Simple, single-skill, proactive candidate |
| "Plan a 5-day trip to Barcelona" | multiple | Ambiguous — weather, activities, maybe hotels |
| "Do I need a visa for Thailand?" | visa | Single-skill, conditional on nationality |
| "Convert 500 USD to Euros" | currency | Simplest possible, cheapest across levels |
| "Find cheap flights from DC to Rome in June" | flights | Specific, clear parameters |
| "What should I pack for a week in Iceland?" | packing + weather | Two skills collaborate |

---

## Event Schema

```json
{
  "query_id": "uuid",
  "level": 1,
  "timestamp": "ISO-8601",
  "event_type": "prompt_composed | classifier_decision | skill_loaded | tool_registered | proactive_fetch | tool_called | llm_response | error",
  "decision_by": "code | llm",
  "data": {
    "token_count": 0,
    "duration_ms": 0,
    "detail": {}
  }
}
```

---

## Level Behaviors

| Aspect | L1 | L2 | L3 | L4 | L5 |
|--------|----|----|----|----|-----|
| System prompt | All skills hardcoded | Skill menu (summaries) | Route-specific | Route-specific + pre-fetched | Same as L4 |
| Skill loading | N/A (all in prompt) | LLM calls load_skill | Code loads per route | Code loads per route | Code loads per route |
| Tool availability | All always | All generic always | Scoped per route | Scoped per route | MCP per route |
| Routing decision | LLM (implicit) | LLM (implicit) | Classifier (explicit) | Classifier (explicit) | Classifier (explicit) |
| Data fetching | All reactive | All reactive | All reactive | Proactive where confident | Proactive via MCP |

---

## Dashboard Views

1. **Single Level View** — Pick a level, run queries, see the event timeline
2. **Comparison View** — Same query, two levels side-by-side
3. **Token Analysis** — Cost breakdown per level
4. **Decision Map** — Color-coded: blue = code decided, orange = LLM decided

---

## Directory Structure

```
life-engine-learning/
├── main.py                    # Entry point: pick engine + run
├── engines/                   # One engine per level
├── shared/                    # Tools, models, skill loader
├── skills/                    # Travel concierge skills (shared)
├── viz/                       # Dashboard server + event logger
├── logs/                      # Event output (gitignored)
├── archive/                   # Old code preserved
└── docs/                      # This spec
```
