class Card:
    """Represents a playing card"""
    
    VALID_RANKS = ['2', '3', '4', '5', '6', '7', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
    VALID_SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    
    def __init__(self, rank, suit):
        """Initialize a card with rank and suit"""
        if rank not in self.VALID_RANKS:
            raise ValueError(f"Invalid rank: {rank}")
        if suit not in self.VALID_SUITS:
            raise ValueError(f"Invalid suit: {suit}")
            
        self.rank = rank
        self.suit = suit
    
    def __str__(self):
        """String representation of card"""
        return f"{self.rank} of {self.suit}"
    
    def __eq__(self, other):
        """Check if two cards are equal"""
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit
    
    def get_image_path(self):
        """Return the path to the card image"""
        # Convert face cards to abbreviations
        rank_abbr = self.rank
        if self.rank == 'Jack': rank_abbr = 'J'
        elif self.rank == 'Queen': rank_abbr = 'Q'
        elif self.rank == 'King': rank_abbr = 'K'
        elif self.rank == 'Ace': rank_abbr = 'A'
        
        # First letter of suit
        suit_abbr = self.suit[0].lower()
        
        return f"static/images/cards/{rank_abbr}_{suit_abbr}.png"
    
    def as_dict(self):
        """Return a dictionary representation of the card"""
        return {
            'rank': self.rank,
            'suit': self.suit,
            'image': self.get_image_path()
        }
    
    def get_set(self):
        """Determine which set this card belongs to"""
        low_ranks = ['2', '3', '4', '5', '6', '7']
        high_ranks = ['9', '10', 'Jack', 'Queen', 'King', 'Ace']
        
        if self.rank in low_ranks:
            return f"Low {self.suit}"
        elif self.rank in high_ranks:
            return f"High {self.suit}"
        return None  # For 8s, which are not in the game 