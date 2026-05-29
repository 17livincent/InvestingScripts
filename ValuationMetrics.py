"""
    Calculate short-term valuation metrics such as P/E, P/FCF, and EV/EBIT.
"""

from OperationalMetrics import read_saved_fundamentals
import json
import pandas as pd
import numpy as np
import sys

def get_valuation(ticker, df_fundamentals):
    df_fundamentals['date'] = pd.to_datetime(df_fundamentals['date']).astype('datetime64[ns]')
    df_fundamentals = df_fundamentals.sort_values('date')

    rows_list = []
    try:
        with open('data/{}/SHARES_OUTSTANDING.json'.format(ticker)) as shares_outstanding_json:
            shares_outstanding = json.load(shares_outstanding_json)
            for item in shares_outstanding['data']:
                rows_list.append({'date': item['date'],
                                'basic_shares': float(item['shares_outstanding_basic']),
                                'diluted_shares': float(item['shares_outstanding_diluted'])})
        df_shares_outstanding = pd.DataFrame(rows_list)
        df_shares_outstanding['date'] = pd.to_datetime(df_shares_outstanding['date']).astype('datetime64[ns]')
        df_shares_outstanding = df_shares_outstanding.sort_values('date')
    except KeyError as e:
        print(e)
        print(ticker)

    rows_list = []
    try:
        with open('data/{}/TIME_SERIES_WEEKLY_ADJUSTED.json'.format(ticker)) as weekly_stock_json:
            weekly_stock = json.load(weekly_stock_json)
            for item in weekly_stock['Weekly Adjusted Time Series'].keys():
                rows_list.append({'date': item,
                                'adjusted_close': float(weekly_stock['Weekly Adjusted Time Series'][item]['5. adjusted close']),
                                'volume': float(weekly_stock['Weekly Adjusted Time Series'][item]['6. volume'])})
        df_weekly_stock_close = pd.DataFrame(rows_list)
        df_weekly_stock_close['date'] = pd.to_datetime(df_weekly_stock_close['date']).astype('datetime64[ns]')
        df_weekly_stock_close = df_weekly_stock_close.sort_values('date')
    except KeyError as e:
        print(e)
        print(ticker)

    df_merged = pd.merge_asof(
        df_fundamentals,
        df_weekly_stock_close[['date', 'adjusted_close', 'volume']],
        on='date',
        direction='backward')
    df_merged = pd.merge_asof(
        df_merged,
        df_shares_outstanding[['date', 'basic_shares', 'diluted_shares']],
        on='date',
        direction='backward')

    # Calculate market cap
    df_merged['market_cap'] = df_merged['diluted_shares'] * df_merged['adjusted_close']

    # Calculate PE ratio
    df_merged['pe_ttm'] = np.where(df_merged['ttm_net_income'] > 0,
                                   df_merged['market_cap'] / df_merged['ttm_net_income'],
                                   np.nan)
    df_merged['pe_ttm'] = df_merged['pe_ttm'].clip(upper=200)

    # Calculate P/FCF
    df_merged['pfcf'] = np.where(df_merged['ttm_fcf'] > 0,
                                 df_merged['market_cap'] / df_merged['ttm_fcf'],
                                 np.nan)

    # Calculate enterprise value
    df_merged['enterprise_value'] = df_merged['market_cap'] + df_merged['total_debt'] - df_merged['cash']

    # Calculate enterprise value to EBIT ratio
    df_merged['ev_ebit'] = np.where(df_merged['ttm_operating_income'] > 0,
                                    df_merged['enterprise_value'] / df_merged['ttm_operating_income'],
                                    np.nan)
    df_merged['ev_ebit'] = df_merged['ev_ebit'].clip(upper=100)

    # Calculate EV to NOPAT ratio
    df_merged['ev_nopat'] = np.where(df_merged['nopat'] > 0,
                                     df_merged['enterprise_value'] / df_merged['nopat'],
                                     np.nan)

    # Calculate EV to FCF ratio
    df_merged['ev_fcf'] = np.where(df_merged['ttm_fcf'] > 0,
                                   df_merged['enterprise_value'] / df_merged['ttm_fcf'],
                                   np.nan)

    return df_merged

def get_latest_valuation(df_valuation, ticker):
    """
        Get a summary of the latest valuation metrics, given df_valuation
        from get_valuation() of the given ticker.
    """
    latest = df_valuation.iloc[-1]
    return {
        'ticker': ticker,
        'pe_ttm': latest['pe_ttm'],
        'ev_ebit': latest['ev_ebit']
    }