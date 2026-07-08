# Forward Metrics TODO

Planning notes for adding analyst/consensus forward metrics to the watchlist scoring model.

## Goal

Add a forward-looking overlay without letting analyst estimates overpower the current accounting-driven model. The current model is strongest as a historical quality screen; forward metrics should mainly improve valuation, growth, and risk context.

## Metrics To Add

- [x] `forward_pe`
  - Lower is better.
  - Use AlphaVantage `OVERVIEW` field `ForwardPE`.
  - This is sufficient for a first forward-looking scoring upgrade; do not wait for a full consensus-estimates system.
  - Treat negative or zero forward EPS as missing, not as a zero score.

- [x] `implied_forward_eps_growth`
  - Higher is better.
  - Suggested formula: `pe_ttm / forward_pe - 1`.
  - This infers whether forward EPS is expected to be above or below trailing EPS.
  - Example: if `pe_ttm` is `28.7` and `forward_pe` is `38.8`, implied forward EPS growth is about `-26%`.
  - Use mainly as a warning/penalty signal, especially for cyclicals with excellent trailing profitability.

- [ ] `forward_ev_ebit` or `forward_ev_ebitda`
  - Lower is better.
  - Prefer for industrials, miners, utilities, and companies with different capital structures.
  - Use current enterprise value divided by consensus forward EBIT or EBITDA.
  - Defer until a reliable estimate source is available.

- [ ] `forward_fcf_yield`
  - Higher is better.
  - Suggested formula: `estimated_forward_fcf / enterprise_value`.
  - Use only when consensus FCF or enough inputs are available.
  - Defer until a reliable estimate source is available.

- [ ] `forward_revenue_growth`
  - Higher is better.
  - Suggested formula: `next_year_revenue_estimate / current_year_revenue_estimate - 1`.
  - More stable than EPS estimates, so useful in the growth bucket.
  - Defer until a reliable estimate source is available.

- [ ] `forward_eps_growth` or `forward_ebit_growth`
  - Higher is better, but cap extreme values.
  - Suggested formula: `next_year_eps_estimate / current_year_eps_estimate - 1`.
  - Treat sign changes carefully; EPS moving from negative to positive can create unusable ratios.
  - Defer in favor of `implied_forward_eps_growth` from `pe_ttm / forward_pe - 1`.

- [ ] `eps_revision_90d`
  - Higher is better.
  - Suggested formula: `current_forward_eps_estimate / forward_eps_estimate_90_days_ago - 1`.
  - Estimate revision direction may be more useful than the absolute consensus estimate.
  - Defer until estimate history is available.

- [ ] `estimate_dispersion`
  - Lower is better.
  - Suggested formula: `(high_forward_eps_estimate - low_forward_eps_estimate) / abs(mean_forward_eps_estimate)`.
  - Use as a risk component because wide dispersion means lower confidence.
  - Defer until high/low estimate data is available.

## Suggested Score Weights

Keep the four existing buckets, but modestly rebalance total score weights:

```text
quality_score:    40%
growth_score:     15%
valuation_score:  25%
risk_score:       20%
```

This reduces historical quality from 45% to 40% and increases growth from 10% to 15%. Valuation and risk stay unchanged at the top level.

## Suggested Component Weights

### Growth Score

```text
revenue_growth_yoy:            20%
revenue_growth_yoy_3yr_avg:    40%
forward_revenue_growth:        20%
forward_eps_or_ebit_growth:    20%
```

### Valuation Score

First implementation with only AlphaVantage `ForwardPE`:

```text
pe_ttm:                        10%
ev_ebit:                       18%
ev_fcf:                        22%
discount_to_own_median:        25%
forward_pe:                    25%
```

Longer-term version if broader forward estimate data becomes available:

```text
pe_ttm:                        10%
ev_ebit:                       15%
ev_fcf:                        20%
discount_to_own_median:        20%
forward_pe:                    15%
forward_ev_ebit_or_ebitda:     10%
forward_fcf_yield:             10%
```

### Risk Score

```text
debt_to_equity:                30%
ttm_fcf_margin:                30%
ttm_operating_margin:          15%
estimate_dispersion:           15%
negative_revision_penalty:     10%
```

## Cycle-Aware Adjustment

- [ ] Add a modest penalty for peak-earnings cyclicals.

Example rule:

```text
if implied_forward_eps_growth < -0.15 and ttm_roic is top quartile:
    reduce valuation_score modestly
```

This is meant for cases like high-quality miners or commodity producers where trailing returns are excellent, but analysts expect earnings to decline from cyclical highs.

## Implementation Notes

- [ ] Decide estimate source.
  - Phase 1 decision: use AlphaVantage `OVERVIEW.ForwardPE`.
  - Later candidates for richer estimate data: Yahoo Finance, Financial Modeling Prep, Polygon, Tiingo, FactSet/S&P-style exports, or manually maintained local CSV.

- [ ] Store raw estimate payloads under `data/`, similar to AlphaVantage cache behavior.
  - Phase 1 can reuse existing AlphaVantage `OVERVIEW.json` cache.

- [x] Add a normalized database table for forward estimates.
  - Phase 1 table: `forward_metrics`.
  - Implemented columns:
    - `ticker`
    - `date`
    - `forward_pe`
    - `implied_forward_eps_growth`
    - `source`
    - `updated_at`
  - Future richer estimate columns:
    - `fiscal_period`
    - `estimate_type`
    - `mean`
    - `median`
    - `high`
    - `low`
    - `analyst_count`

- [x] Add calculated forward metric outputs to the comparison row.
  - [x] `forward_pe`
  - [x] `implied_forward_eps_growth`
  - `forward_ev_ebit`
  - `forward_ev_ebitda`
  - `forward_fcf_yield`
  - `forward_revenue_growth`
  - `forward_eps_growth`
  - `eps_revision_90d`
  - `estimate_dispersion`

- [x] Add coverage fields.
  - [x] Add `forward_coverage`.
  - [ ] Penalize or classify tickers with very low forward estimate coverage.

- [ ] Keep missing estimates as `NaN`.
  - Let weighted-score availability logic handle missing values.
  - Do not fill unavailable forward metrics with zero before component scoring.

- [ ] Cap or winsorize extreme forward values.
  - Especially `forward_eps_growth`, `forward_pe`, and `estimate_dispersion`.

- [ ] Backtest ranking changes against prior snapshots before enabling the new score by default.

## Existing Scoring Detail To Change

- [ ] Change `*_discount` scoring direction in `Comparisons.py`.

Recommendation: make valuation pure lower-is-better.

Current behavior rewards higher `current multiple / two-year median multiple` ratios. Change this so lower ratios score better:

```text
current / median < 1.0  => cheaper than own history => better
current / median > 1.0  => richer than own history  => worse
```

If premium-to-history is useful, split it into a separate future signal such as `multiple_momentum_score`; do not include it in `valuation_score`.

Document the intended interpretation after changing the direction.

## Recommended Rollout

- [x] Phase 1: Add fields and charts only, with no score impact.
- [x] Phase 2: Add forward metrics to a separate `forward_score`.
- [ ] Phase 3: Blend into `growth_score`, `valuation_score`, and `risk_score`.
- [ ] Phase 4: Compare old and new rankings across at least two weeks of daily snapshots.
- [ ] Phase 5: Make the blended score the default if it improves obvious cases without destabilizing rankings.
