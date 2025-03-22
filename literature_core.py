"""
Literature Card Game - Core Version
A simplified card game implementation with reliable initialization
"""
import os
import random
import logging
import time
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from functools import partial
from kivy.graphics import Color, Rectangle

# Basic logging configuration - writes to console for immediate feedback
logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

# ===================== CARD IMAGE UTILITIES =====================

def get_card_image_path(card):
    """Get the path to a card image"""
    suit = card.suit.lower()
    rank = card.rank.lower()
    
    # Convert 10 to 10, but A to a, K to k, etc.
    if rank not in ['10']:
        rank = rank.lower()
    
    base_path = os.path.join('assets', 'cards')
    image_path = os.path.join(base_path, f"{suit}_{rank}.png")
    
    # Check if the image exists
    if os.path.exists(image_path):
        return image_path
    
    # Fallback to a default card image
    default_path = os.path.join(base_path, "card_back.png")
    if os.path.exists(default_path):
        return default_path
    
    # If no images available, return None and we'll use text instead
    return None

def ensure_card_images():
    """Make sure we have at least some basic card images available"""
    base_path = os.path.join('assets', 'cards')
    os.makedirs(base_path, exist_ok=True)
    
    # Create a simple card back image if it doesn't exist
    card_back_path = os.path.join(base_path, "card_back.png")
    if not os.path.exists(card_back_path):
        log.info(f"Creating basic card back image at {card_back_path}")
        from PIL import Image, ImageDraw
        
        try:
            # Create a simple blue card back
            img = Image.new('RGB', (100, 140), color=(30, 60, 180))
            d = ImageDraw.Draw(img)
            d.rectangle([(5, 5), (95, 135)], outline=(255, 255, 255), width=2)
            img.save(card_back_path)
        except Exception as e:
            log.error(f"Failed to create card back image: {e}")
    
    # Check and log which card images are available
    found_images = 0
    for suit in Card.SUITS:
        for rank in Card.RANKS:
            card = Card(suit, rank)
            if get_card_image_path(card) and get_card_image_path(card) != card_back_path:
                found_images += 1
    
    log.info(f"Found {found_images} card images out of 52 possible cards")

# ===================== GAME CLASSES =====================

class Card:
    """A simple playing card"""
    SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
    
    def __str__(self):
        return f"{self.rank} of {self.suit}"
    
    def get_family(self):
        """Get the card family (used for Literature game rules)"""
        # In Literature, cards are grouped as:
        # Low: A-7
        # High: 8-K
        if self.rank in ['A', '2', '3', '4', '5', '6', '7']:
            return f"Low {self.suit}"
        else:
            return f"High {self.suit}"

class CardWidget(BoxLayout):
    """Widget to display a card with image or text fallback"""
    def __init__(self, card, **kwargs):
        super().__init__(**kwargs)
        self.card = card
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (100, 150)
        self.padding = 5
        
        # Try to load card image
        image_path = get_card_image_path(card)
        
        if image_path:
            # We have an image, show that
            self.image = Image(source=image_path, size_hint=(1, 0.9))
            self.add_widget(self.image)
            
            # Add small label below
            self.label = Label(
                text=str(card),
                size_hint=(1, 0.1),
                font_size='10sp',
                color=(0.9, 0.9, 0.9, 0.7)
            )
            self.add_widget(self.label)
        else:
            # No image, use text-based display
            self.label = Label(
                text=str(card),
                size_hint=(1, 1),
                font_size='14sp'
            )
            
            # Add color based on suit
            if card.suit == 'Hearts' or card.suit == 'Diamonds':
                self.label.color = (0.8, 0.1, 0.1, 1)  # Red for hearts/diamonds
            else:
                self.label.color = (0.1, 0.1, 0.1, 1)  # Black for clubs/spades
                
            self.add_widget(self.label)

class Player:
    """A player with a hand of cards"""
    def __init__(self, name, is_bot=True, team=0):
        self.name = name
        self.hand = []
        self.is_bot = is_bot
        self.team = team  # 0 for first team, 1 for second team
        
    def add_card(self, card):
        self.hand.append(card)
        
    def remove_card(self, suit, rank):
        """Remove a card from player's hand if it exists"""
        for i, card in enumerate(self.hand):
            if card.suit == suit and card.rank == rank:
                return self.hand.pop(i)
        return None
    
    def has_card(self, suit, rank):
        """Check if player has the specified card"""
        for card in self.hand:
            if card.suit == suit and card.rank == rank:
                return True
        return False
    
    def has_card_of_family(self, family):
        """Check if player has any card of a specific family"""
        for card in self.hand:
            if card.get_family() == family:
                return True
        return False

class Bot(Player):
    """AI player that makes automatic moves"""
    def __init__(self, name, team=0):
        super().__init__(name, is_bot=True, team=team)
    
    def take_turn(self, game):
        """Bot takes its turn automatically"""
        log.info(f"Bot {self.name} is taking its turn")
        
        # Simple strategy: randomly ask another player for a card the bot has
        if not self.hand:
            log.info(f"Bot {self.name} has no cards, skipping turn")
            return False
            
        # Choose a random card from hand
        card = random.choice(self.hand)
        
        # Choose a random player from the other team
        other_team = 1 if self.team == 0 else 0
        other_team_players = [p for p in game.players if p.team == other_team]
        
        if not other_team_players:
            return False
            
        target_player = random.choice(other_team_players)
        
        log.info(f"Bot {self.name} asks {target_player.name} for {card}")
        
        # Check if target has the card
        if target_player.has_card(card.suit, card.rank):
            # Success! Get the card
            target_card = target_player.remove_card(card.suit, card.rank)
            if target_card:
                self.add_card(target_card)
                log.info(f"Bot {self.name} got {target_card} from {target_player.name}")
                return True
        
        log.info(f"{target_player.name} doesn't have that card")
        return False

class Game:
    """Core game logic"""
    def __init__(self, num_players=6, human_player_idx=0):
        log.info(f"Creating new game with {num_players} players (human is player {human_player_idx+1})")
        
        # Create players - one human, rest bots, split into teams
        self.players = []
        half = num_players // 2
        
        for i in range(num_players):
            team = 0 if i < half else 1
            if i == human_player_idx:
                self.players.append(Player(f"Player {i+1} (You)", is_bot=False, team=team))
            else:
                self.players.append(Bot(f"Bot {i+1}", team=team))
                
        self.human_player_idx = human_player_idx
        self.current_player_idx = 0
        
        # Team names
        self.team_names = ["Team A", "Team B"]
        
        # Create and deal cards
        self.create_deck()
        self.deal_cards()
        
        # Game state
        self.game_message = "Game started. It's your turn!"
        self.selected_card = None
        
        # Print game setup info
        for player in self.players:
            log.info(f"{player.name} has {len(player.hand)} cards (Team {player.team+1})")
            card_list = ", ".join(str(card) for card in player.hand)
            log.info(f"  Cards: {card_list}")
    
    def create_deck(self):
        """Create a standard deck of cards"""
        self.deck = []
        for suit in Card.SUITS:
            for rank in Card.RANKS:
                self.deck.append(Card(suit, rank))
        
        random.shuffle(self.deck)
        log.info(f"Created and shuffled deck with {len(self.deck)} cards")
    
    def deal_cards(self):
        """Deal cards to all players"""
        cards_per_player = 6 if len(self.players) == 8 else 8
        log.info(f"Dealing {cards_per_player} cards per player")
        
        for _ in range(cards_per_player):
            for player in self.players:
                if self.deck:
                    card = self.deck.pop()
                    player.add_card(card)
                    log.info(f"Dealt {card} to {player.name}")
    
    @property
    def current_player(self):
        return self.players[self.current_player_idx]
    
    @property
    def human_player(self):
        return self.players[self.human_player_idx]
    
    def can_request_from_player(self, from_player, to_player):
        """Check if a player can request from another player"""
        # Players must be on different teams
        return from_player.team != to_player.team
    
    def can_request_card(self, player, suit, rank):
        """Check if a player can request a specific card"""
        # Player must have at least one card of the same family
        requested_card = Card(suit, rank)
        requested_family = requested_card.get_family()
        
        # Player must not already have the card
        if player.has_card(suit, rank):
            return False
            
        # Player must have at least one card from the same family
        return player.has_card_of_family(requested_family)
    
    def next_player(self):
        """Move to the next player and handle bot turns"""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        current = self.current_player
        log.info(f"Turn passed to {current.name} (Team {current.team+1})")
        
        # If it's a bot's turn, automatically play it
        if current.is_bot:
            self.game_message = f"{current.name} is thinking..."
            return current
        else:
            self.game_message = "It's your turn! Ask for a card or make a declaration."
            return current
    
    def handle_bot_turn(self):
        """Let the current bot player take its turn"""
        if not self.current_player.is_bot:
            return False
        
        log.info(f"Bot {self.current_player.name} is taking its turn")
        self.game_message = f"{self.current_player.name} is thinking..."
        
        # Clear message after a delay
        time.sleep(0.5)  # Small delay to simulate thinking
        
        # Let the bot take its turn
        result = self.current_player.take_turn(self)
        
        # Update game message with the result
        if result:
            self.game_message = f"{self.current_player.name} successfully got a card!"
        else:
            self.game_message = f"{self.current_player.name} didn't get a card."
        
        return result

    def request_card(self, target_player_idx, suit, rank):
        """Human player requests a card from another player"""
        # Verify it's the human's turn
        if self.current_player_idx != self.human_player_idx:
            self.game_message = "It's not your turn!"
            return False
        
        human = self.human_player
        target = self.players[target_player_idx]
        
        # Verify the target is valid (different team)
        if not self.can_request_from_player(human, target):
            self.game_message = f"You can only request cards from the other team!"
            return False
        
        # Verify the card request is valid (same family, don't have it)
        if not self.can_request_card(human, suit, rank):
            self.game_message = f"You can only request cards from families you already have!"
            return False
        
        log.info(f"{human.name} asks {target.name} for {rank} of {suit}")
        
        # Check if target has the card
        if target.has_card(suit, rank):
            # Success! Get the card
            card = target.remove_card(suit, rank)
            if card:
                human.add_card(card)
                self.game_message = f"Success! You got {card} from {target.name}"
                return True
        
        self.game_message = f"{target.name} doesn't have that card"
        self.next_player()  # Move to next player after failed request
        return False

    def make_declaration(self, family):
        """Make a declaration for a complete family of cards"""
        # TODO: Implement in a future update
        pass

# ===================== UI SCREENS =====================

class CardSelectionPopup(Popup):
    """Popup for selecting a card to request"""
    def __init__(self, target_player, callback, **kwargs):
        super().__init__(**kwargs)
        self.title = f"Select Card to Request from {target_player.name}"
        self.size_hint = (0.8, 0.8)
        
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Instructions
        instructions = Label(
            text="Select a card to request. You can only request cards\n"
                 "from families you already have but don't have this specific card.",
            size_hint_y=0.2
        )
        layout.add_widget(instructions)
        
        # Card options grouped by family
        scroll = ScrollView()
        self.cards_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.cards_grid.bind(minimum_height=self.cards_grid.setter('height'))
        
        # Group cards by family
        families = {}
        for suit in Card.SUITS:
            for prefix in ["Low", "High"]:
                family = f"{prefix} {suit}"
                families[family] = []
                
                ranks = ['A', '2', '3', '4', '5', '6', '7'] if prefix == "Low" else ['8', '9', '10', 'J', 'Q', 'K']
                for rank in ranks:
                    families[family].append((suit, rank))
        
        # Add family sections
        app = App.get_running_app()
        human_player = app.game.human_player
        
        for family, cards in families.items():
            # Only show families the player has at least one card from
            if human_player.has_card_of_family(family):
                # Add family header
                family_box = BoxLayout(orientation='vertical', size_hint_y=None, height=200)
                
                header = Label(
                    text=family,
                    font_size=18,
                    size_hint_y=0.2,
                    bold=True
                )
                family_box.add_widget(header)
                
                # Add card grid for this family
                card_grid = GridLayout(cols=4, spacing=5)
                
                for suit, rank in cards:
                    # Skip cards the player already has
                    if human_player.has_card(suit, rank):
                        card_btn = Button(
                            text=f"{rank} of {suit}\n(You have it)",
                            disabled=True,
                            background_color=(0.7, 0.7, 0.7, 1)
                        )
                    else:
                        card_btn = Button(
                            text=f"{rank} of {suit}",
                            background_color=(0.9, 0.9, 1, 1)
                        )
                        card_btn.bind(on_release=partial(callback, suit, rank))
                    
                    card_grid.add_widget(card_btn)
                
                family_box.add_widget(card_grid)
                self.cards_grid.add_widget(family_box)
        
        scroll.add_widget(self.cards_grid)
        layout.add_widget(scroll)
        
        # Cancel button
        cancel_btn = Button(
            text="Cancel",
            size_hint_y=0.1,
            background_color=(0.7, 0.3, 0.3, 1)
        )
        cancel_btn.bind(on_release=self.dismiss)
        layout.add_widget(cancel_btn)
        
        self.content = layout

class MainMenuScreen(Screen):
    """Main menu with game options"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Title
        layout.add_widget(Label(
            text="Literature Card Game",
            font_size=32
        ))
        
        # Status label
        self.status = Label(
            text="Welcome! Select an option to begin.",
            font_size=18
        )
        layout.add_widget(self.status)
        
        # Game options
        game6_btn = Button(
            text="Start 6-Player Game",
            size_hint_y=None,
            height=60,
            background_color=(0.2, 0.8, 0.2, 1)
        )
        game6_btn.bind(on_release=lambda x: self.start_game(6))
        layout.add_widget(game6_btn)
        
        game8_btn = Button(
            text="Start 8-Player Game",
            size_hint_y=None,
            height=60,
            background_color=(0.2, 0.8, 0.2, 1)
        )
        game8_btn.bind(on_release=lambda x: self.start_game(8))
        layout.add_widget(game8_btn)
        
        # Exit button
        exit_btn = Button(
            text="Exit Game",
            size_hint_y=None,
            height=60,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        exit_btn.bind(on_release=self.exit_game)
        layout.add_widget(exit_btn)
        
        self.add_widget(layout)
    
    def start_game(self, player_count):
        """Start a new game with the specified number of players"""
        self.status.text = f"Creating {player_count}-player game..."
        
        try:
            # Create new game via the App instance
            app = App.get_running_app()
            success = app.create_game(player_count)
            
            if success:
                self.status.text = "Game created successfully!"
                app.root.current = 'game'
            else:
                self.status.text = "Failed to create game"
        except Exception as e:
            self.status.text = f"Error creating game: {str(e)}"
            log.error(f"Game creation error: {e}")
            return False
    
    def show_error(self, message):
        """Display an error message"""
        self.status.text = message
    
    def exit_game(self, instance):
        App.get_running_app().stop()

class GamePlayScreen(Screen):
    """Game play screen showing cards and controls"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # Game message
        self.game_message = Label(
            text="Waiting for game to start...",
            font_size=18,
            size_hint_y=0.1
        )
        layout.add_widget(self.game_message)
        
        # Player info header
        self.player_info = Label(
            text="Waiting for game to start...",
            font_size=24,
            size_hint_y=0.1
        )
        layout.add_widget(self.player_info)
        
        # Team info
        self.team_info = Label(
            text="Teams: Team A vs Team B",
            font_size=18,
            size_hint_y=0.05
        )
        layout.add_widget(self.team_info)
        
        # Players area
        players_label = Label(
            text="All Players:",
            font_size=18,
            size_hint_y=0.05
        )
        layout.add_widget(players_label)
        
        self.players_grid = GridLayout(
            cols=3,
            spacing=5,
            padding=5,
            size_hint_y=0.2
        )
        layout.add_widget(self.players_grid)
        
        # Cards area
        cards_label = Label(
            text="Your Cards:",
            font_size=18,
            size_hint_y=0.05
        )
        layout.add_widget(cards_label)
        
        self.cards_grid = GridLayout(
            cols=4,
            spacing=10,
            padding=5,
            size_hint_y=0.3
        )
        layout.add_widget(self.cards_grid)
        
        # Control buttons
        controls = BoxLayout(
            orientation='horizontal',
            spacing=15,
            size_hint_y=0.2
        )
        
        next_btn = Button(
            text="Next Player",
            background_color=(0.2, 0.7, 0.2, 1)
        )
        next_btn.bind(on_release=self.next_player)
        controls.add_widget(next_btn)
        
        menu_btn = Button(
            text="Back to Menu",
            background_color=(0.7, 0.2, 0.2, 1)
        )
        menu_btn.bind(on_release=self.return_to_menu)
        controls.add_widget(menu_btn)
        
        layout.add_widget(controls)
        
        # Set auto-play to False initially - will require manual advancement
        self.auto_play = False
        
        # Add the bot control panel
        self.bot_controls = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10, padding=10)
        
        # Add a play/pause button
        self.play_pause_btn = Button(
            text="Auto Play: OFF", 
            background_color=(0.8, 0.4, 0.4, 1),
            size_hint_x=0.5
        )
        self.play_pause_btn.bind(on_release=self.toggle_auto_play)
        self.bot_controls.add_widget(self.play_pause_btn)
        
        # Add a "Next Bot Turn" button for manual control
        self.next_bot_btn = Button(
            text="Process Next Bot Turn",
            background_color=(0.4, 0.8, 0.4, 1),
            size_hint_x=0.5
        )
        self.next_bot_btn.bind(on_release=self.process_single_bot_turn)
        self.bot_controls.add_widget(self.next_bot_btn)
        
        # Add this to the main layout
        layout.add_widget(self.bot_controls)
        
        # Start with slower interval
        self.bot_turn_delay = 5.0  # 5 seconds between bot turns
        Clock.schedule_interval(self.process_bot_turns, self.bot_turn_delay)
        
        self.add_widget(layout)
    
    def toggle_auto_play(self, instance):
        """Toggle automatic bot turn processing"""
        self.auto_play = not self.auto_play
        if self.auto_play:
            self.play_pause_btn.text = "Auto Play: ON"
            self.play_pause_btn.background_color = (0.4, 0.8, 0.4, 1)  # Green
        else:
            self.play_pause_btn.text = "Auto Play: OFF"
            self.play_pause_btn.background_color = (0.8, 0.4, 0.4, 1)  # Red
        
        # Update the game message
        app = App.get_running_app()
        if app.game:
            if self.auto_play:
                app.game.game_message = "Auto play enabled: bots will play automatically"
            else:
                app.game.game_message = "Manual mode: click 'Process Next Bot Turn' to advance"
            self.game_message.text = app.game.game_message
    
    def process_single_bot_turn(self, instance):
        """Process a single bot turn when clicked"""
        app = App.get_running_app()
        if not app.game:
            return
        
        if app.game.current_player.is_bot:
            # Show thinking message
            app.game.game_message = f"{app.game.current_player.name} is thinking..."
            self.game_message.text = app.game.game_message
            self.update_display()
            
            # Schedule the actual bot turn with a slight delay to show the thinking
            Clock.schedule_once(lambda dt: self.execute_bot_turn(), 1.0)
        else:
            app.game.game_message = "It's your turn! Select a player to request a card."
            self.game_message.text = app.game.game_message
    
    def execute_bot_turn(self):
        """Execute the actual bot turn after the thinking delay"""
        app = App.get_running_app()
        if not app.game or not app.game.current_player.is_bot:
            return
        
        # Handle bot turn
        result = app.game.handle_bot_turn()
        self.update_display()
        
        # Schedule moving to next player with a longer delay
        Clock.schedule_once(lambda dt: self.next_player(None), 3.0)  # 3 seconds to see the result
    
    def process_bot_turns(self, dt):
        """Process bot turns automatically on a timer"""
        app = App.get_running_app()
        if not app.game or not self.auto_play:
            return
        
        if app.game.current_player.is_bot:
            self.process_single_bot_turn(None)
    
    def update_display(self):
        """Update display with current game state"""
        app = App.get_running_app()
        
        if not app.game:
            self.player_info.text = "No active game!"
            return False
        
        # Update game message
        self.game_message.text = app.game.game_message
        
        # Update current player info
        human = app.game.human_player
        current = app.game.current_player
        self.player_info.text = f"Current Player: {current.name} ({len(current.hand)} cards)"
        
        # Update team info
        self.team_info.text = f"Teams: {app.game.team_names[0]} vs {app.game.team_names[1]}"
        
        # Clear and update cards grid (only show human player's cards)
        self.cards_grid.clear_widgets()
        
        # Sort cards by suit and rank for easier viewing
        sorted_cards = sorted(human.hand, key=lambda c: (c.suit, Card.RANKS.index(c.rank)))
        
        for card in sorted_cards:
            card_widget = CardWidget(card)
            self.cards_grid.add_widget(card_widget)
        
        # Update players grid
        self.players_grid.clear_widgets()
        for i, player in enumerate(app.game.players):
            # Set button colors based on team and current player
            if player.team == 0:
                bg_color = (0.2, 0.5, 0.8, 1)  # Blue for team A
            else:
                bg_color = (0.8, 0.2, 0.2, 1)  # Red for team B
                
            if player == current:
                # Highlight current player
                bg_color = (0.2, 0.8, 0.2, 1)  # Green for current player
                
            if not player.is_bot:
                # Highlight human player
                bg_color = (0.5, 0.5, 0.9, 1)  # Light blue for human
            
            player_btn = Button(
                text=f"{player.name}\n{len(player.hand)} cards\nTeam {player.team+1}",
                background_color=bg_color
            )
            
            # Only allow selecting players on the other team when it's human's turn
            can_select = (current == human and 
                         player != human and 
                         app.game.can_request_from_player(human, player))
                         
            if can_select:
                player_btn.bind(on_release=lambda btn, idx=i: self.select_player(idx))
            else:
                player_btn.disabled = True
                
            self.players_grid.add_widget(player_btn)
        
        log.info(f"Updated display for {human.name}")
        return True
    
    def select_player(self, player_idx):
        """Handle player selection for card requests"""
        app = App.get_running_app()
        if not app.game:
            return
            
        # Only allow human player to select on their turn
        if app.game.current_player.is_bot:
            self.game_message.text = "It's not your turn!"
            return
            
        target_player = app.game.players[player_idx]
        
        if not app.game.can_request_from_player(app.game.human_player, target_player):
            self.game_message.text = "You can only request cards from the other team!"
            return
            
        # Show card selection popup
        self.show_card_selection(target_player, player_idx)
    
    def show_card_selection(self, target_player, player_idx):
        """Show popup for selecting which card to request"""
        def request_card(suit, rank, instance):
            app = App.get_running_app()
            app.game.request_card(player_idx, suit, rank)
            self.update_display()
            popup.dismiss()
            
        popup = CardSelectionPopup(target_player, request_card)
        popup.open()
    
    def next_player(self, instance):
        """Move to the next player's turn"""
        app = App.get_running_app()
        if app.game:
            app.game.next_player()
            self.update_display()
        else:
            self.player_info.text = "No active game!"
    
    def return_to_menu(self, instance):
        """Return to main menu"""
        # Cancel the scheduled updates
        Clock.unschedule(self.process_bot_turns)
        App.get_running_app().root.current = 'menu'

# ===================== MAIN APPLICATION =====================

class LiteratureGame(App):
    """Main application class"""
    
    def build(self):
        """Build the application UI"""
        log.info("Building Literature Card Game")
        
        # Ensure we have card images
        ensure_card_images()
        
        # Initialize game state
        self.game = None
        self.current_game_id = None
        
        # Create screen manager and screens
        sm = ScreenManager()
        
        # Add menu screen
        self.menu_screen = MainMenuScreen(name='menu')
        sm.add_widget(self.menu_screen)
        
        # Add game screen
        self.game_screen = GamePlayScreen(name='game')
        sm.add_widget(self.game_screen)
        
        return sm
    
    def create_game(self, player_count):
        """Create a new game with the specified number of players"""
        try:
            log.info(f"Creating game with {player_count} players")
            # Create game with human as player 0
            self.game = Game(player_count, human_player_idx=0)
            self.game_screen.update_display()
            return True
        except Exception as e:
            log.error(f"Error creating game: {e}")
            return False

# ===================== APPLICATION ENTRY =====================

if __name__ == "__main__":
    try:
        # Create asset directories
        os.makedirs('assets', exist_ok=True)
        os.makedirs('assets/cards', exist_ok=True)
        
        # Start the application
        log.info("Starting Literature Card Game")
        LiteratureGame().run()
    except Exception as e:
        log.error(f"Critical application error: {e}") 