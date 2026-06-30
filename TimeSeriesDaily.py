"""
    Get time series daily data on tickers.
"""

from RequestAndSave import request_data
import pandas as pd
from datetime import datetime
from TickerData import SAVED_JSON_PATH
from pathlib import Path
import json

DAILY_TIME_SERIES_KEY = 'Time Series (Daily)'
DAILY_FUNCTION_NAME = 'TIME_SERIES_DAILY_ADJUSTED'

def get_saved_time_series_daily_adjusted(ticker_name):
    function_path = SAVED_JSON_PATH.format(ticker_name, DAILY_FUNCTION_NAME)

    with open(function_path) as daily_json:
        return json.load(daily_json)

def get_latest_saved_daily_date(data):
    daily_time_series = data.get(DAILY_TIME_SERIES_KEY, {})
    if not daily_time_series:
        return None

    return max(pd.to_datetime(daily).date() for daily in daily_time_series)

def saved_daily_data_is_current(data):
    return get_latest_saved_daily_date(data) == datetime.now().date()

def get_time_series_daily_adjusted(ticker_name, minimum_date:datetime):
    function_path = SAVED_JSON_PATH.format(ticker_name, DAILY_FUNCTION_NAME)

    df_time_series_daily = pd.DataFrame()

    try:
        saved_data = get_saved_time_series_daily_adjusted(ticker_name)
    except FileNotFoundError:
        saved_data = None

    if saved_data is not None and saved_daily_data_is_current(saved_data):
        data = saved_data
    else:
        data = request_data(DAILY_FUNCTION_NAME,
                            ticker_name,
                            {'outputsize': 'full',
                             'datatype': 'json',
                             'entitlement': 'delayed'})

        if DAILY_TIME_SERIES_KEY in data:
            Path('data/AlphaVantage/{}'.format(ticker_name)).mkdir(exist_ok=True)
            with open(function_path, 'w') as export_json_file:
                json.dump(data, export_json_file, indent=4)
        elif saved_data is not None:
            data = saved_data
        else:
            data = get_saved_time_series_daily_adjusted(ticker_name)

    df_time_series_daily['date'] = [daily for
                                    daily in list(data[DAILY_TIME_SERIES_KEY])
                                    if pd.to_datetime(daily, utc=True) >= minimum_date]

    df_time_series_daily['open'] = [float(data[DAILY_TIME_SERIES_KEY][daily_key]['1. open']) for
                                    daily_key in list(data[DAILY_TIME_SERIES_KEY])
                                    if pd.to_datetime(daily_key, utc=True) >= minimum_date]

    df_time_series_daily['high'] = [float(data[DAILY_TIME_SERIES_KEY][daily_key]['2. high']) for
                                    daily_key in list(data[DAILY_TIME_SERIES_KEY])
                                    if pd.to_datetime(daily_key, utc=True) >= minimum_date]

    df_time_series_daily['low'] = [float(data[DAILY_TIME_SERIES_KEY][daily_key]['3. low']) for
                                    daily_key in list(data[DAILY_TIME_SERIES_KEY])
                                    if pd.to_datetime(daily_key, utc=True) >= minimum_date]

    df_time_series_daily['close'] = [float(data[DAILY_TIME_SERIES_KEY][daily_key]['5. adjusted close']) for
                                     daily_key in list(data[DAILY_TIME_SERIES_KEY])
                                     if pd.to_datetime(daily_key, utc=True) >= minimum_date]

    df_time_series_daily['date'] = pd.to_datetime(df_time_series_daily['date'], utc=True)
    df_time_series_daily = df_time_series_daily.sort_values('date')

    return df_time_series_daily
