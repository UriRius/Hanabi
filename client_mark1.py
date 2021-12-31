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
hintsRecieved = []
UsedTokens = ""
players=[]
p_names=[]
waitUntil=False

#new functions

#this method is used to remove the used hints 
#ALERTA BUGS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! NOMES FA REMOVE DE LES SEVES PISTES I LA POT LIAR BORRANT LA D'ALTRES JUGADORS
def updateHintsRecived(cardOrder):
    for val in hintsRecieved:
        if cardOrder < hintsRecieved[val].split(" ")[0]:
            pos = hintsRecieved[val].split(" ")[0] - 1 
        else:
            pos = hintsRecieved[val].split(" ")[0]
        valor = hintsRecieved[val].split(" ")[1]  
        jugador = hintsRecieved[val].split(" ")[2]  
        hintsRecieved.pop(val)
        hintsRecieved.append(pos + " " + valor + " "+ jugador)

#this method is used to know if the IA has some clues for it
def pistesForIA():
    hints=False
    print("te pistes la IA?")
    i = 0

    for h in hintsRecieved:
        print("iteracio num: ", h)
        print("valor de la i:", i)
        jugador = hintsRecieved[i].split(" ")[2]
        print("jugador: ", jugador)
        print("playerName: ", playerName)
        if jugador == playerName:
            hints = True
        i=i+1
    
    print("PISTES: ",hints)
    return hints



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
                
                print("Totes les pistes fins ara: ", hintsRecieved)

                if showDone:
                    #We request the show action everytime we play
                    showDone=False
                    s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
                    #we have to sleep to get the response before doing anything
                    while waitUntil == False:
                        time.sleep(2)
                    
                try:
                    
                    hintsForIA = pistesForIA()
                    print("sortim de la funcio de pistes")
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
                                    print("L'altre te uns")
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
                        #posem aqui la primera pista rebuda

                        #EN UN FUTUR ES POT INTENTAR FER UN ALGORITME PER SABER QUINA ES LA MILLOR CARTA A JUGAR!!!!!!!!!!!!
                        acceptable = False
                        i = 0
                        print("si tenim pistes")
                        print("len de hints es :", len(hintsRecieved))
                        while not acceptable and i < len(hintsRecieved): 
                            jugador = hintsRecieved[i].split(" ")[2]
                            if jugador == playerName:
                                position = hintsRecieved[i].split(" ")[0]
                                value = hintsRecieved[i].split(" ")[1]
                                print("el primer esta a la pos " + position + " i es " + value)
                                cardOrder = int(position)
                                s.send(GameData.ClientPlayerPlayCardRequest(playerName, cardOrder).serialize())
                                hintsRecieved.pop(i)
                                updateHintsRecived(cardOrder)
                                acceptable = True
                                showDone=True
                                break
                            i=i+1
                        print("SALIIIIIMOOOOO")

                        #ALERTA BUGS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! COM LLEGIM LES PISTES DE TOTS ELS JUGADORS ENTREM AQUI I NO HAURIEM

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
            print("Action valid!")
            print("Current player: " + data.player)
        if type(data) is GameData.ServerPlayerMoveOk:
            #Hem jugat bé una carta
            dataOk = True
            print("Nice move!")
            print("Current player: " + data.player)
        if type(data) is GameData.ServerPlayerThunderStrike:
            #Hem jugat malament una carta
            dataOk = True
            print("OH NO! The Gods are unhappy with you!")
        if type(data) is GameData.ServerHintData:
            #Aqui es reben les pistes
            dataOk = True
            print("Hint type: " + data.type)
            print("Player " + data.destination + " cards with value " + str(data.value) + " are:")
            for i in data.positions:
                hintsRecieved.append(str(i) + " " + str(data.value) + " "+ str(data.destination))
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