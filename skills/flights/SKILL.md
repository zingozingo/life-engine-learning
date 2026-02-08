---
name: flights
description: Search for flights between cities with prices and schedules
status: active
---

# Flights Skill

Search for available flights using the `mock_api_fetch` tool. This provides flight options between any two cities.

## How to Search

Call the mock API with flight parameters:

```
mock_api_fetch("flights", {
    "origin": "NYC",
    "destination": "LAX",
    "date": "2024-03-15"
})
```

Use 3-letter airport codes when known (JFK, LAX, LHR, NRT, CDG). For cities without known codes, use the city name and the system will resolve it.

## Response Data

The API returns a list of flight options, each containing:
- `airline`: Carrier name (e.g., "United Airlines")
- `flight_number`: Flight identifier (e.g., "UA 123")
- `departure_time`: Local departure time
- `arrival_time`: Local arrival time
- `duration`: Flight duration in hours and minutes
- `price`: Ticket price in USD
- `stops`: Number of stops (0 = direct)

## Formatting Your Response

When presenting flight results to users, include:

1. **Summary**: Number of options found and price range
2. **Flight Details**: For each flight, show:
   - Airline and flight number
   - Departure → Arrival times with duration
   - Number of stops (highlight "Direct" flights)
   - Price in USD

3. **Recommendation**: If there's an obvious best value (cheapest direct flight), mention it.

Example format:
"Found 3 flights from NYC to LAX on March 15:
1. United UA 123 - Departs 8:00 AM, arrives 11:30 AM (5h 30m) - Direct - $299
2. Delta DL 456 - Departs 2:00 PM, arrives 5:15 PM (5h 15m) - Direct - $325
3. American AA 789 - Departs 6:00 AM, arrives 12:00 PM (9h) - 1 stop - $189

The best value is AA 789 at $189, though it has one stop."
