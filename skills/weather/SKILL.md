---
name: weather
description: Weather forecasts and current conditions for any city worldwide
status: active
---

# Weather Skill

You can fetch real-time weather data using the Open-Meteo API via `http_fetch`. This is a free API that requires no authentication.

## Step 1: Geocode the City

First, convert the city name to coordinates:

```
http_fetch("https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1")
```

The response contains `results[0].latitude` and `results[0].longitude`.

## Step 2: Fetch Weather Data

Use the coordinates to get weather:

```
http_fetch("https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weathercode,windspeed_10m&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=auto")
```

## Weather Code Reference

| Code | Condition |
|------|-----------|
| 0 | Clear sky |
| 1-3 | Partly cloudy |
| 45-48 | Fog |
| 51-55 | Drizzle |
| 61-65 | Rain |
| 71-77 | Snow |
| 80-82 | Rain showers |
| 95 | Thunderstorm |

## Response Format

Always format weather responses with:
- **Location**: City name and country
- **Current Temperature**: In Celsius (from `current.temperature_2m`)
- **Conditions**: Human-readable from weather code
- **High/Low**: From `daily.temperature_2m_max` and `daily.temperature_2m_min`
- **Wind Speed**: In km/h from `current.windspeed_10m`

Example: "Tokyo, Japan: Currently 22°C and clear. Today's high 25°C, low 18°C. Wind: 12 km/h."

Note: All temperatures from the API are in Celsius.
