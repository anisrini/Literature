import unittest
import os
import logging
from unittest.mock import MagicMock, patch
from kivy.app import App
from kivy.clock import Clock
from kivy.base import EventLoop
from kivy.tests.common import GraphicUnitTest, UnitTestTouch

# Import from main app
from main import (
    Card, Deck, Player, GameState, 
    LiteratureApp, MenuScreen, GameScreen, SettingsScreen
)

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CardTest(unittest.TestCase):
    """Unit tests for the Card class"""
    
    def test_card_creation(self):
        """Test that cards are created with correct attributes"""
        card = Card("Hearts", "A")
        self.assertEqual(card.suit, "Hearts")
        self.assertEqual(card.rank, "A")
    
    def test_card_string_representation(self):
        """Test the string representation of a card"""
        card = Card("Spades", "K")
        self.assertEqual(str(card), "K of Spades")

class DeckTest(unittest.TestCase):
    """Unit tests for the Deck class"""
    
    def test_deck_creation(self):
        """Test that a deck has 52 cards when created"""
        deck = Deck()
        self.assertEqual(len(deck.cards), 52)
    
    def test_deck_shuffle(self):
        """Test that shuffling changes card order"""
        deck1 = Deck()
        deck2 = Deck()
        # Store original order
        original_order = [str(card) for card in deck1.cards]
        
        # Shuffle one deck
        deck1.shuffle()
        shuffled_order = [str(card) for card in deck1.cards]
        
        # Check that at least some cards changed position
        self.assertNotEqual(original_order, shuffled_order)
        
        # Check that the second deck remains unshuffled
        unshuffled_order = [str(card) for card in deck2.cards]
        self.assertEqual(original_order, unshuffled_order)
    
    def test_deck_dealing(self):
        """Test that cards are dealt correctly to players"""
        deck = Deck()
        players = [Player(f"Player {i}", i) for i in range(3)]
        
        # Deal 5 cards to each player
        deck.deal(players, 5)
        
        # Check that each player received 5 cards
        for player in players:
            self.assertEqual(len(player.hand), 5)
        
        # Check that deck has correct number of cards remaining
        self.assertEqual(len(deck.cards), 52 - (5 * 3))

class PlayerTest(unittest.TestCase):
    """Unit tests for the Player class"""
    
    def test_player_creation(self):
        """Test player initialization"""
        player = Player("Test Player", 0)
        self.assertEqual(player.name, "Test Player")
        self.assertEqual(player.index, 0)
        self.assertEqual(player.score, 0)
        self.assertEqual(len(player.hand), 0)
    
    def test_add_card(self):
        """Test adding a card to player's hand"""
        player = Player("Test Player", 0)
        card = Card("Diamonds", "Q")
        player.add_card(card)
        
        self.assertEqual(len(player.hand), 1)
        self.assertEqual(player.hand[0], card)

class GameStateTest(unittest.TestCase):
    """Unit tests for the GameState class"""
    
    def test_game_state_creation(self):
        """Test game state initialization"""
        players = [Player(f"Player {i}", i) for i in range(6)]
        game_state = GameState(players)
        
        self.assertEqual(len(game_state.players), 6)
        self.assertEqual(game_state.current_player_index, 0)
        self.assertEqual(len(game_state.teams), 2)
        self.assertEqual(len(game_state.teams[0]), 3)
        self.assertEqual(len(game_state.teams[1]), 3)
        self.assertEqual(game_state.team_scores, [0, 0])
    
    def test_current_player(self):
        """Test current_player property"""
        players = [Player(f"Player {i}", i) for i in range(4)]
        game_state = GameState(players)
        
        self.assertEqual(game_state.current_player, players[0])
    
    def test_next_player(self):
        """Test next_player method"""
        players = [Player(f"Player {i}", i) for i in range(4)]
        game_state = GameState(players)
        
        # Initial player is Player 0
        self.assertEqual(game_state.current_player, players[0])
        
        # Move to next player
        next_player = game_state.next_player()
        self.assertEqual(next_player, players[1])
        self.assertEqual(game_state.current_player_index, 1)
        
        # Test wraparound
        game_state.current_player_index = 3
        next_player = game_state.next_player()
        self.assertEqual(next_player, players[0])
        self.assertEqual(game_state.current_player_index, 0)

class LiteratureAppIntegrationTest(unittest.TestCase):
    """Integration tests for the Literature App"""
    
    def setUp(self):
        """Set up the test environment"""
        # Create app instance but don't run it
        self.app = LiteratureApp()
        
        # Patch the run method to prevent app from actually running
        self.original_run = LiteratureApp.run
        LiteratureApp.run = lambda self: None
    
    def tearDown(self):
        """Clean up after tests"""
        LiteratureApp.run = self.original_run
    
    def test_app_initialization(self):
        """Test app initialization"""
        # Call build to create the UI
        self.app.build()
        
        # Check initial state
        self.assertEqual(self.app.title, 'Literature Card Game')
        self.assertEqual(self.app.player_count, 6)
        self.assertIsNone(self.app.game_state)
        
        # Check screens
        self.assertEqual(len(self.app.screen_manager.screens), 3)
        self.assertEqual(self.app.screen_manager.current, 'menu')
    
    def test_create_game(self):
        """Test game creation process"""
        # Build the app first
        self.app.build()
        
        # Create a game with 6 players
        self.app.player_count = 6
        self.app.create_game()
        
        # Verify game state was created
        self.assertIsNotNone(self.app.game_state)
        self.assertEqual(len(self.app.game_state.players), 6)
        
        # Check that cards were dealt
        cards_per_player = 8  # For 6 players
        for player in self.app.game_state.players:
            self.assertEqual(len(player.hand), cards_per_player)
    
    def test_player_count_changes(self):
        """Test changing player count affects game creation"""
        # Build the app first
        self.app.build()
        
        # Create a game with 8 players
        self.app.player_count = 8
        self.app.create_game()
        
        # Verify game state was created with 8 players
        self.assertEqual(len(self.app.game_state.players), 8)
        
        # Check that cards were dealt (6 per player for 8 players)
        for player in self.app.game_state.players:
            self.assertEqual(len(player.hand), 6)

# UI Tests require Kivy's GraphicUnitTest which runs in the Kivy event loop
class MenuScreenUITest(GraphicUnitTest):
    """UI tests for the MenuScreen"""
    
    def setUp(self):
        super().setUp()
        # Register the app to use in tests
        self.app = LiteratureApp()
        # Patch the run method to prevent app from actually running
        self.original_run = LiteratureApp.run
        LiteratureApp.run = lambda self: None
        
        # Build the app
        self.root = self.app.build()
        # Ensure the event loop is started
        EventLoop.ensure_window()
    
    def tearDown(self):
        LiteratureApp.run = self.original_run
        super().tearDown()
    
    def test_menu_buttons(self):
        """Test that menu buttons exist and have correct text"""
        menu_screen = self.app.menu_screen
        layout = menu_screen.children[0]  # Get the main layout
        
        # Count buttons
        buttons = [child for child in layout.children if hasattr(child, 'text') and child.text]
        
        # There should be at least 4 buttons
        self.assertGreaterEqual(len(buttons), 4)
        
        # Check text of buttons
        button_texts = [b.text for b in buttons]
        
        self.assertIn('Start Game (6 Players)', button_texts)
        self.assertIn('Start Game (8 Players)', button_texts)
        self.assertIn('Settings', button_texts)
        self.assertIn('Quit', button_texts)
    
    @patch('kivy.app.App.get_running_app')
    def test_start_game_button(self, mock_get_running_app):
        """Test that the Start Game button creates a game and switches screens"""
        # Mock the App.get_running_app() to return our app instance
        mock_get_running_app.return_value = self.app
        
        menu_screen = self.app.menu_screen
        
        # Find the start game button
        for child in menu_screen.children[0].children:
            if hasattr(child, 'text') and child.text == 'Start Game (6 Players)':
                start_button = child
                break
        
        # Simulate button press
        start_button.dispatch('on_release')
        
        # Verify the game was created and screen changed
        self.assertIsNotNone(self.app.game_state)
        self.assertEqual(self.app.player_count, 6)
        self.assertEqual(self.app.screen_manager.current, 'game')

class GameScreenUITest(GraphicUnitTest):
    """UI tests for the GameScreen"""
    
    def setUp(self):
        super().setUp()
        # Register the app to use in tests
        self.app = LiteratureApp()
        # Patch the run method to prevent app from actually running
        self.original_run = LiteratureApp.run
        LiteratureApp.run = lambda self: None
        
        # Build the app
        self.root = self.app.build()
        # Create a game
        self.app.create_game()
        # Switch to game screen
        self.app.screen_manager.current = 'game'
        # Ensure the event loop is started
        EventLoop.ensure_window()
    
    def tearDown(self):
        LiteratureApp.run = self.original_run
        super().tearDown()
    
    def test_game_screen_elements(self):
        """Test that game screen has all required elements"""
        game_screen = self.app.game_screen
        
        # Check game info label exists and shows current player
        self.assertIsNotNone(game_screen.game_info)
        self.assertIn(self.app.game_state.current_player.name, game_screen.game_info.text)
        
        # Check cards area exists and has cards
        self.assertIsNotNone(game_screen.cards_area)
        
        # Check back button exists
        back_buttons = [child for child in game_screen.layout.children 
                       if hasattr(child, 'text') and child.text == 'Back to Menu']
        self.assertEqual(len(back_buttons), 1)
    
    def test_card_display(self):
        """Test that cards are displayed properly"""
        game_screen = self.app.game_screen
        
        # Count card buttons in cards area
        card_buttons = [child for child in game_screen.cards_area.children
                       if hasattr(child, 'text')]
        
        # Should have the same number of buttons as cards in current player's hand
        expected_card_count = len(self.app.game_state.current_player.hand)
        self.assertEqual(len(card_buttons), expected_card_count)
        
        # Verify button text matches card text
        card_texts = {str(card) for card in self.app.game_state.current_player.hand}
        button_texts = {button.text for button in card_buttons}
        self.assertEqual(card_texts, button_texts)
    
    @patch('kivy.app.App.get_running_app')
    def test_back_button(self, mock_get_running_app):
        """Test that the Back button returns to the menu screen"""
        # Mock the App.get_running_app() to return our app instance
        mock_get_running_app.return_value = self.app
        
        game_screen = self.app.game_screen
        
        # Find back button
        for child in game_screen.layout.children:
            if hasattr(child, 'text') and child.text == 'Back to Menu':
                back_button = child
                break
        
        # Simulate button press
        back_button.dispatch('on_release')
        
        # Verify screen changed
        self.assertEqual(self.app.screen_manager.current, 'menu')

class EndToEndGameTest(unittest.TestCase):
    """End-to-end tests for game flow"""
    
    def setUp(self):
        """Set up the test environment"""
        # Create app instance but don't run it
        self.app = LiteratureApp()
        # Patch the run method to prevent app from actually running
        self.original_run = LiteratureApp.run
        LiteratureApp.run = lambda self: None
        
        # Build the app
        self.app.build()
    
    def tearDown(self):
        """Clean up after tests"""
        LiteratureApp.run = self.original_run
    
    def test_game_initialization_and_ui_update(self):
        """Test game initialization and UI updates"""
        # Start with 6 players
        self.app.player_count = 6
        self.app.create_game()
        
        # Verify game state
        self.assertIsNotNone(self.app.game_state)
        self.assertEqual(len(self.app.game_state.players), 6)
        
        # Check UI was updated
        game_screen = self.app.game_screen
        self.assertIn(self.app.game_state.current_player.name, game_screen.game_info.text)
        
        # Count cards in UI
        cards_in_ui = len(game_screen.cards_area.children)
        cards_in_hand = len(self.app.game_state.current_player.hand)
        self.assertEqual(cards_in_ui, cards_in_hand)
    
    def test_player_turn_cycle(self):
        """Test cycling through player turns"""
        # Initialize game with 6 players
        self.app.player_count = 6
        self.app.create_game()
        
        # Get initial player
        initial_player = self.app.game_state.current_player
        
        # Cycle through all 6 players
        for i in range(6):
            # Keep track of current player
            current_player = self.app.game_state.current_player
            
            # Move to next player
            next_player = self.app.game_state.next_player()
            
            # Verify next player is different (except on last iteration when we wrap around)
            if i < 5:
                self.assertNotEqual(current_player, next_player)
            else:
                self.assertEqual(next_player, initial_player)
            
            # Simulate updating the UI for next player
            self.app.game_screen.update_ui(self.app.game_state)
            
            # Verify UI shows correct player
            self.assertIn(next_player.name, self.app.game_screen.game_info.text)

# Run the tests if this file is executed directly
if __name__ == '__main__':
    unittest.main() 