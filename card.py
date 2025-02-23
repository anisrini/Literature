class Card:
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        
    def __str__(self) -> str:
        return f"{self.rank} of {self.suit}"
    
    def get_set(self) -> str:
        """Returns the set name this card belongs to"""
        # Minor sets are 2-7
        minor_ranks = ['2', '3', '4', '5', '6', '7']
        # Major sets are 9, 10, Jack, Queen, King, Ace
        major_ranks = ['9', '10', 'Jack', 'Queen', 'King', 'Ace']
        
        if self.rank in minor_ranks:
            return f"Minor {self.rank}"
        elif self.rank in major_ranks:
            return f"Major {self.get_short_rank()}"  # Use short rank for consistency
        else:
            raise ValueError(f"Card {self.rank} of {self.suit} doesn't belong to any set")

    def get_set_cards(self) -> list:
        """Returns all possible cards in this card's set"""
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        return [Card(suit, self.rank) for suit in suits]
    
    def get_symbol(self) -> str:
        """Returns the symbol for the card's suit"""
        symbols = {'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠'}
        return symbols[self.suit]
    
    def get_short_rank(self) -> str:
        """Returns shortened version of rank"""
        short_ranks = {'10': '10', 'Jack': 'J', 'Queen': 'Q', 'King': 'K', 'Ace': 'A'}
        return short_ranks.get(self.rank, self.rank) 

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank 