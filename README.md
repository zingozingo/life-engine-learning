# Life Engine Learning

A hands-on learning project for building AI agents with Pydantic AI.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Anthropic API key

## Setup

```bash
# Clone the repository
git clone <repo-url>
cd life-engine-learning

# Create .env with your API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Install dependencies
uv sync

# Run the chatbot
uv run python main.py
```

## What It Does

CLI chatbot with:
- **Progressive disclosure skills**: Agent loads detailed instructions on-demand
- **MCP integration**: Filesystem access via Model Context Protocol
- **Logfire observability**: All agent runs traced automatically

## Project Structure

```
life-engine-learning/
├── main.py              # Entry point: agent, tools, CLI loop
├── skill_loader.py      # Skill discovery and prompt building
├── skills/              # Skill definitions (YAML frontmatter + Markdown)
│   ├── filesystem/      # MCP filesystem operations (active)
│   ├── time/            # Current time tool (active)
│   ├── weather/         # Open-Meteo API (active)
│   ├── math/            # MCP math server (planned)
│   └── database/        # Database operations (planned)
├── archive/             # Historical experiments
├── decisions.md         # Architectural decisions log
└── pyproject.toml       # Dependencies
```

## Roadmap

See `ROADMAP.md` for learning phases and next steps.
