---
name: activities
description: Local attractions, tours, restaurants, and things to do
status: active
---

# Activities Skill

Discover local attractions, tours, restaurants, and experiences using the `mock_api_fetch` tool.

## How to Search

Call the mock API with activity search parameters:

```
mock_api_fetch("activities", {
    "city": "Rome",
    "category": "attractions"  // or "tours", "restaurants", "experiences"
})
```

Categories:
- `attractions`: Museums, landmarks, parks
- `tours`: Guided tours, day trips
- `restaurants`: Dining recommendations
- `experiences`: Unique local activities

## Response Data

The API returns activities with:
- `name`: Activity or venue name
- `type`: Specific type (museum, walking tour, trattoria, etc.)
- `rating`: Guest rating (out of 5)
- `review_count`: Number of reviews
- `price_range`: $ to $$$$ or specific prices for tours
- `duration`: Time needed (for tours/attractions)
- `description`: Brief description
- `highlights`: Key features or must-sees

## Formatting Your Response

Present activities in a browsable format:

1. **Category Header**: What type of activities you're showing
2. **Activity Cards**: For each activity:
   - Name with type
   - Rating with review count
   - Price range or specific cost
   - Duration if applicable
   - Brief description (1-2 sentences)

3. **Pro Tips**: Add local insights when relevant (best time to visit, reservations needed, etc.)

Example format:
"Top Attractions in Rome:

🏛️ Colosseum
   Ancient amphitheater • ★★★★★ (45,230 reviews)
   💰 €16 entry • ⏱️ 2-3 hours
   Iconic Roman arena, best visited early morning to avoid crowds.

🎨 Vatican Museums
   Art museum • ★★★★★ (38,100 reviews)
   💰 €17 entry • ⏱️ 3-4 hours
   Home to the Sistine Chapel. Book tickets online to skip lines.

💡 Tip: Get the Roma Pass for free public transport and museum discounts!"
