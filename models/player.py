class Player:
    """Player model for the Literature game"""
    
    def __init__(self, name, player_id):
        self.name = name
        self.id = player_id
        self.hand = []  # List of cards in player's hand
        self.team = self.id % 2  # Team 0 or 1 (even/odd)
    
    def add_card(self, card):
        """Add a card to the player's hand"""
        self.hand.append(card)
    
    def remove_card(self, card):
        """Remove a card from the player's hand"""
        if card in self.hand:
            self.hand.remove(card)
            return True
        return False
    
    def has_card(self, rank, suit):
        """Check if the player has a specific card"""
        return any(c.rank == rank and c.suit == suit for c in self.hand)
    
    def has_root_card(self, set_name):
        """Check if player has a card from the specified set"""
        for card in self.hand:
            if card.get_set() == set_name:
                return True
        return False 