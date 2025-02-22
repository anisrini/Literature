class Card:
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        
    def __str__(self) -> str:
        return f"{self.rank} of {self.suit}"
    
    def get_symbol(self) -> str:
        """Returns the symbol for the card's suit"""
        symbols = {'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠'}
        return symbols[self.suit]
    
    def get_short_rank(self) -> str:
        """Returns shortened version of rank"""
        short_ranks = {'10': '10', 'Jack': 'J', 'Queen': 'Q', 'King': 'K', 'Ace': 'A'}
        return short_ranks.get(self.rank, self.rank) 