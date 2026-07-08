# Comparison Metrics

`Comparisons.py` creates comparison PNGs for each watchlist in `watchlists.json`:

- `<watchlist> Operational Comparisons.png`
- `<watchlist> Valuation Comparisons.png`
- `<watchlist> Valuation Scatters.png`
- `<watchlist> Risk Comparisons.png`
- `<watchlist> Time Series Daily Comparisons.png`

Operational charts use about six years of history. Valuation charts and daily price-change charts use about two years of history. Scatter charts use the latest combined comparison row for each stock. Percent-based operational metrics and price changes are shown as percentages on the chart axis. Daily price-change charts can include AlphaVantage index symbols, such as `SPX`, alongside stock tickers when those symbols appear in `watchlists.json`.

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

## Valuation Scatters: `ev_ebit` to `ttm_roic`

The `Valuation Scatters` figure includes a scatter plot with:

- X-axis: `ev_ebit`
- Y-axis: `ttm_roic`

This chart compares valuation against business quality.

How to interpret it:

- Upper left is generally most attractive: high ROIC and low EV/EBIT.
- Upper right can be high quality but expensive: high ROIC and high EV/EBIT.
- Lower left can be cheap but lower quality: low ROIC and low EV/EBIT.
- Lower right is usually least attractive: low ROIC and high EV/EBIT.

The scatter plot should be read as a starting point, not a final ranking. A company with high ROIC can deserve a higher EV/EBIT if its growth and durability are better. A low EV/EBIT company may be cheap for a reason if profits are declining or cyclical.

## Valuation Scatters: `ev_fcf` to `ttm_roic`

The `Valuation Scatters` figure also includes a scatter plot with:

- X-axis: `ev_fcf`
- Y-axis: `ttm_roic`

This chart compares whole-business market valuation against return on invested capital. It is similar to the EV/EBIT scatter, but uses free cash flow instead of operating income.

How to interpret it:

- Upper left is generally most attractive: high ROIC and low EV/FCF.
- Upper right can be high quality but expensive: high ROIC and high EV/FCF.
- Lower left can be statistically cheap but lower quality: low ROIC and low EV/FCF.
- Lower right is usually least attractive: low ROIC and high EV/FCF.

EV/FCF is useful because free cash flow is the cash left after operating needs and capital expenditures. A company with high ROIC and low EV/FCF may be converting capital into attractive profits while trading at a modest cash-flow valuation. That combination can signal a potentially interesting candidate for deeper review.

Be careful with this scatter when free cash flow is temporarily distorted. Working-capital timing, unusually high or low capital expenditures, acquisitions, customer prepayments, or one-time cash items can make EV/FCF look better or worse than the normalized business. In this project, `ev_fcf` is not calculated when TTM free cash flow is zero or negative, and it is clipped at 200.

## Risk Comparisons: `ttm_roic_3yr_avg` to `ttm_roic_3yr_std`

The `Risk Comparisons` figure includes a scatter plot with:

- X-axis: `ttm_roic_3yr_avg`
- Y-axis: `ttm_roic_3yr_std`

This chart compares average return on invested capital with the volatility of that return. Both values are calculated from `ttm_roic` observations in the recent three-year window, and a summary is missing unless there are at least `MIN_HISTORY_OBSERVATIONS` valid observations.

How to interpret it:

- Lower right is generally most attractive: high average ROIC with low ROIC volatility.
- Upper right can be high quality but less predictable: high average ROIC with volatile returns.
- Lower left is stable but less profitable: low average ROIC with low volatility.
- Upper left is usually weakest: low average ROIC with high volatility.

`ttm_roic_3yr_avg` shows the recent normalized level of capital productivity. A higher value means the business has generated more after-tax operating profit per dollar of invested capital over the recent history, not just in the latest period.

`ttm_roic_3yr_std` shows how much ROIC has varied around that three-year average. A lower standard deviation suggests more consistent returns, while a higher standard deviation suggests cyclical earnings, margin instability, acquisition effects, data noise, or a business whose economics change meaningfully from period to period.

The best risk profile is usually a company that combines a high `ttm_roic_3yr_avg` with a low `ttm_roic_3yr_std`. That combination means the company has produced strong returns and has done so consistently. A high average ROIC with high volatility can still be attractive, but it needs more context because the latest ROIC may not represent the durable earning power of the business.

## Price Change Percent Graph: `close_change_perc`

The time series daily comparison figure plots:

- X-axis: `date`
- Y-axis: `close_change_perc`

This chart compares stock and index price performance over the same recent window used for valuation charts, currently about two years.

In this project, `TimeSeriesDaily.get_time_series_daily_adjusted()` requests AlphaVantage `TIME_SERIES_DAILY_ADJUSTED` data with delayed entitlement for stock tickers, saves successful responses to `data/<TICKER>/TIME_SERIES_DAILY_ADJUSTED.json`, and falls back to that saved file if the request does not return `Time Series (Daily)`.

For index symbols, `IndexData.get_index_time_series_daily()` requests AlphaVantage `INDEX_DATA` daily rows and returns filtered daily OHLC data. Index symbols are identified from the AlphaVantage index catalog loaded by `IndexData.get_index_list()`.

`Comparisons.py` filters the returned daily rows to the requested date range, sorts them by date, then calculates `close_change_perc` from the first close value in that filtered range:

```text
initial_close_value = first close in selected date range
close_change_perc = (close - initial_close_value) / initial_close_value
```

How to interpret it:

- Positive values mean the symbol's close is above the starting close for the selected range.
- Negative values mean the symbol's close is below the starting close for the selected range.
- A line that rises faster than peers shows stronger price appreciation over the selected range.
- Index lines provide market or benchmark context and are not included in operational, valuation, or score outputs.
- This graph is market-price performance only. It is not part of the quality, growth, valuation, risk, or total score.
- Price change should be read alongside business and valuation metrics. A rising stock can become expensive, and a falling stock can reflect either opportunity or deteriorating fundamentals.

## Printed Rankings

`Comparisons.py` prints each watchlist's stock rows ranked by greatest `ttm_roic`, then calculates the scored watchlist table. Index symbols are excluded from the printed operational and valuation rankings because they do not have company fundamentals.

The scored output includes:

- `quality_score`
- `growth_score`
- `valuation_score`
- `risk_score`
- `forward_score`
- `total_score`
- `quality_coverage`
- `valuation_coverage`
- `forward_coverage`
- `history_coverage`
- `classification`

Scores are percentile ranks within the current watchlist. They are useful for relative screening, not as absolute market ratings.

The valuation score combines two ideas:

- Lower current valuation multiples rank better for `pe_ttm`, `ev_ebit`, and `ev_fcf`.
- The `*_discount` fields compare the current multiple with the ticker's own two-year median as `current multiple / two-year median multiple`. Values above `1.0` mean the current multiple is above its two-year median, and these higher ratios rank better in the valuation score.

The forward score is a separate, non-ranking overlay. It does not affect `quality_score`, `growth_score`, `valuation_score`, `risk_score`, `total_score`, or `classification`.

- Lower `forward_pe` ranks better and contributes 70% of `forward_score`.
- Higher `implied_forward_eps_growth` ranks better and contributes 30% of `forward_score`.
- `implied_forward_eps_growth` is calculated as `pe_ttm / forward_pe - 1`.
- `forward_coverage` reports how many forward score inputs are available.
