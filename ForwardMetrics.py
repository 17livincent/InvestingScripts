"""
Parse and calculate forward-looking metrics from AlphaVantage OVERVIEW data.
"""

from datetime import datetime, timezone
import math

import numpy as np
import pandas as pd


FORWARD_METRICS_SOURCE = "AlphaVantage OVERVIEW"


def get_positive_float(value):
    positive_float = np.nan

    if value not in (None, "", "None", "null", "-"):
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            numeric_value = np.nan

        if math.isfinite(numeric_value) and numeric_value > 0:
            positive_float = numeric_value

    return positive_float


def calculate_implied_forward_eps_growth(pe_ttm, forward_pe):
    pe_ttm = get_positive_float(pe_ttm)
    forward_pe = get_positive_float(forward_pe)
    implied_forward_eps_growth = np.nan

    if pd.notna(pe_ttm) and pd.notna(forward_pe):
        implied_forward_eps_growth = pe_ttm / forward_pe - 1

    return implied_forward_eps_growth


def get_forward_metrics_from_overview(overview_json, pe_ttm=None, as_of_date=None):
    forward_pe = get_positive_float(overview_json.get("ForwardPE"))
    implied_forward_eps_growth = calculate_implied_forward_eps_growth(pe_ttm, forward_pe)

    if as_of_date is None:
        as_of_date = datetime.now(timezone.utc).date()

    return pd.DataFrame(
        [
            {
                "date": pd.to_datetime(as_of_date),
                "forward_pe": forward_pe,
                "implied_forward_eps_growth": implied_forward_eps_growth,
                "source": FORWARD_METRICS_SOURCE,
            }
        ]
    )


def get_latest_forward_metrics(df_forward_metrics, ticker):
    latest_forward_metrics = {
        "ticker": ticker,
        "forward_pe": np.nan,
        "implied_forward_eps_growth": np.nan,
    }

    if not df_forward_metrics.empty:
        latest = df_forward_metrics.sort_values("date").iloc[-1]
        latest_forward_metrics["forward_pe"] = latest["forward_pe"]
        latest_forward_metrics["implied_forward_eps_growth"] = latest[
            "implied_forward_eps_growth"
        ]

    return latest_forward_metrics
