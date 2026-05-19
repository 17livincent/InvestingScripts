"""
    Calculate short-term valuation metrics such as P/E, P/FCF, and EV/EBIT.
"""

from OperationalMetrics import read_saved_fundamentals
import json
import pandas as pd
import numpy as np

def get_valuation(ticker, df_fundamentals):
    df_fundamentals['Date'] = pd.to_datetime(df_fundamentals['Date'])
    df_fundamentals = df_fundamentals.sort_values('Date')

    rows_list = []
    with open('data/{}/SHARES_OUTSTANDING.json'.format(ticker)) as shares_outstanding_json:
        shares_outstanding = json.load(shares_outstanding_json)
        for item in shares_outstanding['data']:
            rows_list.append({'Date': item['date'],
                              'BasicSharesOutstanding': float(item['shares_outstanding_basic']),
                              'DilutedSharesOutstanding': float(item['shares_outstanding_diluted'])})
    df_shares_outstanding = pd.DataFrame(rows_list)
    df_shares_outstanding['Date'] = pd.to_datetime(df_shares_outstanding['Date'])
    df_shares_outstanding = df_shares_outstanding.sort_values('Date')

    rows_list = []
    with open('data/{}/TIME_SERIES_WEEKLY_ADJUSTED.json'.format(ticker)) as weekly_stock_json:
        weekly_stock = json.load(weekly_stock_json)
        for item in weekly_stock['Weekly Adjusted Time Series'].keys():
            rows_list.append({'Date': item,
                              'StockAdjustedClose': float(weekly_stock['Weekly Adjusted Time Series'][item]['5. adjusted close'])})
    df_weekly_stock_close = pd.DataFrame(rows_list)
    df_weekly_stock_close['Date'] = pd.to_datetime(df_weekly_stock_close['Date'])
    df_weekly_stock_close = df_weekly_stock_close.sort_values('Date')

    df_merged = pd.merge_asof(
        df_fundamentals,
        df_weekly_stock_close[['Date', 'StockAdjustedClose']],
        on='Date',
        direction='backward')
    df_merged = pd.merge_asof(
        df_merged,
        df_shares_outstanding[['Date', 'BasicSharesOutstanding', 'DilutedSharesOutstanding']],
        on='Date',
        direction='backward')

    # Calculate market cap
    df_merged['MarketCap'] = df_merged['DilutedSharesOutstanding'] * df_merged['StockAdjustedClose']

    # Calculate PE ratio
    df_merged['PE_TTM'] = np.where(df_fundamentals['TTM_NetIncome'] > 0,
                               df_merged['MarketCap'] / df_fundamentals['TTM_NetIncome'],
                               np.nan)
    df_merged['PE_TTM'] = df_merged['PE_TTM'].clip(upper=200)

    # Calculate P/FCF
    df_merged['PFCF'] = np.where(df_fundamentals['TTM_FreeCashFlow'] > 0,
                                 df_merged['MarketCap'] / df_fundamentals['TTM_FreeCashFlow'],
                                 np.nan)

    # Calculate enterprise value
    df_merged['EnterpriseValue'] = df_merged['MarketCap'] + df_fundamentals['TotalDebt'] - df_fundamentals['Cash']

    # Calculate enterprise value to EBIT ratio
    df_merged['EV_EBIT'] = np.where(df_fundamentals['TTM_OperatingIncome'] > 0,
                                    df_merged['EnterpriseValue'] / df_fundamentals['TTM_OperatingIncome'],
                                    np.nan)
    df_merged['EV_EBIT'] = df_merged['EV_EBIT'].clip(upper=100)

    # Calculate EVto NOPAT ratio
    df_merged['EV_NOPAT'] = np.where(df_fundamentals['TTM_NOPAT'] > 0,
                                     df_merged['EnterpriseValue'] / df_fundamentals['TTM_NOPAT'],
                                     np.nan)

    # Calculate EV to FCF ratio
    df_merged['EV_FCF'] = np.where(df_fundamentals['TTM_FreeCashFlow'] > 0,
                                   df_merged['EnterpriseValue'] / df_fundamentals['TTM_FreeCashFlow'],
                                   np.nan)

    return df_merged
