from typing import List
from card import Card

class Player:
    def __init__(self, name: str):
        self.name = name
        self.hand = []
    
    def add_card(self, card: Card):
        """Adds a card to the player's hand"""
        self.hand.append(card)
    
    def show_hand(self) -> List[str]:
        """Returns a list of cards in the player's hand"""
        return [str(card) for card in self.hand]
    
    def visualize_hand(self) -> List[str]:
        """Creates a visual representation of the cards"""
        if not self.hand:
            return []
        
        # Sort cards by suit and rank for better visualization
        self.hand.sort(key=lambda card: (card.suit, card.rank))
        
        cards = []
        for card in self.hand:
            symbol = card.get_symbol()
            rank = card.get_short_rank()
            cards.append(f"┌─────┐")
            cards.append(f"│{rank:<2}   │")
            cards.append(f"│  {symbol}  │")
            cards.append(f"│   {rank:>2}│")
            cards.append(f"└─────┘")
        return cards 