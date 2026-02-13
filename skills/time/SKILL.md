---
name: time
description: Get current date, time, and timezone information. Use for any question involving today's date, current time, day of the week, or when the user references relative dates like 'tomorrow', 'next week', 'this weekend'.
status: active
---

# Time Skill

## When to Use

Use this skill for any query that references:
- Current date or time ("what day is it?", "what time is it?")
- Relative dates ("tomorrow", "next week", "this Friday", "this weekend")
- Day of the week ("is today Monday?")
- Timezone conversions ("what time is it in Tokyo?")
- Date context for other skills ("find me a flight for tomorrow" — call this first to resolve "tomorrow" to a concrete date)

## Tool Usage

```
get_current_datetime("UTC")
```

Pass a timezone identifier to get the current date and time in that timezone. Defaults to UTC if no timezone is specified.

### Common Timezone Identifiers

- `America/New_York` — US Eastern
- `America/Chicago` — US Central
- `America/Denver` — US Mountain
- `America/Los_Angeles` — US Pacific
- `Europe/London` — UK
- `Europe/Paris` — Central Europe
- `Europe/Berlin` — Central Europe
- `Asia/Tokyo` — Japan
- `Asia/Shanghai` — China
- `Asia/Kolkata` — India
- `Australia/Sydney` — Australia Eastern
- `Pacific/Auckland` — New Zealand

## Example Workflow

User: "Find me a flight for tomorrow from NYC to LA"

1. Call `get_current_datetime("America/New_York")` to get today's date
2. Compute tomorrow's date from the result
3. Call `mock_api_fetch("flights", {"origin": "NYC", "destination": "LAX", "date": "..."})` with the resolved date
