import os
import logging
import traceback
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
from functools import partial
from kivy.properties import ObjectProperty

# Configure more verbose logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('literature_game_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set initial window size
Window.size = (1280, 720)
Window.minimum_width, Window.minimum_height = 800, 600

class DebugPopup(Popup):
    """Popup for displaying debug information and errors to the user"""
    def __init__(self, title, message, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.size_hint = (0.8, 0.6)
        self.auto_dismiss = True
        
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Message label
        msg_label = Label(
            text=message,
            text_size=(self.width * 0.8, None),
            size_hint_y=0.8,
            halign='left',
            valign='top'
        )
        
        # Close button
        close_button = Button(
            text="Close",
            size_hint_y=0.2,
            on_release=self.dismiss
        )
        
        content.add_widget(msg_label)
        content.add_widget(close_button)
        self.content = content

class Card:
    """Represents a playing card"""
    SUITS = ['Spades', 'Hearts', 'Diamonds', 'Clubs']
    RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        logger.debug(f"Created card: {self}")
    
    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    """Represents a deck of 52 cards"""
    def __init__(self):
        logger.debug("Initializing new deck")
        self.cards = []
        try:
            self.cards = [Card(suit, rank) for suit in Card.SUITS for rank in Card.RANKS]
            logger.debug(f"Deck created with {len(self.cards)} cards")
        except Exception as e:
            logger.error(f"Error creating deck: {e}")
            logger.error(traceback.format_exc())
    
    def shuffle(self):
        """Shuffle the deck of cards"""
        logger.debug("Shuffling deck")
        try:
            import random
            random.shuffle(self.cards)
            logger.debug("Deck shuffled successfully")
        except Exception as e:
            logger.error(f"Error shuffling deck: {e}")
            logger.error(traceback.format_exc())
    
    def deal(self, players, cards_per_player):
        """Deal cards to players"""
        logger.debug(f"Dealing {cards_per_player} cards to {len(players)} players")
        try:
            for _ in range(cards_per_player):
                for player in players:
                    if self.cards:
                        card = self.cards.pop()
                        logger.debug(f"Dealing {card} to {player.name}")
                        player.add_card(card)
                    else:
                        logger.warning("Ran out of cards while dealing")
                        return
            logger.debug("Cards dealt successfully")
        except Exception as e:
            logger.error(f"Error dealing cards: {e}")
            logger.error(traceback.format_exc())

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
        try:
            self.hand.append(card)
            logger.debug(f"Added {card} to {self.name}'s hand, now has {len(self.hand)} cards")
        except Exception as e:
            logger.error(f"Error adding card to player's hand: {e}")
            logger.error(traceback.format_exc())

class GameState:
    """Manages the game state"""
    def __init__(self, players):
        logger.debug(f"Initializing game state with {len(players)} players")
        try:
            self.players = players
            self.current_player_index = 0
            
            # Split players into two teams (first half vs second half)
            half = len(players) // 2
            self.teams = [players[:half], players[half:]]
            logger.debug(f"Created teams: Team 1 with {len(self.teams[0])} players, Team 2 with {len(self.teams[1])} players")
            
            self.team_scores = [0, 0]
            logger.debug("Game state initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing game state: {e}")
            logger.error(traceback.format_exc())
    
    @property
    def current_player(self):
        try:
            return self.players[self.current_player_index]
        except Exception as e:
            logger.error(f"Error getting current player: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def next_player(self):
        """Move to the next player"""
        try:
            logger.debug(f"Moving from player {self.current_player_index} to next player")
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            logger.debug(f"New current player: {self.current_player.name} (index {self.current_player_index})")
            return self.current_player
        except Exception as e:
            logger.error(f"Error moving to next player: {e}")
            logger.error(traceback.format_exc())
            return None

class MenuScreen(Screen):
    """Main menu screen with game options"""
    status_label = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        logger.debug("Initializing MenuScreen")
        try:
            super().__init__(**kwargs)
            
            layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
            
            # Title
            title = Label(
                text='Literature Card Game',
                font_size=40,
                size_hint_y=0.3
            )
            
            # Status label for feedback
            self.status_label = Label(
                text='Ready to start game',
                font_size=16,
                size_hint_y=0.1,
                color=(0, 1, 0, 1)  # Green text
            )
            
            # Buttons
            start_button = Button(
                text='Start Game (6 Players)',
                size_hint_y=0.15,
                background_color=(0.2, 0.7, 0.2, 1)  # Green button
            )
            start_button.bind(on_release=lambda x: self.handle_start_button(6))
            
            start_button_alt = Button(
                text='Start Game (8 Players)',
                size_hint_y=0.15,
                background_color=(0.2, 0.7, 0.2, 1)  # Green button
            )
            start_button_alt.bind(on_release=lambda x: self.handle_start_button(8))
            
            settings_button = Button(
                text='Settings',
                size_hint_y=0.15
            )
            settings_button.bind(on_release=self.open_settings)
            
            quit_button = Button(
                text='Quit',
                size_hint_y=0.15,
                background_color=(0.7, 0.2, 0.2, 1)  # Red button
            )
            quit_button.bind(on_release=self.quit_game)
            
            # Add widgets to layout
            layout.add_widget(title)
            layout.add_widget(self.status_label)
            layout.add_widget(start_button)
            layout.add_widget(start_button_alt)
            layout.add_widget(settings_button)
            layout.add_widget(quit_button)
            
            self.add_widget(layout)
            logger.debug("MenuScreen initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing MenuScreen: {e}")
            logger.error(traceback.format_exc())
            self.show_error(f"Error initializing menu: {e}")
    
    def handle_start_button(self, player_count):
        """Handle start button press with visual feedback"""
        logger.debug(f"Start button pressed for {player_count} players")
        self.status_label.text = f"Starting game with {player_count} players..."
        self.status_label.color = (0, 0, 1, 1)  # Blue for processing
        
        # Use Clock to delay the actual game start to allow UI update
        Clock.schedule_once(partial(self.start_game, player_count), 0.5)
    
    def start_game(self, player_count, *largs):
        """Start a new game with the specified number of players"""
        logger.debug(f"Starting game with {player_count} players")
        try:
            app = App.get_running_app()
            logger.debug(f"Retrieved running app: {app}")
            
            if app is None:
                error_msg = "Could not get running app instance"
                logger.error(error_msg)
                self.status_label.text = error_msg
                self.status_label.color = (1, 0, 0, 1)  # Red for error
                return
            
            app.player_count = player_count
            logger.debug(f"Set player_count to {player_count}")
            
            # Create game with better error handling
            try:
                app.create_game()
                logger.debug("Game created")
            except Exception as e:
                error_msg = f"Failed to create game: {e}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                self.status_label.text = error_msg
                self.status_label.color = (1, 0, 0, 1)  # Red for error
                self.show_error(error_msg)
                return
            
            # Only switch if game creation was successful
            if app.game_state is not None:
                self.status_label.text = "Game created successfully, switching to game screen..."
                self.status_label.color = (0, 1, 0, 1)  # Green for success
                Clock.schedule_once(lambda dt: setattr(app.screen_manager, 'current', 'game'), 0.5)
                logger.debug("Scheduled switch to game screen")
            else:
                error_msg = "Game state is None after creation"
                logger.error(error_msg)
                self.status_label.text = error_msg
                self.status_label.color = (1, 0, 0, 1)  # Red for error
                self.show_error(error_msg)
        except Exception as e:
            error_msg = f"Error starting game: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self.status_label.text = error_msg
            self.status_label.color = (1, 0, 0, 1)  # Red for error
            self.show_error(error_msg)
    
    def open_settings(self, *args):
        """Open the settings screen"""
        logger.debug("Opening settings screen")
        try:
            app = App.get_running_app()
            if app and hasattr(app, 'screen_manager'):
                app.screen_manager.current = 'settings'
            else:
                self.show_error("Cannot access screen manager")
        except Exception as e:
            logger.error(f"Error opening settings: {e}")
            logger.error(traceback.format_exc())
            self.show_error(f"Error opening settings: {e}")
    
    def quit_game(self, *args):
        """Exit the application"""
        logger.debug("Quitting game")
        try:
            App.get_running_app().stop()
        except Exception as e:
            logger.error(f"Error quitting game: {e}")
            logger.error(traceback.format_exc())
    
    def show_error(self, message):
        """Show error popup"""
        popup = DebugPopup(title="Error", message=message)
        popup.open()

class GameScreen(Screen):
    """Main game screen where gameplay happens"""
    def __init__(self, **kwargs):
        logger.debug("Initializing GameScreen")
        try:
            super().__init__(**kwargs)
            
            self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
            
            # Status bar at the top
            self.status_bar = BoxLayout(size_hint_y=0.1)
            self.game_info = Label(
                text='Game screen - waiting for game to start',
                font_size=18
            )
            self.status_bar.add_widget(self.game_info)
            self.layout.add_widget(self.status_bar)
            
            # Cards area - will be populated when game starts
            self.cards_area = GridLayout(cols=4, spacing=10, size_hint_y=0.7)
            self.layout.add_widget(self.cards_area)
            
            # Player controls
            controls = BoxLayout(size_hint_y=0.1, spacing=10)
            
            next_turn_button = Button(
                text="Next Turn",
                size_hint_x=0.3
            )
            next_turn_button.bind(on_release=self.next_turn)
            
            back_button = Button(
                text='Back to Menu',
                size_hint_x=0.3,
                background_color=(0.7, 0.2, 0.2, 1)  # Red button
            )
            back_button.bind(on_release=self.back_to_menu)
            
            controls.add_widget(next_turn_button)
            controls.add_widget(back_button)
            self.layout.add_widget(controls)
            
            self.add_widget(self.layout)
            logger.debug("GameScreen initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing GameScreen: {e}")
            logger.error(traceback.format_exc())
            # We can't show error popup here yet as we're still in init
    
    def on_enter(self):
        """Called when the screen is entered"""
        logger.debug("Entered GameScreen")
        # Try to update the UI when screen is entered
        app = App.get_running_app()
        if app and hasattr(app, 'game_state') and app.game_state:
            self.update_ui(app.game_state)
        else:
            self.game_info.text = "Error: No game state available"
            logger.error("No game state available when entering game screen")
    
    def next_turn(self, *args):
        """Move to the next player's turn"""
        logger.debug("Next turn button pressed")
        app = App.get_running_app()
        if app and app.game_state:
            app.game_state.next_player()
            self.update_ui(app.game_state)
        else:
            self.game_info.text = "Error: Cannot proceed to next turn"
            logger.error("Cannot proceed to next turn - no game state")
    
    def update_ui(self, game_state):
        """Update the UI with the current game state"""
        logger.debug("Updating game UI")
        try:
            if game_state and game_state.current_player:
                self.game_info.text = f"Current Player: {game_state.current_player.name}"
                logger.debug(f"Updated game info text: {self.game_info.text}")
                
                # Clear existing cards
                self.cards_area.clear_widgets()
                logger.debug("Cleared existing cards")
                
                # Display current player's cards
                for card in game_state.current_player.hand:
                    card_btn = Button(
                        text=str(card), 
                        size_hint_y=None, 
                        height=50,
                        background_color=(0.9, 0.9, 1, 1)  # Light blue for cards
                    )
                    self.cards_area.add_widget(card_btn)
                
                logger.debug(f"Added {len(game_state.current_player.hand)} card buttons to UI")
            else:
                error_msg = "Cannot update UI - game_state or current_player is None"
                logger.error(error_msg)
                self.game_info.text = error_msg
                self.show_error(error_msg)
        except Exception as e:
            error_msg = f"Error updating game UI: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self.game_info.text = error_msg
            self.show_error(error_msg)
    
    def back_to_menu(self, *args):
        """Return to main menu"""
        logger.debug("Returning to menu")
        try:
            app = App.get_running_app()
            if app and hasattr(app, 'screen_manager'):
                app.screen_manager.current = 'menu'
            else:
                self.show_error("Cannot access screen manager")
        except Exception as e:
            logger.error(f"Error returning to menu: {e}")
            logger.error(traceback.format_exc())
            self.show_error(f"Error returning to menu: {e}")
    
    def show_error(self, message):
        """Show error popup"""
        popup = DebugPopup(title="Game Error", message=message)
        popup.open()

class SettingsScreen(Screen):
    """Settings screen for game configuration"""
    def __init__(self, **kwargs):
        logger.debug("Initializing SettingsScreen")
        try:
            super().__init__(**kwargs)
            
            layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
            
            layout.add_widget(Label(
                text='Settings',
                font_size=30,
                size_hint_y=0.2
            ))
            
            # Sound settings
            sound_row = BoxLayout(size_hint_y=0.1)
            sound_row.add_widget(Label(text='Sound Effects:'))
            sound_switch = Button(
                text='On',
                size_hint_x=0.3
            )
            sound_row.add_widget(sound_switch)
            layout.add_widget(sound_row)
            
            # Animation settings
            anim_row = BoxLayout(size_hint_y=0.1)
            anim_row.add_widget(Label(text='Animations:'))
            anim_switch = Button(
                text='On',
                size_hint_x=0.3
            )
            anim_row.add_widget(anim_switch)
            layout.add_widget(anim_row)
            
            # Debug options
            debug_row = BoxLayout(size_hint_y=0.1)
            debug_row.add_widget(Label(text='Debug Mode:'))
            debug_button = Button(
                text='Show Debug Info',
                size_hint_x=0.3
            )
            debug_button.bind(on_release=self.show_debug_info)
            debug_row.add_widget(debug_button)
            layout.add_widget(debug_row)
            
            # Back button
            back_button = Button(
                text='Back to Menu',
                size_hint_y=0.1,
                background_color=(0.7, 0.2, 0.2, 1)  # Red button
            )
            back_button.bind(on_release=self.back_to_menu)
            layout.add_widget(back_button)
            
            self.add_widget(layout)
            logger.debug("SettingsScreen initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing SettingsScreen: {e}")
            logger.error(traceback.format_exc())
    
    def show_debug_info(self, *args):
        """Show debug information"""
        logger.debug("Showing debug info")
        app = App.get_running_app()
        
        debug_text = "Debug Information:\n\n"
        
        if app:
            debug_text += f"App: {app}\n"
            debug_text += f"Player Count: {getattr(app, 'player_count', 'Not set')}\n"
            
            if hasattr(app, 'game_state') and app.game_state:
                gs = app.game_state
                debug_text += f"Game State: Active\n"
                debug_text += f"Players: {len(gs.players)}\n"
                debug_text += f"Current Player: {gs.current_player.name if gs.current_player else 'None'}\n"
                debug_text += f"Teams: {len(gs.teams[0])} vs {len(gs.teams[1])}\n"
            else:
                debug_text += "Game State: None\n"
        else:
            debug_text += "App instance not available\n"
        
        popup = DebugPopup(title="Debug Information", message=debug_text)
        popup.open()
    
    def back_to_menu(self, *args):
        """Return to main menu"""
        logger.debug("Returning to menu from settings")
        try:
            app = App.get_running_app()
            if app and hasattr(app, 'screen_manager'):
                app.screen_manager.current = 'menu'
            else:
                popup = DebugPopup(title="Error", message="Cannot access screen manager")
                popup.open()
        except Exception as e:
            logger.error(f"Error returning to menu from settings: {e}")
            logger.error(traceback.format_exc())
            popup = DebugPopup(title="Error", message=f"Error returning to menu: {e}")
            popup.open()

class LiteratureApp(App):
    """Main application class for Literature card game"""
    
    def __init__(self, **kwargs):
        logger.debug("Initializing LiteratureApp")
        try:
            super().__init__(**kwargs)
            self.game_state = None
            self.player_count = 6  # Default player count
            logger.debug("LiteratureApp initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing LiteratureApp: {e}")
            logger.error(traceback.format_exc())
    
    def build(self):
        """Build the application UI"""
        logger.debug("Building LiteratureApp UI")
        try:
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
        except Exception as e:
            logger.error(f"Error building LiteratureApp UI: {e}")
            logger.error(traceback.format_exc())
            # Return a basic layout with error message in case build fails
            layout = BoxLayout(orientation='vertical')
            layout.add_widget(Label(text=f"Error building UI: {e}"))
            return layout
    
    def create_game(self):
        """Initialize a new game with the current player count"""
        logger.debug(f"Creating new game with {self.player_count} players")
        try:
            # Initialize players
            player_names = [f"Player {i+1}" for i in range(self.player_count)]
            players = [Player(name, i) for i, name in enumerate(player_names)]
            logger.debug(f"Created {len(players)} players")
            
            # Deal cards
            deck = Deck()
            deck.shuffle()
            
            # Calculate cards per player based on player count
            cards_per_player = 6 if self.player_count == 8 else 8
            logger.debug(f"Cards per player: {cards_per_player}")
            
            # Deal cards to players
            deck.deal(players, cards_per_player)
            
            # Log each player's hand
            for player in players:
                logger.debug(f"{player.name}'s hand: {', '.join(str(card) for card in player.hand)}")
            
            # Initialize game state with players
            self.game_state = GameState(players)
            logger.debug("Game state initialized")
            
            return True  # Return success
        except Exception as e:
            logger.error(f"Error creating game: {e}")
            logger.error(traceback.format_exc())
            # Create a popup to show the error
            if hasattr(self, 'menu_screen'):
                Clock.schedule_once(
                    lambda dt: self.menu_screen.show_error(f"Failed to create game: {str(e)}"), 
                    0.1
                )
            return False  # Return failure

if __name__ == '__main__':
    try:
        # Create necessary directories for assets
        os.makedirs('assets/cards', exist_ok=True)
        os.makedirs('assets/sounds', exist_ok=True)
        
        logger.debug("Starting LiteratureApp")
        # Start the app
        app = LiteratureApp()
        app.run()
    except Exception as e:
        logger.critical(f"Critical error running app: {e}")
        logger.critical(traceback.format_exc())
        
        # Try to show error in a basic window if possible
        from kivy.app import App
        from kivy.uix.label import Label
        from kivy.uix.boxlayout import BoxLayout
        
        class ErrorApp(App):
            def build(self):
                layout = BoxLayout(orientation='vertical', padding=20)
                layout.add_widget(Label(
                    text=f"Critical Error: {str(e)}\n\nPlease check the log file for details.",
                    halign='center'
                ))
                return layout
        
        ErrorApp().run() 