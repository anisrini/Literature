import random
from typing import List
from card import Card
from player import Player

class Deck:
    SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    RANKS = ['Ace', '2', '3', '4', '5', '6', '7', '9', '10', 'Jack', 'Queen', 'King']  # Removed '8'
    
    def __init__(self):
        self.cards = []
        self.build()
    
    def build(self):
        """Creates a new deck of 48 cards (excluding 8s)"""
        self.cards = [Card(suit, rank) for suit in self.SUITS for rank in self.RANKS]
    
    def shuffle(self):
        """Shuffles the deck"""
        random.shuffle(self.cards)
    
    def deal(self, players: List['Player'], cards_per_player: int):
        """Deals cards to players"""
        if not (4 <= len(players) <= 8):
            raise ValueError("Number of players must be between 4 and 8")
        
        if len(players) * cards_per_player > len(self.cards):
            raise ValueError("Not enough cards to deal")
            
        for _ in range(cards_per_player):
            for player in players:
                if self.cards:
                    player.add_card(self.cards.pop())
    
    def restack(self):
        """Restacks the deck with all 48 cards"""
        self.build() 