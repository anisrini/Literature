from kivy.uix.scatter import Scatter
from kivy.graphics import Color, Rectangle, Line
from kivy.core.text import Label as CoreLabel
from kivy.metrics import dp
import logging

logger = logging.getLogger(__name__)

class Card(Scatter):
    """
    Represents a playing card widget in the UI.
    Handles the visual representation and interaction of a single card.
    """
    def __init__(self, suit, rank, **kwargs):
        super().__init__(**kwargs)
        self.suit = suit
        self.rank = rank
        self.face_up = True
        self.is_current_player = False
        self.do_rotation = False
        self.do_scale = False
        
        # Card symbols for suits
        self.symbols = {
            'Hearts': '♥', 
            'Diamonds': '♦',
            'Clubs': '♣', 
            'Spades': '♠'
        }
        
        self.bind(pos=self._redraw, size=self._redraw)
        self.draw_card()
    
    def _redraw(self, *args):
        """Redraw card when position or size changes"""
        self.draw_card()
    
    def draw_card(self, dt=None):
        """Draws the card with rank and suit"""
        self.canvas.after.clear()
        with self.canvas.after:
            # Draw card background and border
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.8, 0.8, 0.8, 1)
            Line(rectangle=[self.x, self.y, self.width, self.height], width=1.5)
            
            # Set color based on suit
            Color(*(1, 0, 0, 1) if self.suit in ['Hearts', 'Diamonds'] else (0, 0, 0, 1))
            
            # Draw rank and suit in corners and center
            self._draw_card_elements()
            
            # Highlight current player's cards
            if self.is_current_player:
                self._draw_highlight()

    def _draw_card_elements(self):
        """Draws the rank and suit elements on the card"""
        # Top left rank
        rank_label = CoreLabel(text=self.rank, font_size=dp(20))
        rank_label.refresh()
        Rectangle(texture=rank_label.texture, 
                 pos=(self.x + dp(10), self.y + self.height - dp(30)),
                 size=rank_label.texture.size)
        
        # Center suit
        suit_label = CoreLabel(text=self.symbols[self.suit], font_size=dp(50))
        suit_label.refresh()
        Rectangle(texture=suit_label.texture,
                 pos=(self.center_x - suit_label.texture.size[0]/2,
                      self.center_y - suit_label.texture.size[1]/2),
                 size=suit_label.texture.size)
        
        # Bottom right rank and suit
        bottom_label = CoreLabel(text=f"{self.rank}{self.symbols[self.suit]}", 
                               font_size=dp(20))
        bottom_label.refresh()
        Rectangle(texture=bottom_label.texture,
                 pos=(self.x + self.width - dp(30), self.y + dp(10)),
                 size=bottom_label.texture.size)

    def _draw_highlight(self):
        """Draws highlight effect for current player's cards"""
        Color(1, 1, 0, 0.2)  # Subtle yellow highlight
        Rectangle(pos=self.pos, size=self.size)
        Color(1, 1, 0, 0.8)  # Brighter yellow border
        Line(rectangle=[self.x, self.y, self.width, self.height], width=dp(2)) 