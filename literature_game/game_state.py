from typing import List, Optional, Tuple
from literature_game.player import Player
from literature_game.card import Card
import logging

logger = logging.getLogger(__name__)

class GameState:
    def __init__(self, players: List[Player]):
        self.players = players
        self.current_turn = 0
        self.team1_sets = 0
        self.team2_sets = 0
        self.last_request = None  # (requester_idx, requested_idx, card)
        self.last_transfer = None  # (from_idx, to_idx, card)
        self.last_set_winner = None  # "Team 1", "Team 2", or "No Winner"
        self.game_phase = "TURN_START"  # TURN_START, REQUESTING, DECLARING
        self.declaring_set = None  # Set being declared
        self.game_over = False

    def is_team1(self, player_idx: int) -> bool:
        """Returns True if player is on team 1 (odd numbers)"""
        return player_idx % 2 == 1

    def get_teammate_indices(self, player_idx: int) -> List[int]:
        """Returns indices of player's teammates"""
        return [i for i in range(len(self.players)) if i % 2 == player_idx % 2]

    def can_request_card(self, player_idx: int, card: Card) -> bool:
        """Check if player can request the specified card"""
        player = self.players[player_idx]
        return player.has_root_card(card.get_set())

    def handle_card_request(self, requester_idx: int, target_idx: int, card: Card) -> bool:
        """Process a card request. Returns True if card was transferred."""
        target = self.players[target_idx]
        if card in target.hand:
            # Transfer card
            target.hand.remove(card)
            self.players[requester_idx].hand.append(card)
            self.last_transfer = (target_idx, requester_idx, card)
            return True
        return False

    def validate_declaration(self, player_idx: int, set_name: str, 
                           card_assignments: List[Tuple[int, Card]]) -> Tuple[bool, str]:
        """Validates a set declaration. Returns (success, winner)"""
        # Verify all cards are accounted for
        # Check if cards are actually with assigned players
        # Determine if declaration was correct
        # Return appropriate result
        pass 

    def __eq__(self, other):
        """Compare game states"""
        if not isinstance(other, GameState):
            return False
        
        # Compare basic attributes
        basic_equal = (self.current_turn == other.current_turn and
                      self.team1_sets == other.team1_sets and
                      self.team2_sets == other.team2_sets and
                      self.game_phase == other.game_phase)
        
        # Compare player hands
        hands_equal = all(
            len(p1.hand) == len(p2.hand) and all(c1 == c2 for c1, c2 in zip(p1.hand, p2.hand))
            for p1, p2 in zip(self.players, other.players)
        )
        
        return basic_equal and hands_equal 