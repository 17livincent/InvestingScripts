# Notes

## Raw Data Layer

Store raw AlphaVantage payloads.
Tables:
- income_statement
- balance_sheet
- cash_flow
- weekly_prices
- shares_outstanding

## Derived Metrics Layer

Store calculated metrics.

Table:
- operational_metrics
- valuation_metrics

Columns:
- ticker
- date
- ttm_roic
- ttm_operating_margin
- pe_ttm
- ev_ebit
- etc.

## Incremental Updates

1. Check raw data layer.  Check how recent the latest month and weekly metrics were.  If so, update them.

2. Update derived tables which are the filtered raw data.

3. Then update calculated tables which are based on the derived tables.

4. From there, query the derived and calculated tables.
