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

#For each card in hand there is going to be 3 attributes, the value (default 0), the color (default None) and a Tagç
#with values Res, jugable, descartable, perillosa, perillosajugable
Hand = [["0", "None", "Res"],["0", "None", "Res"],["0", "None", "Res"],["0", "None", "Res"],["0", "None", "Res"]]
Color = [["red", "yellow", "green", "blue", "white"],["red", "yellow", "green", "blue", "white"],["red", "yellow", "green", "blue", "white"],
["red", "yellow", "green", "blue", "white"],["red", "yellow", "green", "blue", "white"]]
Valors = [["1", "2", "3", "4", "5"],["1", "2", "3", "4", "5"],["1", "2", "3", "4", "5"],["1", "2", "3", "4", "5"],["1", "2", "3", "4", "5"]]
hintsRecieved = []
hintsForIA = []
UsedTokens = ""
players=[]
PlayedCards= []
DiscartedCards= []
p_names=[]
waitUntil=False

#new functions
"""This function is used to update the new hints that every player recives"""
def addHintsRecived(NewHint):
    if NewHint in hintsRecieved:
        print("Ja tenim aquesta pista")
    else:
        print("aquesta pista l'agefim " + NewHint)
        hintsRecieved.append(NewHint)

"""This function is used to remove the hint a the IA or a player played/discard"""
def RemoveHint(RemHint):
    
    print("Totes les pistes fins ara dels jugadors: ", hintsRecieved)
    print("Totes les pistes fins ara per la IA: ", hintsForIA)

    cardIndex = RemHint.split(" ")[0]
    jugador = RemHint.split(" ")[1]
    
    #if the player is not the IA remove from the list hints Recived
    if jugador != playerName:

        for val in hintsRecieved:
            HRcardIndex = val.split(" ")[0]
            HRjugador = val.split(" ")[2]
            if HRcardIndex == cardIndex and HRjugador == jugador:
                print("La pista es pot borrar pel jugador , index:", cardIndex)
                valIndex = hintsRecieved.index(val)
                hintsRecieved.pop(valIndex)

                tmp = hintsRecieved
                for b in tmp:
                    position = b.split(" ")[0]
                    tipus = b.split(" ")[1]
                    jg = b.split(" ")[2]

                    hintsRecieved.pop(0)

                    if HRcardIndex < position and jg == jugador:
                        newPos = int(position) - 1 
                        hintsRecieved.append(str(newPos) + " " + tipus + " "+ jg)
                    else:
                        hintsRecieved.append(position + " " + tipus + " "+ jg)
    else:
        for val in hintsForIA:
            HRcardIndex = val.split(" ")[0]

            if HRcardIndex == cardIndex:
                print("La pista es pot borrar per la IA, index:", cardIndex)
                valIndex = hintsForIA.index(val)
                hintsForIA.pop(valIndex)

                tmp = hintsForIA
                for b in tmp:
                    position = b.split(" ")[0]
                    tipus = b.split(" ")[1]

                    hintsForIA.pop(0)

                    if HRcardIndex < position:
                        newPos = int(position) - 1 
                        hintsForIA.append(str(newPos) + " " + tipus)
                    else:
                        hintsForIA.append(position + " " + tipus)

    
    print("Sortim de la borramenta")


def addHintsForIA(NewHint):
    print("Fent update per la IA")
    print("Totes les pistes fins ara per la IA: ", hintsForIA)
    
    cardposition = NewHint.split(" ")[0]
    cardvalue = NewHint.split(" ")[1]

    if NewHint in hintsForIA:
        print("Ja tenim aquesta pista")
    else:
        hintsForIA.append(NewHint)

def isDangerous(value, color):
    #This function returns True if discarting the card is dangerous
    if value == "5":
        return True
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
    if carta in PlayedCards:
        return False
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
    if carta in PlayedCards:
        return True
    for c in DiscartedCards:
        val = c.split(" ")[1]
        col = c.split(" ")[3]
        if val == "1" and col == color and DiscartedCards.count(c) == 3: return True
        if int(val) < int(value) and col == color and DiscartedCards.count(c) == 2: return True
    return False
    
def TagHand(ma):
    #This function changes the tag for every card in a given hand
    i = 0
    for card in ma:
        value = card.split(" ")[0]
        color = card.split(" ")[1]
        
        if isDangerous(value , color):
            tag = "perillosa"
        elif isJugaPerill(value, color):
            tag = "perillosajugable"
        elif isJugable(value, color):
            tag = "jugable"
        elif isDescartable(value, color):
            tag = "descartable"
        else:
            tag = "Res"
        
        carta = value + " " + color + " " + tag
        ma[i] = carta
        i += 1

def BestMove():
    solution = "discard 0"
    #if queden tokens blaus
        #'descarregar' mans dels altres jugadors amb les seves hot cards
        #if tenen perilloses
            #return avisar de perilloses
        #elif tenen perilloses&jugables 
            #return avisar de perilloses&jugables
        #elif puc jugar 100% segur
            #return jugar 100%
        #elif tenen jugables
            #return avisar jugables
        #elif puc jugar 50% segur
            #return jugar 50%
        #elif puc descartar 100%
            #return descartar 100%
        #elif tenen descartables
            #return avisar descartables
        #elif puc descartar 50%
            #return descartar 50%
        #elif tinc algunes etiquetes posades
            #return descartar RES
        #else
            #return descartar random
    #else
        #if puc descartar 100%
            #return descartar 100%
        #elif puc jugar 100% segur
            #return jugar 100%
        #elif puc jugar 50% segur
            #return jugar 50%
        #elif puc descartar 50%
            #return descartar 50%
        #elif tinc algunes etiquetes posades
            #return descartar RES
        #else
            #return descartar random

    return solution            

def manageInput():
    global run
    global status
    #Boolean that controls if a show has been done
    showDone=True
    #True if it's the first time we acces to the players attrb.
    first=True
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
                
                print("Totes les pistes fins ara dels jugadors: ", hintsRecieved)
                print("Totes les pistes fins ara per la IA: ", hintsForIA)

                if showDone:
                    #We request the show action everytime we play
                    showDone=False
                    s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
                    #we have to sleep to get the response before doing anything
                    while waitUntil == False:
                        time.sleep(2)
                    
                try:
                    
                    if not hintsForIA:
                        print("no te pistes no")
                        has_ones = False
                        for p in players:
                            #We check the hand of every player
                            if first:
                                first=False
                                p_names.append(p.name)

                            for c in p.hand:
                                valor = c.toString().split(" ")[3]
                                if valor == "1;":
                                    print("Diu que te uns")
                                    has_ones = True
                        
                        #EN UN FUTUR ES POT INTENTAR FER UN ALGORITME PER SABER QUINA ES LA MILLOR PISTA A DONAR!!!!!!!!!!!!
                        #EN UN FUTUR ES POT INTENTAR FER UN ALGORITME PER SABER QUINA ES LA MILLOR CARTA A DESCARTAR!!!!!!!!
                        showDone=True
                        if has_ones:
                            s.send(GameData.ClientHintData(playerName, p_names[1], "value", 1).serialize())
                        else:
                            print("no hi han uns")
                            if UsedTokens=="0":
                                print("jugem")
                                #play first
                                s.send(GameData.ClientPlayerPlayCardRequest(playerName, 0).serialize())

                            else:
                                print("descartem")
                                #discard first
                                s.send(GameData.ClientPlayerDiscardCardRequest(playerName, 0).serialize())

                    else: 
                        #La IA ha rebut pistes
                        #cada pista te el seguent format: (posicio, valor, jugador)

                        #EN UN FUTUR ES POT INTENTAR FER UN ALGORITME PER SABER QUINA ES LA MILLOR CARTA A JUGAR!!!!!!!!!!!!
                     
                        print("si tenim pistes")
                        print("len de hints es :", len(hintsForIA))
                     
                        position = hintsForIA[0].split(" ")[0]
                        value = hintsForIA[0].split(" ")[1]
                        print("el primer esta a la pos " + position + " i es " + value)
                        cardOrder = int(position)
                        s.send(GameData.ClientPlayerPlayCardRequest(playerName, cardOrder).serialize())
                        #hintsForIA.pop(0)
                        showDone=True

                except:
                    print("Ups problemita, hem fallat en algo 0w0")
                    continue
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
            players= data.players
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
            RemHint = (str(data.cardHandIndex) + " " + str(data.lastPlayer))
            RemoveHint(RemHint)
            print("Action valid!")
            print("Current player: " + data.player)
        if type(data) is GameData.ServerPlayerMoveOk:
            #Hem jugat bé una carta
            dataOk = True
            print("Card played: " +  str(data.card.value)+ " " + str(data.card.color))
            print("Played by: " +  str(data.lastPlayer))
            RemHint = (str(data.cardHandIndex) + " " + str(data.lastPlayer))
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
                
                if str(data.destination) != playerName:
                    NewHint = (str(i) + " " + str(data.value) + " "+ str(data.destination))
                    addHintsRecived(NewHint)
                else:
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