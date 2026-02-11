# Life Engine Learning

A hands-on learning project for building AI agents with Pydantic AI. Travel Concierge theme with 4 engine levels + 3 overlays demonstrating different architectural patterns.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Anthropic API key

## Setup

```bash
git clone <repo-url>
cd life-engine-learning
echo "ANTHROPIC_API_KEY=your-key-here" > .env
make install
```

## Quick Reference

```bash
make                  # show all commands
make chat             # start Level 1 chatbot
make chat level=2     # start Level 2 (coming soon)
make dashboard        # start dashboard server on port 8000
make start            # dashboard + chat together, opens browser
make stop             # stop dashboard
make status           # check what's running
make logs             # list session files with summaries
make clean-logs       # wipe session files
```

**Daily workflow:**
```bash
make start            # dashboard opens, chat starts
                      # ... interact ...
quit                  # chat exits, dashboard keeps running
make stop             # stop dashboard when done for the day
```

## What It Does

Travel Concierge AI built 4 different ways, with 3 orthogonal overlays:
- **Level 1**: Monolith — all skills in one giant prompt
- **Level 2**: Selective Loading — skills loaded on demand (coming soon)
- **Level 3**: Explicit Routing — query classification drives selection (coming soon)
- **Level 4**: Adaptive Context — proactive fetching and context engineering (coming soon)

Overlays (can be enabled on any level): Execution Orchestration, Context Persistence, Human-in-the-Loop.

Dashboard visualizes what happens at each level so you can compare the tradeoffs.

## Project Structure

```
life-engine-learning/
├── main.py              # Entry point: pick engine level
├── engines/             # Engine implementations (L1-L4)
├── shared/              # Tools, models, skill loader
├── skills/              # Travel skills (weather, flights, hotels, etc.)
├── viz/                 # Dashboard server + event logger
├── logs/                # Session event logs (gitignored)
├── docs/ARCHITECTURE_SPEC.md  # Architecture specification (4+3 model)
└── decisions.md         # Architectural decisions log
```

## Dashboard

The dashboard visualizes agent execution with the **Four Questions** framework:
- **Q1: Who Decides?** — Code, LLM, or human?
- **Q2: What Does It See?** — Context available for the decision
- **Q3: What Can Go Wrong?** — Blast radius assessment
- **Q4: Where's the Human?** — Human-in-the-loop patterns

Start with `make start` or `make dashboard`, then open http://localhost:8000.

See [docs/FOUR_QUESTIONS.md](docs/FOUR_QUESTIONS.md) for the full framework.

## Observability

- **Event logging**: Every query writes a session JSON to `logs/`
- **Logfire**: Pydantic AI auto-instrumentation for tracing
- **Dashboard**: Event timeline with Four Questions annotations
