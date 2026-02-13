# Activities Category Guide

## Categories

- **attractions**: Museums, landmarks, parks, historical sites
- **tours**: Guided tours, day trips, walking tours
- **restaurants**: Dining recommendations by cuisine and price
- **experiences**: Unique local activities, classes, workshops

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

### Example

"Top Attractions in Rome:

Colosseum
   Ancient amphitheater — 4.8/5 (45,230 reviews)
   $16 entry — 2-3 hours
   Iconic Roman arena, best visited early morning to avoid crowds.

Vatican Museums
   Art museum — 4.9/5 (38,100 reviews)
   $17 entry — 3-4 hours
   Home to the Sistine Chapel. Book tickets online to skip lines.

Tip: Get the Roma Pass for free public transport and museum discounts!"
