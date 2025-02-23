from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from literature_game.gui.components.card import Card
import logging
from kivy.properties import BooleanProperty, ObjectProperty

logger = logging.getLogger(__name__)

class PlayerHand(Widget):
    """
    Represents a player's hand of cards in the UI.
    Handles the layout and management of cards for a single player.
    """
    is_current = BooleanProperty(False)
    player = ObjectProperty(None)
    
    def __init__(self, player, is_current=False, **kwargs):
        # Initialize instance variables first
        self._layout_scheduled = False  # Move this up
        self._cleanup_trigger = None
        self.highlight = None
        self.cards = []
        
        # Call super after basic initialization
        super().__init__(**kwargs)
        
        # Set up player and state
        self.player = player
        self.is_current = is_current
        
        # Create cleanup trigger
        self._cleanup_trigger = Clock.create_trigger(self.cleanup_cards, 0)
        
        # Set team color based on player ID
        self.team_color = (get_color_from_hex('#FFD700') if player.id % 2 == 0 
                          else get_color_from_hex('#1E90FF'))
        
        # Bind to both size and pos changes
        self.bind(
            size=self._trigger_layout,
            pos=self._trigger_layout,
            is_current=self._on_current_changed
        )
        
        # Initialize canvas and schedule first layout
        self._init_canvas()
        Clock.schedule_once(self.force_layout, 0)

    def _on_current_changed(self, instance, value):
        """Handle changes to is_current property"""
        self._init_canvas()

    def _trigger_layout(self, *args):
        """Trigger a layout update only if not already scheduled"""
        if not self._layout_scheduled:
            Clock.schedule_once(self.layout_cards)

    def _init_canvas(self):
        """Initialize the canvas with background and highlight"""
        self.canvas.before.clear()
        with self.canvas.before:
            # Draw background
            Color(*self.team_color, 0.3)
            self.background = Rectangle(pos=self.pos, size=self.size)
            
            # Draw highlight if current
            if self.is_current:
                Color(*self.team_color, 0.5)
                self.highlight = Rectangle(
                    pos=(self.pos[0] - dp(5), self.pos[1] - dp(5)),
                    size=(self.size[0] + dp(10), self.size[1] + dp(10))
                )
            else:
                self.highlight = None

    def cleanup_cards(self, *args):
        """Clean up card widgets properly"""
        for card in self.cards:
            if card.parent:
                card.parent.remove_widget(card)
        self.cards = []

    def force_layout(self, dt=None):
        """Force a complete layout refresh"""
        self._layout_scheduled = False
        self._init_canvas()
        self.layout_cards(dt)

    def layout_cards(self, dt=None):
        """Layout the cards in the hand"""
        if self._layout_scheduled:
            return
        self._layout_scheduled = True
        
        try:
            self.cleanup_cards()
            self.clear_widgets()
            self.cards = []
            
            if not self.player.hand:
                return
            
            # Calculate card dimensions with minimum sizes
            num_cards = len(self.player.hand)
            min_spacing = dp(5)
            
            # Calculate maximum card width that will fit
            available_width = self.width - (2 * min_spacing)
            max_card_width = min(dp(80), (available_width - (num_cards - 1) * min_spacing) / num_cards)
            max_card_height = min(dp(112), self.height * 0.8)
            
            # Calculate total width of all cards with spacing
            total_width = (num_cards * max_card_width) + ((num_cards - 1) * min_spacing)
            
            # Center the cards horizontally
            start_x = (self.width - total_width) / 2
            
            # Center cards vertically
            start_y = (self.height - max_card_height) / 2
            
            # Create and position cards using relative coordinates
            for i in range(num_cards):
                card_data = self.player.hand[i]
                
                # Calculate relative position
                rel_x = start_x + (i * (max_card_width + min_spacing))
                rel_y = start_y
                
                # Create card widget with position and size
                card_widget = Card(
                    suit=card_data.suit,
                    rank=str(card_data.rank),
                    size=(max_card_width, max_card_height),
                    pos=(rel_x, rel_y)  # Set position directly
                )
                card_widget.is_current_player = self.is_current
                
                self.cards.append(card_widget)
                self.add_widget(card_widget)
                
                logger.debug(
                    f"Card {i} positioned at rel({rel_x}, {rel_y}) "
                    f"in hand size({self.width}, {self.height})"
                )
            
        except Exception as e:
            logger.error(f"Error laying out cards for {self.player.name}: {str(e)}")
        finally:
            self._layout_scheduled = False

    def update_layout(self):
        """Update the hand's layout and appearance"""
        if not self._layout_scheduled:
            self.force_layout()

    def on_size(self, *args):
        """Handle size changes"""
        self._trigger_layout()

    def on_pos(self, *args):
        """Handle position changes"""
        self._trigger_layout()

    # ... (rest of the PlayerHand class implementation) 