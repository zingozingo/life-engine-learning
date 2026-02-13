---
name: visa
description: Visa requirements and travel document information
status: active
---

# Visa Skill

## When to Use

Use this skill for questions about visa requirements, entry requirements, travel documents, or whether a passport holder needs a visa for a specific destination.

## Tool Usage

```
mock_api_fetch("visa", {
    "passport": "US",
    "destination": "Japan"
})
```

Use 2-letter country codes for passports (US, UK, CA, AU, DE, FR, etc.) and full country names for destinations.

For detailed response handling, formatting examples, and edge cases, see `references/response_guide.md`.
