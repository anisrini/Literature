import pygame
import math
from typing import List
from player import Player
import pygame_gui
import logging

# Add at the start of the file, after imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('literature_game.log'),
        logging.StreamHandler()
    ]
)

class TableGUI:
    def __init__(self, screen_size=(1024, 768)):
        pygame.init()
        # Set up windowed display with resizable flag
        self.screen_size = screen_size
        self.screen = pygame.display.set_mode(screen_size, pygame.RESIZABLE)
        pygame.display.set_caption("Literature Card Game")
        
        # Initialize UI Manager and clock
        self.ui_manager = pygame_gui.UIManager(screen_size)
        self.clock = pygame.time.Clock()
        
        # Modern color scheme
        self.TABLE_GREEN = (34, 139, 34)  # Forest green
        self.BORDER_GOLD = (218, 165, 32)  # Golden border
        self.WHITE = (255, 255, 255)
        self.BLACK = (20, 20, 20)  # Soft black
        self.RED = (220, 20, 60)   # Crimson red
        self.BACKGROUND = (16, 24, 32)  # Dark blue-grey
        
        # Add team colors
        self.TEAM1_COLOR = (255, 223, 0)  # Yellow
        self.TEAM2_COLOR = (30, 144, 255)  # Blue
        
        # Game state info
        self.current_turn = 0  # Index of current player
        self.last_request = None  # (requester_idx, requested_idx, card)
        self.last_transfer = None  # (from_idx, to_idx, card)
        self.team1_sets = 0
        self.team2_sets = 0
        
        # Initialize dimensions
        self._update_dimensions()
        
        # Add UI elements for game actions
        self.action_buttons = []
        self.create_action_buttons()
        
    def _update_dimensions(self):
        """Update dimensions when window is resized"""
        # Adjust table dimensions
        self.center = (self.screen_size[0] // 2, self.screen_size[1] // 2)
        self.table_radius = min(self.screen_size) * 0.40
        
        # Adjust card dimensions to fit screen
        self.card_width = int(min(self.screen_size) * 0.07)
        self.card_height = int(self.card_width * 1.4)
        self.card_spacing = int(self.card_width * 0.4)
        
        # Adjust font sizes relative to card size
        font_size = int(self.card_width * 0.32)
        name_font_size = int(self.card_width * 0.42)
        
        # Update fonts with new sizes
        try:
            self.card_font = pygame.font.Font("arial.ttf", font_size)
            self.name_font = pygame.font.Font("arial.ttf", name_font_size)
        except:
            self.card_font = pygame.font.SysFont("arial", font_size)
            self.name_font = pygame.font.SysFont("arial", name_font_size)
            
    def draw_hexagonal_table(self):
        """Draws the hexagonal poker table with gradient and shadow"""
        # Draw shadow
        shadow_points = self._get_hexagon_points(self.table_radius + 15)
        shadow_surface = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        pygame.draw.polygon(shadow_surface, (0, 0, 0, 64), shadow_points)
        self.screen.blit(shadow_surface, (5, 5))  # Offset shadow
        
        # Draw table border with golden trim
        pygame.draw.polygon(self.screen, self.BORDER_GOLD, 
                          self._get_hexagon_points(self.table_radius + 2))
        
        # Draw main table
        pygame.draw.polygon(self.screen, self.TABLE_GREEN, 
                          self._get_hexagon_points(self.table_radius))
        
    def _get_hexagon_points(self, radius):
        """Helper function to get hexagon points"""
        points = []
        for i in range(6):
            angle = i * 60 - 30
            x = self.center[0] + radius * math.cos(math.radians(angle))
            y = self.center[1] + radius * math.sin(math.radians(angle))
            points.append((x, y))
        return points
    
    def draw_card(self, x, y, card, face_up=True):
        """Draws a single card with modern styling"""
        # Card shadow
        shadow_surface = pygame.Surface((self.card_width + 4, self.card_height + 4), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 64), 
                        (0, 0, self.card_width + 4, self.card_height + 4), 
                        border_radius=6)
        self.screen.blit(shadow_surface, (x + 2, y + 2))
        
        if face_up:
            # Card background (white)
            pygame.draw.rect(self.screen, self.WHITE, 
                           (x, y, self.card_width, self.card_height), 
                           border_radius=5)
            
            # Card border
            pygame.draw.rect(self.screen, (200, 200, 200), 
                           (x, y, self.card_width, self.card_height), 
                           1, border_radius=5)
            
            # Determine color based on suit
            color = self.RED if card.suit in ['Hearts', 'Diamonds'] else self.BLACK
            
            # Draw rank
            rank_text = self.card_font.render(card.get_short_rank(), True, color)
            self.screen.blit(rank_text, (x + 6, y + 6))
            
            # Draw large suit symbol in center
            suit_text = self.card_font.render(card.get_symbol(), True, color)
            suit_rect = suit_text.get_rect(center=(
                x + self.card_width//2,
                y + self.card_height//2
            ))
            self.screen.blit(suit_text, suit_rect)
            
            # Draw small rank and suit in bottom right
            small_text = self.card_font.render(f"{card.get_short_rank()}{card.get_symbol()}", True, color)
            small_rect = small_text.get_rect(bottomright=(
                x + self.card_width - 6,
                y + self.card_height - 6
            ))
            self.screen.blit(small_text, small_rect)
        else:
            # Card back design
            # Main background (dark blue)
            pygame.draw.rect(self.screen, (25, 40, 80), 
                           (x, y, self.card_width, self.card_height), 
                           border_radius=5)
            
            # Pattern (diagonal stripes)
            pattern_color = (40, 60, 120)
            stripe_width = 8
            for i in range(-self.card_width, self.card_width + self.card_height, stripe_width * 2):
                start_pos = (x + i, y)
                end_pos = (x + i + self.card_height, y + self.card_height)
                pygame.draw.line(self.screen, pattern_color, start_pos, end_pos, 3)
            
            # Border
            pygame.draw.rect(self.screen, (60, 80, 160), 
                           (x, y, self.card_width, self.card_height), 
                           2, border_radius=5)

    def draw_player_cards(self, x, y, player, is_current_player):
        """Draws all cards in a player's hand in an umbrella/fan formation"""
        num_cards = len(player.hand)
        if num_cards == 0:
            return
            
        # Calculate the arc parameters
        total_angle = 30  # Fan spread angle
        start_angle = -total_angle / 2
        angle_step = total_angle / (num_cards - 1) if num_cards > 1 else 0
        
        # Calculate overlap
        card_overlap = self.card_width * 0.4
        
        for i, card in enumerate(player.hand):
            # Calculate rotation and position
            current_angle = math.radians(start_angle + (i * angle_step))
            
            # Calculate arc position
            arc_radius = self.card_height * 0.2
            offset_x = math.sin(current_angle) * arc_radius
            offset_y = -math.cos(current_angle) * arc_radius
            
            # Calculate final position
            card_x = x + (i * (self.card_width - card_overlap))
            card_y = y + offset_y
            
            # Adjust x position based on angle for fan effect
            card_x += offset_x
            
            # Draw the card (face up only for current player)
            self.draw_card(int(card_x), int(card_y), card, face_up=is_current_player)
            
    def draw_player_hand_background(self, x, y, width, height, player_idx, is_current=False):
        """Draws colored background for player's hand based on team"""
        color = self.TEAM1_COLOR if player_idx % 2 == 1 else self.TEAM2_COLOR
        
        # Create larger rectangle for current player
        padding = 20 if is_current else 10
        border_width = 4 if is_current else 3
        glow_color = (*color, 128) if is_current else (*color, 64)
        
        # Draw glow effect for current player
        if is_current:
            glow_rect = pygame.Rect(x - padding - 2, y - padding - 2, 
                                  width + 2*padding + 4, height + 2*padding + 4)
            pygame.draw.rect(self.screen, glow_color, glow_rect, border_radius=12)
        
        # Draw main border
        rect = pygame.Rect(x - padding, y - padding, 
                         width + 2*padding, height + 2*padding)
        pygame.draw.rect(self.screen, color, rect, border_width, border_radius=10)

    def draw_player_name(self, player_idx, card_x, card_y, total_width, total_height, is_current):
        """Draw player name with current turn indicator"""
        name = f"Player {player_idx + 1}"
        if is_current:
            name += " (Current Turn)"
        
        color = self.TEAM1_COLOR if player_idx % 2 == 1 else self.TEAM2_COLOR
        text = self.name_font.render(name, True, color)
        
        # Calculate text position based on player position
        if player_idx in [4, 5]:  # Left side players
            text_x = card_x - self.card_width * 0.3
            text_y = card_y + total_height // 2
        elif player_idx in [1, 2]:  # Right side players
            text_x = card_x + total_width + self.card_width * 0.3
            text_y = card_y + total_height // 2
        elif player_idx == 0:  # Top player
            text_x = card_x + total_width // 2
            text_y = card_y - self.card_height * 0.3
        else:  # Bottom player
            text_x = card_x + total_width // 2
            text_y = card_y + total_height * 1.3
            
        text_rect = text.get_rect(center=(text_x, text_y))
        
        # Draw shadow and glow for current player
        if is_current:
            # Glow effect
            glow_surface = pygame.Surface(text.get_size(), pygame.SRCALPHA)
            glow_surface.fill((*color, 64))
            glow_rect = glow_surface.get_rect(center=(text_x, text_y))
            self.screen.blit(glow_surface, glow_rect)
        
        # Draw shadow
        shadow_rect = text_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        shadow_text = self.name_font.render(name, True, self.BLACK)
        self.screen.blit(shadow_text, shadow_rect)
        
        # Draw text
        self.screen.blit(text, text_rect)
        
    def draw_game_info(self):
        """Draws game state information"""
        info_font = pygame.font.SysFont("arial", 24)
        y_pos = 20
        spacing = 30
        
        # Draw team scores with background
        team1_text = f"Team 1 Sets: {self.team1_sets}"
        team2_text = f"Team 2 Sets: {self.team2_sets}"
        
        # Team 1 score with background
        score_bg = pygame.Surface((200, 30), pygame.SRCALPHA)
        pygame.draw.rect(score_bg, (*self.TEAM1_COLOR, 128), score_bg.get_rect(), border_radius=5)
        self.screen.blit(score_bg, (20, y_pos))
        text = info_font.render(team1_text, True, self.BLACK)
        self.screen.blit(text, (30, y_pos))
        
        # Team 2 score with background
        score_bg = pygame.Surface((200, 30), pygame.SRCALPHA)
        pygame.draw.rect(score_bg, (*self.TEAM2_COLOR, 128), score_bg.get_rect(), border_radius=5)
        self.screen.blit(score_bg, (20, y_pos + spacing))
        text = info_font.render(team2_text, True, self.BLACK)
        self.screen.blit(text, (30, y_pos + spacing))
        
        # Draw current turn with highlight
        if self.current_turn is not None:
            y_pos += 2 * spacing
            turn_bg = pygame.Surface((250, 30), pygame.SRCALPHA)
            team_color = self.TEAM1_COLOR if self.current_turn % 2 == 1 else self.TEAM2_COLOR
            pygame.draw.rect(turn_bg, (*team_color, 128), turn_bg.get_rect(), border_radius=5)
            self.screen.blit(turn_bg, (20, y_pos))
            
            turn_text = f"Current Turn: Player {self.current_turn + 1}"
            text = info_font.render(turn_text, True, self.BLACK)
            self.screen.blit(text, (30, y_pos))
        
        # Draw last action info
        if self.last_request:
            y_pos += 2 * spacing
            req_idx, target_idx, card = self.last_request
            req_text = f"Player {req_idx + 1} requested {card}"
            text = info_font.render(req_text, True, self.WHITE)
            self.screen.blit(text, (20, y_pos))
            
            target_text = f"from Player {target_idx + 1}"
            text = info_font.render(target_text, True, self.WHITE)
            self.screen.blit(text, (20, y_pos + spacing))
        
        if self.last_transfer:
            y_pos += 2 * spacing
            from_idx, to_idx, card = self.last_transfer
            transfer_text = f"Player {from_idx + 1} gave {card}"
            text = info_font.render(transfer_text, True, self.WHITE)
            self.screen.blit(text, (20, y_pos))
            
            to_text = f"to Player {to_idx + 1}"
            text = info_font.render(to_text, True, self.WHITE)
            self.screen.blit(text, (20, y_pos + spacing))
            
        # Show last set winner if any
        if hasattr(self, 'last_set_winner') and self.last_set_winner:
            y_pos += 2 * spacing
            winner_text = f"Last Set: {self.last_set_winner}"
            text = info_font.render(winner_text, True, self.WHITE)
            self.screen.blit(text, (20, y_pos))
        
    def display_game_state(self, game_state):
        time_delta = self.clock.tick(60)/1000.0
        
        self.screen.fill(self.BACKGROUND)
        self.draw_hexagonal_table()
        
        # Update current turn from game state
        self.current_turn = game_state.current_turn
        self.draw_game_info()
        
        # Draw players and their cards
        for i, player in enumerate(game_state.players):
            angle = i * 60 - 30
            cards_radius = self.table_radius * 0.85
            
            # Calculate positions...
            card_x = self.center[0] + cards_radius * math.cos(math.radians(angle))
            card_y = self.center[1] + cards_radius * math.sin(math.radians(angle))
            
            # Calculate actual width based on number of cards
            overlap = self.card_width * 0.4  # Reduced overlap
            total_width = (len(player.hand) - 1) * (self.card_width - overlap) + self.card_width
            total_height = self.card_height
            
            # Adjust position to center the hand
            card_x -= total_width // 2
            card_y -= total_height // 2
            
            # Draw team color background with highlight for current turn
            is_current = (i == game_state.current_turn)
            self.draw_player_hand_background(card_x, card_y, total_width, total_height, i, is_current)
            
            # Draw player's cards (face up only for current player)
            self.draw_player_cards(card_x, card_y, player, is_current)
            
            # Draw player name
            self.draw_player_name(i, card_x, card_y, total_width, total_height, is_current)
        
        self.ui_manager.update(time_delta)
        self.ui_manager.draw_ui(self.screen)
        pygame.display.flip()
        
    def update_game_state(self, current_turn=None, last_request=None, 
                         last_transfer=None, team1_sets=None, team2_sets=None):
        """Updates the game state information"""
        if current_turn is not None:
            self.current_turn = current_turn
        if last_request is not None:
            self.last_request = last_request
        if last_transfer is not None:
            self.last_transfer = last_transfer
        if team1_sets is not None:
            self.team1_sets = team1_sets
        if team2_sets is not None:
            self.team2_sets = team2_sets
        
    def run(self, players: List[Player]):
        """Main loop for the GUI"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:  # Keep escape to exit
                        running = False
                elif event.type == pygame.VIDEORESIZE:
                    # Handle window resize
                    self.screen_size = (event.w, event.h)
                    self.screen = pygame.display.set_mode(self.screen_size, pygame.RESIZABLE)
                    self._update_dimensions()
                    
            self.display_game_state(players)
            pygame.time.wait(100)
            
        pygame.quit()
        
    def create_action_buttons(self):
        """Create buttons for game actions"""
        button_height = 40
        button_width = 150
        spacing = 20
        
        # Game action buttons (right side)
        self.request_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.screen_size[0] - button_width - spacing, 
                                     self.screen_size[1] - 3 * (button_height + spacing)),
                                    (button_width, button_height)),
            text='Request Card',
            manager=self.ui_manager
        )
        
        self.declare_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.screen_size[0] - button_width - spacing,
                                     self.screen_size[1] - 2 * (button_height + spacing)),
                                    (button_width, button_height)),
            text='Declare Set',
            manager=self.ui_manager
        )

        # Game control buttons (left side)
        self.restart_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((spacing,
                                     self.screen_size[1] - 2 * (button_height + spacing)),
                                    (button_width, button_height)),
            text='Restart Game',
            manager=self.ui_manager
        )

        self.quit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((spacing,
                                     self.screen_size[1] - (button_height + spacing)),
                                    (button_width, button_height)),
            text='Quit Game',
            manager=self.ui_manager
        )
        
    def handle_game_events(self, event, game_state):
        """Handle game-specific events"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.request_button:
                self.show_request_dialog(game_state)
            elif event.ui_element == self.declare_button:
                self.show_declare_dialog(game_state)
            elif event.ui_element == self.restart_button:
                return "RESTART"
            elif event.ui_element == self.quit_button:
                return "QUIT"
                
        # Store selected values when dropdowns change
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if hasattr(self, 'player_dropdown') and event.ui_element == self.player_dropdown:
                self.selected_player = event.text
            elif hasattr(self, 'card_dropdown') and event.ui_element == self.card_dropdown:
                self.selected_card = event.text
                
        elif event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
            if hasattr(self, 'request_dialog') and event.ui_element == self.request_dialog:
                if hasattr(self, 'selected_player') and hasattr(self, 'selected_card'):
                    self.handle_card_request(game_state)
            elif hasattr(self, 'declare_dialog') and event.ui_element == self.declare_dialog:
                self.handle_set_declaration(game_state)
        
        self.ui_manager.process_events(event)
        
    def show_request_dialog(self, game_state):
        """Show dialog for requesting a card"""
        current_player = game_state.current_turn
        logging.info(f"Opening request dialog for Player {current_player + 1}")
        
        # Create dialog window
        dialog_width = 300
        dialog_height = 200  # Reduced back to original height
        dialog_rect = pygame.Rect(
            (self.screen_size[0] - dialog_width) // 2,
            (self.screen_size[1] - dialog_height) // 2,
            dialog_width,
            dialog_height
        )
        
        # Get opponents
        opponents = [i for i in range(len(game_state.players)) 
                    if i % 2 != current_player % 2]
        opponent_options = [f"P{i+1}" for i in opponents]
        logging.info(f"Available opponents: {opponent_options}")
        
        # Get requestable cards
        current_player_obj = game_state.players[current_player]
        major_cards = []
        minor_cards = []
        
        for card in current_player_obj.hand:
            if current_player_obj.has_root_card(card.get_set()):
                set_cards = card.get_set_cards()
                for c in set_cards:
                    if c not in current_player_obj.hand:
                        if "Major" in c.get_set():
                            major_cards.append(c)
                        else:
                            minor_cards.append(c)
        
        # Sort cards within their categories
        major_cards.sort(key=lambda x: (x.suit, x.rank))
        minor_cards.sort(key=lambda x: (x.suit, x.rank))
        
        # Combine sorted lists with major cards first
        requestable_cards = [str(card) for card in major_cards + minor_cards]
        logging.info(f"Requestable cards: {requestable_cards}")
        
        if not requestable_cards:
            logging.warning("No cards available to request")
            self.show_feedback("No cards available to request", (255, 165, 0, 200))
            return
        
        # Create dialog
        self.request_dialog = pygame_gui.windows.ui_confirmation_dialog.UIConfirmationDialog(
            rect=dialog_rect,
            manager=self.ui_manager,
            window_title="Request Card",
            action_long_desc="Choose a player and card to request:",
            action_short_name="Request",
            blocking=False
        )
        
        # Add player dropdown at top
        self.player_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=opponent_options,
            starting_option=opponent_options[0],
            relative_rect=pygame.Rect(20, 20, 260, 30),
            manager=self.ui_manager,
            container=self.request_dialog
        )
        
        # Add card dropdown with normal height but expanded list
        self.card_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=requestable_cards,
            starting_option=requestable_cards[0],
            relative_rect=pygame.Rect(20, 70, 260, 30),  # Normal height
            manager=self.ui_manager,
            container=self.request_dialog,
            expansion_height_limit=250  # Changed from dropdown_height to expansion_height_limit
        )
        
        # Initialize selected values
        self.selected_player = opponent_options[0]
        self.selected_card = requestable_cards[0]

    def show_declare_dialog(self, game_state):
        """Show dialog for declaring a set"""
        current_player = game_state.current_turn
        
        # Create dialog window
        dialog_width = 400
        dialog_height = 400
        dialog_rect = pygame.Rect(
            (self.screen_size[0] - dialog_width) // 2,
            (self.screen_size[1] - dialog_height) // 2,
            dialog_width,
            dialog_height
        )
        
        self.declare_dialog = pygame_gui.windows.ui_confirmation_dialog.UIConfirmationDialog(
            rect=dialog_rect,
            manager=self.ui_manager,
            window_title="Declare Set",
            action_long_desc="Choose a set to declare and assign cards:",
            action_short_name="Declare",
            blocking=False
        )
        
        # Get declarable sets (sets where player has root card)
        current_player_obj = game_state.players[current_player]
        declarable_sets = []
        for card in current_player_obj.hand:
            if current_player_obj.has_root_card(card.get_set()):
                declarable_sets.append(card.get_set())
        declarable_sets = list(set(declarable_sets))  # Remove duplicates
        
        # Set selection dropdown
        self.set_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=declarable_sets,
            starting_option=declarable_sets[0] if declarable_sets else "No sets available",
            relative_rect=pygame.Rect(20, 20, 360, 30),
            manager=self.ui_manager,
            container=self.declare_dialog
        )
        
        # Get teammates
        teammates = game_state.get_teammate_indices(current_player)
        self.card_assignments = {}
        
        # Create card assignment dropdowns for each card in the set
        y_offset = 70
        for i, card in enumerate(current_player_obj.get_set_cards(declarable_sets[0])):
            # Card label
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(20, y_offset, 150, 30),
                text=str(card),
                manager=self.ui_manager,
                container=self.declare_dialog
            )
            
            # Player assignment dropdown
            teammate_options = [f"P{j+1}" for j in teammates]
            dropdown = pygame_gui.elements.UIDropDownMenu(
                options_list=teammate_options,
                starting_option=teammate_options[0],
                relative_rect=pygame.Rect(180, y_offset, 200, 30),
                manager=self.ui_manager,
                container=self.declare_dialog
            )
            self.card_assignments[str(card)] = dropdown
            y_offset += 40
        
        # Complete Declaration button
        self.complete_declaration_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(100, y_offset + 20, 200, 30),
            text="Complete Declaration",
            manager=self.ui_manager,
            container=self.declare_dialog
        ) 

    def animate_card_transfer(self, card, start_pos, end_pos, duration_ms=1000):
        """Animate a card moving from start position to end position"""
        start_time = pygame.time.get_ticks()
        
        # Save initial game state
        initial_screen = self.screen.copy()
        
        while True:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - start_time
            
            if elapsed >= duration_ms:
                break
                
            # Calculate current position using easing function
            progress = elapsed / duration_ms
            # Use ease-out cubic function for smooth deceleration
            progress = 1 - (1 - progress) ** 3
            
            current_x = start_pos[0] + (end_pos[0] - start_pos[0]) * progress
            current_y = start_pos[1] + (end_pos[1] - start_pos[1]) * progress
            
            # Draw frame
            self.screen.blit(initial_screen, (0, 0))
            self.draw_card(int(current_x), int(current_y), card)
            pygame.display.flip()
            
            # Cap frame rate
            pygame.time.wait(16)  # Approximately 60 FPS

    def get_card_position(self, player_idx, card_idx, game_state):
        """Calculate the position of a specific card in a player's hand"""
        angle = player_idx * 60 - 30
        cards_radius = self.table_radius * 0.85
        
        # Base position for the hand
        base_x = self.center[0] + cards_radius * math.cos(math.radians(angle))
        base_y = self.center[1] + cards_radius * math.sin(math.radians(angle))
        
        # Calculate card offset in fan formation
        total_angle = 30
        start_angle = -total_angle / 2
        player_hand = game_state.players[player_idx].hand
        angle_step = total_angle / (len(player_hand) - 1) if len(player_hand) > 1 else 0
        current_angle = math.radians(start_angle + (card_idx * angle_step))
        
        arc_radius = self.card_height * 0.2
        offset_x = math.sin(current_angle) * arc_radius
        offset_y = -math.cos(current_angle) * arc_radius
        
        card_overlap = self.card_width * 0.8
        x = base_x + (card_idx * (self.card_width - card_overlap)) + offset_x
        y = base_y + offset_y
        
        return (x, y)

    def handle_card_request(self, game_state):
        """Handle a card request from the request dialog"""
        try:
            # Get selected player and card from stored values
            target_player = int(self.selected_player.replace('P', '')) - 1
            card_str = self.selected_card
            requester = game_state.current_turn
            
            logging.info(f"Player {requester + 1} requesting {card_str} from Player {target_player + 1}")
            
            # Find the requested card in target player's hand
            requested_card = None
            target_player_obj = game_state.players[target_player]
            for i, card in enumerate(target_player_obj.hand):
                if str(card) == card_str:
                    requested_card = card
                    start_pos = self.get_card_position(target_player, i, game_state)
                    logging.info(f"Found requested card in Player {target_player + 1}'s hand")
                    break
            
            if requested_card:
                # Get end position in requester's hand
                end_pos = self.get_card_position(
                    requester, 
                    len(game_state.players[requester].hand),
                    game_state
                )
                
                # Process the request
                success = game_state.handle_card_request(requester, target_player, requested_card)
                
                if success:
                    logging.info(f"Card transfer successful: {card_str} moved to Player {requester + 1}")
                    # Animate the transfer
                    self.animate_card_transfer(requested_card, start_pos, end_pos)
                    message = f"Card {card_str} transferred successfully!"
                    color = (0, 255, 0, 200)  # Green
                    
                    # Update game state
                    game_state.last_request = (requester, target_player, card_str)
                    game_state.last_transfer = (target_player, requester, card_str)
                    
                    # Rule: If card is found, requester gets another turn
                    game_state.current_turn = requester
                    logging.info(f"Player {requester + 1} gets another turn")
                else:
                    message = f"Player does not have {card_str}"
                    color = (255, 165, 0, 200)  # Orange
                    
                    # Rule: If card is not found, turn goes to requested player
                    game_state.current_turn = target_player
                    logging.info(f"Turn passes to Player {target_player + 1}")
            else:
                message = f"Player does not have {card_str}"
                color = (255, 165, 0, 200)
                # Rule: If card is not found, turn goes to requested player
                game_state.current_turn = target_player
                logging.info(f"Turn passes to Player {target_player + 1}")
                
        except Exception as e:
            logging.error(f"Error processing card request: {str(e)}", exc_info=True)
            message = "Invalid request"
            color = (255, 0, 0, 200)
        
        # Show feedback
        self.show_feedback(message, color)
        logging.info(f"Showing feedback: {message}")
        
        # Close dialog
        self.request_dialog.kill()

    def handle_set_declaration(self, game_state):
        """Handle a set declaration from the declare dialog"""
        current_player = game_state.current_turn
        declared_set = self.set_dropdown.selected_option
        
        # Collect card assignments
        assignments = []
        for card_str, dropdown in self.card_assignments.items():
            player_idx = int(dropdown.selected_option.replace('P', '')) - 1
            assignments.append((player_idx, card_str))
        
        try:
            # Validate the declaration
            success, winner = game_state.validate_declaration(
                current_player, declared_set, assignments
            )
            
            if success:
                message = f"Set {declared_set} declared correctly! {winner} wins the set!"
                color = (0, 255, 0, 200)  # Green
                # Rule: If declaration is correct, declaring player gets another turn
                game_state.current_turn = current_player
                logging.info(f"Player {current_player + 1} gets another turn after successful declaration")
            else:
                if winner == "No Winner":
                    message = f"Incorrect declaration. All cards were in your team. Set removed."
                    color = (255, 165, 0, 200)  # Orange
                else:
                    message = f"Incorrect declaration. {winner} wins the set!"
                    color = (255, 0, 0, 200)  # Red
                
                # Rule: After incorrect declaration, next player gets turn
                game_state.current_turn = (current_player + 1) % len(game_state.players)
                logging.info(f"Turn passes to Player {game_state.current_turn + 1} after failed declaration")
                    
            # Update game state
            game_state.last_set_winner = winner
            if winner == "Team 1":
                game_state.team1_sets += 1
            elif winner == "Team 2":
                game_state.team2_sets += 1
                
        except Exception as e:
            logging.error(f"Error processing declaration: {str(e)}", exc_info=True)
            message = "Invalid declaration"
            color = (255, 0, 0, 200)  # Red
            
        # Show feedback message
        self.show_feedback(message, color)
        logging.info(f"Showing feedback: {message}")
        
        # Close the dialog
        self.declare_dialog.kill()

    def show_feedback(self, message, color):
        """Show a feedback message on screen"""
        # Create semi-transparent surface for message
        feedback_rect = pygame.Rect(
            (self.screen_size[0] - 400) // 2,
            (self.screen_size[1] - 100) // 2,
            400, 100
        )
        
        feedback_surface = pygame.Surface((400, 100), pygame.SRCALPHA)
        pygame.draw.rect(feedback_surface, color, feedback_surface.get_rect(), border_radius=10)
        
        # Render message
        font = pygame.font.SysFont("arial", 24)
        text = font.render(message, True, self.WHITE)
        text_rect = text.get_rect(center=(200, 50))  # Center in feedback surface
        feedback_surface.blit(text, text_rect)
        
        # Show message
        self.screen.blit(feedback_surface, feedback_rect)
        pygame.display.flip()
        
        # Keep message visible briefly
        pygame.time.wait(2000)

    def handle_resize(self, event):
        """Handle window resize event"""
        self.screen_size = (event.w, event.h)
        self.screen = pygame.display.set_mode(self.screen_size, pygame.RESIZABLE)
        self.ui_manager.set_window_resolution(self.screen_size)
        self._update_dimensions()
        
        # Recreate action buttons with new positions
        self.create_action_buttons() 