---
name: currency
description: Exchange rates and currency conversion for travel budgeting
status: active
---

# Currency Skill

Convert between currencies and check exchange rates using the `mock_api_fetch` tool. Useful for travel budgeting and price comparisons.

## How to Convert

Call the mock API with conversion parameters:

```
mock_api_fetch("currency", {
    "amount": 500,
    "from": "USD",
    "to": "EUR"
})
```

Use standard 3-letter currency codes:
- USD (US Dollar), EUR (Euro), GBP (British Pound)
- JPY (Japanese Yen), CNY (Chinese Yuan)
- AUD (Australian Dollar), CAD (Canadian Dollar)
- CHF (Swiss Franc), INR (Indian Rupee)
- MXN (Mexican Peso), BRL (Brazilian Real)

## Response Data

The API returns:
- `from_currency`: Source currency code
- `to_currency`: Target currency code
- `amount`: Original amount
- `rate`: Exchange rate
- `converted`: Converted amount
- `updated_at`: Rate timestamp

## Formatting Your Response

Present conversions clearly:

1. **Conversion Result**: Show the converted amount prominently
2. **Exchange Rate**: Include the rate for reference
3. **Inverse Rate**: Optionally show the reverse conversion rate
4. **Context**: For travel, mention what typical items cost in that currency

Example format:
"💱 Currency Conversion

500.00 USD = 460.50 EUR

Exchange Rate: 1 USD = 0.921 EUR
(1 EUR = 1.086 USD)

For context in the Eurozone:
- Coffee: €3-5
- Metro ticket: €2-3
- Mid-range dinner: €25-40"

## Budget Estimation

When users mention travel budgets, help them understand purchasing power:
- Compare typical costs (meals, transport, accommodation)
- Note if the destination is generally cheaper or more expensive than their home currency
