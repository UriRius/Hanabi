#!/usr/bin/env python3

from sys import argv, stdout
from threading import Thread
import GameData
import socket
from constants import *
import os
import time

if len(argv) < 4:
    print("You need the player name to start the game.")
    #exit(-1)
    playerName = "Test" # For debug
    ip = HOST
    port = PORT
else:
    playerName = argv[3]
    ip = argv[1]
    port = int(argv[2])

run = True

statuses = ["Lobby", "Game", "GameHint"]

status = statuses[0]

hintState = ("", "")

#new variables

#For each card in hand there is going to be 3 attributes, the value (default 0), the color (default None) and a Tag
#with values Res, jugable, descartable, perillosa, perillosajugable
Hand = [["0", "None", "Res"],["0", "None", "Res"],["0", "None", "Res"],["0", "None", "Res"],["0", "None", "Res"]]
hintsRecieved = []
hintsForIA = []
UsedTokens = ""
Players=[]
PlayedCards= []
DiscartedCards= []
p_names=[]
waitUntil=False

#new functions
"""This function is used to remove the hint played/discard"""
def RemoveHint(RemHint):
    cardIndex = RemHint.split(" ")[0]

    start= int(cardIndex)-1
    for i in range(start, 0, -1):
        Hand[i+1] = Hand[i]
    Hand[0]=["0", "None", "Res"]
    print("Sortim de la borramenta")


def addHintsForIA(NewHint):
    card = Hand[0]
    value = card[0]
    color = card[1]
    tag = card[2]

    cardposition = NewHint.split(" ")[0]
    cardvalue = NewHint.split(" ")[1]

    nums = ["1", "2", "3", "4", "5"]
    if cardvalue in nums:
        Hand[cardposition] = cardvalue + " " + color + " " + tag
    else:
        Hand[cardposition] = value + " " + cardvalue + " " + tag
    
    TagHand(Hand)

def most_frequent(List):
    return max(set(List), key = List.count)

def HotCards():
    valors = []
    colors = []
    HotValue = "0"
    HotColor = "black"
    if DiscartedCards:
        for c in DiscartedCards:
            cardvalue = c.split(" ")[1]
            valors.append(cardvalue)
            cardcolor = c.split(" ")[3]
            colors.append(cardcolor)

        HotColor = most_frequent(colors)
        HotValue = most_frequent(valors)
    return HotValue + " " + HotColor

def isDangerous(value, color):
    #This function returns True if discarting the card is dangerous
    Hots = HotCards()
    HotValue = Hots.split(" ")[0]
    HotColor = Hots.split(" ")[0]

    #it's a 5
    if value == "5":
        return True
    #it's the most frequent descarted color/value
    elif value == HotValue or color == HotColor:
        return True
    #it's a between 1 and 4 and the other cards with same value & color had been discarted
    elif value == "1":
        discard = "Card "+ value + " - " + color
        if DiscartedCards.count(discard) > 1: return True
        else: return False
    else:
        discard = "Card "+ value + " - " + color
        if discard in DiscartedCards: return True
        else: return False

def isJugable(value, color):
    #This function returns True if playing the card is save
    carta = "Card "+ value + " - " + color
    #the card has been played
    if carta in PlayedCards:
        return False
    #card below has been played
    for c in PlayedCards:
        val = c.split(" ")[1]
        col = c.split(" ")[3]
        value = int(value) - 1
        if val == str(value) and color == col:
            return True

def isJugaPerill(value, color):
    #This function returns True if discarting the card is dangerous but playing is save
    return isJugable(value, color) and isDangerous(value,color)

def isDescartable(value, color):
    #This function returns True if discarting the card is save
    carta = "Card "+ value + " - " + color
    #the card has been played
    if carta in PlayedCards:
        return True
    #inferior card had been discarted
    for c in DiscartedCards:
        val = c.split(" ")[1]
        col = c.split(" ")[3]
        if val == "1" and col == color and DiscartedCards.count(c) == 3: return True
        if int(val) < int(value) and col == color and DiscartedCards.count(c) == 2: return True
    return False
    
def evaluaCarta(value, color):
    if isJugaPerill(value, color):
        tag = "perillosajugable"
    elif isDescartable(value, color):
        tag = "descartable"
    elif isJugable(value, color):
        tag = "jugable"
    elif isDangerous(value , color):
        tag = "perillosa"
    else:
        tag = "Res"
    return tag
        

def TagHand(ma):
    #This function changes the tag for every card in a given hand
    i = 0
    for card in ma:
        value = card.split(" ")[0]
        color = card.split(" ")[1]
        
        tag = evaluaCarta(value, color)

        carta = value + " " + color + " " + tag
        ma[i] = carta
        i += 1

def downloadPlayersHandsTag():
    PlayersHands = [[0 for i in range(6)]] * (len(Players)-1)
    i = -1
    for p in  Players:
        if p.name != playerName:
            PlayersHands[i][0] = str(p.name)
            j = 1
            for c in p.hand:
                value = c.toClientString().split(" ")[1]
                color = c.toClientString().split(" ")[3]
                tag = evaluaCarta(value, color)
                PlayersHands[i][j] = tag
                j += 1
        i += 1
    return PlayersHands

def SearchPosition(player, position):
    #which card has the player in the given position
    for p in  Players:
        if p.name != player:
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!ALERTA BUG LA MA ESTA BUIDA
            c=p.hand[position]
    return c
    
def getPlayerHand(player):
    hand = []
    for p in  Players:
        if p.name != player:
            for c in p.hand:
                value = c.toClientString().split(" ")[1]
                color = c.toClientString().split(" ")[3]
                hand.append(value)
                hand.append(color)
    return hand

def Value_Color(player, card):
    pista = []
    value = card.split(" ")[0]
    color = card.split(" ")[1]
    hand = getPlayerHand(player)
    valueCounter = hand.count(value)
    colorCounter = hand.count(color)
    if colorCounter >= valueCounter:
        pista.append("value")
        pista.append(value)
    else:
        pista.append("color")
        pista.append(color)
    return pista


def BestMove():
    #final solution
    solution = "10 play 0"
    #solution for every player that will be evaluated later
    semisolution = [11] * len(Players)
    #we still can give hints
    if UsedTokens != "8":
        PlayersHands=downloadPlayersHandsTag() #format -> [[Player_name, tag, tag, tag, tag, tag], [....]]
        L = len(PlayersHands)
        for i in range(L):
            player = PlayersHands[i][0]
            for j in range(1, 6):
                c = PlayersHands[i][j]
                hand_tag = Hand[i][2]
                card=SearchPosition(player, j-1)
                q1 = semisolution[i].split(" ")[0]
                if "perillosa" == c:
                    if int(q1) > 0:
                        pista = Value_Color(player, card)
                        semisolution[i] = "0 " + "hint " + pista[0] + player + pista[1]
                elif "perillosajugable" == c:
                    if int(q1) > 1:
                        pista = Value_Color(player, card)
                        semisolution[i] = "1 "+"hint " + pista[0] + player + pista[1]
                elif "jugable" == hand_tag:
                    if int(q1) > 2:
                        semisolution[i] = "2 "+"play " + str(i)
                elif "jugable" == c:
                    if int(q1) > 3:
                        pista = Value_Color(player, card)
                        semisolution[i] = "3 "+"hint " + pista[0] + player + pista[1]
                if "descartable" == hand_tag and UsedTokens != "0":
                    if int(q1) > 4:
                        semisolution[i] = "4 "+"discard " + str(i)
                elif "descartables" == c:
                    if int(q1) > 5:
                        pista = Value_Color(player, card)
                        semisolution[i] = "5 "+"hint " + pista[0] + player + pista[1]
                elif "Res" == hand_tag and UsedTokens != "0":
                    if int(q1) > 6:
                        semisolution[i] = "6 "+"discard " + str(i)
                else:
                    if int(q1) > 7:
                        pista = Value_Color(player, card)
                        semisolution[i] = "7 "+"hint " + pista[0] + player + pista[1]
                
    else:
        L = len(Hand)
        for i in range(L):
            c = Hand[i][3]
            q1 = semisolution[i].split(" ")[0]
            if "descartable" == c and UsedTokens != "0":
                if int(q1) > 0:
                    semisolution[i] = "0 "+"discard " + str(i)
            elif "jugable" == c:
                if int(q1) > 1:
                    semisolution[i] = "1 "+ "play " + str(i)
            elif "Res" == c and UsedTokens != "0":
                if int(q1) > 2:
                    semisolution[i] = "2 "+"discard " + str(i)
            elif UsedTokens != "0":
                if int(q1) > 3:
                    semisolution[i] = "3 "+"discard " + str(i)
            else:
                if int(q1) > 4:
                    semisolution[i] = "4 "+"play " + str(i)
        

    for sol in semisolution:
        q1 = solution.split(" ")[0]
        q2 = sol.split(" ")[0]
        if int(q1) > int(q2):
            solution = sol

    solution = solution[1:]
    return solution            

def manageInput():
    global run
    global status
    #Boolean that controls if a show has been done
    DoShow=True
    #True if it's the first time we acces to the players attrb.
    while run:
        command = input()
        if command == "exit":
            run = False
            os._exit(0)
        else:
            if status == statuses[0]:
                #If status==Lobby we send start request
                s.send(GameData.ClientPlayerStartRequest(playerName).serialize())
            else:
                if DoShow:
                    #We request the show action everytime we play
                    DoShow=False
                    s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
                    #we have to sleep to get the response before doing anything
                    while waitUntil == False:
                        time.sleep(2)
                    
                #try:
                #BstMv options are (play <num>), (discard <num>), (hint <type> <player> <value>)
                BstMv=BestMove()

                move = BstMv.split(" ")[0]
                num = BstMv.split(" ")[1]
                
                if move == "play":
                    s.send(GameData.ClientPlayerPlayCardRequest(playerName, num).serialize())
                elif move == "discard":
                    s.send(GameData.ClientPlayerDiscardCardRequest(playerName, num).serialize())
                else:
                    player = BstMv.split(" ")[2]
                    value = BstMv.split(" ")[3]
                    s.send(GameData.ClientHintData(playerName, player, num, value).serialize())
                
                #except:
                    #print("Ups problemita, hem fallat en algo 0w0")
                    #continue
        stdout.flush()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    request = GameData.ClientPlayerAddData(playerName)
    s.connect((HOST, PORT))
    s.send(request.serialize())
    data = s.recv(DATASIZE)
    data = GameData.GameData.deserialize(data)
    if type(data) is GameData.ServerPlayerConnectionOk:
        print("Connection accepted by the server. Welcome " + playerName)
    print("[" + playerName + " - " + status + "]: ", end="")
    Thread(target=manageInput).start()
    while run:
        dataOk = False
        data = s.recv(DATASIZE)
        if not data:
            continue
        data = GameData.GameData.deserialize(data)
        if type(data) is GameData.ServerPlayerStartRequestAccepted:
            dataOk = True
            print("Ready: " + str(data.acceptedStartRequests) + "/"  + str(data.connectedPlayers) + " players")
            data = s.recv(DATASIZE)
            data = GameData.GameData.deserialize(data)
        if type(data) is GameData.ServerStartGameData:
            dataOk = True
            print("Game start!")
            s.send(GameData.ClientPlayerReadyData(playerName).serialize())
            status = statuses[1]
        if type(data) is GameData.ServerGameStateData:
            #Aqui es rep el show
            dataOk = True
            waitUntil = True
            print("Current player: " + data.currentPlayer)
            print("Player hands: ")
            #Aqui actualitzem la nostra variable de players per tenir la seva ma en tot moment
            Players= data.players
            for p in data.players:
                print(p.toClientString())
            print("Table cards: ")
            for pos in data.tableCards:
                print(pos + ": [ ")
                for c in data.tableCards[pos]:
                    #AQUI ES PODEN AGAFAR LES CARTES JUGADES
                    PlayedCards.append[c.toClientString()]
                    print(c.toClientString() + " ")
                print("]")
            print("Discard pile: ")
            for c in data.discardPile:
                DiscartedCards.append[c.toClientString()]
                print("\t" + c.toClientString())           
            UsedTokens=str(data.usedNoteTokens)
            print("Note tokens used: " + str(data.usedNoteTokens) + "/8")
            print("Storm tokens used: " + str(data.usedStormTokens) + "/3")
        if type(data) is GameData.ServerActionInvalid:
            dataOk = True
            print("Invalid action performed. Reason:")
            print(data.message)
        if type(data) is GameData.ServerActionValid:
            dataOk = True
            print("Card played Valid: " +  str(data.card.value)+ " " + str(data.card.color))
            print("Played by Valid: " +  str(data.lastPlayer))
            RemHint = (str(data.cardHandIndex))
            if str(data.lastPlayer) == playerName:
                RemoveHint(RemHint)
            print("Action valid!")
            print("Current player: " + data.player)
        if type(data) is GameData.ServerPlayerMoveOk:
            #Hem jugat bé una carta
            dataOk = True
            print("Card played: " +  str(data.card.value)+ " " + str(data.card.color))
            print("Played by: " +  str(data.lastPlayer))
            RemHint = (str(data.cardHandIndex))
            if str(data.lastPlayer) == playerName:
                RemoveHint(RemHint)
            print("Action valid!")
            print("Nice move!")
            print("Current player: " + data.player)
        if type(data) is GameData.ServerPlayerThunderStrike:
            #Hem jugat malament una carta
            dataOk = True
            print("Card played OH NO: " +  str(data.card.value)+ " " + str(data.card.color))
            print("Played by OH NO: " +  str(data.lastPlayer))
            print("OH NO! The Gods are unhappy with you!")
        if type(data) is GameData.ServerHintData:
            #Aqui es reben les pistes
            dataOk = True
            print("Hint type: " + data.type)
            print("Player " + data.destination + " cards with value " + str(data.value) + " are:")
            for i in data.positions:
                if str(data.destination) == playerName:
                    NewHint = (str(i) + " " + str(data.value))
                    addHintsForIA(NewHint)
                print("\t" + str(i))
        if type(data) is GameData.ServerInvalidDataReceived:
            dataOk = True
            print(data.data)
        if type(data) is GameData.ServerGameOver:
            dataOk = True
            print(data.message)
            print(data.score)
            print(data.scoreMessage)
            stdout.flush()
            #run = False
            print("Ready for a new game!")
        if not dataOk:
            print("Unknown or unimplemented data type: " +  str(type(data)))
        print("[" + playerName + " - " + status + "]: ", end="")
        stdout.flush()