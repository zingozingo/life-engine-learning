# The Four Questions Framework

A framework for understanding and explaining AI agent decisions at every step.

## Overview

Every event in an agent's execution can be analyzed through four fundamental questions. These questions reveal the architectural tradeoffs between different designs and help developers understand what's actually happening inside their agents.

## The Four Questions

### Q1: Who Decides?

**Who made this decision — deterministic code or the LLM?**

This is the most fundamental question. It divides the world into:
- **CODE decides** (explicit, deterministic, predictable)
- **LLM decides** (implicit, probabilistic, flexible)
- **HUMAN decides** (approval gates, manual intervention)

Neither is inherently better — they're tradeoffs:
- Code decisions are fast, cheap, and predictable, but inflexible
- LLM decisions are flexible and can handle ambiguity, but expensive and sometimes surprising
- Human decisions are high-quality but slow and don't scale

### Q2: What Does It See?

**What information is available to whoever is making this decision?**

Context is everything. Understanding what's visible at each decision point explains:
- Why certain mistakes happen (the decider didn't have the right information)
- Where token costs accumulate (everything in context costs tokens)
- What could be optimized (remove irrelevant context, add missing context)

At different levels:
- Level 1: The LLM sees EVERYTHING (all skills, all tools) — maximum context, maximum cost
- Level 3: The classifier sees only the query — minimal context, cheap decision
- Level 4: The LLM sees pre-fetched data — right context, reduced round-trips

### Q3: What Can Go Wrong?

**What's the blast radius if this step fails or makes a mistake?**

Risk assessment drives architecture decisions:
- **LOW risk**: Read-only operations, reversible actions, bounded costs
- **MEDIUM risk**: Wasted resources, wrong answers, user frustration
- **HIGH risk**: Side effects, data corruption, security issues, real-world consequences

The rule: Match autonomy to blast radius. Low-risk actions can be fully autonomous. High-risk actions need human gates.

### Q4: Where's the Human?

**At what point does a human enter the loop, if at all?**

Human involvement patterns:
- **Never**: Fully autonomous, fire-and-forget
- **Review at End**: Agent runs, human checks output
- **Approval Gates**: Human approves before high-risk actions
- **Continuous Oversight**: Human monitors real-time
- **Engineering Only**: Human designed the system but isn't in the runtime loop

The right pattern depends on the stakes and the trust level.

## Applying the Framework

For every event in your agent's execution:

1. **Identify who decided** — Was this choice made by code, LLM, or human?
2. **Map the context** — What information was available when the decision was made?
3. **Assess the risk** — What happens if this goes wrong? What's the worst case?
4. **Locate the human** — Where does human judgment enter, if at all?

## Level-by-Level Patterns

| Aspect | Level 1: Monolith | Level 2: Skills | Level 3: Classifier | Level 4: Adaptive Context |
|--------|-------------------|-----------------|---------------------|--------------------------|
| Routing | LLM (implicit) | LLM (implicit) | Code (explicit) | Code (explicit) |
| Skill Loading | All always | LLM loads on demand | Code loads per route | Code loads per route |
| Tool Availability | All always | All always | Scoped per route | Scoped per route |
| Data Fetching | Reactive only | Reactive only | Reactive only | Proactive + Reactive |

## Design Principles

1. **Push decisions toward code when possible** — Cheaper, faster, more predictable
2. **Use LLM decisions for ambiguity** — When rules can't capture the nuance
3. **Match autonomy to blast radius** — High-risk actions need more oversight
4. **Minimize context for cheap decisions** — Classifiers don't need full skill details
5. **Pre-fetch when confidence is high** — Eliminate round trips for predictable needs

## Further Reading

- See `docs/ARCHITECTURE_SPEC.md` for the full Travel Concierge architecture specification (4+3 model)
- See `decisions.md` for architectural decisions log
