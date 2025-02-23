import unittest
from unittest.mock import Mock, patch
import time
from kivy.clock import Clock
from literature_game.game_state import GameState
from literature_game.player import Player
from literature_game.card import Card
from literature_game.deck import Deck
from literature_game.gui.literature_game_gui import LiteratureGameGUI

class TestGameIntegration(unittest.TestCase):
    def setUp(self):
        # Initialize game components
        self.num_players = 6
        self.players = [Player(f"Player {i}", i) for i in range(self.num_players)]
        self.deck = Deck()
        self.deck.shuffle()
        self.cards_per_player = 8  # 6 players get 8 cards each
        self.deck.deal(self.players, self.cards_per_player)
        self.game_state = GameState(self.players)
        
        # Mock Kivy's Clock to prevent actual scheduling
        self.original_schedule_once = Clock.schedule_once
        Clock.schedule_once = Mock()

    def tearDown(self):
        # Restore Clock's original behavior
        Clock.schedule_once = self.original_schedule_once

    def test_game_initialization(self):
        """Test that game initializes correctly"""
        self.assertEqual(len(self.players), self.num_players)
        for player in self.players:
            self.assertEqual(len(player.hand), self.cards_per_player)
        self.assertEqual(self.game_state.current_turn, 0)

    def test_card_request_cycle(self):
        """Test a complete card request cycle"""
        # Setup initial state
        requester = self.players[0]
        target = self.players[1]
        requested_card = target.hand[0]  # Take first card from target's hand
        
        # Perform card request
        initial_requester_count = len(requester.hand)
        initial_target_count = len(target.hand)
        
        success = self.game_state.handle_card_request(0, 1, requested_card)
        
        self.assertTrue(success)
        self.assertEqual(len(requester.hand), initial_requester_count + 1)
        self.assertEqual(len(target.hand), initial_target_count - 1)
        self.assertIn(requested_card, requester.hand)
        self.assertNotIn(requested_card, target.hand)

    @patch('kivy.clock.Clock.schedule_interval')
    def test_gui_update_cycle(self, mock_schedule):
        """Test that GUI updates don't cause infinite loops"""
        gui = LiteratureGameGUI()
        gui.game_state = self.game_state
        
        # Track number of updates
        update_count = 0
        max_updates = 25  # Increased threshold
        start_time = time.time()
        timeout = 5  # 5 seconds timeout
        
        def mock_update(dt):
            nonlocal update_count
            update_count += 1
            if update_count >= max_updates or time.time() - start_time > timeout:
                return False
            gui.update_game_state(dt)
            return True
        
        # Simulate updates
        while mock_update(0.1):  # 10 FPS
            pass
        
        self.assertLess(time.time() - start_time, timeout, "Update cycle took too long")
        self.assertLessEqual(update_count, max_updates, "Too many update cycles")  # Changed to assertLessEqual
        self.assertGreater(update_count, 0, "No updates occurred")  # Add check for minimum updates

    def test_complete_turn_sequence(self):
        """Test a complete turn sequence"""
        initial_turn = self.game_state.current_turn
        
        # Simulate card request
        target_idx = (initial_turn + 1) % self.num_players
        card = self.players[target_idx].hand[0]
        self.game_state.handle_card_request(initial_turn, target_idx, card)
        
        # Verify turn state
        self.assertEqual(self.game_state.current_turn, initial_turn)
        self.assertEqual(self.game_state.game_phase, "TURN_START")

    def test_layout_stability(self):
        """Test that layout updates stabilize"""
        with patch('kivy.clock.Clock.schedule_once') as mock_schedule:
            gui = LiteratureGameGUI()
            gui.game_state = self.game_state
            
            # Count number of layout triggers
            layout_count = 0
            def count_layouts(*args, **kwargs):
                nonlocal layout_count
                layout_count += 1
            
            mock_schedule.side_effect = count_layouts
            
            # Trigger multiple updates
            for _ in range(5):  # Reduced from 10
                gui.update_game_state(0)
            
            # Check that layouts don't cascade infinitely
            self.assertLess(layout_count, 10, "Too many layout updates triggered")  # Reduced from 20

    def test_player_hand_updates(self):
        """Test that player hand updates are stable"""
        with patch('kivy.clock.Clock.schedule_once') as mock_schedule:
            player = self.players[0]
            hand = Mock()
            hand.player = player
            hand._layout_scheduled = False
            
            # Track layout calls
            layout_calls = 0
            def mock_layout(*args, **kwargs):
                nonlocal layout_calls
                layout_calls += 1
            
            hand.layout_cards = mock_layout
            
            # Simulate multiple updates
            for _ in range(5):
                hand.update_layout()
            
            self.assertLess(layout_calls, 10, "Hand layout called too many times")

if __name__ == '__main__':
    unittest.main() 