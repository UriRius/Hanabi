#!/usr/bin/env python3

from sys import argv, stdout
from threading import Thread
import GameData
import socket
from constants import *
import os


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

hintsRecieved = []

players=[]

def manageInput():
    global run
    global status
    #boolea que controla si es fa o no un show
    faltaInfo=True
    while run:
        #Utilitzem input per controlara la IA
        command = input()
        if command == "exit":
            run = False
            os._exit(0)
        else:
            if status == statuses[0]:
                #si status es Lobby es fa un ready req.
                s.send(GameData.ClientPlayerStartRequest(playerName).serialize())
            else:
                #Status es Game/Gamehint
                print("Totes les pistes fins ara: ", hintsRecieved)
                
                for p in players:
                    #Accedim els atributs de cada jugador d'aquesta manera
                    print(p.name)
                    print(p.hand)
                    #un player te per atributs el nom, la ma i ready
                
                if faltaInfo:
                    #fem un show cada vegada abans de jugar
                    faltaInfo=False
                    #La info es rep en la funcio de sota
                    s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
                
                try:
                    if not hintsRecieved:
                        #La IA no ha rebut pistes
                        print("jugo la carta 0")
                        
                        #Es torna a posar el bolea a true pel proxim cop que es jugi
                        faltaInfo=True
                        
                        #EN UN FUTUR ES POT INTENTAR FER UN ALGORITME PER SABER QUINA ES LA MILLOR PISTA A DONAR!!!!!!!!!!!!
                        #EN UN FUTUR ES POT INTENTAR FER UN ALGORITME PER SABER QUINA ES LA MILLOR CARTA A DESCARTAR!!!!!!!!
                        s.send(GameData.ClientPlayerPlayCardRequest(playerName, 0).serialize())
                    else: 
                        #La IA ha rebut pistes
                        #cada pista te el seguent format: (posicio, valor)
                        #posem aqui la primera pista rebuda

                        #EN UN FUTUR ES POT INTENTAR FER UN ALGORITME PER SABER QUINA ES LA MILLOR CARTA A JUGAR!!!!!!!!!!!!
                        hintsRecieved_First = hintsRecieved[0]

                        position = hintsRecieved_First.split(" ")[0]
                        value = hintsRecieved_First.split(" ")[1]
                        print("el primer esta a la pos " + position + " i es " + value)
                        cardOrder = int(position)

                        s.send(GameData.ClientPlayerPlayCardRequest(playerName, cardOrder).serialize())
                        hintsRecieved.pop(0)
                except:
                    print("Ups problemita, hem fallat en algo OwO")
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
            print("Current player: " + data.currentPlayer)
            print("Player hands: ")
            players= data.players
            for p in data.players:
                print(p.toString())
            print("Table cards: ")
            for pos in data.tableCards:
                print(pos + ": [ ")
                for c in data.tableCards[pos]:
                    print(c.toString() + " ")
                print("]")
            print("Discard pile: ")
            for c in data.discardPile:
                print("\t" + c.toString())            
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
                hintsRecieved.append(str(i) + " " + str(data.value))
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