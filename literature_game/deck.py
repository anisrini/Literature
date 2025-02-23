import random
from typing import List, TYPE_CHECKING
from literature_game.card import Card
import logging

if TYPE_CHECKING:
    from literature_game.player import Player  # Only used for type hints

logger = logging.getLogger(__name__)

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
        logger.info(f"Starting to deal {cards_per_player} cards to {len(players)} players")
        
        if not (4 <= len(players) <= 8):
            logger.error(f"Invalid number of players: {len(players)}")
            raise ValueError("Number of players must be between 4 and 8")
        
        if len(players) * cards_per_player > len(self.cards):
            logger.error(f"Not enough cards: need {len(players) * cards_per_player}, have {len(self.cards)}")
            raise ValueError("Not enough cards to deal")
            
        for i in range(cards_per_player):
            for player in players:
                if self.cards:
                    card = self.cards.pop()
                    player.add_card(card)
                    logger.debug(f"Dealt {card} to {player.name}")
        
        logger.info("Finished dealing cards")
    
    def restack(self):
        """Restacks the deck with all 48 cards"""
        self.build() 