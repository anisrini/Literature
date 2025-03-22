import os
import logging
import random
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('literature_game.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set initial window size
Window.size = (1280, 720)
Window.minimum_width, Window.minimum_height = 800, 600

# ======== GAME LOGIC CLASSES ========

class Card:
    """Represents a playing card"""
    SUITS = ['Spades', 'Hearts', 'Diamonds', 'Clubs']
    RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
    
    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    """Represents a deck of 52 cards"""
    def __init__(self):
        logger.debug("Initializing new deck")
        self.cards = [Card(suit, rank) for suit in Card.SUITS for rank in Card.RANKS]
        logger.debug(f"Deck created with {len(self.cards)} cards")
    
    def shuffle(self):
        """Shuffle the deck of cards"""
        logger.debug("Shuffling deck")
        random.shuffle(self.cards)
    
    def deal(self, players, cards_per_player):
        """Deal cards to players"""
        logger.debug(f"Dealing {cards_per_player} cards to {len(players)} players")
        for _ in range(cards_per_player):
            for player in players:
                if self.cards:
                    player.add_card(self.cards.pop())

class Player:
    """Represents a player in the game"""
    def __init__(self, name, index):
        logger.debug(f"Creating player: {name}, index: {index}")
        self.name = name
        self.index = index
        self.hand = []
        self.score = 0
    
    def add_card(self, card):
        """Add a card to player's hand"""
        self.hand.append(card)
        logger.debug(f"Added {card} to {self.name}'s hand, now has {len(self.hand)} cards")

class GameState:
    """Manages the game state"""
    def __init__(self, players):
        logger.debug(f"Initializing game state with {len(players)} players")
        self.players = players
        self.current_player_index = 0
        
        # Split players into two teams (first half vs second half)
        half = len(players) // 2
        self.teams = [players[:half], players[half:]]
        self.team_scores = [0, 0]
        logger.debug("Game state initialized successfully")
    
    @property
    def current_player(self):
        return self.players[self.current_player_index]
    
    def next_player(self):
        """Move to the next player"""
        logger.debug(f"Moving from player {self.current_player_index} to next player")
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        logger.debug(f"New current player: {self.current_player.name} (index {self.current_player_index})")
        return self.current_player

# ======== UI SCREENS ========

class MenuScreen(Screen):
    """Main menu screen with game options"""
    def __init__(self, **kwargs):
        logger.debug("Initializing MenuScreen")
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Title
        title = Label(
            text='Literature Card Game',
            font_size=40,
            size_hint_y=0.3
        )
        layout.add_widget(title)
        
        # Status label for feedback
        self.status_label = Label(
            text='Ready to start a new game',
            font_size=16,
            size_hint_y=0.1
        )
        layout.add_widget(self.status_label)
        
        # Buttons
        start_button = Button(
            text='Start Game (6 Players)',
            size_hint_y=0.15,
            background_color=(0.2, 0.7, 0.2, 1)  # Green button
        )
        start_button.bind(on_press=self.start_6_player_game)
        layout.add_widget(start_button)
        
        start_button_alt = Button(
            text='Start Game (8 Players)',
            size_hint_y=0.15,
            background_color=(0.2, 0.7, 0.2, 1)  # Green button
        )
        start_button_alt.bind(on_press=self.start_8_player_game)
        layout.add_widget(start_button_alt)
        
        settings_button = Button(
            text='Settings',
            size_hint_y=0.15
        )
        settings_button.bind(on_press=self.open_settings)
        layout.add_widget(settings_button)
        
        quit_button = Button(
            text='Quit',
            size_hint_y=0.15,
            background_color=(0.7, 0.2, 0.2, 1)  # Red button
        )
        quit_button.bind(on_press=self.quit_game)
        layout.add_widget(quit_button)
        
        self.add_widget(layout)
        logger.debug("MenuScreen initialized successfully")
    
    def start_6_player_game(self, instance):
        logger.debug("Starting 6-player game")
        self.status_label.text = "Starting 6-player game..."
        app = App.get_running_app()
        app.start_game(6)
    
    def start_8_player_game(self, instance):
        logger.debug("Starting 8-player game")
        self.status_label.text = "Starting 8-player game..."
        app = App.get_running_app()
        app.start_game(8)
    
    def open_settings(self, instance):
        logger.debug("Opening settings screen")
        app = App.get_running_app()
        app.root.current = 'settings'
    
    def quit_game(self, instance):
        logger.debug("Quitting game")
        App.get_running_app().stop()
    
    def show_error(self, message):
        """Display error message in status label"""
        logger.error(f"Error: {message}")
        self.status_label.text = f"Error: {message}"
        self.status_label.color = (1, 0, 0, 1)  # Red text

class GameScreen(Screen):
    """Main game screen where gameplay happens"""
    def __init__(self, **kwargs):
        logger.debug("Initializing GameScreen")
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Player info
        self.game_info = Label(
            text="Waiting for game to start...",
            font_size=24,
            size_hint_y=0.1
        )
        self.layout.add_widget(self.game_info)
        
        # Cards display area
        self.cards_area = GridLayout(cols=4, spacing=5, size_hint_y=0.7)
        self.layout.add_widget(self.cards_area)
        
        # Game controls
        controls = BoxLayout(spacing=10, size_hint_y=0.2)
        
        self.next_btn = Button(
            text="Next Player",
            background_color=(0.2, 0.7, 0.2, 1)  # Green button
        )
        self.next_btn.bind(on_press=self.next_player)
        controls.add_widget(self.next_btn)
        
        self.back_btn = Button(
            text="Back to Menu",
            background_color=(0.7, 0.2, 0.2, 1)  # Red button
        )
        self.back_btn.bind(on_press=self.back_to_menu)
        controls.add_widget(self.back_btn)
        
        self.layout.add_widget(controls)
        
        self.add_widget(self.layout)
        logger.debug("GameScreen initialized successfully")
    
    def update_ui(self, game_state):
        """Update the UI with the current game state"""
        logger.debug("Updating game UI")
        try:
            self.game_info.text = f"Current Player: {game_state.current_player.name}"
            
            # Clear existing cards
            self.cards_area.clear_widgets()
            
            # Add current player's cards
            for card in game_state.current_player.hand:
                card_btn = Button(
                    text=str(card),
                    background_color=(0.9, 0.9, 1, 1),
                    size_hint_y=None,
                    height=50
                )
                self.cards_area.add_widget(card_btn)
            
            logger.debug(f"Added {len(game_state.current_player.hand)} cards to UI")
        except Exception as e:
            logger.error(f"Error updating game UI: {e}")
            self.game_info.text = f"Error: {e}"
    
    def next_player(self, instance):
        """Move to the next player's turn"""
        logger.debug("Next player button pressed")
        app = App.get_running_app()
        if app.game_state:
            app.game_state.next_player()
            self.update_ui(app.game_state)
        else:
            self.game_info.text = "Error: No active game"
    
    def back_to_menu(self, instance):
        """Return to main menu"""
        logger.debug("Back to menu button pressed")
        app = App.get_running_app()
        app.root.current = 'menu'

class SettingsScreen(Screen):
    """Settings screen for game configuration"""
    def __init__(self, **kwargs):
        logger.debug("Initializing SettingsScreen")
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(
            text='Settings',
            font_size=30,
            size_hint_y=0.2
        ))
        
        # Back button
        back_button = Button(
            text='Back to Menu',
            size_hint_y=0.1,
            background_color=(0.7, 0.2, 0.2, 1)  # Red button
        )
        back_button.bind(on_press=self.back_to_menu)
        layout.add_widget(back_button)
        
        self.add_widget(layout)
        logger.debug("SettingsScreen initialized successfully")
    
    def back_to_menu(self, instance):
        """Return to main menu"""
        logger.debug("Returning to menu from settings")
        app = App.get_running_app()
        app.root.current = 'menu'

# ======== MAIN APP CLASS ========

class LiteratureApp(App):
    """Main application class for Literature card game"""
    
    def __init__(self, **kwargs):
        logger.debug("Initializing LiteratureApp")
        super().__init__(**kwargs)
        self.game_state = None
        self.player_count = 6  # Default player count
    
    def build(self):
        """Build the application UI"""
        logger.debug("Building LiteratureApp UI")
        self.title = 'Literature Card Game'
        self.screen_manager = ScreenManager(transition=FadeTransition())
        
        # Create and add screens
        self.menu_screen = MenuScreen(name='menu')
        self.game_screen = GameScreen(name='game')
        self.settings_screen = SettingsScreen(name='settings')
        
        self.screen_manager.add_widget(self.menu_screen)
        self.screen_manager.add_widget(self.game_screen)
        self.screen_manager.add_widget(self.settings_screen)
        
        # Start with menu screen
        self.screen_manager.current = 'menu'
        
        logger.debug("LiteratureApp UI built successfully")
        return self.screen_manager
    
    def start_game(self, player_count):
        """Initialize a new game with the specified player count"""
        logger.debug(f"Starting new game with {player_count} players")
        try:
            # Set player count
            self.player_count = player_count
            
            # Initialize players
            player_names = [f"Player {i+1}" for i in range(player_count)]
            players = [Player(name, i) for i, name in enumerate(player_names)]
            logger.debug(f"Created {len(players)} players")
            
            # Create and shuffle deck
            deck = Deck()
            deck.shuffle()
            
            # Calculate cards per player based on player count
            cards_per_player = 6 if player_count == 8 else 8
            logger.debug(f"Cards per player: {cards_per_player}")
            
            # Deal cards to players
            deck.deal(players, cards_per_player)
            
            # Log each player's hand
            for player in players:
                logger.debug(f"{player.name}'s hand: {', '.join(str(card) for card in player.hand)}")
            
            # Initialize game state with players
            self.game_state = GameState(players)
            logger.info("Game state initialized successfully")
            
            # Update game screen UI
            self.game_screen.update_ui(self.game_state)
            
            # Switch to game screen
            self.screen_manager.current = 'game'
            logger.info("Game started successfully")
            
        except Exception as e:
            logger.error(f"Error starting game: {e}")
            self.menu_screen.show_error(f"Failed to start game: {e}")

# ======== APP ENTRY POINT ========

if __name__ == '__main__':
    try:
        # Create necessary directories for assets
        os.makedirs('assets/cards', exist_ok=True)
        os.makedirs('assets/sounds', exist_ok=True)
        
        logger.info("Starting Literature Card Game")
        app = LiteratureApp()
        app.run()
    except Exception as e:
        logger.critical(f"Critical error running app: {e}")
