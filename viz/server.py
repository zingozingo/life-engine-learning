"""FastAPI dashboard server.

Serves the visualization dashboard and provides API endpoints
for querying session data.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from viz.events import EventLogger

app = FastAPI(
    title="Travel Concierge Dashboard",
    description="Visualization dashboard for comparing engine levels",
)


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the dashboard homepage."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Travel Concierge Dashboard</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                text-align: center;
                padding: 2rem;
            }
            h1 {
                font-size: 3rem;
                margin-bottom: 0.5rem;
            }
            .subtitle {
                font-size: 1.5rem;
                opacity: 0.9;
                margin-bottom: 2rem;
            }
            .status {
                background: rgba(255,255,255,0.2);
                padding: 1rem 2rem;
                border-radius: 8px;
                display: inline-block;
            }
            .api-link {
                margin-top: 2rem;
                font-size: 0.9rem;
                opacity: 0.8;
            }
            a {
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧳 Travel Concierge</h1>
            <p class="subtitle">Multi-Level Agent Architecture Dashboard</p>
            <div class="status">🚧 Coming Soon</div>
            <p class="api-link">
                API available at <a href="/api/sessions">/api/sessions</a> |
                <a href="/docs">/docs</a>
            </p>
        </div>
    </body>
    </html>
    """


@app.get("/api/sessions")
async def list_sessions():
    """List all session summaries."""
    sessions = EventLogger.load_all_sessions()
    return [
        {
            "query_id": s.query_id,
            "level": s.level,
            "query_text": s.query_text,
            "started_at": s.started_at.isoformat(),
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "total_tokens": s.total_tokens,
            "event_count": len(s.events),
        }
        for s in sessions
    ]


@app.get("/api/sessions/{query_id}")
async def get_session(query_id: str):
    """Get a specific session by query_id."""
    from pathlib import Path

    filepath = Path("logs") / f"session_{query_id}.json"
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Session {query_id} not found")

    session = EventLogger.load_session(filepath)
    return session.model_dump()
