---
name: activities
description: Local attractions, tours, restaurants, and things to do
status: active
---

# Activities Skill

## When to Use

Use this skill for questions about things to do, sightseeing, entertainment, restaurants, tours, and local experiences at a destination.

## Tool Usage

```
mock_api_fetch("activities", {
    "city": "Rome",
    "category": "attractions"
})
```

Available categories: `attractions`, `tours`, `restaurants`, `experiences`.

For detailed category descriptions, response fields, and formatting guide, see `references/category_guide.md`.
