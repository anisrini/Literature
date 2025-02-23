from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.clock import Clock
# from kivy.core.audio import SoundLoader  # Comment out audio import
from kivy.properties import ObjectProperty
from literature_game.gui.components.game_table import GameTable
from literature_game.gui.components.ui_elements import ScorePanel, ActionButtons, GameFeedback
import logging
import os

logger = logging.getLogger(__name__)

# Define the UI in Kivy language
Builder.load_string('''
<LiteratureGameGUI>:
    canvas.before:
        Color:
            rgba: 0.2, 0.2, 0.2, 1  # Dark gray background
        Rectangle:
            pos: self.pos
            size: self.size
    
    GameTable:
        id: game_table
        size_hint: 0.8, 0.8
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
    
    BoxLayout:  # Score panel container
        orientation: 'vertical'
        size_hint: 0.2, 1
        pos_hint: {'x': 0}
        padding: dp(10)
        spacing: dp(10)
        
        ScorePanel:
            id: score_panel
            size_hint_y: 0.3
    
    BoxLayout:  # Action buttons container
        orientation: 'vertical'
        size_hint: 0.2, 1
        pos_hint: {'right': 1}
        padding: dp(10)
        spacing: dp(10)
        
        ActionButtons:
            id: action_buttons
            size_hint_y: 0.3
''')

class LiteratureGameGUI(FloatLayout):
    game_state = ObjectProperty(None)  # Use Kivy property for proper binding
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info("Initializing Literature Game GUI")
        self._update_scheduled = False  # Add flag to prevent multiple updates
        self._init_widgets()
        
        # Reduce update frequency to 10 FPS (was 30)
        Clock.schedule_interval(self.update_game_state, 1.0/10.0)
    
    def _init_widgets(self):
        """Initialize all widgets"""
        logger.info('GUI: Initializing widgets')
        
        try:
            # Initialize feedback widget
            self.feedback = GameFeedback()
            self.add_widget(self.feedback)
            
            # Comment out sound initialization
            # self.load_sounds()
            
        except Exception as e:
            logger.error(f"Error initializing widgets: {str(e)}")
            # Continue even if sound loading fails
    
    # Comment out sound-related methods
    # """
    # def load_sounds(self):
    #     """Load game sound effects"""
    #     logger.info("Loading game sounds")
    #     try:
    #         sound_files = {
    #             'card_transfer': 'assets/card_transfer.wav',
    #             'set_declaration': 'assets/set_declaration.wav'
    #         }
            
    #         for sound_name, sound_path in sound_files.items():
    #             if os.path.exists(sound_path):
    #                 self.sounds[sound_name] = SoundLoader.load(sound_path)
    #                 logger.debug(f"Loaded sound: {sound_name}")
    #             else:
    #                 logger.warning(f"Sound file not found: {sound_path}")
            
    #     except Exception as e:
    #         logger.error(f"Error loading sounds: {str(e)}")
    #         # Continue without sounds if loading fails
    
    # def play_sound(self, sound_name):
    #     """Play a sound by name"""
    #     try:
    #         if sound_name in self.sounds and self.sounds[sound_name]:
    #             self.sounds[sound_name].play()
    #             logger.debug(f"Playing sound: {sound_name}")
    #     except Exception as e:
    #         logger.error(f"Error playing sound {sound_name}: {str(e)}")
    # """
    
    def on_game_state(self, instance, value):
        """Called when game_state property changes"""
        logger.info('GUI: Game state updated')
        if value:  # If we have a valid game state
            # Update the game table
            if hasattr(self.ids, 'game_table'):
                self.ids.game_table.setup_game(value)
            
            # Update score panel
            if hasattr(self.ids, 'score_panel'):
                self.ids.score_panel.game_state = value
                self.ids.score_panel.update_scores(value)
    
    def update_game_state(self, dt):
        """Regular update of game state display"""
        if self._update_scheduled or not self.game_state:
            return
        
        try:
            self._update_scheduled = True
            
            # Validate game state
            if not hasattr(self.game_state, 'players') or not self.game_state.players:
                logger.error("Invalid game state detected")
                return
                
            # Verify all components exist
            if not all(hasattr(self.ids, attr) for attr in ['game_table', 'score_panel']):
                logger.error("Missing required UI components")
                return
            
            self.update_score_panel()
            self.update_game_table()
            
        except Exception as e:
            logger.error(f"Error in game state update: {str(e)}")
        finally:
            self._update_scheduled = False
    
    def update_score_panel(self):
        """Update the score panel with current game state"""
        if hasattr(self.ids, 'score_panel') and self.game_state:
            self.ids.score_panel.update_scores(self.game_state)
    
    def update_game_table(self):
        """Update the game table display"""
        try:
            if hasattr(self.ids, 'game_table'):
                self.ids.game_table.update(self.game_state)
        except Exception as e:
            logger.error(f"Error updating game table: {str(e)}") 