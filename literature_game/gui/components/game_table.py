from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
from kivy.metrics import dp
from literature_game.gui.components.player_hand import PlayerHand
import logging

logger = logging.getLogger(__name__)

class GameTable(Widget):
    """
    Main game table widget that manages the layout of player hands
    and coordinates card movements.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_state = None
        self.hands = []
    
    def update(self, game_state):
        """Update the game table display with current game state"""
        try:
            if game_state != self.game_state:
                self.setup_game(game_state)
            else:
                # Update existing display
                for hand in self.hands:
                    hand.update()
        except Exception as e:
            logger.error(f"Error updating game table: {str(e)}")

    # ... (GameTable implementation) 