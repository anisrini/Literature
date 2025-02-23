from kivy.tests.common import GraphicUnitTest, UnitTestTouch
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from unittest.mock import Mock, patch
import time

from literature_game.gui.literature_game_gui import LiteratureGameGUI
from literature_game.gui.components.game_table import GameTable
from literature_game.gui.components.player_hand import PlayerHand
from literature_game.game_state import GameState
from literature_game.player import Player
from literature_game.deck import Deck
from literature_game.card import Card

class TestVisualizationIntegration(GraphicUnitTest):
    def setUp(self):
        super().setUp()
        # Initialize game components
        self.num_players = 6
        self.players = [Player(f"Player {i}", i) for i in range(self.num_players)]
        self.deck = Deck()
        self.deck.shuffle()
        self.cards_per_player = 8
        self.deck.deal(self.players, self.cards_per_player)
        self.game_state = GameState(self.players)
        
        # Create main GUI and wait for it to be ready
        self.gui = LiteratureGameGUI()
        self.render(self.gui)
        self.advance_frames(2)  # Wait for initial render
        
        # Set game state and wait for update
        self.gui.game_state = self.game_state
        self.advance_frames(10)  # Increased wait time for layout
        
        # Verify initial setup
        self.assertTrue(all(len(hand.cards) > 0 for hand in self.gui.ids.game_table.hands))
        
        # Store initial window size
        self.original_size = Window.size

    def tearDown(self):
        super().tearDown()
        # Restore window size
        Window.size = self.original_size

    def test_initial_layout(self):
        """Test that initial layout is correct"""
        game_table = self.gui.ids.game_table
        self.assertIsNotNone(game_table)
        self.assertEqual(len(game_table.hands), self.num_players)
        
        for i, hand in enumerate(game_table.hands):
            self.assertEqual(len(hand.cards), len(self.players[i].hand))
            
            # Check relative positioning
            for card in hand.cards:
                # Get relative position
                rel_x = card.x
                rel_y = card.y
                
                # Verify card is within hand bounds
                self.assertTrue(0 <= rel_x <= hand.width,
                    f"Card x position {rel_x} outside hand width {hand.width}")
                self.assertTrue(0 <= rel_y <= hand.height,
                    f"Card y position {rel_y} outside hand height {hand.height}")

    def test_window_resize(self):
        """Test that layout adapts to window resizing"""
        self.gui.game_state = self.game_state
        self.advance_frames(5)
        
        # Store initial relative positions
        initial_positions = {}
        for i, hand in enumerate(self.gui.ids.game_table.hands):
            initial_positions[i] = [(card.x, card.y) for card in hand.cards]
        
        # Resize window
        Window.size = (Window.width * 1.5, Window.height * 1.5)
        self.advance_frames(5)
        
        # Verify positions updated correctly
        for i, hand in enumerate(self.gui.ids.game_table.hands):
            for card in hand.cards:
                self.assertTrue(0 <= card.x <= hand.width,
                    f"Card x position {card.x} outside hand width {hand.width}")
                self.assertTrue(0 <= card.y <= hand.height,
                    f"Card y position {card.y} outside hand height {hand.height}")

    def test_card_visibility(self):
        """Test that cards remain visible during state changes"""
        self.gui.game_state = self.game_state
        self.advance_frames(5)
        
        # Count initial visible cards
        initial_card_count = sum(len(hand.cards) for hand in self.gui.ids.game_table.hands)
        
        # Simulate turn change
        self.game_state.current_turn = (self.game_state.current_turn + 1) % self.num_players
        self.advance_frames(5)
        
        # Verify card count hasn't changed
        final_card_count = sum(len(hand.cards) for hand in self.gui.ids.game_table.hands)
        self.assertEqual(initial_card_count, final_card_count)

    def test_card_transfer_animation(self):
        """Test that card transfers are properly visualized"""
        self.advance_frames(5)  # Wait for initial layout
        
        # Setup card transfer
        from_player = self.players[0]
        to_player = self.players[1]
        card_to_transfer = from_player.hand[0]
        
        # Store initial counts
        initial_from_count = len(from_player.hand)
        initial_to_count = len(to_player.hand)
        
        # Perform transfer
        self.game_state.handle_card_request(1, 0, card_to_transfer)
        self.gui.update_game_state(0)
        self.advance_frames(10)
        
        # Get hands after update
        from_hand = self.gui.ids.game_table.hands[0]
        to_hand = self.gui.ids.game_table.hands[1]
        
        # Verify counts
        self.assertEqual(len(from_player.hand), initial_from_count - 1)
        self.assertEqual(len(to_player.hand), initial_to_count + 1)
        self.assertEqual(len(from_hand.cards), len(from_player.hand))
        self.assertEqual(len(to_hand.cards), len(to_player.hand))

    def test_current_player_highlight(self):
        """Test that current player highlighting works"""
        self.advance_frames(5)
        
        for i in range(self.num_players):
            self.game_state.current_turn = i
            self.gui.update_game_state(0)
            self.advance_frames(5)
            
            for j, hand in enumerate(self.gui.ids.game_table.hands):
                self.assertEqual(hand.is_current, j == i)
                if j == i:
                    self.assertIsNotNone(hand.highlight)
                else:
                    self.assertIsNone(hand.highlight)

    def test_layout_stability(self):
        """Test that layouts remain stable during rapid updates"""
        # Store initial layout
        initial_layouts = {}
        for i, hand in enumerate(self.gui.ids.game_table.hands):
            initial_layouts[i] = [(card.x, card.y) for card in hand.cards]
            self.assertGreater(len(initial_layouts[i]), 0)  # Verify we have cards
        
        # Perform rapid updates
        for _ in range(5):  # Reduced number of updates
            self.game_state.current_turn = (self.game_state.current_turn + 1) % self.num_players
            self.gui.update_game_state(0)
            self.advance_frames(2)
        
        # Verify layouts haven't changed significantly
        for i, hand in enumerate(self.gui.ids.game_table.hands):
            current_layout = [(card.x, card.y) for card in hand.cards]
            # Allow small position differences due to floating point
            self.assertEqual(len(current_layout), len(initial_layouts[i]))
            for (x1, y1), (x2, y2) in zip(current_layout, initial_layouts[i]):
                self.assertAlmostEqual(x1, x2, delta=dp(1))
                self.assertAlmostEqual(y1, y2, delta=dp(1))

    def test_score_panel_updates(self):
        """Test that score panel updates correctly"""
        self.gui.game_state = self.game_state
        self.advance_frames(5)
        
        # Verify initial scores
        score_panel = self.gui.ids.score_panel
        self.assertEqual(score_panel.team1_score.text, 'Team 1 Score: 0')
        self.assertEqual(score_panel.team2_score.text, 'Team 2 Score: 0')
        
        # Update scores
        self.game_state.team1_sets = 1
        # Force update
        self.gui.update_score_panel()
        self.advance_frames(5)  # Wait for update to propagate
        
        # Verify updated score
        self.assertEqual(score_panel.team1_score.text, 'Team 1 Score: 1')

    def advance_frames(self, count):
        """Helper method to advance frames in the test"""
        for _ in range(count):
            Clock.tick()
            time.sleep(0.01) 