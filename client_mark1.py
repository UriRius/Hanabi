#!/usr/bin/env python3

from sys import argv, stdout
from threading import Thread
import GameData
import game
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

#class extensions
#names are in Catalan to avoid confussions
class Jugador(game.Player):
    def __init__(self, player) -> None:
        super().__init__(player.name)
        self.semisolution = "11 play 0"
        self.ma = []
        if self.name != playerName:
            for c in player.hand:
                s = Carta(c.id, c.value, c.color, "Res")
                self.ma.append(s)
        else: 
            for i in range(5):
                s = Carta(i,0,"","Res")
                self.ma.append(s)

    def tagHand(self):
        for c in self.hand:
            c.evaluaCarta()

    def SemiSolution(self, move):
        self.semisolution=move

    def cleanSemiSolution(self):
        self.semisolution = "11 play 0"

    def getSemiID(self):
        return int(self.semisolution.split(" ")[0])

    def countValue(self, value):
        counter = 0
        for c in self.hand:
            if c.value == value:
                counter+=1
        return counter

    def countColor(self, color):
        counter = 0
        for c in self.hand:
            if c.color == color:
                counter+=1
        return counter

    def ActualizaHand(self, hand):
        for c in hand:
            m = self.ma[hand.index(c)]
            if m.id != c.id:
                self.ma.pop(hand.index(c))
                k = Carta(c.id, c.value, c.color, "Res")
                self.ma.insert(hand.index(c),k)

    def BestMoveIA(self):
        ## IA player is preasumed 
        self.cleanSemiSolution()
        for card in self.ma:
            q1 = self.getSemiID()
            cardIndex = self.ma.index(card)
            if "jugable" == card.tag or "perillosajugable"== card.tag:
                if q1 > 1:
                    self.semisolution = "1 "+ "play " + cardIndex
            elif "descartable" == card.tag:
                if q1 > 0:
                    self.semisolution = "0 "+"discard " + cardIndex
            elif "Res" == card.tag:
                if q1 > 2:
                    self.semisolution = "2 "+"discard " + cardIndex
            else:
                if q1 > 3:
                    self.semisolution = "3 discard 4"
            
    def Value_Color(self, card):
        pista = []
        if card.hintColor != "" or card.hintValue != 0:
            if card.hintColor != "":
                pista.append("value")
                pista.append(card.value)
            else:
                pista.append("color")
                pista.append(card.color)
        else:
            valueCounter = self.countValue(card.value)
            colorCounter = self.countColor(card.color)
            if colorCounter <= valueCounter:
                pista.append("value")
                pista.append(str(card.value))
            else:
                pista.append("color")
                pista.append(card.color)
        return pista
    
    #calcular el millor move per cada jugador
    def BestMove(self):
        self.cleanSemiSolution()
        for card in self.ma:
            q1 = self.getSemiID()
            pista = self.Value_Color(card)
            if card.tag == "jugable":
                if q1 > 0:
                    self.semisolution = "0 "+"hint " + pista[0] + " " + self.name + " " + pista[1]
            elif "perillosa" == card.tag:
                if q1 > 1:
                    self.semisolution = "1 " + "hint " + pista[0] + " " + self.name + " " + pista[1]

class Carta(game.Card):
    def __init__(self, id,value,color, tag) -> None:
        super().__init__(id,value,color)
        self.tag = tag
        self.hintColor = ""
        self.hintValue = 0

class Joc(object):
    #I refer as card of the same those cards that share value and color
    def __init__(self) -> None:
        super().__init__()
        self.DiscardPile = []
        self.PlayedCards = {}
        self.UsedTokens = 0
        self.Players = []
        self.Hints = []
        self.currentPlayer = ""

    """returns the agent position in Players"""
    def agentPosition(self):
        return self.Players.index(playerName)
            
    def creaJugador(self, players):
        for p in players:
            j = Jugador(p)
            self.Players.append(j)

    def actualitzaJugador(self, players):
        for p in players:
            self.Players[players.index(p)].ActualizaHand(p.hand)

    def LoadDiscardPile(self,DiscardPile):
        self.DiscardPile = []
        for c in DiscardPile:
            carta = Carta(c.id,c.value,c.color,"")
            self.DiscardPile.append(carta)

    def updateJugador(self, players):
        if not self.Players:
            self.creaJugador(players)
        else:
            self.actualitzaJugador(players)

    """Returns if a card of the same type has been played"""
    def estaJugada(self, carta):
        if carta.color != "":
            return carta.value in self.PlayedCards[carta.color]
        else: return False
       

    """Counts how many cards of the same type had been discarted"""
    def countDiscarted(self, carta):
        res = 0
        for i in self.DiscardPile:
            if i.value == carta.value and i.color==carta.color:
                res += 1
        return res

    def countDiscartedVal(self, carta):
        res = 0
        for i in self.DiscardPile:
            if i.value == carta.value:
                res += 1
        return res

    """Returns if the inferior cards with the same color have been discarted"""
    def inferiorsDiscarted(self, carta):
        for c in self.DiscardPile:
            if c.color == carta.color:
                i=self.countDiscarted(c)
                if c.value == 1 and i==3: return True
                elif int(i.value) < carta.value and i == 2: return True
            else:
                i=self.countDiscartedVal(c)
                if c.value == 1 and i==15: return True
                elif int(i.value) < carta.value and i == 10: return True
        return False

    """Increases the used tokens"""
    def incUsedTokens(self):
        self.UsedTokens+=1

    """Decreases the used tokens"""
    def decUsedTokens(self):
        self.UsedTokens-=1

    def FindPlayer(self, name):
        for p in self.Players:
            if p.name == name: 
                return p
        p=game.Player(name)
        return Jugador(p)

    def addHint(self, playerName, type, value, positions):
        p = self.FindPlayer(playerName)
        for i in positions:
            if type == "color":
                p.ma[i].hintColor = value
                p.ma[i].color = value
            else:
                p.ma[i].hintValue = value
                p.ma[i].value = value

    """returns if a card is in the hand of any player"""
    def InHand(self, carta):
        estaMA = False
        for i in self.Players:
            estaMA = (carta in i.hand)
        return estaMA

    def colorComplet(self, carta):
        if carta.color != "":
            return 5 in self.PlayedCards[carta.color]
        else: return False       

    def colorNoJugat(self, carta):
        return not self.PlayedCards[carta.color]

    def cartaMenorJugada(self, carta):
        if self.colorNoJugat(carta) and carta.value == 1: return True
        return (carta.value-1) in self.PlayedCards[carta.color]

    """returns if a card is dangerous (discarting the card implies losing points)"""
    def isDangerous(self, carta, player):
        #it's a 5 and could be played in the future
        if carta.value == 5:
            return True
        #si em donen el valor duna carta i no es jugable ni descartable es perillos
        elif not(self.isJugable(carta, player)) and not(self.isDescartable(carta)):
            return True
        return False

    """This function returns if playing the card is save"""
    def isJugable(self, carta, player):
        if player.name == playerName:
            if carta.hintColor != "" and carta.hintValue != 0:
                return self.cartaMenorJugada(carta)
            else:
                return False
        else:            
            return self.cartaMenorJugada(carta)

    """This function returns True if discarting the card is dangerous but playing is save"""
    def isJugaPerill(self, carta, player):
        return self.isJugable(carta, player) and self.isDangerous(carta, player)


    """This function returns if discarting the card is save"""
    def isDescartable(self, carta):
        #a card with same value&color has been played
        if self.estaJugada(carta): return True
        #color complet
        elif self.colorComplet(carta): return True
        #inferior card had been discarted
        return self.inferiorsDiscarted(carta)


    def evaluarTotesLesCartes(self): 
        for p in self.Players:
            for c in p.ma:
                self.evaluaCarta(c, p)

    """Changes the tag of a card"""
    def evaluaCarta(self, carta, player):
        if self.isJugaPerill(carta, player):
            tag = "perillosajugable"
        elif self.isDescartable(carta):
            tag = "descartable"
        elif self.isJugable(carta, player):
            tag = "jugable"
        elif self.isDangerous(carta, player):
            tag = "perillosa"
        else:
            tag = "Res"
        carta.tag = tag

    def teJugables(self, player):
        for c in player.hand:
            if c.tag == "jugable": return True
        return False

    def retornaJugable(self, player):
        for c in player.hand:
            if c.tag == "jugable":
                return str(player.hand.index(c))
        return "0"
        
    def teDescatables(self, player):
        for c in player.hand:
            if c.tag == "descartable": return True
        return False

    def retornaDescartable(self, player):
        for c in player.hand:
            if c.tag == "descartable":
                return str(player.hand.index(c))
        return "0"

    def teRes(self, player):
        for c in player.hand:
            if c.tag == "Res": return True
        return False

    def retornaRes(self, player):
        for c in player.hand:
            if c.tag == "Res":
                return str(player.hand.index(c))
        return "0"

    def BestMove(self):
        #final solution
        solution = "10 play 0"

        #semisolution for every player that will be evaluated later
        self.evaluarTotesLesCartes()
        #we still can give hints
        for player in self.Players:
            if player.name != playerName and self.UsedTokens != 8:
                player.BestMove()
            else:
                player.BestMoveIA()

        for player in self.Players:
            q1 = solution.split(" ")[0]
            q2 = player.getSemiID()
            if int(q1) > int(q2):
                solution = player.semisolution

        solution = solution[2:]
        return solution 


joc = Joc()

def manageInput():
    global run
    global status
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
                #We request the show action everytime we play
                s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
                #we have to sleep to get the show response before doing anything
                time.sleep(2)
                #try:

                #BstMv options are (play <num>), (discard <num>), (hint <type> <player> <value>)
                BstMv=joc.BestMove()

                print(BstMv)

                move = BstMv.split(" ")[0]
                num = BstMv.split(" ")[1]
                
                if move == "play":
                    s.send(GameData.ClientPlayerPlayCardRequest(playerName, num).serialize())
                elif move == "discard":
                    s.send(GameData.ClientPlayerDiscardCardRequest(playerName, num).serialize())
                else:
                    player = BstMv.split(" ")[2]
                    value = BstMv.split(" ")[3]
                    if num == "value":
                        value = int(value)
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
            print("Current player: " + data.currentPlayer)
            joc.currentPlayer = data.currentPlayer
            print("Player hands: ")
            #Aqui actualitzem la nostra variable de players per tenir la seva ma en tot moment
            joc.updateJugador(data.players)
            for p in data.players:
                print(p.toClientString())
                for card in p.hand:
                    print("Carta: "+ str(card.value) + " - " + str(card.color))
            print("Table cards: ")
            joc.PlayedCards = data.tableCards
            for pos in data.tableCards:
                print(pos + ": [ ")
                for c in data.tableCards[pos]:
                    print(c.toClientString() + " ")
                print("]")
            print("Discard pile: ")
            joc.LoadDiscardPile(data.discardPile)
            for c in data.discardPile:
                print("\t" + c.toClientString())           
            joc.UsedTokens=int(data.usedNoteTokens)
            print("Note tokens used: " + str(data.usedNoteTokens) + "/8")
            print("Storm tokens used: " + str(data.usedStormTokens) + "/3")
        if type(data) is GameData.ServerActionInvalid:
            dataOk = True
            print("Invalid action performed. Reason:")
            print(data.message)
        if type(data) is GameData.ServerActionValid:
            #Hem descartat
            dataOk = True
            print("Action valid!")
            print("Current player: " + data.player)
        if type(data) is GameData.ServerPlayerMoveOk:
            #Hem jugat bé una carta
            dataOk = True
            print("Action valid!")
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
                print("\t" + str(i))
            joc.addHint(data.destination, data.type, data.value, data.positions)
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