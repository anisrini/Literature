import random
from models.card import Card

class GameState:
    """Represents the state of a Literature game"""
    
    def __init__(self, players):
        self.players = players
        self.current_turn = 0
        self.team1_sets = 0
        self.team2_sets = 0
        self.game_log = []
        self.game_over = False
    
    def create_deck(self):
        """Create a standard deck of cards (minus 8s)"""
        deck = []
        for suit in ['Hearts', 'Diamonds', 'Clubs', 'Spades']:
            for rank in ['2', '3', '4', '5', '6', '7', '9', '10', 'Jack', 'Queen', 'King', 'Ace']:
                deck.append(Card(rank, suit))
        return deck

    def deal_cards(self):
        """Shuffle and deal cards to players"""
        # Create the deck
        deck = self.create_deck()
        
        # Shuffle
        random.shuffle(deck)
        
        # Deal cards evenly to players
        num_players = len(self.players)
        cards_per_player = len(deck) // num_players
        
        for i, player in enumerate(self.players):
            start = i * cards_per_player
            end = start + cards_per_player
            player.hand = deck[start:end]
        
        # Log the deal
        self.add_to_log("GAME_START", {
            "player_count": num_players,
            "first_player": self.current_turn
        })
    
    def request_card(self, requesting_player, target_player, rank, suit):
        """Process a request for a card from another player"""
        # Validate that it's the requesting player's turn
        if requesting_player != self.current_turn:
            return False
        
        # Validate that target is not on the same team
        if requesting_player % 2 == target_player % 2:
            return False
        
        # Look for the card in target's hand
        target = self.players[target_player]
        requester = self.players[requesting_player]
        
        # Check if target has the card
        target_has_card = target.has_card(rank, suit)
        
        # Log the request
        self.add_to_log("CARD_REQUEST", {
            "requester": requesting_player,
            "target": target_player,
            "card": {"rank": rank, "suit": suit},
            "success": target_has_card
        })
        
        if target_has_card:
            # Find the card object
            for card in target.hand:
                if card.rank == rank and card.suit == suit:
                    # Transfer card
                    target.hand.remove(card)
                    requester.hand.append(card)
                    break
            
            # Player keeps their turn after successful request
            return True
        else:
            # Transfer turn to target
            self.current_turn = target_player
            return False
    
    def declare_set(self, declaring_player, set_name, card_assignments):
        """Process a declaration of a complete set
        
        Args:
            declaring_player: ID of the player making the declaration
            set_name: Name of the set being declared (e.g. "Low Hearts")
            card_assignments: Dict mapping card IDs to player IDs
            
        Returns:
            Tuple of (success, team_that_won_set)
        """
        # Validate it's the player's turn
        if declaring_player != self.current_turn:
            return False, None
        
        declaring_player_obj = self.players[declaring_player]
        declaring_team = declaring_player % 2  # 0 or 1
        
        # Determine which ranks are in this set
        set_type, set_suit = set_name.split(' ', 1)
        if set_type == "Low":
            expected_ranks = ['2', '3', '4', '5', '6', '7']
        elif set_type == "High":
            expected_ranks = ['9', '10', 'Jack', 'Queen', 'King', 'Ace']
        else:
            return False, None  # Invalid set name
        
        # Build the list of expected cards in this set
        expected_cards = []
        for rank in expected_ranks:
            expected_cards.append((rank, set_suit))
        
        # Check if all cards are accounted for
        all_correct = True
        
        for (rank, suit) in expected_cards:
            player_id = card_assignments.get(f"{rank}_{suit}")
            if player_id is None:
                # Missing card assignment
                all_correct = False
                break
            
            # Check if the assigned player has this card
            player = self.players[player_id]
            has_card = player.has_card(rank, suit)
            
            if not has_card:
                all_correct = False
                break
        
        # Log the declaration
        self.add_to_log("SET_DECLARATION", {
            "player": declaring_player,
            "set": set_name,
            "success": all_correct
        })
        
        # Update game state based on result
        if all_correct:
            # Award point to the declaring team
            if declaring_team == 0:
                self.team1_sets += 1
            else:
                self.team2_sets += 1
            
            # Remove cards from players' hands
            for (rank, suit) in expected_cards:
                player_id = card_assignments[f"{rank}_{suit}"]
                player = self.players[player_id]
                
                # Find and remove the card
                for card in player.hand[:]:  # Copy to avoid modification issues
                    if card.rank == rank and card.suit == suit:
                        player.hand.remove(card)
                        break
            
            # Check for game end
            if self.team1_sets + self.team2_sets == 8:  # All 8 sets collected
                self.game_over = True
                self.add_to_log("GAME_OVER", {
                    "team1_sets": self.team1_sets,
                    "team2_sets": self.team2_sets,
                    "winning_team": 1 if self.team1_sets > self.team2_sets else 2
                })
            
            return True, declaring_team
        else:
            # Award point to the opposing team
            opposing_team = 1 - declaring_team
            if opposing_team == 0:
                self.team1_sets += 1
            else:
                self.team2_sets += 1
            
            # Check for game end
            if self.team1_sets + self.team2_sets == 8:  # All 8 sets collected
                self.game_over = True
                self.add_to_log("GAME_OVER", {
                    "team1_sets": self.team1_sets,
                    "team2_sets": self.team2_sets,
                    "winning_team": 1 if self.team1_sets > self.team2_sets else 2
                })
            
            # Transfer turn to a player on the opposite team
            opposite_team_players = [p for p in range(len(self.players)) if p % 2 == opposing_team]
            if opposite_team_players:
                self.current_turn = opposite_team_players[0]
            
            return False, opposing_team
    
    def add_to_log(self, action_type, details):
        """Add an entry to the game log"""
        self.game_log.append({
            "action": action_type,
            "details": details,
            "turn": self.current_turn
        }) 