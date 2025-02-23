from kivy.app import App
from kivy.config import Config
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from literature_game.gui.literature_game_gui import LiteratureGameGUI
from literature_game.startup_ui import StartupUI
from literature_game.game_state import GameState
from literature_game.deck import Deck
from literature_game.player import Player
import logging

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

# Set window size and make it resizable
Config.set('graphics', 'width', '1920')
Config.set('graphics', 'height', '1080')
Config.set('graphics', 'resizable', True)
Config.write()

class LiteratureApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_state = None
        self.game_gui = None
        logger.info("LiteratureApp initialized")

    def build(self):
        logger.info("Initializing Literature Game application")
        # Create screen manager
        self.screen_manager = ScreenManager(transition=FadeTransition())
        
        # Create startup screen
        startup_screen = Screen(name='startup')
        self.startup = StartupUI()
        self.startup.app = self
        startup_screen.add_widget(self.startup)
        self.screen_manager.add_widget(startup_screen)
        logger.debug("Startup screen initialized")
        
        return self.screen_manager
    
    def start_game(self, num_players):
        logger.info(f"Starting new game with {num_players} players")
        # Initialize players
        player_names = [f"Player {i+1}" for i in range(num_players)]
        players = [Player(name, i) for i, name in enumerate(player_names)]
        
        # Deal cards
        deck = Deck()
        deck.shuffle()
        cards_per_player = 6 if num_players == 8 else 8
        logger.debug(f"Dealing {cards_per_player} cards per player")
        deck.deal(players, cards_per_player)
        
        # Log each player's hand
        for player in players:
            logger.debug(f"{player.name}'s hand: {', '.join(str(card) for card in player.hand)}")
        
        # Initialize game state with players
        self.game_state = GameState(players)
        logger.info("Game state initialized")
        
        # Create game screen
        game_screen = Screen(name='game')
        self.game_gui = LiteratureGameGUI()
        self.game_gui.game_state = self.game_state
        game_screen.add_widget(self.game_gui)
        logger.debug("Game screen initialized")
        
        # Add game screen and switch to it
        self.screen_manager.add_widget(game_screen)
        self.screen_manager.current = 'game'
        logger.info("Game started successfully")

if __name__ == '__main__':
    LiteratureApp().run()
