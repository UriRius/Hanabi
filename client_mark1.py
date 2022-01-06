#!/usr/bin/env python3

from sys import argv, stdout
from threading import Thread
import GameData
import socket
from constants import *
import os
import time


"""TODO
   - TENIR CONTROLADES LES CARTES QUE SON PISTA, LES JUGADES I LES DESCARTADES
   - NO TORNAR A DONAR PISTES JA DONADES!!!!!!!
   - ARREGLAR ELS BUGS QUE HI HAGI
   - BORRAR PISTES BE LES PISTES JUGADES DELS PLAYERS
   - ALGORITME PER JUGAR
   - ALGORITME PER DESCARTAR
   - ALGORITME PER DONAR PISTA"""

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
hintsRecieved = []
hintsForIA = []
UsedTokens = ""
players=[]
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

    if NewHint in hintsForIA:
        print("Ja tenim aquesta pista")
    else:
        hintsForIA.append(NewHint)

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
                            s.send(GameData.ClientHintData(playerName, p_names[0], "value", 1).serialize())
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
            #Aqui inicialitzem la nostra variable de players
            players= data.players
            for p in data.players:
                print(p.toClientString())
            print("Table cards: ")
            for pos in data.tableCards:
                print(pos + ": [ ")
                for c in data.tableCards[pos]:
                    print(c.toClientString() + " ")
                print("]")
            print("Discard pile: ")
            for c in data.discardPile:
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
            run = False
        if not dataOk:
            print("Unknown or unimplemented data type: " +  str(type(data)))
        print("[" + playerName + " - " + status + "]: ", end="")
        stdout.flush()