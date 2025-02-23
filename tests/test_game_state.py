import unittest
from literature_game.game_state import GameState
from literature_game.player import Player
from literature_game.card import Card

class TestGameState(unittest.TestCase):
    def setUp(self):
        self.players = [Player(f"Player {i}", i) for i in range(6)]
        self.game_state = GameState(self.players)
        self.test_card = Card('Hearts', 'Ace')
    
    def test_init(self):
        """Test game state initialization"""
        self.assertEqual(len(self.game_state.players), 6)
        self.assertEqual(self.game_state.current_turn, 0)
        self.assertEqual(self.game_state.team1_sets, 0)
        self.assertEqual(self.game_state.team2_sets, 0)
    
    def test_is_team1(self):
        """Test team assignment"""
        self.assertFalse(self.game_state.is_team1(0))  # Player 0 is team 2
        self.assertTrue(self.game_state.is_team1(1))   # Player 1 is team 1
    
    def test_get_teammate_indices(self):
        """Test teammate identification"""
        teammates = self.game_state.get_teammate_indices(0)
        self.assertEqual(set(teammates), {0, 2, 4})  # Team 2 players
    
    def test_handle_card_request(self):
        """Test card request handling"""
        # Give card to player 1
        self.players[1].add_card(self.test_card)
        
        # Player 0 requests card from player 1
        success = self.game_state.handle_card_request(0, 1, self.test_card)
        self.assertTrue(success)
        self.assertIn(self.test_card, self.players[0].hand)
        self.assertNotIn(self.test_card, self.players[1].hand) 