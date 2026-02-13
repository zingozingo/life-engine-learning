---
name: weather
description: Weather forecasts and current conditions for any city worldwide
status: active
---

# Weather Skill

## When to Use

Use this skill for questions about weather, forecasts, temperature, or current conditions in any location.

## Approach

Fetch real-time weather data using the Open-Meteo API via `http_fetch`. This is a free API requiring no authentication.

1. **Geocode the city** — convert city name to coordinates:
   `http_fetch("https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1")`
   Response contains `results[0].latitude` and `results[0].longitude`.

2. **Fetch weather** — use coordinates to get current conditions and forecast:
   `http_fetch("https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weathercode,windspeed_10m&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=auto")`

For detailed API parameters, response fields, weather code reference, and formatting guide, see `references/api_reference.md`.
