import pandas as pd
import csv
import time

set = "ONE"
format    = "PremierDraft"
gameDataFilename = "./rawData/game_data_public." + set + "." + format +".csv"

thinGameData = "./rawData/thin_game_data_public." + set + "." + format + ".csv"

header = []
relevantCols = []

start_time = time.time()
def findRelevantCols(header):
    for col in range(len(header)):
        # header[16] = "won" -> hardcoded due to cards possibly having the substring in their name
        if ("deck_" in str(header[col]) or col == 16):
            relevantCols.append(header[col])
    print(relevantCols)
    print("Size of relevantCols: " + str(len(relevantCols)))

with open(gameDataFilename, "r") as f:
    reader = csv.reader(f)
    header = next(reader)
    print(header)
    print("############ \n\n\n")
    findRelevantCols(header)

df = pd.read_csv(gameDataFilename, usecols=relevantCols)
df.to_csv(thinGameData)
print("Process executed in: " + str(time.time() - start_time) + " seconds")