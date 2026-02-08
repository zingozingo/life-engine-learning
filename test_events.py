#!/usr/bin/env python3
"""Quick test of the event logging system.

This is a throwaway test script, not production code.
Run with: uv run python test_events.py
"""

from pathlib import Path

from shared.models import DecisionBy
from viz.events import EventLogger


def main():
    print("Testing event logger...\n")

    # Create logger for Level 1
    logger = EventLogger(level=1, log_dir="logs")

    # Start a query
    query_id = logger.start_query("What's the weather in Tokyo?")
    print(f"Started query: {query_id}\n")

    # Log some events
    logger.log_prompt_composed(
        query_id,
        prompt_text="You are a travel concierge assistant. You help users with weather, flights, hotels...",
        token_count=500,
        skills_included=["weather", "flights", "hotels", "activities"],
    )

    logger.log_tool_registered(query_id, "http_fetch", token_count=50)

    logger.log_llm_request(query_id, model="claude-sonnet-4-5", token_count=550)

    logger.log_tool_called(
        query_id,
        tool_name="http_fetch",
        parameters={
            "url": "https://api.open-meteo.com/v1/forecast",
            "params": {"latitude": 35.6762, "longitude": 139.6503},
        },
        result_summary='{"current": {"temperature_2m": 22, "weather_code": 0}}',
        decision_by=DecisionBy.LLM,
        duration_ms=150,
    )

    logger.log_llm_response(
        query_id,
        response_text="The weather in Tokyo is currently sunny with a temperature of 22°C. Perfect for sightseeing!",
        token_count=35,
        duration_ms=800,
    )

    # End query and get session
    session = logger.end_query(query_id)

    # Print the session JSON
    print("=" * 60)
    print("SESSION JSON:")
    print("=" * 60)
    print(session.model_dump_json(indent=2))
    print()

    # Verify file was written
    filepath = Path("logs") / f"session_{query_id}.json"
    if filepath.exists():
        print(f"✓ Session file written: {filepath}")
        print(f"✓ File size: {filepath.stat().st_size} bytes")
    else:
        print(f"✗ Session file NOT found: {filepath}")

    # Test loading it back
    loaded = EventLogger.load_session(filepath)
    print(f"✓ Session loaded back successfully")
    print(f"  - Query: {loaded.query_text}")
    print(f"  - Events: {len(loaded.events)}")
    print(f"  - Total tokens: {loaded.total_tokens}")


if __name__ == "__main__":
    main()
