"""
    Get time series daily data on tickers.
"""

from RequestAndSave import request_data
import pandas as pd
from datetime import datetime
from TickerData import SAVED_JSON_PATH
from pathlib import Path
import json

def get_time_series_daily_adjusted(ticker_name, minimum_date:datetime):
    function_path = SAVED_JSON_PATH.format(ticker_name, 'TIME_SERIES_DAILY_ADJUSTED')

    df_time_series_daily = pd.DataFrame()

    data = request_data('TIME_SERIES_DAILY_ADJUSTED',
                        ticker_name,
                        {'outputsize': 'compact',
                         'datatype': 'json',
                         'entitlement': 'delayed'})

    if 'Time Series (Daily)' in data:
        Path('data/{}'.format(ticker_name)).mkdir(exist_ok=True)
        with open(function_path, 'w') as export_json_file:
            json.dump(data, export_json_file, indent=4)
    else:
        with open('data/{}/TIME_SERIES_DAILY_ADJUSTED.json'.format(ticker_name)) as daily_json:
            data = json.load(daily_json)

    df_time_series_daily['date'] = [daily for
                                    daily in list(data['Time Series (Daily)'])
                                    if pd.to_datetime(daily, utc=True) >= minimum_date]

    df_time_series_daily['open'] = [float(data['Time Series (Daily)'][daily_key]['1. open']) for
                                    daily_key in list(data['Time Series (Daily)'])
                                    if pd.to_datetime(daily_key, utc=True) >= minimum_date]

    df_time_series_daily['high'] = [float(data['Time Series (Daily)'][daily_key]['2. high']) for
                                    daily_key in list(data['Time Series (Daily)'])
                                    if pd.to_datetime(daily_key, utc=True) >= minimum_date]

    df_time_series_daily['low'] = [float(data['Time Series (Daily)'][daily_key]['3. low']) for
                                    daily_key in list(data['Time Series (Daily)'])
                                    if pd.to_datetime(daily_key, utc=True) >= minimum_date]

    df_time_series_daily['close'] = [float(data['Time Series (Daily)'][daily_key]['4. close']) for
                                    daily_key in list(data['Time Series (Daily)'])
                                    if pd.to_datetime(daily_key, utc=True) >= minimum_date]

    df_time_series_daily['date'] = pd.to_datetime(df_time_series_daily['date'], utc=True)
    df_time_series_daily = df_time_series_daily.sort_values('date')

    return df_time_series_daily
