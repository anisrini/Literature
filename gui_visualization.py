from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.modalview import ModalView
from kivy.graphics import Color, Rectangle, Line, Ellipse, RoundedRectangle
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import ObjectProperty, NumericProperty, ListProperty
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.core.text import Label as CoreLabel
from functools import partial
from kivy.metrics import dp
import math
from kivy.utils import get_color_from_hex
from kivy.core.audio import SoundLoader
from kivy.logger import Logger
import logging

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
    game_state = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        logger.info("Initializing Literature Game GUI")
        super().__init__(**kwargs)
        
        # Initialize game table first
        self.game_table = None
        Clock.schedule_once(self._init_widgets)
    
    def _init_widgets(self, dt):
        """Initialize all widgets after the base widget is ready"""
        logger.info('GUI: Initializing widgets')
        
        # Get game table reference
        self.game_table = self.ids.game_table
        if not self.game_table:
            logger.error('GUI: Could not find game table')
            return
            
        # Setup game table if game state exists
        if self.game_state:
            self.game_table.setup_game(self.game_state)
            
        # Add feedback widget
        self.feedback = GameFeedback()
        self.add_widget(self.feedback)
        
        # Initialize sounds
        self.load_sounds()
        
        # Start update loop
        Clock.schedule_interval(self.update, 1.0/60.0)
        logger.info('GUI: Widget initialization complete')

    def on_game_state(self, instance, value):
        """Called when game_state property changes"""
        logger.info('GUI: Game state updated')
        if self.game_table and value:
            self.game_table.setup_game(value)
    
    def load_sounds(self):
        """Load game sound effects"""
        self.card_transfer_sound = SoundLoader.load('assets/card_transfer.wav')
        self.set_declaration_sound = SoundLoader.load('assets/set_declaration.wav')
    
    def show_request_dialog(self):
        logger.info('GUI: Showing request dialog')
        if not self.game_state:
            logger.warning('GUI: Cannot show request dialog - no game state')
            return
        
        dialog = RequestDialog(
            game_state=self.game_state,
            current_player=self.game_state.current_turn
        )
        dialog.bind(on_dismiss=self.handle_request_result)
        dialog.open()
        logger.info('GUI: Request dialog opened')

    def handle_request_result(self, dialog):
        logger.info('GUI: Handling request dialog result')
        if hasattr(dialog, 'selected_player') and hasattr(dialog, 'selected_card'):
            if dialog.selected_player and dialog.selected_card:
                logger.info(f'GUI: Processing request - Player: {dialog.selected_player}, Card: {dialog.selected_card}')
                self.handle_card_request(
                    target_player=int(dialog.selected_player.split()[-1]) - 1,
                    card_str=dialog.selected_card
                )
            else:
                logger.warning('GUI: Incomplete selection in request dialog')
        else:
            logger.error('GUI: Invalid dialog state')

    def setup_game_table(self, dt=None):
        """Setup the game table with game state"""
        logger.info('GUI: Setting up game table')
        self.game_table = self.ids.game_table
        if not self.game_table:
            logger.error('GUI: Failed to get game_table from ids')
            return
        logger.info('GUI: Got game table reference')
        self.game_table.setup_game(self.game_state)
        logger.info('GUI: Completed game table setup')

    def update(self, dt):
        # Get score panel
        score_panel = self.ids.score_panel
        
        # Update scores and turn
        score_panel.team1_score.text = f'Team 1 Score: {self.game_state.team1_sets}'
        score_panel.team2_score.text = f'Team 2 Score: {self.game_state.team2_sets}'
        score_panel.current_turn.text = f'Current Turn: Player {self.game_state.current_turn + 1}'
        
        # Update only when current player changes
        if hasattr(self, 'game_table') and self.game_table.hands:
            current_player = self.game_state.current_turn
            if not hasattr(self, '_last_current_player') or self._last_current_player != current_player:
                self._last_current_player = current_player
                for hand in self.game_table.hands:
                    hand.is_current = (hand.player == self.game_state.players[current_player])
                    if hand.is_current != hand._last_is_current:  # Only layout if current state changed
                        hand._last_is_current = hand.is_current
                        hand.layout_cards()

    def handle_card_request(self, target_player, card_str):
        logger.info(f'GUI: Processing card request to Player {target_player + 1} for card {card_str}')
        try:
            requester = self.game_state.current_turn
            logger.info(f'GUI: Requester is Player {requester + 1}')
            
            # Find the requested card
            requested_card = None
            target_player_obj = self.game_state.players[target_player]
            for i, card in enumerate(target_player_obj.hand):
                if str(card) == card_str:
                    requested_card = card
                    logger.info(f'GUI: Found requested card at index {i}')
                    break
            
            if requested_card:
                logger.info('GUI: Processing card transfer')
                from_hand = self.game_table.hands[target_player]
                to_hand = self.game_table.hands[requester]
                
                success = self.game_state.handle_card_request(requester, target_player, requested_card)
                logger.info(f'GUI: Card request success: {success}')
                
                if success:
                    self.feedback.show_message(
                        "Card Transfer Successful!",
                        f"Player {requester + 1} received {card_str} from Player {target_player + 1}",
                        "success"
                    )
                    self.play_card_transfer_sound()
                    logger.info('GUI: Starting card transfer animation')
                    self.game_table.animate_card_transfer(
                        from_hand.cards[i], from_hand, to_hand
                    )
                else:
                    logger.warning('GUI: Card request failed')
                    self.feedback.show_message(
                        "Card Request Failed",
                        f"Player {target_player + 1} doesn't have {card_str}",
                        "error"
                    )
            else:
                logger.warning(f'GUI: Requested card {card_str} not found')
                self.feedback.show_message(
                    "Invalid Request",
                    "Selected card not found in player's hand",
                    "warning"
                )
                
        except Exception as e:
            logger.error(f'GUI: Error in card request: {str(e)}')
            self.feedback.show_message(
                "Error Processing Request",
                str(e),
                "error"
            )

    def play_card_transfer_sound(self):
        if self.card_transfer_sound:
            self.card_transfer_sound.play()

    def play_set_declaration_sound(self):
        if self.set_declaration_sound:
            self.set_declaration_sound.play()

    def handle_set_declaration(self, game_state):
        """Handle a set declaration attempt"""
        try:
            # Get the current player and their declaration
            current_player = self.game_state.current_turn
            current_player_obj = self.game_state.players[current_player]
            
            # Get the declared set and team assignments from the dialog
            declared_set = game_state.declared_set
            team_cards = game_state.team_card_assignments
            
            # Process the declaration
            success, winner = self.game_state.handle_set_declaration(
                current_player,
                declared_set,
                team_cards
            )
            
            # Show appropriate feedback
            if success:
                winner_text = f"Team {1 if current_player % 2 == 0 else 2}"
                self.feedback.show_message(
                    f"Set Declaration Successful!",
                    f"{winner_text} wins the {declared_set} set",
                    "declare"
                )
                self.play_set_declaration_sound()
            else:
                if winner == "No Winner":
                    self.feedback.show_message(
                        "Invalid Declaration",
                        "All cards were in your team. Set removed.",
                        "warning"
                    )
                else:
                    loser_team = 1 if current_player % 2 == 0 else 2
                    winner_team = 3 - loser_team  # If loser is 1, winner is 2 and vice versa
                    self.feedback.show_message(
                        "Declaration Failed",
                        f"Team {winner_team} wins the set!",
                        "error"
                    )
                    
        except Exception as e:
            self.feedback.show_message(
                "Error Processing Declaration",
                str(e),
                "error"
            )

    def on_size(self, *args):
        logger.debug(f"GUI resized to {self.size}")
        # ... existing resize code ...
        
    def on_touch_down(self, touch):
        logger.debug(f"Touch down event at {touch.pos}")
        # ... existing touch handling code ...
        
    def on_touch_up(self, touch):
        logger.debug(f"Touch up event at {touch.pos}")
        # ... existing touch handling code ...
        
    def update_game_state(self, game_state):
        logger.debug("Updating game state display")
        # ... existing update code ...
        
    def draw_cards(self, cards, position):
        logger.debug(f"Drawing cards at position {position}")
        # ... existing drawing code ...
        
    def handle_card_selection(self, card):
        logger.info(f"Card selected: {card}")
        # ... existing selection code ...
        
    def handle_player_action(self, action_type, *args):
        logger.info(f"Player action: {action_type}, args: {args}")
        # ... existing action handling code ...
        
    def show_error(self, message):
        logger.error(f"GUI Error: {message}")
        # ... existing error display code ...
        
    def show_message(self, message):
        logger.info(f"Displaying message: {message}")
        # ... existing message display code ...

class GameTable(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_state = None
        self.hands = []
        
        # Add persistent table background
        with self.canvas.before:
            Color(0.133, 0.545, 0.133, 1)  # Forest green
            self.table_bg = Rectangle(pos=self.pos, size=self.size)
            
            # Add border
            Color(0.855, 0.647, 0.125, 1)  # Golden
            self.table_border = Line(rectangle=self.pos + self.size, width=2)
        
        # Bind size and position updates
        self.bind(pos=self._update_canvas, size=self._update_canvas)
    
    def _update_canvas(self, *args):
        """Update canvas when size or position changes"""
        self.table_bg.pos = self.pos
        self.table_bg.size = self.size
        self.table_border.rectangle = [*self.pos, *self.size]

    def setup_game(self, game_state):
        logger.info(f'Table: Setting up game table with {len(game_state.players)} players')
        self.game_state = game_state
        Clock.schedule_once(lambda dt: self.setup_table())
    
    def setup_table(self, *args):
        if not self.game_state:
            logger.error('Table: Cannot setup table - no game state')
            return
            
        logger.info('Table: Beginning table setup')
        self.clear_widgets()
        self.hands = []
        
        # Calculate dimensions
        table_width = self.width * 0.8
        table_height = self.height * 0.8
        logger.info(f'Table: Table dimensions - Width: {table_width}, Height: {table_height}')

        # Position players around the table
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
        
        for i, player in enumerate(self.game_state.players):
            logger.info(f'Table: Setting up Player {i+1} hand')
            rel_x, rel_y = positions[i]
            x = self.pos[0] + (rel_x * table_width)
            y = self.pos[1] + (rel_y * table_height)
            logger.info(f'Table: Player {i+1} position - X: {x}, Y: {y}')
            
            is_current = (i == self.game_state.current_turn)
            hand = PlayerHand(
                player=player,
                is_current=is_current,
                pos=(x - dp(125), y - dp(75)),
                size=(dp(250), dp(150))
            )
            self.hands.append(hand)
            self.add_widget(hand)
            logger.info(f'Table: Added Player {i+1} hand with {len(player.hand)} cards')

    def animate_card_transfer(self, card_widget, from_hand, to_hand, on_complete=None):
        """Handle card transfer animation between hands"""
        # Remove card from source hand
        from_hand.remove_widget(card_widget)
        self.add_widget(card_widget)  # Add to table for animation
        
        # Calculate start and end positions
        start_pos = (
            from_hand.x + from_hand.cards.index(card_widget) * dp(30),
            from_hand.y
        )
        end_pos = (
            to_hand.x + len(to_hand.cards) * dp(30),
            to_hand.y
        )
        
        def transfer_complete(*args):
            self.remove_widget(card_widget)  # Remove from table
            to_hand.add_card(card_widget)    # Add to destination hand
            if on_complete:
                on_complete()
        
        # Start animation
        card_widget.animate_transfer(start_pos, end_pos, transfer_complete)

class Card(Scatter):
    def __init__(self, suit, rank, **kwargs):
        super().__init__(**kwargs)
        self.suit = suit
        self.rank = rank
        self.face_up = True
        self.is_current_player = False
        self.do_rotation = False
        self.do_scale = False
        
        # Card symbols
        self.symbols = {
            'Hearts': '♥', 
            'Diamonds': '♦',
            'Clubs': '♣', 
            'Spades': '♠'
        }
        
        # Bind position and size updates
        self.bind(pos=self._redraw, size=self._redraw)
        
        # Draw card immediately
        self.draw_card()
    
    def _redraw(self, *args):
        """Redraw card when position or size changes"""
        self.draw_card()
    
    def draw_card(self, dt=None):
        self.canvas.after.clear()
        with self.canvas.after:
            # Card background
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Card border
            Color(0.8, 0.8, 0.8, 1)  # Gray border
            Line(rectangle=[self.x, self.y, self.width, self.height], width=1.5)
            
            # Draw rank and suit
            Color(*(1, 0, 0, 1) if self.suit in ['Hearts', 'Diamonds'] else (0, 0, 0, 1))
            
            # Top left rank
            rank_label = CoreLabel(text=self.rank, font_size=dp(20))
            rank_label.refresh()
            Rectangle(texture=rank_label.texture, 
                     pos=(self.x + dp(10), self.y + self.height - dp(30)),
                     size=rank_label.texture.size)
            
            # Center suit (larger for better visibility)
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
            
            # Add highlight for current player's cards
            if self.is_current_player:
                Color(1, 1, 0, 0.2)  # Subtle yellow highlight
                Rectangle(pos=self.pos, size=self.size)
                Color(1, 1, 0, 0.8)  # Brighter yellow border
                Line(rectangle=[self.x, self.y, self.width, self.height], width=dp(2))

class PlayerHand(Widget):
    def __init__(self, player, is_current=False, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.cards = []
        self.is_current = is_current
        self._last_is_current = is_current
        self._layout_scheduled = False
        self._layout_trigger = Clock.create_trigger(self.layout_cards, 0)
        self.team_color = get_color_from_hex('#FFD700') if player.id % 2 == 0 else get_color_from_hex('#1E90FF')
        
        # Bind position and size updates
        self.bind(pos=self._trigger_layout, size=self._trigger_layout)
        
        # Draw background
        with self.canvas.before:
            Color(*self.team_color, 0.3)
            self.background = Rectangle(pos=self.pos, size=self.size)
            
            if is_current:
                Color(*self.team_color, 0.5)
                self.highlight = Rectangle(
                    pos=(self.pos[0] - dp(5), self.pos[1] - dp(5)),
                    size=(self.size[0] + dp(10), self.size[1] + dp(10))
                )
        
        # Schedule initial layout
        Clock.schedule_once(self.layout_cards)
    
    def _trigger_layout(self, *args):
        """Trigger a layout update using the clock trigger"""
        self._update_canvas(*args)
        self._layout_trigger()

    def _update_canvas(self, *args):
        """Update canvas when size or position changes"""
        self.background.pos = self.pos
        self.background.size = self.size
        if hasattr(self, 'highlight'):
            self.highlight.pos = (self.pos[0] - dp(5), self.pos[1] - dp(5))
            self.highlight.size = (self.size[0] + dp(10), self.size[1] + dp(10))
    
    def layout_cards(self, dt=None):
        if self._layout_scheduled:
            logger.info(f'Hand: Layout already scheduled for {self.player.name}')
            return
        self._layout_scheduled = True
        
        logger.info(f'Hand: Starting card layout for {self.player.name}')
        self.clear_widgets()
        self.cards = []
        
        if not self.player.hand:
            logger.info(f'Hand: No cards to layout for {self.player.name}')
            self._layout_scheduled = False
            return
        
        try:
            num_cards = len(self.player.hand)
            logger.info(f'Hand: Laying out {num_cards} cards for {self.player.name}')
            
            # Calculate layout with improved positioning
            card_width = dp(80)
            card_height = dp(112)
            overlap = dp(30)
            spacing = card_width - overlap
            
            # Calculate total width of all cards with overlap
            total_width = card_width + (num_cards - 1) * spacing
            
            # Calculate starting x position to center the cards within the hand widget
            # Account for the widget's padding and ensure cards stay within bounds
            padding = dp(10)
            available_width = self.width - (2 * padding)
            start_x = self.x + padding
            
            if total_width < available_width:
                # Center cards if they fit within the widget
                start_x += (available_width - total_width) / 2
            else:
                # Adjust overlap to fit cards within available width if needed
                spacing = (available_width - card_width) / (num_cards - 1) if num_cards > 1 else 0
            
            # Calculate vertical position with padding
            card_y = self.y + padding
            
            for i, card in enumerate(self.player.hand):
                logger.info(f'Hand: Creating card widget {i+1} for {self.player.name} - {card}')
                card_widget = Card(
                    suit=card.suit,
                    rank=str(card.rank),
                    size=(card_width, card_height),
                    pos=(start_x + i * spacing, card_y)
                )
                card_widget.is_current_player = self.is_current
                self.cards.append(card_widget)
                self.add_widget(card_widget)
                logger.info(f'Hand: Added card widget {i+1} to {self.player.name}\'s hand')
        except Exception as e:
            logger.error(f'Hand: Error laying out cards for {self.player.name}: {str(e)}')
        finally:
            self._layout_scheduled = False
            logger.info(f'Hand: Completed card layout for {self.player.name}')
    
    def add_card(self, card_widget):
        """Add a card to the hand"""
        if not self._layout_scheduled:
            self.cards.append(card_widget)
            self.add_widget(card_widget)
            self._layout_trigger()
    
    def remove_card(self, card_widget):
        """Remove a card from the hand"""
        if card_widget in self.cards and not self._layout_scheduled:
            self.cards.remove(card_widget)
            self.remove_widget(card_widget)
            self._layout_trigger()

class ScorePanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize the labels as object properties
        self.team1_score = Label(
            text='Team 1 Score: 0',
            size_hint_y=None,
            height=40
        )
        self.team2_score = Label(
            text='Team 2 Score: 0',
            size_hint_y=None,
            height=40
        )
        self.current_turn = Label(
            text='Current Turn: Player 1',
            size_hint_y=None,
            height=40
        )
        
        # Add the labels to the layout
        self.add_widget(self.team1_score)
        self.add_widget(self.team2_score)
        self.add_widget(self.current_turn)

class ActionButtons(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Store reference to parent GUI
        Clock.schedule_once(self._get_parent_gui)
    
    def _get_parent_gui(self, dt):
        # Find parent LiteratureGameGUI instance
        self.parent_gui = self.parent

    def request_card(self):
        """Show request dialog when button is pressed"""
        if hasattr(self, 'parent_gui'):
            self.parent_gui.show_request_dialog()

    def declare_set(self):
        """Show declare dialog when button is pressed"""
        if hasattr(self, 'parent_gui'):
            self.parent_gui.show_declare_dialog()

    def restart_game(self):
        """Restart the game"""
        if hasattr(self, 'parent_gui'):
            self.parent_gui.restart_game()

    def quit_game(self):
        """Quit the application"""
        App.get_running_app().stop()

class RequestDialog(ModalView):
    def __init__(self, game_state, current_player, **kwargs):
        super().__init__(**kwargs)
        self.selected_player = None
        self.selected_card = None
        self.size_hint = (0.8, 0.8)
        self.game_state = game_state
        self.current_player = current_player
        
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        # Get opponents
        opponents = [i for i in range(len(game_state.players)) 
                    if i % 2 != current_player % 2]
        self.player_dropdown = DropDown()
        for i in opponents:
            btn = Button(
                text=f'Player {i+1}',
                size_hint_y=None,
                height=dp(44)
            )
            btn.bind(on_release=lambda btn: self.select_player(btn.text))
            self.player_dropdown.add_widget(btn)
        
        # Get requestable cards
        current_player_obj = game_state.players[current_player]
        requestable_cards = []
        for card in current_player_obj.hand:
            if current_player_obj.has_root_card(card.get_set()):
                set_cards = card.get_set_cards()
                requestable_cards.extend([c for c in set_cards 
                                       if c not in current_player_obj.hand])
        
        self.card_dropdown = DropDown()
        for card in sorted(requestable_cards, key=lambda x: (x.get_set(), x.suit)):
            btn = Button(
                text=str(card),
                size_hint_y=None,
                height=dp(44)
            )
            btn.bind(on_release=lambda btn: self.select_card(btn.text))
            self.card_dropdown.add_widget(btn)
        
        # Add widgets to layout
        layout.add_widget(Label(text='Select Player to Request From:'))
        self.player_button = Button(text='Select Player')
        self.player_button.bind(on_release=self.player_dropdown.open)
        layout.add_widget(self.player_button)
        
        layout.add_widget(Label(text='Select Card to Request:'))
        self.card_button = Button(text='Select Card')
        self.card_button.bind(on_release=self.card_dropdown.open)
        layout.add_widget(self.card_button)
        
        confirm_button = Button(
            text='Confirm Request',
            size_hint_y=None,
            height=dp(50)
        )
        confirm_button.bind(on_release=self.confirm_request)
        layout.add_widget(confirm_button)
        
        self.add_widget(layout) 

    def select_player(self, player_text):
        self.selected_player = player_text
        self.player_button.text = player_text
        self.player_dropdown.dismiss()

    def select_card(self, card_text):
        self.selected_card = card_text
        self.card_button.text = card_text
        self.card_dropdown.dismiss()

    def confirm_request(self, *args):
        if self.selected_player and self.selected_card:
            self.dismiss()

class GameFeedback(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(400), dp(100))
        self.opacity = 0
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        
        # Create background
        with self.canvas.before:
            Color(0, 0, 0, 0.8)  # Semi-transparent black
            self.bg = Rectangle(pos=self.pos, size=self.size)
            
        # Main message label
        self.message_label = Label(
            text='',
            font_size=dp(20),
            size_hint_y=0.7,
            bold=True
        )
        self.add_widget(self.message_label)
        
        # Sub-message for additional info
        self.sub_message_label = Label(
            text='',
            font_size=dp(16),
            size_hint_y=0.3,
            color=(0.8, 0.8, 0.8, 1)  # Light gray
        )
        self.add_widget(self.sub_message_label)
        
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _update_rect(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size
    
    def show_message(self, message, sub_message="", message_type="info"):
        """Show feedback message with type-based styling"""
        self.message_label.text = message
        self.sub_message_label.text = sub_message
        
        # Color scheme based on message type
        colors = {
            "success": (0, 0.8, 0, 1),      # Green
            "error": (0.8, 0, 0, 1),        # Red
            "warning": (0.8, 0.6, 0, 1),    # Orange
            "info": (0, 0.6, 0.8, 1),       # Blue
            "transfer": (0.8, 0.8, 0, 1),   # Yellow
            "declare": (0.5, 0, 0.8, 1)     # Purple
        }
        
        # Update message color
        self.message_label.color = colors.get(message_type, colors["info"])
        
        # Create and start animation
        anim = (
            Animation(opacity=1, duration=0.3) +  # Fade in
            Animation(opacity=1, duration=2.0) +  # Stay visible
            Animation(opacity=0, duration=0.3)    # Fade out
        )
        anim.start(self) 