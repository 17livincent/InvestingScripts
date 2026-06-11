"""
    Get index data.
"""

from RequestAndSave import request_index_catalog, get_api_key
import json
import requests

def request_index_list():
    data_json = request_index_catalog()

    if data_json:
        with open('data/INDEX_CATALOG.json', 'w') as export_json_file:
            json.dump(data_json, export_json_file, indent=4)
    return data_json

def get_index_list():
    index_list_dict = {}
    try:
        with open('data/INDEX_CATALOG.json', 'r') as json_file:
            index_list_dict = json.load(json_file)
    except FileNotFoundError as e:
        print(e)
        index_list_dict = request_index_list()

    return index_list_dict

def get_index_time_series_daily(index_symbol):
    url = 'https://www.alphavantage.co/query?function={}&symbol={}&interval={}&apikey={}'.format('INDEX_DATA',
                                                                                                 index_symbol,
                                                                                                 'daily',
                                                                                                 get_api_key())
    r = requests.get(url)
    data = r.json()
    return data
