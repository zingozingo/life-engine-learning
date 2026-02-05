---
name: weather
description: Get current weather data for any location worldwide
tools_required: [http_request]
---

# Weather Skill

You can fetch weather data using the Open-Meteo API via the http_request tool.

## How to Get Weather

1. Use method: GET
2. Use URL: https://api.open-meteo.com/v1/forecast
3. Use params:
   - latitude: The location's latitude
   - longitude: The location's longitude
   - current: Comma-separated variables like temperature_2m,wind_speed_10m,weather_code

## Example Call

For Miami weather:
http_request(
    method="GET",
    url="https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": 25.7617,
        "longitude": -80.1918,
        "current": "temperature_2m,wind_speed_10m"
    }
)

## Common City Coordinates
- Miami: 25.7617, -80.1918
- New York: 40.7128, -74.0060
- Los Angeles: 34.0522, -118.2437
- London: 51.5074, -0.1278

For other cities, use your knowledge of geography to determine coordinates.

For reference files, use read_skill_resource("weather", "references/api_reference.md").
