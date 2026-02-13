"""Generic tools shared across engine levels.

These tools are registered on agents and can be called by the LLM.
"""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx


async def http_fetch(url: str) -> str:
    """Fetch data from a URL via HTTP GET.

    Args:
        url: The URL to fetch

    Returns:
        Response text on success, error message on failure
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.TimeoutException:
        return json.dumps({"error": "Request timed out after 10 seconds"})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}: {e.response.reason_phrase}"})
    except httpx.RequestError as e:
        return json.dumps({"error": f"Request failed: {str(e)}"})


def mock_api_fetch(endpoint: str, params: dict) -> str:
    """Fetch mock data for skills without real APIs.

    Args:
        endpoint: The API endpoint name (flights, hotels, activities, currency, visa)
        params: Query parameters

    Returns:
        Mock JSON response data
    """
    if endpoint == "flights":
        return json.dumps({
            "results": [
                {
                    "airline": "United Airlines",
                    "flight_number": "UA 234",
                    "departure_time": "08:00 AM",
                    "arrival_time": "11:30 AM",
                    "duration": "5h 30m",
                    "price": 299,
                    "stops": 0
                },
                {
                    "airline": "Delta",
                    "flight_number": "DL 567",
                    "departure_time": "02:15 PM",
                    "arrival_time": "05:45 PM",
                    "duration": "5h 30m",
                    "price": 325,
                    "stops": 0
                },
                {
                    "airline": "American Airlines",
                    "flight_number": "AA 891",
                    "departure_time": "06:00 AM",
                    "arrival_time": "01:30 PM",
                    "duration": "9h 30m",
                    "price": 189,
                    "stops": 1
                }
            ],
            "query": params
        })

    elif endpoint == "hotels":
        return json.dumps({
            "results": [
                {
                    "name": "Grand Hotel Central",
                    "rating": 4,
                    "review_score": 8.7,
                    "price_per_night": 185,
                    "location": "City Center",
                    "amenities": ["Free WiFi", "Breakfast included", "Fitness center"],
                    "distance_to_center": "0.3 km"
                },
                {
                    "name": "Comfort Inn Downtown",
                    "rating": 3,
                    "review_score": 7.9,
                    "price_per_night": 95,
                    "location": "Downtown",
                    "amenities": ["Free WiFi", "Parking", "24h reception"],
                    "distance_to_center": "1.1 km"
                },
                {
                    "name": "Luxury Palace Hotel",
                    "rating": 5,
                    "review_score": 9.4,
                    "price_per_night": 450,
                    "location": "Historic District",
                    "amenities": ["Spa", "Rooftop pool", "Fine dining", "Concierge"],
                    "distance_to_center": "0.5 km"
                }
            ],
            "query": params
        })

    elif endpoint == "activities":
        category = params.get("category", "attractions")
        if category == "restaurants":
            return json.dumps({
                "results": [
                    {
                        "name": "La Trattoria Bella",
                        "type": "Italian restaurant",
                        "rating": 4.6,
                        "review_count": 1243,
                        "price_range": "$$",
                        "description": "Authentic Italian cuisine with handmade pasta"
                    },
                    {
                        "name": "Sakura Sushi",
                        "type": "Japanese restaurant",
                        "rating": 4.8,
                        "review_count": 892,
                        "price_range": "$$$",
                        "description": "Premium omakase and fresh sashimi"
                    }
                ],
                "query": params
            })
        else:
            return json.dumps({
                "results": [
                    {
                        "name": "National Museum",
                        "type": "Museum",
                        "rating": 4.7,
                        "review_count": 15420,
                        "price_range": "$15 entry",
                        "duration": "2-3 hours",
                        "description": "World-class art and historical exhibits"
                    },
                    {
                        "name": "Historic Walking Tour",
                        "type": "Guided tour",
                        "rating": 4.9,
                        "review_count": 3200,
                        "price_range": "$25 per person",
                        "duration": "3 hours",
                        "description": "Expert-led tour of historic landmarks"
                    },
                    {
                        "name": "Central Park",
                        "type": "Park",
                        "rating": 4.8,
                        "review_count": 45000,
                        "price_range": "Free",
                        "duration": "1-4 hours",
                        "description": "Iconic urban park perfect for walking and picnics"
                    }
                ],
                "query": params
            })

    elif endpoint == "currency":
        # Static exchange rates for reproducibility
        rates = {
            ("USD", "EUR"): 0.92,
            ("USD", "GBP"): 0.79,
            ("USD", "JPY"): 149.50,
            ("EUR", "USD"): 1.09,
            ("EUR", "GBP"): 0.86,
            ("GBP", "USD"): 1.27,
            ("GBP", "EUR"): 1.16,
            ("JPY", "USD"): 0.0067,
        }
        from_curr = params.get("from", "USD")
        to_curr = params.get("to", "EUR")
        amount = params.get("amount", 100)
        rate = rates.get((from_curr, to_curr), 1.0)
        converted = round(amount * rate, 2)

        return json.dumps({
            "from_currency": from_curr,
            "to_currency": to_curr,
            "amount": amount,
            "rate": rate,
            "converted": converted,
            "updated_at": "2024-03-15T12:00:00Z"
        })

    elif endpoint == "visa":
        # Mock visa data for common routes
        passport = params.get("passport", "US")
        destination = params.get("destination", "").lower()

        # Visa-free destinations for US passport
        visa_free = ["japan", "uk", "france", "germany", "italy", "spain", "canada", "mexico"]

        if destination in visa_free:
            return json.dumps({
                "visa_required": False,
                "duration_allowed": "90 days",
                "documents_needed": ["Valid passport", "Return ticket", "Proof of accommodation"],
                "notes": "Passport must be valid for at least 6 months beyond travel dates"
            })
        else:
            return json.dumps({
                "visa_required": True,
                "visa_type": "Tourist Visa",
                "duration_allowed": "30 days",
                "validity": "6 months",
                "processing_time": "5-10 business days",
                "documents_needed": [
                    "Valid passport",
                    "Completed application form",
                    "Passport photo",
                    "Proof of travel itinerary",
                    "Bank statements"
                ],
                "cost": "$50-100",
                "notes": "Apply at least 2 weeks before travel"
            })

    else:
        return json.dumps({
            "error": f"Unknown endpoint: {endpoint}",
            "available_endpoints": ["flights", "hotels", "activities", "currency", "visa"]
        })


def get_current_datetime(timezone: str = "UTC") -> str:
    """Get current date, time, and timezone information.

    Args:
        timezone: IANA timezone identifier (e.g., 'UTC', 'America/New_York', 'Asia/Tokyo')

    Returns:
        Formatted JSON string with current date, time, day of week, and timezone info
    """
    try:
        tz = ZoneInfo(timezone)
    except (KeyError, Exception):
        return json.dumps({
            "error": f"Unknown timezone: {timezone}. Use IANA timezone identifiers like 'UTC', 'America/New_York', 'Asia/Tokyo'."
        })

    now = datetime.now(tz)
    return json.dumps({
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "day_of_week": now.strftime("%A"),
        "timezone": timezone,
        "utc_offset": now.strftime("%z"),
        "iso": now.isoformat(),
    })
