"""
    Request and save data from the AlphaVantage API.
"""
import json
import requests
import subprocess
from pathlib import Path

def request_and_save_json(function, symbol):
    '''
        Get data from AlphaVantage with the given function and symbol.
        Saves to a JSON file in data/.
    '''
    result = subprocess.run(['pass', 'show', 'Keys/AlphaVantage'], capture_output=True, text=True)
    key = result.stdout

    url = 'https://www.alphavantage.co/query?function={}&symbol={}&apikey={}'.format(function, symbol, key)
    r = requests.get(url)
    data = r.json()

    if data:
        Path('data/{}'.format(symbol)).mkdir(exist_ok=True)
        with open('data/{}/{}.json'.format(symbol, function), 'w') as export_json_file:
            json.dump(data, export_json_file, indent=4)

request_and_save_json('CASH_FLOW', 'SNDK')
