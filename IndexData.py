"""
    Get index data.
"""

from RequestAndSave import request_index_catalog, request_data
import json
from datetime import datetime
import pandas as pd
from pathlib import Path

def request_index_list():
    data_json = request_index_catalog()

    if data_json:
        with open('data/AlphaVantage/INDEX_CATALOG.json', 'w') as export_json_file:
            json.dump(data_json, export_json_file, indent=4)
    return data_json

def get_index_list():
    index_list_dict = {}
    try:
        Path('data/AlphaVantage').mkdir(exist_ok=True)
        with open('data/AlphaVantage/INDEX_CATALOG.json', 'r') as json_file:
            index_list_dict = json.load(json_file)
    except FileNotFoundError as e:
        print(e)
        index_list_dict = request_index_list()

    return index_list_dict

def get_index_time_series_daily(index_symbol, minimum_date: datetime):
    data_json = request_data('INDEX_DATA', index_symbol, {'interval': 'daily'})
    df_index_data = pd.DataFrame()

    if data_json and 'data' in data_json and data_json['data']:
        df_index_data = pd.DataFrame.from_records(data_json['data'])
        df_index_data = df_index_data.reindex(columns=['date', 'open', 'high', 'low', 'close'])
        df_index_data['date'] = pd.to_datetime(df_index_data['date'], utc=True, errors='coerce')

        for column in ['open', 'high', 'low', 'close']:
            df_index_data[column] = pd.to_numeric(df_index_data[column], errors='coerce')

        df_index_data = df_index_data.loc[df_index_data['date'] >= minimum_date,
                                          ['date', 'open', 'high', 'low', 'close']]
        df_index_data = df_index_data.dropna(subset=['date', 'close'])
        df_index_data = df_index_data.sort_values('date')
    else:
        print("WARNING: no daily index data for {}.".format(index_symbol))

    return df_index_data
