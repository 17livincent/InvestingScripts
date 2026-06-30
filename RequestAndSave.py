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

ALPHAVANTAGE_QUERY_URL = 'https://www.alphavantage.co/query'
MAX_REQUEST_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1
REQUEST_SESSION = requests.Session()

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
    key = result.stdout.strip()

    if result.returncode != 0:
        raise RuntimeError('Unable to read AlphaVantage API key from pass: {}'.format(result.stderr.strip()))
    if not key:
        raise RuntimeError('AlphaVantage API key from pass is empty.')

    return key

def get_clean_query_value(value, field_name):
    clean_value = str(value).strip()

    if not clean_value:
        raise ValueError('{} must not be empty.'.format(field_name))

    return clean_value

def should_retry_invalid_api_call(data):
    error_message = data.get('Error Message') if isinstance(data, dict) else None

    return error_message and 'Invalid API call' in error_message

def request_data(function, symbol, params:dict=None):
    request_params = dict(params or {})
    request_params.update({
        'function': get_clean_query_value(function, 'function'),
        'symbol': get_clean_query_value(symbol, 'symbol'),
        'apikey': get_api_key()
    })

    data = {}
    for attempt in range(MAX_REQUEST_ATTEMPTS):
        response = REQUEST_SESSION.get(ALPHAVANTAGE_QUERY_URL, params=request_params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not should_retry_invalid_api_call(data) or attempt == MAX_REQUEST_ATTEMPTS - 1:
            break

        print('WARNING: AlphaVantage returned invalid API call for {} and {}. Retrying.'.format(
            request_params['function'],
            request_params['symbol']))
        time.sleep(RETRY_DELAY_SECONDS)

    return data

def request_and_save_json(function, symbol):
    '''
        Get data from AlphaVantage with the given function and symbol.
        Saves to a JSON file in data/.
    '''
    data = request_data(function, symbol)

    if data and 'Information' not in data:
        Path('data/AlphaVantage/{}'.format(symbol)).mkdir(exist_ok=True)
        with open('data/AlphaVantage/{}/{}.json'.format(symbol, function), 'w') as export_json_file:
            json.dump(data, export_json_file, indent=4)
    else:
        print("WARNING: received for {}:\r\n{}".format(function, data))

def request_index_catalog():
    params = {'function': 'INDEX_CATALOG',
              'datatype': 'json',
              'apikey': get_api_key()}
    r = REQUEST_SESSION.get(ALPHAVANTAGE_QUERY_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data
