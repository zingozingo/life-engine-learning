# Execution Orchestration — Roadmap & Patterns

## Overview

This document captures the planned execution orchestration patterns for the Life Engine Learner. Execution orchestration is **Overlay A** in the 4+3 architecture — it changes *how work flows* (how many context windows, how they coordinate) and composes independently with any level.

The levels determine *what goes in each window*. The execution patterns determine *how many windows there are and how they talk to each other*.

## The Seven Patterns

Listed in order of complexity. Each builds on the previous.

### 1. Sequential (Current — Level 1)
Single agent, single context window, grows per round.
- **Token shape:** One window, linear growth per round
- **Error model:** Fail = fail. No isolation.
- **Status:** Implemented (Level 1 monolith)

### 2. One-off Sub-agent
Main agent spawns a focused sub-agent for a specific task. Sub-agent gets a clean context window, does work, returns summary.
- **Token shape:** Main window + temporary sub-window. Sub-window result summarized back.
- **Error model:** Sub-agent failure contained. Main agent can retry or proceed without.
- **Example:** "Research flights" -> sub-agent searches APIs, returns top 3 options
- **Status:** Planned

### 3. Chained Sub-agents
Output of agent A feeds into agent B feeds into agent C. Each gets focused context.
- **Token shape:** N sequential windows. Each gets its predecessor's output (summarized).
- **Error model:** Critical design question — per-step options:
  - **Retry:** Re-run failed step (with backoff?)
  - **Skip:** Proceed with partial data (downstream must handle gaps)
  - **Abort:** Kill the chain, return what we have
  - **Fallback:** Try alternate path for the failed step
- **Chain definition needed:** Sequence of steps, each with input/output contract, error strategy
- **Example:** Research -> Analyze -> Summarize pipeline. If Analyze fails, do we summarize raw research or abort?
- **Status:** Planned — design chain definition format and error handling strategy

### 4. Phased Execution
Task decomposed into phases, each with sub-steps. An orchestrator manages the phases.
- **Token shape:** Orchestrator window + phase-specific windows. Orchestrator carries summary context.
- **Error model:** Phase-level retry. Orchestrator decides whether to re-phase or skip.
- **Example:** Claude Code's file editing: plan phase -> edit phase -> verify phase
- **Status:** Planned

### 5. Parallel Sub-agents
Multiple sub-agents work simultaneously on different aspects. Results merged by orchestrator.
- **Token shape:** N parallel windows. Orchestrator window receives all results.
- **Error model:** Partial success possible — 2 of 3 sub-agents succeed, merge what we have.
- **Example:** Weather in Phoenix + Weather in Dallas + Flights from DC — all searched simultaneously
- **Status:** Planned

### 6. Agent Teams
Multiple persistent agents with shared state, peer-to-peer messaging, specialized roles.
- **Token shape:** N persistent windows + shared task list. Agents communicate via messages.
- **Error model:** Team resilience — if one agent fails, others can pick up or reassign work.
- **Example:** Planner + Researcher + Coder + Tester team (Opus 4.6 agent teams)
- **Requires:** Shared memory (Overlay B: Context Persistence)
- **Status:** Planned — depends on Overlay B

### 7. Supervisor/Worker
Supervisor delegates, monitors, redirects. Workers report back. Supervisor can reassign.
- **Token shape:** Supervisor window + N worker windows. Supervisor sees all summaries.
- **Error model:** Supervisor-managed. Can reassign failed work, adjust strategy, add workers.
- **Example:** 16-agent C compiler stress test (Anthropic's benchmark)
- **Status:** Planned — most advanced pattern

## How Patterns Compose With Levels

The execution pattern is about *how many windows*. The level is about *what's in each window*.

| Pattern | At L1 | At L2 | At L3 | At L4 |
|---------|-------|-------|-------|-------|
| Sequential | Everything in one growing window | Same, but skills loaded on demand | Same, but context scoped per route | Same, but proactive pre-fetch |
| One-off sub | Sub gets full monolith context | Sub loads only relevant skills | Sub's context scoped by classifier | Sub gets pre-fetched data |
| Chained | Each step gets full context | Each step loads what it needs | Each step classified independently | High-confidence steps pre-loaded |
| Parallel | Each parallel agent = full monolith | Each loads independently | Each classified independently | Parallel pre-fetch possible |

**Key insight:** Higher levels make execution patterns MORE efficient because each sub-agent's window is leaner. A chained workflow at L1 stuffs everything into every step. The same chain at L3 gives each step only what it needs.

## Chained Workflow Requirements (To Design)

When we implement chained workflows, we need:

1. **Chain definition format** — sequence of steps with input/output contracts
2. **Chain runner** — executes steps, passes outputs, handles errors
3. **Error strategy per step** — retry/skip/abort/fallback, configurable
4. **Observability** — dashboard shows chain as a whole, not just individual queries
5. **Teaching integration** — new event types (chain_step_started, chain_step_completed, chain_error_handled) with insight generators for chain-level metrics

## Implementation Priority

1. **One-off sub-agent** — simplest multi-window pattern. Good test of the framework.
2. **Chained sub-agents** — primary interest. Error handling is the design challenge.
3. **Parallel sub-agents** — natural extension of chains for independent subtasks.
4. **Phased execution** — useful for complex tasks. Claude Code already demonstrates this.
5. **Agent teams / Supervisor** — most advanced. Depends on shared memory (Overlay B).

## Open Questions

- Chain definition format: YAML? Python dataclass? DSL?
- Error handling defaults: retry-first or abort-first?
- Observability: How does the dashboard visualize a chain vs a single query? Timeline per step? Nested view?
- Teaching: How do we compare "same chain at L1 vs L3" when the chain itself changes behavior at different levels?
- Shared memory for agent teams: SQLite? In-memory? Structured files?
