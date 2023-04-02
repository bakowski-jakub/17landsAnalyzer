import scrython
import pandas as pd
import csv
import time
import json
from dask import dataframe as dd

set = "ONE"
format    = "PremierDraft"
gameDataFilename = "game_data_public." + set + "." + format +".csv"
setOracle = set + "_oracle.json"

rows = []

with open(gameDataFilename, "r") as f:
    reader = csv.reader(f)
    header = next(reader)
    rows.append(next(reader))
    print(rows)