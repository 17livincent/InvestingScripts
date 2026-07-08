"""
Get index data.
"""

from RequestAndSave import request_index_catalog, request_data
import json
from datetime import datetime
import pandas as pd
from pathlib import Path

INDEX_DATA_PATH = "data/AlphaVantage/{}/INDEX_DATA.json"
INDEX_DATA_KEY = "data"


def request_index_list():
    data_json = request_index_catalog()

    if data_json:
        with open("data/AlphaVantage/INDEX_CATALOG.json", "w") as export_json_file:
            json.dump(data_json, export_json_file, indent=4)
    return data_json


def get_index_list():
    index_list_dict = {}
    try:
        Path("data/AlphaVantage").mkdir(exist_ok=True)
        with open("data/AlphaVantage/INDEX_CATALOG.json", "r") as json_file:
            index_list_dict = json.load(json_file)
    except FileNotFoundError as e:
        print(e)
        index_list_dict = request_index_list()

    return index_list_dict


def get_saved_index_data(index_symbol):
    with open(INDEX_DATA_PATH.format(index_symbol), "r") as index_json:
        return json.load(index_json)


def save_index_data(index_symbol, data_json):
    Path("data/AlphaVantage/{}".format(index_symbol)).mkdir(exist_ok=True)
    with open(INDEX_DATA_PATH.format(index_symbol), "w") as export_json_file:
        json.dump(data_json, export_json_file, indent=4)


def get_latest_saved_index_date(data_json):
    index_rows = data_json.get(INDEX_DATA_KEY, [])
    if not index_rows:
        return None

    dates = pd.to_datetime(
        [row.get("date") for row in index_rows], errors="coerce"
    ).dropna()
    if dates.empty:
        return None

    return dates.max().date()


def saved_index_data_is_current(data_json):
    return get_latest_saved_index_date(data_json) == datetime.now().date()


def get_index_time_series_daily(index_symbol, minimum_date: datetime):
    try:
        saved_data_json = get_saved_index_data(index_symbol)
    except FileNotFoundError:
        saved_data_json = None

    df_index_data = pd.DataFrame()

    if saved_data_json is not None and saved_index_data_is_current(saved_data_json):
        data_json = saved_data_json
    else:
        data_json = request_data("INDEX_DATA", index_symbol, {"interval": "daily"})

        if data_json and INDEX_DATA_KEY in data_json and data_json[INDEX_DATA_KEY]:
            save_index_data(index_symbol, data_json)
        elif saved_data_json is not None:
            print(
                "WARNING: no daily index data from AlphaVantage for {}. Pulling from saved file if exists.".format(
                    index_symbol
                )
            )
            data_json = saved_data_json
        else:
            data_json = {}

    if data_json and INDEX_DATA_KEY in data_json and data_json[INDEX_DATA_KEY]:
        df_index_data = pd.DataFrame.from_records(data_json[INDEX_DATA_KEY])
        df_index_data["date"] = pd.to_datetime(df_index_data["date"], utc=True)
        df_index_data = df_index_data.dropna(subset=["date", "close"])
        df_index_data = df_index_data.reindex(
            columns=["date", "open", "high", "low", "close"]
        )
        df_index_data = df_index_data.loc[
            df_index_data["date"] >= minimum_date,
            ["date", "open", "high", "low", "close"],
        ]
        for column in ["open", "high", "low", "close"]:
            df_index_data[column] = pd.to_numeric(
                df_index_data[column], errors="coerce"
            )

        df_index_data = df_index_data.sort_values("date")
    else:
        print("WARNING: no daily index data for {}.".format(index_symbol))

    return df_index_data
