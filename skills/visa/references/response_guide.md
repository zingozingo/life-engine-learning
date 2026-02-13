# Visa Response Guide

## Response Data

The API returns visa information with these fields:
- `visa_required`: Boolean (true/false)
- `visa_type`: Type if required (tourist, business, transit)
- `duration_allowed`: How long you can stay
- `validity`: How long the visa is valid
- `processing_time`: Typical processing time
- `documents_needed`: List of required documents
- `cost`: Visa fee if applicable
- `notes`: Special conditions or exceptions

## Formatting Your Response

Present visa information clearly:

1. **Quick Answer**: Visa required or not (yes/no upfront)
2. **Stay Duration**: How long you can stay
3. **Requirements**: If visa needed, list:
   - Type of visa
   - Required documents
   - Processing time and cost
4. **Important Notes**: Any special conditions

### Example: Visa Not Required

"US Passport → Japan

No visa required for tourism

- Stay: Up to 90 days
- Requirements: Valid passport (6+ months), return ticket
- Note: Register address if staying 90 days

You can enter Japan visa-free for tourism or business."

### Example: Visa Required

"US Passport → India

Visa required

- Type: e-Tourist Visa (eTV)
- Stay: Up to 30 days
- Processing: 3-5 business days
- Cost: $25-100 depending on duration
- Documents: Passport copy, photo, travel itinerary

Apply online at the official visa portal before departure."
