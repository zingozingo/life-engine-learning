# Life Engine Learning - Developer Commands
# Run `make help` to see available commands

.PHONY: help chat dashboard start stop status logs clean-logs install

# Default target
help:
	@echo "Life Engine Learning - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "  make chat [level=N]  Run chatbot (default level=1)"
	@echo "  make dashboard       Start dashboard server (foreground)"
	@echo "  make start           Start dashboard + chat together"
	@echo "  make stop            Stop any running dashboard"
	@echo "  make status          Show what's running"
	@echo "  make logs            List recent session files"
	@echo "  make clean-logs      Delete all session files"
	@echo "  make install         Install dependencies (uv sync)"
	@echo ""

# Default level for chat
level ?= 1

# Run the chatbot interactively
chat:
	uv run python main.py $(level)

# Start dashboard server in foreground
dashboard:
	uv run uvicorn viz.server:app --reload --port 8000

# Start dashboard + chat together
start: stop
	@echo "Starting dashboard on http://localhost:8000..."
	@uv run uvicorn viz.server:app --port 8000 > /dev/null 2>&1 & echo $$! > .dashboard.pid
	@sleep 2
	@if lsof -i :8000 > /dev/null 2>&1; then \
		echo "Dashboard running (PID: $$(cat .dashboard.pid))"; \
		open http://localhost:8000 2>/dev/null || true; \
	else \
		echo "Failed to start dashboard"; \
		rm -f .dashboard.pid; \
		exit 1; \
	fi
	@echo ""
	@echo "Starting chat (type 'quit' to exit)..."
	@echo ""
	@uv run python main.py $(level) || true
	@echo ""
	@echo "Chat ended. Stopping dashboard..."
	@$(MAKE) -s stop

# Stop any running dashboard
stop:
	@if [ -f .dashboard.pid ]; then \
		PID=$$(cat .dashboard.pid); \
		if kill -0 $$PID 2>/dev/null; then \
			kill $$PID 2>/dev/null; \
			echo "Stopped dashboard (PID: $$PID)"; \
		fi; \
		rm -f .dashboard.pid; \
	fi
	@# Safety net: kill any uvicorn on port 8000
	@lsof -ti :8000 | xargs kill 2>/dev/null || true

# Show what's running
status:
	@echo "Dashboard status:"
	@if [ -f .dashboard.pid ]; then \
		PID=$$(cat .dashboard.pid); \
		if kill -0 $$PID 2>/dev/null; then \
			echo "  Running (PID: $$PID)"; \
		else \
			echo "  Not running (stale PID file)"; \
		fi; \
	elif lsof -i :8000 > /dev/null 2>&1; then \
		echo "  Running on port 8000 (no PID file)"; \
	else \
		echo "  Not running"; \
	fi

# List recent session files with details
logs:
	@echo "Session logs:"
	@echo ""
	@if [ -d logs ] && [ "$$(ls -A logs/*.json 2>/dev/null)" ]; then \
		for f in logs/session_*.json; do \
			echo "$$f"; \
			python3 -c "import json; d=json.load(open('$$f')); print(f\"  Level: {d['level']} | Query: {d['query_text'][:50]}...\" if len(d['query_text'])>50 else f\"  Level: {d['level']} | Query: {d['query_text']}\"); print(f\"  Events: {len(d['events'])} | Tokens: {d['total_tokens']}\"); print()"; \
		done; \
	else \
		echo "  No session files found"; \
	fi

# Delete all session files
clean-logs:
	@echo "This will delete all session files in logs/"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	@rm -f logs/session_*.json
	@echo "Cleaned."

# Install dependencies
install:
	uv sync
