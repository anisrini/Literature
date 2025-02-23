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
        self._setup_in_progress = False
        self.bind(pos=self._update_positions, size=self._update_positions)
    
    def _update_positions(self, *args):
        """Update positions of all hands when table size/position changes"""
        if not self.hands or not self.game_state:
            return
            
        try:
            positions = self._calculate_player_positions(len(self.game_state.players))
            for i, hand in enumerate(self.hands):
                rel_x, rel_y = positions[i]
                hand.pos = (
                    self.pos[0] + (rel_x * self.width) - hand.width/2,
                    self.pos[1] + (rel_y * self.height) - hand.height/2
                )
        except Exception as e:
            logger.error(f"Error updating positions: {str(e)}")
    
    def setup_game(self, game_state):
        """Initialize the game table with the given game state"""
        if self._setup_in_progress or game_state == self.game_state:
            logger.debug("Setup already in progress or same game state")
            return
        
        try:
            self._setup_in_progress = True
            logger.info("Starting game table setup")
            
            # Store old positions if they exist
            old_positions = {}
            if self.hands:
                for hand in self.hands:
                    old_positions[hand.player.id] = hand.pos
            
            self.game_state = game_state
            self.clear_widgets()
            self.hands = []
            
            # Calculate positions for each player's hand
            num_players = len(game_state.players)
            positions = self._calculate_player_positions(num_players)
            
            # Create and position player hands
            for i, player in enumerate(game_state.players):
                is_current = (i == game_state.current_turn)
                
                hand = PlayerHand(
                    player=player,
                    is_current=is_current,
                    size=(dp(250), dp(150))
                )
                
                # Position the hand
                if player.id in old_positions:
                    hand.pos = old_positions[player.id]
                else:
                    rel_x, rel_y = positions[i]
                    hand.pos = (
                        self.pos[0] + (rel_x * self.width) - hand.width/2,
                        self.pos[1] + (rel_y * self.height) - hand.height/2
                    )
                
                self.hands.append(hand)
                self.add_widget(hand)
                
                # Force initial layout
                hand.force_layout(0)
            
            logger.info(f"Game table setup complete with {len(self.hands)} hands")
            
        except Exception as e:
            logger.error(f"Error during game table setup: {str(e)}")
        finally:
            self._setup_in_progress = False
    
    def _calculate_player_positions(self, num_players):
        """Calculate relative positions for player hands around the table"""
        positions = [
            (0.5, 0.95),    # Top
            (0.85, 0.85),   # Top right
            (0.95, 0.5),    # Right
            (0.85, 0.15),   # Bottom right
            (0.5, 0.05),    # Bottom
            (0.15, 0.15),   # Bottom left
            (0.05, 0.5),    # Left
            (0.15, 0.85),   # Top left
        ]
        return positions[:num_players]
    
    def update(self, game_state):
        """Update the game table display with current game state"""
        try:
            if not game_state:
                return
                
            if game_state != self.game_state:
                self.setup_game(game_state)
            else:
                # Update hands to match game state
                for i, hand in enumerate(self.hands):
                    if not hand.player:
                        continue
                    
                    # Update current state
                    current_state = (i == game_state.current_turn)
                    if hand.is_current != current_state:
                        hand.is_current = current_state
                    
                    # Force layout if card count changed
                    if len(hand.cards) != len(hand.player.hand):
                        hand.force_layout(0)
                        
        except Exception as e:
            logger.error(f"Error during game table update: {str(e)}")

    # ... (GameTable implementation) 