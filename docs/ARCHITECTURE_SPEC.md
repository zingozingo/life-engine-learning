# Travel Concierge - Architecture Specification

**Created:** 2026-02-10
**Supersedes:** docs/SPEC.md (5-level model)
**Status:** Active

---

## Core Model: 4 Levels + 3 Overlays

The architecture is organized into **4 core levels** that define how the agent processes queries, plus **3 orthogonal overlays** that add capabilities without changing the core level structure.

---

## The 4 Levels

### Level 1: Monolith
Everything hardcoded in one prompt. All skills, all tools, every query.

**Characteristics:**
- System prompt contains ALL skill instructions (~3,687 tokens)
- ALL tools registered on every query (~658 tokens)
- No routing decisions - LLM figures out relevance implicitly
- Highest token cost per query (baseline for comparison)

**Teaching Focus:** Token costs, the "monolith tax," why this doesn't scale.

**Status:** Complete and instrumented.

---

### Level 2: Selective Loading
Skills loaded on demand via `load_skill` tool.

**Characteristics:**
- System prompt contains skill summaries only (~200 tokens)
- LLM calls `load_skill(skill_name)` to get full instructions
- Tools still all registered (no scoping yet)
- LLM decides which skills to load (implicit routing)

**Teaching Focus:** Progressive disclosure pattern, skill abstraction.

**Status:** Stub only.

---

### Level 3: Explicit Routing
Query classification drives skill and tool selection.

**Characteristics:**
- Lightweight classifier runs first (small model or rules)
- Classification determines which skills load
- Tools scoped per route (e.g., creative routes get no tools)
- Code decides routing (explicit), LLM executes

**Teaching Focus:** Implicit vs explicit decisions, routing patterns.

**Status:** Stub only.

---

### Level 4: Adaptive Context Engineering
Proactive data fetching and optimized context composition.

**Characteristics:**
- High-confidence routes trigger proactive API calls
- Data injected into prompt before LLM runs
- Context optimized per query type
- Eliminates round-trips for predictable needs

**Teaching Focus:** Proactive vs reactive patterns, context engineering.

**Status:** Stub only.

---

## The 3 Overlays

Overlays are orthogonal capabilities that can be enabled on any level.

### Overlay A: Execution Orchestration
How tool calls are managed and executed.

**Aspects:**
- Parallel vs sequential tool execution
- Error handling and retry strategies
- Timeout management
- Result aggregation

**Can be added to:** Any level (L1-L4)

---

### Overlay B: Context Persistence
How conversation state is managed across queries.

**Aspects:**
- Message history accumulation
- Context window management
- Summarization strategies
- Session boundaries

**Can be added to:** Any level (L1-L4)

---

### Overlay C: Human-in-the-Loop
Where and how humans participate in the flow.

**Aspects:**
- Approval gates for high-stakes actions
- Clarification requests
- Override mechanisms
- Audit trails

**Can be added to:** Any level (L1-L4)

---

## Four Questions Framework

The Four Questions are a cross-cutting annotation framework that applies to every event at every level:

1. **Q1: Who Decides?** - Code, LLM, or Human made this decision
2. **Q2: What Does It See?** - What information was available at decision time
3. **Q3: What Can Go Wrong?** - Blast radius and failure modes
4. **Q4: Where's the Human?** - Human involvement at this point

These appear as contextual annotations in the dashboard, not as separate sections.

---

## Skills (Unchanged)

| Skill | Description | Tools It Uses |
|-------|-------------|---------------|
| `weather` | Forecasts, conditions, packing weather advice | `http_fetch` (Open-Meteo) |
| `flights` | Flight search, price comparison | `mock_api_fetch` |
| `hotels` | Accommodation search, ratings | `mock_api_fetch` |
| `activities` | Attractions, tours, restaurants | `mock_api_fetch` |
| `currency` | Exchange rates, conversion | `mock_api_fetch` |
| `visa` | Visa requirements, entry rules | `mock_api_fetch` |
| `packing` | Packing lists | None (LLM reasoning) |

---

## Generic Tools (Unchanged)

| Tool | Description | Levels |
|------|-------------|--------|
| `http_fetch` | GET/POST to any URL | All |
| `mock_api_fetch` | Query mock travel APIs | All |
| `load_skill` | Load skill instructions | L2 only |

---

## Event Schema

```json
{
  "query_id": "uuid",
  "level": 1-4,
  "timestamp": "ISO-8601",
  "event_type": "prompt_composed | classifier_decision | skill_loaded | tool_registered | proactive_fetch | tool_called | api_call | error",
  "decision_by": "code | llm | human",
  "data": { ... },
  "round_number": 1
}
```

Note: `api_call` = one complete API round-trip with real token counts.

---

## Level Behaviors (4 Levels)

| Aspect | L1 (done) | L2 | L3 | L4 |
|--------|-----------|----|----|-----|
| System prompt | All skills hardcoded | Skill menu (summaries) | Route-specific | Route-specific + pre-fetched |
| Skill loading | N/A (all in prompt) | LLM calls load_skill | Code loads per route | Code loads per route |
| Tool availability | All always | All generic always | Scoped per route | Scoped per route |
| Routing decision | LLM (implicit) | LLM (implicit) | Classifier (explicit) | Classifier (explicit) |
| Data fetching | All reactive | All reactive | All reactive | Proactive where confident |

---

## Dashboard Views

1. **Single Level View** - Pick a level, run queries, see the event timeline (implemented)
2. **Comparison View** - Same query, two levels side-by-side (planned)
3. **Token Analysis** - Cost breakdown per level (planned)
4. **Decision Map** - Color-coded: blue = code, orange = LLM, green = human (integrated)

---

## Educational Content Principles

1. **Every number traces to a measurement.** No estimates, no hardcoding. The three-tier accuracy model (Measured/Computed/Verified) applies to all levels.

2. **Content is derived from data, not written as filler.** Insights about token costs are computed from real measurements. Conceptual content is cleanly separated.

3. **Progressive learning mirrors progressive disclosure.** L1 teaches cost. L2 teaches the skill pattern. L3 teaches routing. L4 teaches context management.

4. **The Four Questions are annotations, not sections.** They appear as contextual notes on dashboard events.

5. **Comparison is the primary teaching tool.** Side-by-side views of the same query at different levels.

---

## Decision Log Reference

- **2026-02-10:** Restructured from 5 levels to 4 levels + 3 overlays.
- **2026-02-10:** Added Execution Orchestration overlay.
- **2026-02-10:** Added Context Persistence overlay.
- **2026-02-10:** Reframed L4 as adaptive context engineering.
- **2026-02-10:** Confirmed Four Questions as cross-cutting annotation framework.

*This is a living document. The core model - 4 levels + 3 overlays - is the stable foundation everything builds on.*
