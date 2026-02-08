---
name: hotels
description: Search for hotels and accommodations with ratings and prices
status: active
---

# Hotels Skill

Search for hotel accommodations using the `mock_api_fetch` tool. Find options ranging from budget to luxury in any destination.

## How to Search

Call the mock API with hotel search parameters:

```
mock_api_fetch("hotels", {
    "city": "Paris",
    "checkin": "2024-03-15",
    "checkout": "2024-03-18",
    "guests": 2
})
```

## Response Data

The API returns hotel options with:
- `name`: Hotel name
- `rating`: Star rating (1-5)
- `review_score`: Guest review score (out of 10)
- `price_per_night`: Nightly rate in USD
- `total_price`: Total for the stay
- `location`: Neighborhood or area
- `amenities`: List of included amenities (WiFi, breakfast, pool, etc.)
- `distance_to_center`: Distance to city center

## Formatting Your Response

Present hotel results with:

1. **Summary**: Number of options, date range, and price range
2. **Hotel Details**: For each hotel:
   - Name with star rating (★★★★☆)
   - Review score and location
   - Price per night and total
   - Key amenities (2-3 highlights)

3. **Categories**: Group by budget tier if helpful:
   - Budget: Under $100/night
   - Mid-range: $100-250/night
   - Luxury: Over $250/night

Example format:
"Found 3 hotels in Paris for March 15-18 (3 nights):

★★★★☆ Hotel Le Marais - 8.7/10
   📍 Le Marais, 0.5 km to center
   💰 $180/night ($540 total)
   ✓ Free WiFi, Breakfast included

★★★☆☆ Ibis Bastille - 7.9/10
   📍 Bastille, 1.2 km to center
   💰 $95/night ($285 total)
   ✓ Free WiFi, 24h reception"
