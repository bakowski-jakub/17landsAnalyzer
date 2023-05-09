import scrython
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import csv
import time
import json
import re


set = "ONE"
format    = "PremierDraft"
gameDataFilename = "./rawData/game_data_public." + set + "." + format +".csv"
setOracle = "./rawData/" + set + "_oracle.json"

#thinGameData = "./rawData/thin_game_data_public." + set + "." + format + ".csv"
thinGameData = "./rawData/thin_game_data_public.ONE.PremierDraft.csv"

header = []

gamesParsed = 500000

# this constant is actually an amount of cards in the set + 2 (to account for column "won" and row counter - in order to simplify further operations)
cardsInSet = 272

#
bucketSize = 60
basicLandArray = ["deck_Plains", "deck_Island", "deck_Swamp", "deck_Mountain", "deck_Forest"]

######################################
###
### MASKS
###

maskBasicLand = np.empty(cardsInSet, dtype = np.int16)
maskNonBasicLand = np.empty(cardsInSet, dtype = np.int16)
maskTapLand = np.empty(cardsInSet, dtype = np.int16)
maskAllLand = np.empty(cardsInSet, dtype = np.int16)

maskCmcVal = np.empty(cardsInSet, dtype = np.int16)

######################################

######################################
###
### BUCKETS
###

bucketLand = np.empty(bucketSize, dtype = np.int32)
bucketLandWin = np.empty(bucketSize, dtype = np.int32)
bucketLandAvgCmc = np.empty(bucketSize, dtype = np.int32)

bucketTap = np.empty(bucketSize, dtype = np.int32)
bucketTapWin = np.empty(bucketSize, dtype = np.int32)
bucketTapAvgCmc = np.empty(bucketSize, dtype = np.int32)

##
## CMC NAMING CONVENTION
##
# VERY LOW  -> CMC < 2.3
# LOW       -> CMC 2.3 - 2.5
# NORMAL    -> CMC 2.5 - 2.7
# HIGH      -> CMC 2.7 - 2.9
# VERY HIGH -> CMC > 2.9

bucketLandCmcVeryLow = np.empty(bucketSize, dtype = np.int32)
bucketLandCmcVeryLowWin = np.empty(bucketSize, dtype = np.int32)
bucketTapCmcVeryLow = np.empty(bucketSize, dtype = np.int32)
bucketTapCmcVeryLowWin = np.empty(bucketSize, dtype = np.int32)

bucketLandCmcLow = np.empty(bucketSize, dtype = np.int32)
bucketLandCmcLowWin = np.empty(bucketSize, dtype = np.int32)  
bucketTapCmcLow = np.empty(bucketSize, dtype = np.int32)
bucketTapCmcLowWin = np.empty(bucketSize, dtype = np.int32)

bucketLandCmcNormal = np.empty(bucketSize, dtype = np.int32)
bucketLandCmcNormalWin = np.empty(bucketSize, dtype = np.int32)
bucketTapCmcNormal = np.empty(bucketSize, dtype = np.int32)
bucketTapCmcNormalWin = np.empty(bucketSize, dtype = np.int32)

bucketLandCmcHigh = np.empty(bucketSize, dtype = np.int32)
bucketLandCmcHighWin = np.empty(bucketSize, dtype = np.int32)
bucketTapCmcHigh = np.empty(bucketSize, dtype = np.int32)
bucketTapCmcHighWin = np.empty(bucketSize, dtype = np.int32)

bucketLandCmcVeryHigh = np.empty(bucketSize, dtype = np.int32)
bucketLandCmcVeryHighWin = np.empty(bucketSize, dtype = np.int32)
bucketTapCmcVeryHigh = np.empty(bucketSize, dtype = np.int32)
bucketTapCmcVeryHighWin = np.empty(bucketSize, dtype = np.int32)

land17WR = 0
land16WR = 0

tap17WR = 0
tap16WR = 0

land17WRVeryLow = 0
land16WRVeryLow = 0
tap17WRVeryLow = 0
tap16WRVeryLow = 0

land17WRLow = 0
land16WRLow = 0
tap17WRLow = 0
tap16WRLow = 0

land17WRNormal = 0
land16WRNormal = 0
tap17WRNormal = 0
tap16WRNormal = 0

land17WRHigh = 0
land16WRHigh = 0
tap17WRHigh = 0
tap16WRHigh = 0

land17WRVeryHigh = 0
land16WRVeryHigh = 0
tap17WRVeryHigh = 0
tap16WRVeryHigh = 0

######################################
def namePruning(string):
    prefix = "deck_"
    string = string.replace(prefix,'')
    return string

def findCmc(cardName, setOracle):
    cmc = 0
    for key in range(len(setOracle)):
        if setOracle[key]['name'] == cardName:
            cmc = setOracle[key]['cmc']
    return cmc

def populateMaskBasicLand(header):
    for col in range(len(header)):
        maskBasicLand[col] = 0
        for basic in range(len(basicLandArray)):
            if (basicLandArray[basic] in str(header[col])):
                maskBasicLand[col] = 1

def populateMaskNonBasicLand(header, setOracle):
    for col in range(len(header)):
        maskTapLand[col] = 0
        maskNonBasicLand[col] = 0
        for key in range(len(setOracle)):
            if maskBasicLand[col] != 1:
                cardName = namePruning(header[col])
                if(setOracle[key]['name'] == cardName) and "Land" in setOracle[key]['type_line']:
                    maskNonBasicLand[col] = 1
                    if("enters the battlefield tapped" in setOracle[key]['oracle_text'] and "enters the battlefield tapped unless you control two" not in setOracle[key]['oracle_text']):
                        maskTapLand[col] = 1
                    if(setOracle[key]['name'] == "Terramorphic Expanse"):
                        maskTapLand[col] = 1
                        print(col)

def populateMaskAllLand():
    for i in range(cardsInSet):
        maskAllLand[i] = (maskBasicLand[i] + maskNonBasicLand[i] + maskTapLand[i])
        if maskAllLand[i] > 0:
            maskAllLand[i] = 1 
         
def populateMaskCmcVal(header, setOracle):
    for col in range(len(header)):
        maskCmcVal[col] = 0
        for key in range(len(setOracle)):
            cardName = namePruning(header[col])
            if maskAllLand[col] != 1:
                maskCmcVal[col] = findCmc(cardName, setOracle)

def initializeBuckets(bucketSize):
    for i in range(bucketSize):
        bucketLand[i] = 0
        bucketLandWin[i] = 0
        bucketTap[i] = 0
        bucketTapWin[i] = 0

        bucketLandCmcVeryLow[i] = 0
        bucketLandCmcVeryLowWin[i] = 0
        bucketTapCmcVeryLow[i] = 0
        bucketTapCmcVeryLowWin[i] = 0
        bucketLandCmcLow[i] = 0
        bucketLandCmcLowWin[i] = 0
        bucketTapCmcLow[i] = 0
        bucketTapCmcLowWin[i] = 0
        bucketLandCmcNormal[i] = 0
        bucketLandCmcNormalWin[i] = 0
        bucketTapCmcNormal[i] = 0
        bucketTapCmcNormalWin[i] = 0
        bucketLandCmcHigh[i] = 0
        bucketLandCmcHighWin[i] = 0
        bucketTapCmcHigh[i] = 0
        bucketTapCmcHighWin[i] = 0
        bucketLandCmcVeryHigh[i] = 0
        bucketLandCmcVeryHighWin[i] = 0
        bucketTapCmcVeryHigh[i] = 0
        bucketTapCmcVeryHighWin[i] = 0

def processRow(row):
    deckLandArray = 0
    deckLandCount = 0
    deckArray = 0
    tapPresent = False

    deckArray = row
    deckLandArray = np.multiply(deckArray, maskAllLand)
    deckLandCount = np.sum(deckLandArray)
    #print("Deck land count: " + str(deckLandCount) + "\n")
    # throwing out all TE decks (219 - terramorphic expanse)
    if(deckLandArray[219] == 1):
        return
    deckTapArray = np.multiply(deckLandArray, maskTapLand)
    if(np.sum(deckTapArray) != 0 ):
        tapPresent = True
    
    deckTotalMana = np.sum(np.multiply(deckArray, maskCmcVal))
    #print("Deck total mana: " + str(deckTotalMana) + "\n")
    deckTotalCards = np.sum(deckArray)
    deckTotalCards = deckTotalCards - deckArray[0]
    #print("Deck total cards: " + str(deckTotalCards) + "\n")
    deckNonLandCards = np.subtract(deckTotalCards, np.sum(deckLandCount))
    #print("Deck nonland cards: " + str(deckNonLandCards) + "\n")
    deckAvgCmc = deckTotalMana / deckNonLandCards
    #print("Deck avg cmc: " + str(deckAvgCmc) + "\n")
    #print("###\n")
    if tapPresent == True:
        bucketTap[deckLandCount] = bucketTap[deckLandCount] + 1
        if deckArray[1] == True:
            bucketTapWin[deckLandCount] = bucketTapWin[deckLandCount] + 1
        if deckAvgCmc < 2.3:
            bucketTapCmcVeryLow[deckLandCount] = bucketTapCmcVeryLow[deckLandCount] + 1
            if deckArray[1] == True:
                bucketTapCmcVeryLowWin[deckLandCount] = bucketTapCmcVeryLowWin[deckLandCount] + 1
        elif deckAvgCmc < 2.5:
            bucketTapCmcLow[deckLandCount] = bucketTapCmcLow[deckLandCount] + 1
            if deckArray[1] == True:
                bucketTapCmcLowWin[deckLandCount] = bucketTapCmcLowWin[deckLandCount] + 1
        elif deckAvgCmc < 2.7:
            bucketTapCmcNormal[deckLandCount] = bucketTapCmcNormal[deckLandCount] + 1
            if deckArray[1] == True:
                bucketTapCmcNormalWin[deckLandCount] = bucketTapCmcNormalWin[deckLandCount] + 1
        elif deckAvgCmc < 2.9:
            bucketTapCmcHigh[deckLandCount] = bucketTapCmcHigh[deckLandCount] + 1
            if deckArray[1] == True:
                bucketTapCmcHighWin[deckLandCount] = bucketTapCmcHighWin[deckLandCount] + 1
        elif deckAvgCmc > 2.9:
            bucketTapCmcVeryHigh[deckLandCount] = bucketTapCmcVeryHigh[deckLandCount] + 1
            if deckArray[1] == True:
                bucketTapCmcVeryHighWin[deckLandCount] = bucketTapCmcVeryHighWin[deckLandCount] + 1
    else:
        bucketLand[deckLandCount] = bucketLand[deckLandCount] + 1
        if deckArray[1] == True:
            bucketLandWin[deckLandCount] = bucketLandWin[deckLandCount] + 1
        if deckAvgCmc < 2:
            bucketLandCmcVeryLow[deckLandCount] = bucketLandCmcVeryLow[deckLandCount] + 1
            if deckArray[1] == True:
                bucketLandCmcVeryLowWin[deckLandCount] = bucketLandCmcVeryLowWin[deckLandCount] + 1
        elif deckAvgCmc < 2.2:
            bucketLandCmcLow[deckLandCount] = bucketLandCmcLow[deckLandCount] + 1
            if deckArray[1] == True:
                bucketLandCmcLowWin[deckLandCount] = bucketLandCmcLowWin[deckLandCount] + 1
        elif deckAvgCmc < 2.4:
            bucketLandCmcNormal[deckLandCount] = bucketLandCmcNormal[deckLandCount] + 1
            if deckArray[1] == True:
                bucketLandCmcNormalWin[deckLandCount] = bucketLandCmcNormalWin[deckLandCount] + 1
        elif deckAvgCmc < 2.6:
            bucketLandCmcHigh[deckLandCount] = bucketLandCmcHigh[deckLandCount] + 1
            if deckArray[1] == True:
                bucketLandCmcHighWin[deckLandCount] = bucketLandCmcHighWin[deckLandCount] + 1
        elif deckAvgCmc > 2.6:
            bucketLandCmcVeryHigh[deckLandCount] = bucketLandCmcVeryHigh[deckLandCount] + 1
            if deckArray[1] == True:
                bucketLandCmcVeryHighWin[deckLandCount] = bucketLandCmcVeryHighWin[deckLandCount] + 1

def retrieveBucketData():
    land17WR = bucketLandWin[17] / bucketLand[17]
    land16WR = bucketLandWin[16] / bucketLand[16]

    tap17WR = bucketTapWin[17] / bucketTap[17]
    tap16WR = bucketTapWin[16] / bucketTap[16]

    land17WRVeryLow = bucketLandCmcVeryLowWin[17] / bucketLandCmcVeryLow[17]
    land16WRVeryLow = bucketLandCmcVeryLowWin[16] / bucketLandCmcVeryLow[16]
    tap17WRVeryLow = bucketTapCmcVeryLowWin[17] / bucketTapCmcVeryLow[17]
    tap16WRVeryLow = bucketTapCmcVeryLowWin[16] / bucketTapCmcVeryLow[16]

    land17WRLow = bucketLandCmcLowWin[17] / bucketLandCmcLow[17]
    land16WRLow = bucketLandCmcLowWin[16] / bucketLandCmcLow[16]
    tap17WRLow = bucketTapCmcLowWin[17] / bucketTapCmcLow[17]
    tap16WRLow = bucketTapCmcLowWin[16] / bucketTapCmcLow[16]

    land17WRNormal = bucketLandCmcNormalWin[17] / bucketLandCmcNormal[17]
    land16WRNormal = bucketLandCmcNormalWin[16] / bucketLandCmcNormal[16]
    tap17WRNormal = bucketTapCmcNormalWin[17] / bucketTapCmcNormal[17]
    tap16WRNormal = bucketTapCmcNormalWin[16] / bucketTapCmcNormal[16]

    land17WRHigh = bucketLandCmcHighWin[17] / bucketLandCmcHigh[17]
    land16WRHigh = bucketLandCmcHighWin[16] / bucketLandCmcHigh[16]
    tap17WRHigh = bucketTapCmcHighWin[17] / bucketTapCmcHigh[17]
    tap16WRHigh = bucketTapCmcHighWin[16] / bucketTapCmcHigh[16]

    land17WRVeryHigh = bucketLandCmcVeryHighWin[17] / bucketLandCmcVeryHigh[17]
    land16WRVeryHigh = bucketLandCmcVeryHighWin[16] / bucketLandCmcVeryHigh[16]
    tap17WRVeryHigh = bucketTapCmcVeryHighWin[17] / bucketTapCmcVeryHigh[17]
    tap16WRVeryHigh = bucketTapCmcVeryHighWin[16] / bucketTapCmcVeryHigh[16]

    print("########################################\n")
    print("DECKS IN GENERAL [NO CMC CONSIDERATION]: \n")
    print("###\n")
    print("DECKS WITH NO TAPLANDS: \n")
    print("17 lands: \n")
    print("TOTAL GAMES: " + str(bucketLand[17]) + "\n")
    print("WIN RATE: " + str(land17WR) + "\n")
    print("###\n")
    print("16 lands: \n")
    print("TOTAL GAMES: " + str(bucketLand[16]) + "\n")
    print("WIN RATE: " + str(land16WR) + "\n")
    print("########################################\n")
    print("DECKS WITH TAPLANDS: \n")
    print("17 lands: \n")
    print("TOTAL GAMES: " + str(bucketTap[17]) + "\n") 
    print("WIN RATE: " + str(tap17WR) + "\n")
    print("###\n")
    print("16 lands: \n")
    print("TOTAL GAMES: " + str(bucketTap[16]) + "\n")
    print("WIN RATE: " + str(tap16WR))
    print("\n\n\n")
    print("########################################\n")
    print("DECKS IN GENERAL [VERY LOW CMC]: \n")
    print("###\n")
    print("DECKS WITH NO TAPLANDS: \n")
    print("17 lands: \n")
    print("TOTAL GAMES: " + str(bucketLandCmcVeryLow[17]) + "\n")
    print("WIN RATE: " + str(land17WRVeryLow) + "\n")
    print("###\n")
    print("16 lands: \n")
    print("TOTAL GAMES: " + str(bucketLandCmcVeryLow[16]) + "\n")
    print("WIN RATE: " + str(land16WRVeryLow) + "\n")
    print("########################################\n")
    print("DECKS WITH TAPLANDS: \n")
    print("17 lands: \n")
    print("TOTAL GAMES: " + str(bucketTapCmcVeryLow[17]) + "\n") 
    print("WIN RATE: " + str(tap17WRVeryLow) + "\n")
    print("###\n")
    print("16 lands: \n")
    print("TOTAL GAMES: " + str(bucketTapCmcVeryLow[16]) + "\n")
    print("WIN RATE: " + str(tap16WRVeryLow))
    print("\n\n\n")
    print("########################################\n")
    print("DECKS IN GENERAL [LOW CMC]: \n")
    print("###\n")
    print("DECKS WITH NO TAPLANDS: \n")
    print("17 lands: \n")
    print("TOTAL GAMES: " + str(bucketLandCmcLow[17]) + "\n")
    print("WIN RATE: " + str(land17WRLow) + "\n")
    print("###\n")
    print("16 lands: \n")
    print("TOTAL GAMES: " + str(bucketLandCmcLow[16]) + "\n")
    print("WIN RATE: " + str(land16WRLow) + "\n")
    print("########################################\n")
    print("DECKS WITH TAPLANDS: \n")
    print("17 lands: \n")
    print("TOTAL GAMES: " + str(bucketTapCmcLow[17]) + "\n") 
    print("WIN RATE: " + str(tap17WRLow) + "\n")
    print("###\n")
    print("16 lands: \n")
    print("TOTAL GAMES: " + str(bucketTapCmcLow[16]) + "\n")
    print("WIN RATE: " + str(tap16WRLow))
    print("\n\n\n")
    print("########################################\n")
    print("DECKS IN GENERAL [NORMAL CMC]: \n")
    print("###\n")
    print("DECKS WITH NO TAPLANDS: \n")
    print("17 lands: \n")
    print("TOTAL GAMES: " + str(bucketLandCmcNormal[17]) + "\n")
    print("WIN RATE: " + str(land17WRNormal) + "\n")
    print("###\n")
    print("16 lands: \n")
    print("TOTAL GAMES: " + str(bucketLandCmcNormal[16]) + "\n")
    print("WIN RATE: " + str(land16WRNormal) + "\n")
    print("########################################\n")
    print("DECKS WITH TAPLANDS: \n")
    print("17 lands: \n")
    print("TOTAL GAMES: " + str(bucketTapCmcNormal[17]) + "\n") 
    print("WIN RATE: " + str(tap17WRNormal) + "\n")
    print("###\n")
    print("16 lands: \n")
    print("TOTAL GAMES: " + str(bucketTapCmcNormal[16]) + "\n")
    print("WIN RATE: " + str(tap16WRNormal))
    print("\n\n\n")
    print("########################################\n")
    print("DECKS IN GENERAL [HIGH CMC]: \n")
    print("###\n")
    print("DECKS WITH NO TAPLANDS: \n")
    print("17 lands: \n")
    print("TOTAL GAMES: " + str(bucketLandCmcHigh[17]) + "\n")
    print("WIN RATE: " + str(land17WRHigh) + "\n")
    print("###\n")
    print("16 lands: \n")
    print("TOTAL GAMES: " + str(bucketLandCmcHigh[16]) + "\n")
    print("WIN RATE: " + str(land16WRHigh) + "\n")
    print("########################################\n")
    print("DECKS WITH TAPLANDS: \n")
    print("17 lands: \n")
    print("TOTAL GAMES: " + str(bucketTapCmcHigh[17]) + "\n") 
    print("WIN RATE: " + str(tap17WRHigh) + "\n")
    print("###\n")
    print("16 lands: \n")
    print("TOTAL GAMES: " + str(bucketTapCmcHigh[16]) + "\n")
    print("WIN RATE: " + str(tap16WRHigh))
    print("########################################\n")
    print("DECKS IN GENERAL [VERY HIGH CMC]: \n")
    print("###\n")
    print("DECKS WITH NO TAPLANDS: \n")
    print("17 lands: \n")
    print("TOTAL GAMES: " + str(bucketLandCmcVeryHigh[17]) + "\n")
    print("WIN RATE: " + str(land17WRVeryHigh) + "\n")
    print("###\n")
    print("16 lands: \n")
    print("TOTAL GAMES: " + str(bucketLandCmcVeryHigh[16]) + "\n")
    print("WIN RATE: " + str(land16WRVeryHigh) + "\n")
    print("########################################\n")
    print("DECKS WITH TAPLANDS: \n")
    print("17 lands: \n")
    print("TOTAL GAMES: " + str(bucketTapCmcVeryHigh[17]) + "\n") 
    print("WIN RATE: " + str(tap17WRVeryHigh) + "\n")
    print("###\n")
    print("16 lands: \n")
    print("TOTAL GAMES: " + str(bucketTapCmcVeryHigh[16]) + "\n")
    print("WIN RATE: " + str(tap16WRVeryHigh))
    X = ['not specified', 'VL','L','N','H', 'VH']
    Y17tap = [tap17WR, tap17WRVeryLow, tap17WRLow, tap17WRNormal, tap17WRHigh, tap17WRVeryHigh]
    Y17noTap = [land17WR, land17WRVeryLow, land17WRLow, land17WRNormal, land17WRHigh, land17WRVeryHigh]
    Y16tap = [tap16WR, tap16WRVeryLow, tap16WRLow, tap16WRNormal, tap16WRHigh, tap16WRVeryHigh]
    Y16noTap = [land16WR, land16WRVeryLow, land16WRLow, land16WRNormal, land16WRHigh, land16WRVeryHigh]

    X_axis = np.arange(len(X))
    
    plt.bar(X_axis - 0.2, Y17noTap, 0.1, label = '17 lands [no taplands]')
    plt.bar(X_axis - 0.1, Y17tap, 0.1, label = '17 lands [taplands]')
    plt.bar(X_axis + 0.1, Y16noTap, 0.1, label = '16 lands [no taplands]')
    plt.bar(X_axis + 0.2, Y16tap, 0.1, label = '16 lands [taplands]')
    
    plt.xticks(X_axis, X)
    plt.xlabel("Groups")
    plt.ylabel("WR")
    plt.title("WR of decks sorted by CMC value")
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    start = time.time()
    oracleJson = [json.loads(line) for line in open(setOracle, 'r')]
    headerStartTime = time.time()
    with open(thinGameData, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        headerEndTime = time.time()
    print("Header succesfully read [time: " + str(headerEndTime - headerStartTime) + "s].\n")
    maskStartTime = time.time()
    populateMaskBasicLand(header)
    populateMaskNonBasicLand(header, oracleJson)
    populateMaskAllLand()
    populateMaskCmcVal(header, oracleJson)
    #print(header)
    #print(maskCmcVal)
    maskEndTime = time.time()
    print(maskTapLand)
    print("Masks succesfully populated [time: " + str(maskEndTime - maskStartTime) + "s].\n")
    bucketStartTime = time.time()
    initializeBuckets(bucketSize)
    bucketEndTime = time.time()
    print("Buckets succesfully initialized [time: " + str(bucketEndTime - bucketStartTime) + "s].\n")
    dfReadStartTime = time.time()
    df = pd.read_csv(thinGameData, nrows=gamesParsed)
    dfReadEndTime = time.time()
    print("Data frame succesfully loaded (n = " + str(gamesParsed) + ") [time: " + str(dfReadEndTime - dfReadStartTime) + "s].\n")
    dfApplyStartTime = time.time()
    #df = df.apply(processRow(), axis=1)
    df = df.apply(lambda row: processRow(row), axis=1)
    dfApplyEndTime = time.time()
    print("Data frame processing succesful (n = " + str(gamesParsed) + ") [time: " + str(dfApplyEndTime - dfApplyStartTime) + "s].\n")
    retrieveBucketData()
    end = time.time()
    print("Program executed succesfully [time: " + str(end - start) + "s].\n")
            

