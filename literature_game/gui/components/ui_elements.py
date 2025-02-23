from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty
import logging

logger = logging.getLogger(__name__)

class ScorePanel(BoxLayout):
    """Displays game scores and current turn information"""
    game_state = ObjectProperty(None)
    team1_score_text = StringProperty('Team 1 Score: 0')
    team2_score_text = StringProperty('Team 2 Score: 0')
    current_turn_text = StringProperty('Current Turn: Player 1')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(5)
        
        # Create score labels
        self.team1_score = Label(
            text=self.team1_score_text,
            size_hint_y=None,
            height=dp(30)
        )
        self.team2_score = Label(
            text=self.team2_score_text,
            size_hint_y=None,
            height=dp(30)
        )
        self.current_turn = Label(
            text=self.current_turn_text,
            size_hint_y=None,
            height=dp(30)
        )
        
        # Add labels to the panel
        self.add_widget(self.team1_score)
        self.add_widget(self.team2_score)
        self.add_widget(self.current_turn)
        
        # Bind property changes
        self.bind(
            team1_score_text=self.team1_score.setter('text'),
            team2_score_text=self.team2_score.setter('text'),
            current_turn_text=self.current_turn.setter('text')
        )
    
    def on_game_state(self, instance, value):
        """Update when game state changes"""
        if value:
            self.update_scores(value)
            
    def update_scores(self, game_state):
        """Update score display from game state"""
        if not game_state:
            return
            
        self.team1_score_text = f'Team 1 Score: {game_state.team1_sets}'
        self.team2_score_text = f'Team 2 Score: {game_state.team2_sets}'
        self.current_turn_text = f'Current Turn: Player {game_state.current_turn + 1}'

class ActionButtons(BoxLayout):
    """Provides buttons for game actions"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(5)
        
        # Create action buttons
        request_button = Button(
            text='Request Card',
            size_hint_y=None,
            height=dp(40)
        )
        declare_button = Button(
            text='Declare Set',
            size_hint_y=None,
            height=dp(40)
        )
        
        # Add buttons to the layout
        self.add_widget(request_button)
        self.add_widget(declare_button)

class RequestDialog(ModalView):
    """Dialog for requesting cards from other players"""
    # ... (RequestDialog implementation)

class GameFeedback(BoxLayout):
    """Displays game feedback messages with animations"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (dp(400), dp(100))
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.opacity = 0
        
        # Create message labels
        self.message = Label(
            text='',
            size_hint_y=0.7
        )
        self.sub_message = Label(
            text='',
            size_hint_y=0.3
        )
        
        # Add labels to the layout
        self.add_widget(self.message)
        self.add_widget(self.sub_message)
    
    def show_message(self, text, sub_text='', duration=2.0):
        """Show a message with animation"""
        self.message.text = text
        self.sub_message.text = sub_text
        
        # Create fade animation
        anim = (Animation(opacity=1, duration=0.3) + 
                Animation(opacity=1, duration=duration) +
                Animation(opacity=0, duration=0.3))
        anim.start(self) 