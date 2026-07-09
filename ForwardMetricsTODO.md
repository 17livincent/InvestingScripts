# Forward Metrics TODO

Planning notes for adding AlphaVantage `OVERVIEW` forward metrics to the standalone `forward_score`.

## Goal

Add a forward-looking overlay without letting analyst estimates overpower the current accounting-driven model. The current model is strongest as a historical quality screen; `forward_score` should remain a separate context score rather than being blended into the main `total_score` until ranking changes are reviewed.

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

- [ ] `peg_ratio`
  - Lower is better.
  - Use AlphaVantage `OVERVIEW` field `PEGRatio`.
  - Treat negative, zero, or missing PEG values as missing, not as a zero score.
  - Cap or winsorize extreme values before ranking so stale or distorted analyst-growth assumptions do not dominate `forward_score`.

## Forward Score Weights

Current raised implementation using AlphaVantage `OVERVIEW` only:

```text
forward_pe:                    50%
peg_ratio:                     30%
implied_forward_eps_growth:    20%
```

This keeps `forward_score` valuation-led while adding a growth-adjusted valuation signal. `implied_forward_eps_growth` remains a smaller warning/confirmation signal so PEG and implied growth do not double-count analyst growth too heavily.

## Implementation Notes

- [ ] Decide estimate source.
  - Use AlphaVantage `OVERVIEW.ForwardPE`.
  - Use AlphaVantage `OVERVIEW.PEGRatio`.

- [ ] Store raw estimate payloads under `data/`, similar to AlphaVantage cache behavior.
  - Reuse existing AlphaVantage `OVERVIEW.json` cache.

- [x] Add a normalized database table for forward estimates.
  - Table: `forward_metrics`.
  - Implemented columns:
    - `ticker`
    - `date`
    - `forward_pe`
    - `implied_forward_eps_growth`
    - `source`
    - `updated_at`
  - Next columns:
    - `peg_ratio`

- [x] Add calculated forward metric outputs to the comparison row.
  - [x] `forward_pe`
  - [x] `implied_forward_eps_growth`
  - [ ] `peg_ratio`

- [x] Add coverage fields.
  - [x] Add `forward_coverage`.
  - [ ] Penalize or classify tickers with very low forward estimate coverage.

- [ ] Keep missing estimates as `NaN`.
  - Let weighted-score availability logic handle missing values.
  - Do not fill unavailable forward metrics with zero before component scoring.

- [ ] Cap or winsorize extreme forward values.
  - Especially `forward_pe` and `peg_ratio`.

- [ ] Backtest ranking changes against prior snapshots before enabling the new score by default.

## Recommended Rollout

- [x] Phase 1: Add fields and charts only, with no score impact.
- [x] Phase 2: Add forward metrics to a separate `forward_score`.
- [ ] Phase 3: Add `peg_ratio` to `forward_metrics`, comparison output, and `forward_score`.
- [ ] Phase 4: Compare old and new `forward_score` rankings across at least two weeks of daily snapshots.
