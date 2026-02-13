# Open-Meteo API Reference

## Geocoding API

**Endpoint:** `https://geocoding-api.open-meteo.com/v1/search`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `name` | Yes | City name to search |
| `count` | No | Number of results (default 10) |
| `language` | No | Language for results (default: en) |

**Response:**
```json
{
  "results": [
    {
      "id": 1850147,
      "name": "Tokyo",
      "latitude": 35.6895,
      "longitude": 139.69171,
      "country": "Japan",
      "admin1": "Tokyo"
    }
  ]
}
```

## Forecast API

**Endpoint:** `https://api.open-meteo.com/v1/forecast`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `latitude` | Yes | Location latitude (-90 to 90) |
| `longitude` | Yes | Location longitude (-180 to 180) |
| `current` | No | Current weather variables (comma-separated) |
| `daily` | No | Daily forecast variables (comma-separated) |
| `timezone` | No | Timezone (use "auto" for automatic) |

**Current Variables:**
- `temperature_2m` - Temperature at 2m height (°C)
- `weathercode` - WMO weather code
- `windspeed_10m` - Wind speed at 10m (km/h)
- `relative_humidity_2m` - Relative humidity (%)

**Daily Variables:**
- `temperature_2m_max` - Maximum temperature (°C)
- `temperature_2m_min` - Minimum temperature (°C)
- `weathercode` - Weather code for the day

## Weather Codes (WMO)

| Code | Description |
|------|-------------|
| 0 | Clear sky |
| 1 | Mainly clear |
| 2 | Partly cloudy |
| 3 | Overcast |
| 45 | Fog |
| 48 | Depositing rime fog |
| 51 | Light drizzle |
| 53 | Moderate drizzle |
| 55 | Dense drizzle |
| 61 | Slight rain |
| 63 | Moderate rain |
| 65 | Heavy rain |
| 71 | Slight snow |
| 73 | Moderate snow |
| 75 | Heavy snow |
| 77 | Snow grains |
| 80 | Slight rain showers |
| 81 | Moderate rain showers |
| 82 | Violent rain showers |
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
