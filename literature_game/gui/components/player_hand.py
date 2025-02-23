from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from literature_game.gui.components.card import Card
import logging

logger = logging.getLogger(__name__)

class PlayerHand(Widget):
    """
    Represents a player's hand of cards in the UI.
    Handles the layout and management of cards for a single player.
    """
    def __init__(self, player, is_current=False, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.cards = []
        self.is_current = is_current
        self._last_is_current = is_current
        self._layout_scheduled = False
        self._layout_trigger = Clock.create_trigger(self.layout_cards, 0)
        
        # Set team color based on player ID
        self.team_color = (get_color_from_hex('#FFD700') if player.id % 2 == 0 
                          else get_color_from_hex('#1E90FF'))
        
        self.bind(pos=self._trigger_layout, size=self._trigger_layout)
        self._init_canvas()
        Clock.schedule_once(self.layout_cards)
    
    def _init_canvas(self):
        """Initialize the canvas with background and highlight"""
        with self.canvas.before:
            Color(*self.team_color, 0.3)
            self.background = Rectangle(pos=self.pos, size=self.size)
            
            if self.is_current:
                Color(*self.team_color, 0.5)
                self.highlight = Rectangle(
                    pos=(self.pos[0] - dp(5), self.pos[1] - dp(5)),
                    size=(self.size[0] + dp(10), self.size[1] + dp(10))
                )

    # ... (rest of the PlayerHand class implementation) 