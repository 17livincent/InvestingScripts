"""
    Compare multiple companies.
"""
from CalculateFundamentals import get_fundamentals, get_latest_metrics
import pandas as pd

tickers = ['PLTR', 'TEAM', 'APH', 'F', 'SNDK', 'BROS']

comparison_rows = []

for ticker in tickers:
    df_calculated = get_fundamentals(ticker)
    comparison_rows.append(get_latest_metrics(df_calculated, ticker))

df_comparison = pd.DataFrame(comparison_rows)
df_comparison = df_comparison.sort_values(by='TTM_ROIC', ascending=False)
print(df_comparison)
