import os
import GameData
from game import Game
from game import Player
from game import Card
from constants import *
import sys

#!/usr/bin/env python3

from sys import argv, stdout
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
class Jugador(Player):
    def __init__(self, player) -> None:
        super().__init__(player.name)
        self.semisolution = "11 play 0"
        self.ma = []
        for c in player.hand:
            s = Carta(c, "Res")
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

class Carta(Card):
    def __init__(self, card, tag) -> None:
        super().__init__(card.id,card.value,card.color)
        self.tag = tag
        self.hintColor = ""
        self.hintValue = 0

class Joc(object):
    #I refer as card of the same those cards that share value and color
    def __init__(self) -> None:
        super().__init__()
        self.DiscardPile = []
        self.PlayedCards = []
        self.UsedTokens = 0
        self.Players = []
        self.Hints = []

    """returns the agent position in Players"""
    def agentPosition(self):
        return self.Players.index(playerName)
            
    
    """adds a card to the PlayedPile"""
    def addPlayedCard(self, carta):
        self.PlayedCards.append(carta)

    """Returns if a card of the same type has been played"""
    def estaJugada(self, carta):
        for i in self.PlayedCards:
            if i.value == carta.value and i.color == carta.color:
                return True
        return False

    """adds a card to the DiscardPile"""
    def addDiscardedCard(self, carta):
        self.DiscardPile.append(carta)

    """Counts how many cards of the same type had been discarted"""
    def countDiscarted(self, carta):
        res = 0
        for i in self.DiscardPile:
            if i.value == carta.value and i.color==carta.color:
                res += 1
        return res

    """Returns if the inferior cards with the same color have been discarted"""
    def inferiorsDiscarted(self, carta):
        for c in self.DiscardPile:
            if c.color == carta.color:
                i=self.countDiscarted(c)
                if c.value == "1" and i==3: return True
                elif int(i.value) < int(carta.value) and i == 2: return True
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

    ########################################################
    def addHint(self, playerName, type, value, positions):
        p = self.FindPlayer(playerName)
        for i in positions:
            if type == "color":
                p.hand[i].hintColor = value
            else:
                p.hand[i].hintValue = value
    

    """returns if a card is played"""
    def IsPlayed(self, carta):
        return (carta in self.PlayedCards)

    """returns if a card is discarted"""
    def IsDiscarted(self, carta):
        return (carta in self.DiscardPile)

    """returns if a card is in the hand of any player"""
    def InHand(self, carta):
        estaMA = False
        for i in self.Players:
            estaMA = (carta in i.hand)
        return estaMA

    """returns if a card is dangerous (discarting the card implies losing points)"""
    def isDangerous(self, carta):
        #it's a 5 and could be played in the future
        if carta.value == "5":
            return True
        #it's a between 1 and 4 and the other cards with same value & color had been discarted
        else:
            count = self.countDiscarted(carta)
            if carta.value == "1" and count > 1:
                return True
            else:
                if count == 1: return True
                return False

    """This function returns if playing the card is save"""
    def isJugable(self, carta):
        #a card with same attributes has been played
        if self.estaJugada(carta):
            return False
        #it's a 1 and there are no cards in table
        elif carta.value == "1" and not self.PlayedCards:
            return True
        #the card below has been played
        else:
            for c in self.PlayedCards:
                Cvalue = int(c.value) + 1
                if carta.value == str(Cvalue) and carta.color == c.color:
                    return True
            return False
    
    """This function returns True if discarting the card is dangerous but playing is save"""
    def isJugaPerill(self, carta):
        return self.isJugable(carta) and self.isDangerous(carta)


    """This function returns if discarting the card is save"""
    def isDescartable(self, carta):
        #a card with same value&color has been played
        if self.estaJugada(carta): return True
        #inferior card had been discarted
        return self.inferiorsDiscarted(carta)

    """Changes the tag of a card"""
    def evaluaCarta(self, carta):
        if self.isJugaPerill(carta):
            tag = "perillosajugable"
        elif self.isDescartable(carta):
            tag = "descartable"
        elif self.isJugable(carta):
            tag = "jugable"
        elif self.isDangerous(carta):
            tag = "perillosa"
        else:
            tag = "Res"
        carta.tag = tag

    def Value_Color(self, player, card):
        pista = []
        valueCounter = player.countValue(card.value)
        colorCounter = player.countColor(card.color)
        if colorCounter >= valueCounter:
            pista.append("value")
            pista.append(card.value)
        else:
            pista.append("color")
            pista.append(card.color)
        return pista

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
        agent = self.agentPosition()
        #we still can give hints
        if self.UsedTokens != 8:
            for player in self.Players:
                for card in player.hand:
                    q1 = player.getSemiID()
                    pista = self.Value_Color(player, card)
                    if "perillosa" == card.tag and player != self.Player[agent]:
                        if q1 > 0:
                            player.semisolution = "0 " + "hint " + pista[0] + " " + player + " " + pista[1]
                    elif "perillosajugable" == card.tag and player != self.Player[agent]:
                        if q1 > 1:
                            player.semisolution = "1 "+"hint " + pista[0] + " " + player + " " + pista[1]
                    elif self.teJugables(self.Player[agent]):
                        if q1 > 2:
                            pos = self.retornaJugable(self.Player[agent])
                            player.semisolution = "2 "+"play " + pos
                    elif "jugable" == card.tag and player != self.Player[agent]:
                        if q1 > 3:
                            player.semisolution = "3 "+"hint " + pista[0] + " " + player + " " + pista[1]
                    if self.UsedTokens != 0 and self.teDescartables(self.Player[agent]):
                        if q1 > 4:
                            pos = self.retornaDescartable(self.Players[agent])
                            player.semisolution = "4 "+"discard " + pos
                    elif "descartables" == card.tag and player != self.Player[agent]:
                        if q1 > 5:
                            player.semisolution = "5 "+"hint " + pista[0] + " " + player + " " + pista[1]
                    elif self.UsedTokens != 0 and self.teRes(self.Players[agent]):
                        if q1 > 6:
                            pos = self.retornaRes(self.Players[agent])
                            player.semisolution = "6 "+"discard " + pos
                    else:
                        if q1 > 7 and player != self.Player[agent]:
                            player.semisolution = "7 "+"hint " + pista[0] + " " + player + " " + pista[1]
                    
        else:
            player=self.Player[agent]
            tenimTokens=self.UsedTokens != 0
            for card in player.hand:
                q1 = player.getSemiID()
                cardIndex = player.hand.index(card)
                if "descartable" == card.tag and tenimTokens:
                    if q1 > 0:
                        player.semisolution = "0 "+"discard " + cardIndex
                elif "jugable" == card.tag:
                    if q1 > 1:
                        player.semisolution = "1 "+ "play " + cardIndex
                elif "Res" == card.tag and tenimTokens:
                    if q1 > 2:
                        player.semisolution = "2 "+"discard " + cardIndex
                elif tenimTokens:
                    if q1 > 3:
                        player.semisolution = "3 "+"discard " + cardIndex
                else:
                    if q1 > 4:
                        player.semisolution = "4 "+"play " + cardIndex
            

        for player in self.Players:
            q1 = solution.split(" ")[0]
            q2 = player.getSemiID()
            if int(q1) > int(q2):
                solution = player.semisolution

        solution = solution[2:]
        return solution 


joc = Joc()

game = Game()



game.addPlayer("Uri")
game.addPlayer("Papa")
game.addPlayer("Uri2")
game.addPlayer("Papa2")


game.setPlayerReady("Uri")
game.setPlayerReady("Papa")
game.setPlayerReady("Uri2")
game.setPlayerReady("Papa2")


game.start()

players = game.getPlayers()
jugadors = []
for p in players:
    j = Jugador(p)
    jugadors.append(j)

p = players[2]


print(p.name)
o = players.index(p)
print(players.index(p))
print(jugadors[players.index(p)].name)


c = [5,6,3,4,1,2]

print (c)
print(c.index(2))
i = c.index(2)
c.pop(i)
print(c)
c.insert(i,9)
print(c)

playedCards = {
            "red": [],
            "yellow": [],
            "green": [],
            "blue": [],
            "white": []
        }

rojos = [1,2,3]
print("Cartas rojas" + str(rojos))
c =  2
esta = c in rojos 
print (esta)

ply = playedCards["red"]

playedCards["red"].append(4)
playedCards["red"].append(5)
playedCards["red"].append(2)
playedCards["blue"].append(1)
print(ply)
aa = c in ply
print(aa)