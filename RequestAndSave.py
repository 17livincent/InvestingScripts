"""
    Request and save data from the AlphaVantage API.
"""
import json
import requests
import subprocess
from pathlib import Path
import pandas as pd
import time
import argparse

functions = [
    'BALANCE_SHEET',
    'CASH_FLOW',
    'INCOME_STATEMENT',
    'SHARES_OUTSTANDING',
    'TIME_SERIES_WEEKLY_ADJUSTED'
    ]

recency = {
    'BALANCE_SHEET': 'quarter',
    'CASH_FLOW': 'quarter',
    'INCOME_STATEMENT': 'quarter',
    'SHARES_OUTSTANDING': 'quarter',
    'TIME_SERIES_WEEKLY_ADJUSTED': 'week'
}

def get_api_key():
    result = subprocess.run(['pass', 'show', 'Keys/AlphaVantagePremium'], capture_output=True, text=True)
    key = result.stdout
    return key.strip()

def request_data(function, symbol, params:dict=None):
    url = 'https://www.alphavantage.co/query?function={}&symbol={}&apikey={}'.format(function,
                                                                                     symbol,
                                                                                     get_api_key())
    r = requests.get(url, params)
    data = r.json()
    return data

def request_and_save_json(function, symbol):
    '''
        Get data from AlphaVantage with the given function and symbol.
        Saves to a JSON file in data/.
    '''
    data = request_data(function, symbol)

    if data and 'Information' not in data:
        Path('data/{}'.format(symbol)).mkdir(exist_ok=True)
        with open('data/{}/{}.json'.format(symbol, function), 'w') as export_json_file:
            json.dump(data, export_json_file, indent=4)
    else:
        print("WARNING: received for {}:\r\n{}".format(function, data))

def request_index_catalog():
    url = 'https://www.alphavantage.co/query?function={}&datatype={}&apikey={}'.format('INDEX_CATALOG',
                                                                                       'json',
                                                                                       get_api_key())
    r = requests.get(url)
    data = r.json()
    return data
