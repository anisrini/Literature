import logging
import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Set window size
Window.size = (800, 600)

# ======== GAME LOGIC CLASSES ========

class Card:
    """Simple playing card"""
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
    
    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Player:
    """Player with a hand of cards"""
    def __init__(self, name):
        self.name = name
        self.hand = []
    
    def add_card(self, card):
        self.hand.append(card)

class Game:
    """Manages game state"""
    def __init__(self, player_count=6):
        # Create players
        self.players = [Player(f"Player {i+1}") for i in range(player_count)]
        self.current_player_index = 0
        
        # Create and deal cards
        self.create_deck()
        self.deal_cards()
        
        logger.info(f"Game created with {player_count} players")
        for player in self.players:
            logger.info(f"{player.name} has {len(player.hand)} cards")
    
    def create_deck(self):
        """Create a standard deck of cards"""
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        self.deck = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(self.deck)
        logger.info(f"Created and shuffled deck with {len(self.deck)} cards")
    
    def deal_cards(self):
        """Deal cards to all players"""
        cards_per_player = 6 if len(self.players) == 8 else 8
        
        for _ in range(cards_per_player):
            for player in self.players:
                if self.deck:
                    player.add_card(self.deck.pop())
    
    @property
    def current_player(self):
        return self.players[self.current_player_index]
    
    def next_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        return self.current_player

# ======== UI CLASSES ========

class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Title
        title = Label(text='Literature Card Game', font_size=30)
        layout.add_widget(title)
        
        # Status Label
        self.status = Label(text='Ready to start a new game', font_size=14)
        layout.add_widget(self.status)
        
        # Game buttons
        btn_6 = Button(text='Start 6-Player Game', background_color=(0, 0.7, 0, 1))
        btn_6.bind(on_press=self.start_6_player_game)
        layout.add_widget(btn_6)
        
        btn_8 = Button(text='Start 8-Player Game', background_color=(0, 0.7, 0, 1))
        btn_8.bind(on_press=self.start_8_player_game)
        layout.add_widget(btn_8)
        
        # Exit button
        btn_exit = Button(text='Exit Game', background_color=(0.7, 0, 0, 1))
        btn_exit.bind(on_press=self.exit_game)
        layout.add_widget(btn_exit)
        
        self.add_widget(layout)
    
    def start_6_player_game(self, instance):
        self.status.text = "Starting 6-player game..."
        app = App.get_running_app()
        app.start_game(6)
    
    def start_8_player_game(self, instance):
        self.status.text = "Starting 8-player game..."
        app = App.get_running_app()
        app.start_game(8)
    
    def exit_game(self, instance):
        App.get_running_app().stop()

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Player info
        self.player_label = Label(text="Waiting for game to start...", font_size=20)
        self.layout.add_widget(self.player_label)
        
        # Cards display
        self.cards_grid = GridLayout(cols=4, spacing=5, size_hint_y=0.7)
        self.layout.add_widget(self.cards_grid)
        
        # Game controls
        controls = BoxLayout(spacing=10, size_hint_y=0.2)
        
        self.next_btn = Button(text="Next Player")
        self.next_btn.bind(on_press=self.next_player)
        controls.add_widget(self.next_btn)
        
        self.back_btn = Button(text="Back to Menu")
        self.back_btn.bind(on_press=self.back_to_menu)
        controls.add_widget(self.back_btn)
        
        self.layout.add_widget(controls)
        
        self.add_widget(self.layout)
    
    def update_display(self, game):
        """Update the display for the current player"""
        try:
            self.player_label.text = f"Current Player: {game.current_player.name}"
            
            # Clear the grid
            self.cards_grid.clear_widgets()
            
            # Add cards for the current player
            for card in game.current_player.hand:
                card_btn = Button(
                    text=str(card),
                    background_color=(0.9, 0.9, 1, 1),
                    size_hint_y=None,
                    height=40
                )
                self.cards_grid.add_widget(card_btn)
            
            logger.info(f"Updated display for {game.current_player.name} with {len(game.current_player.hand)} cards")
        except Exception as e:
            logger.error(f"Error updating display: {e}")
            self.player_label.text = f"Error: {str(e)}"
    
    def next_player(self, instance):
        app = App.get_running_app()
        if app.game:
            app.game.next_player()
            self.update_display(app.game)
        else:
            self.player_label.text = "Error: No active game"
    
    def back_to_menu(self, instance):
        app = App.get_running_app()
        app.root.current = 'menu'

class LiteratureApp(App):
    def build(self):
        self.title = 'Literature Card Game'
        self.game = None
        
        # Create screen manager and screens
        sm = ScreenManager()
        
        self.menu_screen = MenuScreen(name='menu')
        self.game_screen = GameScreen(name='game')
        
        sm.add_widget(self.menu_screen)
        sm.add_widget(self.game_screen)
        
        return sm
    
    def start_game(self, player_count):
        """Start a new game with the specified number of players"""
        try:
            logger.info(f"Creating new game with {player_count} players")
            
            # Create new game
            self.game = Game(player_count)
            
            # Update game screen
            self.game_screen.update_display(self.game)
            
            # Switch to game screen
            self.root.current = 'game'
            
            logger.info("Game started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start game: {e}")
            self.menu_screen.status.text = f"Error: {str(e)}"

if __name__ == '__main__':
    try:
        LiteratureApp().run()
    except Exception as e:
        logger.error(f"Application error: {e}") 