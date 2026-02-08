"""FastAPI dashboard server.

Serves the visualization dashboard and provides API endpoints
for querying session data and annotations.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from viz.annotations import get_annotations, get_annotation_for_event, get_all_levels
from viz.events import EventLogger

app = FastAPI(
    title="Travel Concierge Dashboard",
    description="Visualization dashboard for comparing engine levels",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the dashboard homepage."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    # Fallback if static files not built yet
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
            .container { text-align: center; padding: 2rem; }
            h1 { font-size: 3rem; margin-bottom: 0.5rem; }
            .subtitle { font-size: 1.5rem; opacity: 0.9; margin-bottom: 2rem; }
            .status { background: rgba(255,255,255,0.2); padding: 1rem 2rem; border-radius: 8px; }
            a { color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧳 Travel Concierge</h1>
            <p class="subtitle">Multi-Level Agent Architecture Dashboard</p>
            <div class="status">🚧 Static files not found. Run from project root.</div>
        </div>
    </body>
    </html>
    """


@app.get("/api/levels")
async def list_levels():
    """List all available engine levels."""
    return get_all_levels()


@app.get("/api/annotations/{level}")
async def get_level_annotations(level: int):
    """Get annotations for a specific level."""
    if level < 1 or level > 5:
        raise HTTPException(status_code=404, detail=f"Level {level} not found")
    return get_annotations(level)


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
async def get_session(query_id: str, annotated: bool = Query(default=False)):
    """Get a specific session by query_id.

    Args:
        query_id: The session ID
        annotated: If true, include Four Questions annotations for each event
    """
    filepath = Path("logs") / f"session_{query_id}.json"
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Session {query_id} not found")

    session = EventLogger.load_session(filepath)
    result = session.model_dump()

    if annotated:
        # Add annotations to each event
        for event in result["events"]:
            event_type = event["event_type"]
            annotation = get_annotation_for_event(event_type, result["level"])
            event["annotation"] = annotation

    return result
