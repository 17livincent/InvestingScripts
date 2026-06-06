---
name: stock-analyzer-trader
description: Analyze medium- to long-term stock candidates using this InvestingScripts repository's computed operational metrics, valuation metrics, watchlist rankings, comparison JSON files, and generated charts. Use when Codex is asked to interpret watchlist rankings, compare tickers as long-term investments, explain why a stock's metric changed versus another ticker, suggest relevant peer tickers to add to a watchlist, recommend new metrics or script augmentations, improve scoring or classifications based on observed outperformance, or combine this repo's quantitative outputs with current company or market context.
---

# Stock Analyzer Trader

## Overview

Use this skill to turn this repository's calculated stock metrics into practical screening judgment for medium- to long-term investing. Anchor conclusions in the project's computed data, then add qualitative context about business quality, durability, valuation, risk, and relevant current or historical events.

## Core Workflow

1. Identify the requested universe: a watchlist name from `watchlists.json`, specific tickers, or a comparison file under `data/*_Comparison.json`.
2. Load the computed outputs before forming a view:
   - `watchlists.json` for ticker membership.
   - `data/<WATCHLIST>_Comparison.json` for scored rows, coverage fields, classifications, and latest metric values.
   - `data/* Operational Comparisons.png` and `data/* Valuation Comparisons.png` when visual trend or chart interpretation is requested.
   - `ComparisonMetrics.md` when metric definitions or interpretation details are needed.
   - Source scripts such as `Comparisons.py`, `OperationalMetrics.py`, and `ValuationMetrics.py` when a calculation detail is unclear.
   - Underlying fundamentals, shares, prices, or saved payloads when the investment judgment depends on the drivers behind a ratio.
3. Separate what the data says from what is inferred. State whether a claim comes from computed metrics, current-event research, industry knowledge, or an inference.
4. Prefer relative, watchlist-specific conclusions. Scores are percentile ranks within the current watchlist, not absolute market ratings.
5. Check whether the watchlist is industry-consistent before trusting ranks. Prefer watchlists built around one industry, sub-industry, or set of economically similar business models; flag mixed watchlists as screening-only because margins, leverage, capital intensity, and valuation norms may not be comparable.
6. Frame outputs for at least a one-year holding period. Emphasize durable business performance, balance-sheet risk, valuation discipline, and whether current price expectations look reasonable versus the company's quality and growth.

## Quantitative Lens

Prioritize these dimensions:

- Quality: `quality_score`, `ttm_roic`, `ttm_roic_3yr_avg`, `ttm_roic_3yr_std`, `ttm_operating_margin`, and `ttm_fcf_margin`.
- Growth: `growth_score`, current `revenue_growth_yoy`, and `revenue_growth_yoy_3yr_avg`.
- Valuation: `valuation_score`, `pe_ttm`, `ev_ebit`, `ev_fcf`, and current multiple versus two-year median discount fields.
- Risk: `risk_score`, `debt_to_equity`, free-cash-flow margin, operating margin, missing data, negative denominators, and cyclical exposure.
- Owner economics: revenue per share, FCF per share, EPS per share, share-count trend, dilution, buybacks, and dividends when available or worth adding.
- Data quality: `quality_coverage`, `valuation_coverage`, `history_coverage`, and `classification`.

Use `total_score` as a starting rank, not the final answer. Explain the component tradeoffs behind it, especially when a company ranks highly because of valuation but has weaker quality, or ranks lower because a strong business is expensive.

When coverage is below 0.6 or `classification` is `Incomplete data`, avoid strong conclusions. Explain which missing metrics would matter most before judging the stock.

When a conclusion depends on metric durability, inspect raw drivers instead of relying only on ratios: revenue, operating income, net income, operating cash flow, capital expenditures, debt, cash, share count, and invested capital.

## Watchlist Analysis

For prompts like "analyze this watchlist" or "interpret these rankings":

1. Summarize the top candidates by total score and classification.
2. State whether the watchlist is industry- or business-model-consistent. Recommend splitting it into per-industry or similar-industry watchlists when comparisons mix structurally different companies.
3. Call out quality leaders, growth leaders, valuation bargains, and risk outliers separately.
4. Identify disagreements between the score and the business narrative, such as:
   - High quality but expensive valuation.
   - Cheap valuation with weak growth or declining returns.
   - Strong current metrics but weak three-year consistency.
   - Good operating margins but poor free-cash-flow conversion.
5. Mention data gaps and stale or missing rows before making recommendations.
6. End with a ranked short list and the key metric/event that could change the view.

## Ticker Versus Ticker

For prompts comparing ticker X and ticker Y:

1. Compare quality, growth, valuation, risk, and data coverage side by side.
2. Check whether the companies are economically comparable. If they are not, explain which metrics become less useful and which industry-specific lens is needed.
3. Ask what expectations the current valuation embeds: growth, margin durability, capital intensity, and multiple stability. Use a compact base/bull/bear or implied-expectations framing when the decision is close.
4. Decide which looks more attractive for a long-term investor only after explaining the tradeoff and margin of safety.
5. Favor the company with more durable ROIC, stronger free-cash-flow generation, better per-share compounding, cleaner balance sheet, and a valuation that does not require heroic growth assumptions.
6. If one ticker is cheaper but structurally weaker, say so directly.
7. If the metrics are too close or coverage is poor, state that the conclusion is low-confidence and explain what additional evidence would break the tie.

## Peer Suggestions

For prompts asking what tickers to add to a watchlist:

1. Inspect the existing watchlist theme and current constituents.
2. Recommend keeping watchlists per-industry, sub-industry, or economically similar business model whenever practical.
3. Search current public sources for relevant public-company peers, competitors, suppliers, or adjacent business models when the set could have changed.
4. Prefer comparable business models, market exposures, and financial profiles so the repo's percentile scoring remains meaningful.
5. Provide a concise rationale for each ticker and flag any that may require different metrics to evaluate well, such as banks, insurers, REITs, highly cyclical commodity businesses, or unprofitable growth companies.

## Metric And Script Augmentations

For prompts asking what other metrics or script changes would create more insight:

1. Start from the user's decision need: quality screening, valuation discipline, risk control, peer comparison, event diagnosis, or score improvement.
2. Identify blind spots in the current model before proposing additions. Common gaps include:
   - Per-share compounding: revenue per share, EPS per share, FCF per share, and share-count CAGR.
   - Capital allocation: buyback yield, share count dilution, dividend payout, acquisition intensity, and reinvestment rate.
   - Balance-sheet durability: net debt to EBITDA or EBIT, interest coverage, cash conversion, and debt maturity context when available.
   - Earnings quality: accruals, operating cash flow versus net income, stock-based compensation, working-capital swings, and one-time items.
   - Growth quality: gross margin trend, operating leverage, revenue volatility, organic versus acquired growth, and segment concentration.
   - Valuation context: free-cash-flow yield, earnings yield, sales multiple for low-margin businesses, historical percentile bands, and sector-relative multiples.
   - Price behavior: one-year and three-year total return, drawdown, volatility, and relative strength versus peers or a benchmark.
3. Recommend augmentations in implementation-sized chunks. Name the affected scripts or tables, the input data needed, the formula or method, and why the metric would improve decisions.
4. Prefer metrics available from existing AlphaVantage payloads and saved data before proposing new data vendors.
5. Flag metrics that are industry-specific or dangerous to compare across mixed watchlists.

## Scoring Improvement From Outcomes

For prompts like "how can scoring improve knowing ticker X outperformed ticker Y":

1. Treat observed outperformance as evidence to investigate, not proof that every current weight is wrong.
2. Define the outcome precisely: start date, end date, price return versus total return, benchmark, and whether the comparison should include drawdown or volatility.
3. Reconstruct what the model would have known at the start of the period. Avoid using later fundamentals, revised ranks, or future events as if they were known at decision time.
4. Compare the old signal profile for X and Y:
   - Which component favored the winner: quality, growth, valuation, risk, history, or coverage?
   - Which component incorrectly penalized or over-rewarded a ticker?
   - Did missing data, clipping, sector mismatch, or cyclicality distort the rank?
5. Attribute the stock return before changing the scoring model. Separate business performance from multiple expansion or contraction, starting valuation, buybacks, dividends, sector beta, macro rates, narrative shifts, and one-time events.
6. Propose scoring changes as hypotheses, such as adjusting weights, adding a metric, changing classification thresholds, adding sector-specific rules, or using valuation relative to history rather than only peers.
7. Recommend validation before adopting changes. Prefer simple walk-forward tests across multiple tickers and dates, with guardrails against overfitting to one pair.
8. If the user asks for code changes, implement the narrowest practical scoring experiment and preserve the current baseline for comparison.

## Event And Metric Explanations

For prompts asking why a metric improved or worsened over a time frame:

1. Identify the metric definition from `ComparisonMetrics.md` or the calculation scripts.
2. Inspect the relevant computed history when available, not just the latest row.
3. Break the metric into drivers. For example:
   - ROIC: operating income, tax rate, debt, equity, cash, and invested capital.
   - Operating margin: revenue mix, pricing, cost structure, and operating expenses.
   - FCF margin: operating cash flow, capital expenditures, and working capital timing.
   - Valuation multiples: market cap, share count, debt, cash, and trailing earnings or cash flow.
4. Use current and historical public sources for company-specific events, earnings commentary, acquisitions, divestitures, regulation, litigation, macro cycles, or sector shocks that may explain the change.
5. Distinguish confirmed causes from plausible explanations when source data does not prove causality.

## Research Rules

Browse or otherwise verify current facts whenever the answer depends on recent information, including peer suggestions, management changes, earnings commentary, macro events, regulation, litigation, recent stock moves, or "today/latest/current" framing.

Use primary or high-quality sources where possible:

- Company filings, investor relations, earnings releases, and transcripts.
- Regulator or court documents for legal and regulatory matters.
- Reputable financial news for recent events.
- Exchange, index, or company pages for ticker identity and listing status.

Do not present personalized financial advice. Phrase conclusions as research judgments based on the available data, time horizon, and assumptions.

## Output Style

Keep the answer decision-oriented:

- Lead with the conclusion or ranked view when the user asks for a decision.
- Include the 3-6 most important metrics rather than every column.
- Use compact tables for direct ticker comparisons.
- Include citations when web research is used.
- State confidence, the thesis, key risks, valuation/margin-of-safety view, and what evidence would change the conclusion.
