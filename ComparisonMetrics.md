# Comparison Metrics

`Comparisons.py` creates two comparison PNGs for each watchlist in `watchlists.json`:

- `<watchlist> Operational Comparisons.png`
- `<watchlist> Valuation Comparisons.png`

Operational charts use about six years of history. Valuation charts use about two years of history. Percent-based operational metrics are shown as percentages on the chart axis.

This file describes the metrics graphed by `Comparisons.py`, how they are calculated in this project, and how to read higher or lower values.

## General Interpretation

No single metric is enough to judge a company. Operational metrics describe business quality and trend. Valuation metrics describe how much the market is currently paying for that business quality. The most useful comparisons are usually between similar companies, similar business models, or a single company through time.

Negative, missing, or clipped values need extra care:

- `NaN` values appear when the denominator is zero, negative, or missing.
- `pe_ttm` is only calculated when TTM net income is positive and is clipped at 200.
- `ev_ebit` is only calculated when TTM operating income is positive and is clipped at 100.
- `ev_fcf` is only calculated when TTM free cash flow is positive and is clipped at 200.
- Extremely high valuation ratios often mean the business is expensive, temporarily depressed, barely profitable, or the metric is not useful for that period.

## Operational Metrics

### `ttm_roic`

Trailing twelve month return on invested capital.

In this project:

```text
NOPAT = operating_income * (1 - effective_tax_rate)
invested_capital = total_debt + shareholder_equity - cash
ttm_roic = TTM NOPAT / 4-quarter average invested_capital
```

Higher is generally better. A higher ROIC means the company is producing more after-tax operating profit for each dollar of capital tied up in the business.

How to interpret it:

- Rising ROIC usually suggests improving business quality, better capital allocation, operating leverage, or stronger margins.
- Falling ROIC can suggest weakening profitability, overinvestment, margin pressure, acquisitions that are not earning enough, or cyclicality.
- Very high ROIC is attractive when it is durable, but compare it with growth and valuation. A great business can still be a poor investment if the market price is too high.
- Negative or missing ROIC means the company is losing operating money, has invalid invested capital, or has unusable source data for the period.

### `revenue_growth_yoy`

Year-over-year quarterly revenue growth.

In this project:

```text
revenue_growth_yoy = current quarter total_revenue / total_revenue 4 quarters ago - 1
```

Higher is generally better, as long as the growth is profitable and sustainable.

How to interpret it:

- Positive growth means revenue is higher than the same quarter one year earlier.
- Faster growth is usually valuable when margins and returns on capital remain strong.
- Slowing growth can be normal for mature companies, but sharp declines may indicate demand weakness, pricing pressure, lost share, or cyclicality.
- Negative growth is not always bad for cyclical companies, but it deserves context.
- Revenue growth without good margins or ROIC can destroy value if it requires too much capital or comes from low-quality sales.

### `ttm_operating_margin`

Trailing twelve month operating margin.

In this project:

```text
ttm_operating_margin = TTM operating_income / TTM total_revenue
```

Higher is generally better. A higher operating margin means more revenue turns into operating profit before interest and taxes.

How to interpret it:

- Rising margins can indicate better pricing power, cost control, scale benefits, or a richer product mix.
- Falling margins can indicate competitive pressure, input cost inflation, discounting, weaker utilization, or investment spending.
- Compare margins within the same industry. Software, payments, retailers, manufacturers, and banks have very different normal margin ranges.
- A lower-margin business can still be attractive if it has high asset turnover, durable growth, or a low valuation.

### `ttm_fcf_margin`

Trailing twelve month free cash flow margin.

In this project:

```text
free_cash_flow = operating_cash_flow - capital_expenditures
ttm_fcf_margin = TTM free_cash_flow / TTM total_revenue
```

Higher is generally better. A higher FCF margin means more revenue becomes cash that can be used for reinvestment, debt repayment, buybacks, dividends, or acquisitions.

How to interpret it:

- Rising FCF margin is often a strong sign because cash generation is improving relative to sales.
- Falling FCF margin can indicate lower profitability, higher working-capital needs, heavier capital spending, or temporary timing effects.
- Negative FCF margin means the company consumed cash over the trailing year.
- FCF can be lumpy. Large capital expenditure cycles, inventory builds, customer prepayments, or one-time cash items can distort short periods.

## Valuation Metrics

### `pe_ttm`

Trailing price-to-earnings ratio.

In this project:

```text
market_cap = diluted_shares * adjusted_close
pe_ttm = market_cap / TTM net_income
```

Lower is generally cheaper, but not automatically better. P/E tells you how much the market is paying for each dollar of trailing net income.

How to interpret it:

- A lower P/E can indicate a cheaper stock, lower growth expectations, higher perceived risk, or temporarily elevated earnings.
- A higher P/E can indicate an expensive stock, strong expected growth, high business quality, or temporarily depressed earnings.
- P/E is not calculated when TTM net income is zero or negative.
- P/E is less useful for cyclical companies near profit troughs or peaks because trailing earnings may not represent normalized earnings.

### `ev_ebit`

Enterprise value to trailing operating income.

In this project:

```text
enterprise_value = market_cap + total_debt - cash
ev_ebit = enterprise_value / TTM operating_income
```

Lower is generally cheaper, but not automatically better. EV/EBIT compares the value of the whole business, including debt and cash, to operating profit before interest and taxes.

How to interpret it:

- Lower EV/EBIT usually means investors are paying less for each dollar of operating earnings.
- Higher EV/EBIT can be justified by stronger growth, higher ROIC, more durable earnings, or lower business risk.
- EV/EBIT is often better than P/E when comparing companies with different debt levels or tax rates.
- EV/EBIT is not calculated when TTM operating income is zero or negative.

### `ev_fcf`

Enterprise value to trailing free cash flow.

In this project:

```text
enterprise_value = market_cap + total_debt - cash
free_cash_flow = operating_cash_flow - capital_expenditures
ev_fcf = enterprise_value / TTM free_cash_flow
```

Lower is generally cheaper, but not automatically better. EV/FCF compares the value of the whole business to the cash it generated over the trailing year.

How to interpret it:

- Lower EV/FCF usually means investors are paying less for each dollar of free cash flow.
- Higher EV/FCF can be reasonable for companies with durable high growth, unusually strong reinvestment opportunities, or temporarily depressed free cash flow.
- EV/FCF is especially useful for mature companies where free cash flow is stable and recurring.
- EV/FCF can be misleading when free cash flow is temporarily boosted or depressed by working capital, capital expenditure timing, or one-time cash items.
- EV/FCF is not calculated when TTM free cash flow is zero or negative.

## Scatter Plot: `ev_ebit` to `ttm_roic`

The valuation comparison figure includes a scatter plot with:

- X-axis: `ev_ebit`
- Y-axis: `ttm_roic`

This chart compares valuation against business quality.

How to interpret it:

- Upper left is generally most attractive: high ROIC and low EV/EBIT.
- Upper right can be high quality but expensive: high ROIC and high EV/EBIT.
- Lower left can be cheap but lower quality: low ROIC and low EV/EBIT.
- Lower right is usually least attractive: low ROIC and high EV/EBIT.

The scatter plot should be read as a starting point, not a final ranking. A company with high ROIC can deserve a higher EV/EBIT if its growth and durability are better. A low EV/EBIT company may be cheap for a reason if profits are declining or cyclical.

## Printed Rankings

`Comparisons.py` also prints watchlist tables ranked two ways:

- Greatest `ttm_roic`: favors higher business returns.
- Lowest `pe_ttm`: favors lower earnings multiples.

The script also calculates `ROIC_EV_SCORE` in the printed comparison table:

```text
ROIC_EV_SCORE = ttm_roic / ev_ebit
```

Higher is generally better for this score because it combines higher business returns with a lower EV/EBIT multiple. Treat it as a rough screen only. It can overstate companies with temporarily high ROIC, temporarily low EV/EBIT, cyclical earnings, or stale data.
