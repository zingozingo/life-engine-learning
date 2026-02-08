# Life Engine Learning - Developer Commands
# Run `make help` to see available commands

.PHONY: help chat dashboard start stop restart status logs clean-logs install

# Default target
help:
	@echo "Life Engine Learning - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "  make dashboard       Start dashboard server (background)"
	@echo "  make chat [level=N]  Run chatbot (default level=1)"
	@echo "  make start           Start dashboard (if needed) + chat"
	@echo "  make stop            Stop dashboard server"
	@echo "  make restart         Restart dashboard server"
	@echo "  make status          Show what's running"
	@echo "  make logs            List recent session files"
	@echo "  make clean-logs      Delete all session files"
	@echo "  make install         Install dependencies (uv sync)"
	@echo ""
	@echo "Dashboard is a persistent service. Chat sessions are independent."
	@echo "Start dashboard once, run multiple chat sessions, stop when done."
	@echo ""

# Default level for chat
level ?= 1

# Start dashboard server in background (idempotent - safe to call multiple times)
dashboard:
	@if lsof -i :8000 > /dev/null 2>&1; then \
		echo "Dashboard already running at http://localhost:8000"; \
	else \
		echo "Starting dashboard..."; \
		uv run uvicorn viz.server:app --port 8000 > /dev/null 2>&1 & echo $$! > .dashboard.pid; \
		sleep 2; \
		if lsof -i :8000 > /dev/null 2>&1; then \
			echo "Dashboard running at http://localhost:8000"; \
			open http://localhost:8000 2>/dev/null || true; \
		else \
			echo "Failed to start dashboard"; \
			rm -f .dashboard.pid; \
			exit 1; \
		fi; \
	fi

# Run the chatbot interactively (dashboard-independent)
chat:
	@uv run python main.py $(level)

# Start dashboard (if not running) then start chat
start: dashboard
	@echo ""
	@$(MAKE) -s chat level=$(level)

# Stop the dashboard server
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
	@PID=$$(lsof -ti :8000 2>/dev/null); \
	if [ -n "$$PID" ]; then \
		kill $$PID 2>/dev/null; \
		echo "Stopped process on port 8000 (PID: $$PID)"; \
	fi
	@if ! lsof -i :8000 > /dev/null 2>&1; then \
		echo "Dashboard stopped"; \
	fi

# Restart the dashboard
restart: stop dashboard

# Show what's running
status:
	@echo "Dashboard status:"
	@if lsof -i :8000 > /dev/null 2>&1; then \
		PID=$$(lsof -ti :8000 2>/dev/null); \
		echo "  Running at http://localhost:8000 (PID: $$PID)"; \
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
