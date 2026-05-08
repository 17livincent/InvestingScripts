"""
    Example AlphaVantage request.
"""

import requests
import subprocess
import json

result = subprocess.run(['pass', 'show', 'Keys/AlphaVantage'], capture_output=True, text=True)
key = result.stdout

if key != '':
    url = 'https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol=SNDK&apikey={}'.format(key)
    r = requests.get(url)
    data = r.json()

    print(data['symbol'])
    print(data['annualReports'])
else:
    print("Invalid key.")