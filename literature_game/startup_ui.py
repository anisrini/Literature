from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import NumericProperty
import logging

logger = logging.getLogger(__name__)

Builder.load_string('''
<StartupUI>:
    canvas.before:
        Color:
            rgba: 0.2, 0.2, 0.2, 1  # Dark gray background
        Rectangle:
            pos: self.pos
            size: self.size
    
    BoxLayout:
        orientation: 'vertical'
        size_hint: 0.6, 0.6
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        spacing: dp(20)
        padding: dp(30)
        
        Label:
            text: 'Literature Card Game'
            font_size: dp(32)
            size_hint_y: 0.3
        
        Label:
            text: 'Select Number of Players'
            font_size: dp(24)
            size_hint_y: 0.2
        
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.2
            spacing: dp(20)
            
            ToggleButton:
                text: '6 Players'
                group: 'players'
                size_hint_x: 0.5
                state: 'down' if root.selected_players == 6 else 'normal'
                on_press: root.selected_players = 6
            
            ToggleButton:
                text: '8 Players'
                group: 'players'
                size_hint_x: 0.5
                state: 'down' if root.selected_players == 8 else 'normal'
                on_press: root.selected_players = 8
        
        Button:
            text: 'Start Game'
            size_hint_y: 0.2
            disabled: not root.selected_players
            on_release: root.start_game()
            
        Button:
            text: 'Quit'
            size_hint_y: 0.2
            on_release: root.quit_game()
''')

class StartupUI(FloatLayout):
    selected_players = NumericProperty(0)  # 0 means no selection
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        logger.info("StartupUI initialized")
    
    def start_game(self):
        if self.app and self.selected_players:
            logger.info(f"Starting game with {self.selected_players} players")
            self.app.start_game(self.selected_players)
    
    def quit_game(self):
        if self.app:
            logger.info("Quitting game")
            self.app.stop() 