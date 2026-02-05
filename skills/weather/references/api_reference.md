# Open-Meteo API Reference

## Endpoint
`https://api.open-meteo.com/v1/forecast`

## Required Parameters
- `latitude`: Float (-90 to 90)
- `longitude`: Float (-180 to 180)

## Optional Parameters
- `current`: Comma-separated list of current weather variables
  - `temperature_2m`: Temperature at 2m height (°C)
  - `wind_speed_10m`: Wind speed at 10m height (km/h)
  - `relative_humidity_2m`: Relative humidity (%)
  - `precipitation`: Precipitation (mm)
  - `weather_code`: WMO weather code

## Example
```
GET /v1/forecast?latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m
```

## Weather Codes
- 0: Clear sky
- 1-3: Partly cloudy
- 45-48: Fog
- 51-55: Drizzle
- 61-65: Rain
- 71-77: Snow
- 95: Thunderstorm