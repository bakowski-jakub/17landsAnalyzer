import scrython
import pandas as pd
import csv
import time
import json
from dask import dataframe as dd


set = "ONE"
format    = "PremierDraft"
gameDataFilename = "./rawData/game_data_public." + set + "." + format +".csv"
setOracle = "./rawData/" + set + "_oracle.json"

header = []
rows = []

landList = []
cardList = []

deckList = []

gamesParsed = 100

totalGames17 = 0
totalWins17 = 0
averageCmc17 = 0

totalGames16 = 0
totalWins16 = 0
averageCmc16 = 0

def populateLandList():
    search = scrython.cards.Search(q="t:land" + " " + "set:" + set, format="string")
    landCount = search.total_cards()
    for i in range(landCount):
        landName = search.data(i, 'name')
        landName = "deck_" + landName
        landList.append(landName)

def presentLands(landList):
    print("All land types present in the set: \n")
    for land in landList:
        print(land)

def tallyLands(data, row):
    sum = 0
    for land in landList:
        sum = sum + int(data.loc[row, land])
    return sum

def populateCardList(header):
    entryCount = len(header)
    for i in range(entryCount):
        if "deck_" in header[i]:
            cardList.append(header[i])

def populateDeckList(data, row):
    cardName = []
    cardNum  = []
    for card in cardList:
        #print("Card: " + str(card) + "\n")
        #print("Row: " + str(row) + "\n")
        #print("Data.loc[row,card]: " + data.loc[row,card] + "\n")
        if int(data.loc[row, card]) != 0:
            cardName.append(card)
            num = int(data.loc[row,card])
            cardNum.append(num)
    final = list(zip(cardName, cardNum))
    return final

def namePruning(string):
    prefix = "deck_"
    string = string.replace(prefix,'')
    return string

def findCmc(cardName, oracleJson):
    #time.sleep(0.1)
    #card = scrython.cards.Named(exact=string)
    cmc = 0
    for key in range(len(oracleJson)):
        if oracleJson[key]['name'] == cardName:
            cmc = oracleJson[key]['cmc']
    return cmc

def findDeckAvgCmc(decklist, oracleJson):
    playablesTally = 0
    totalMana = 0
    deckSize = len(decklist)
    for i in range(deckSize):
        name = str(decklist[i][0])
        if name not in landList:
            name = namePruning(name)
            cmc = findCmc(name, oracleJson)
            numCards = int(decklist[i][1])
            print(name + " - " + str(numCards) + " cmc: " + str(cmc)) 
            playablesTally = playablesTally + numCards
            totalMana = totalMana + (numCards * cmc)
    avgCmc = totalMana / playablesTally
    return avgCmc

def findWinRate(totalGames, totalWins):
    return totalWins / totalGames

def findAvgCmc(gamesParsed, avgCmc):
    return avgCmc / gamesParsed

if __name__ == "__main__":
    start = time.time()
    populateLandList()
    #presentLands(landList)
    oracleJson = [json.loads(line) for line in open(setOracle, 'r')]

    print('\n')

    with open(gameDataFilename, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        populateCardList(header)
        #print(cardList)
        for row in range(gamesParsed):
            print("Local data: " + str(row) + " out of games parsed (" + str(gamesParsed) +")\n")
            rows.append(next(reader))
        data = pd.DataFrame(rows, columns = header)
        for row in range(gamesParsed):
            print("Analytics: " + str(row) + " out of games parsed (" + str(gamesParsed) +")\n")
            deckList = populateDeckList(data, row)
            avgCmc = findDeckAvgCmc(deckList, oracleJson)
            print('\n')
            lands = tallyLands(data, row)
            win = data.loc[row, "won"]
            print("Total lands: " + str(lands))
            print("Average CMC: " + str(avgCmc))
            print("On the play: " + str(data.loc[row,"on_play"]))
            print("Won: " + win)
            if lands == 17:
                totalGames17 = totalGames17+1
                averageCmc17 = averageCmc17 + avgCmc
                if str(win) == "True":
                    totalWins17 = totalWins17+1
            if lands == 16:
                totalGames16 = totalGames16+1
                averageCmc16 = averageCmc16 + avgCmc
                if str(win) == "True":
                    totalWins16 = totalWins16+1
            deckList = []
            rows = []
            avgCmc = 0
            lands = 0
            win = 0
        print("\n")
        print("###\n")
        print("Games parsed: " + str(gamesParsed) + "\n")
        print("###\n")
        print("\n")
        print("17 lands total games: " + str(totalGames17) + "\n")
        print("17 lands total wins: " + str(totalWins17) + "\n")
        print("17 lands WR: " + str(findWinRate(totalGames17, totalWins17)) + "\n")
        print("17 lands avg CMC: " + str(findAvgCmc(totalGames17, averageCmc17)) + "\n")
        print("###\n")
        print("16 lands total games: " + str(totalGames16) + "\n")
        print("16 lands total wins: " + str(totalWins16) + "\n")
        print("16 lands WR: " + str(findWinRate(totalGames16, totalWins16)) + "\n")
        print("16 lands avg CMC: " + str(findAvgCmc(totalGames16, averageCmc16)) + "\n")
        print("\n")
        print("\n")
        print("\n")
        end = time.time()
            

