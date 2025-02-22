import pygame
import math
from typing import List
from player import Player

class TableGUI:
    def __init__(self, screen_size=(1024, 768)):
        pygame.init()
        self.screen_size = screen_size
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Literature Card Game")
        
        # Modern color scheme
        self.TABLE_GREEN = (34, 139, 34)  # Forest green
        self.BORDER_GOLD = (218, 165, 32)  # Golden border
        self.WHITE = (255, 255, 255)
        self.BLACK = (20, 20, 20)  # Soft black
        self.RED = (220, 20, 60)   # Crimson red
        self.BACKGROUND = (16, 24, 32)  # Dark blue-grey
        
        # Table dimensions
        self.center = (screen_size[0] // 2, screen_size[1] // 2)
        self.table_radius = min(screen_size) * 0.35
        
        # Card dimensions (larger cards)
        self.card_width = 80
        self.card_height = 112
        self.card_spacing = 30
        
        # Load custom font if available, otherwise use default
        try:
            self.card_font = pygame.font.Font("arial.ttf", 28)
            self.name_font = pygame.font.Font("arial.ttf", 36)
        except:
            self.card_font = pygame.font.SysFont("arial", 28)
            self.name_font = pygame.font.SysFont("arial", 36)
            
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
    
    def draw_card(self, x, y, card):
        """Draws a single card with modern styling"""
        # Card shadow
        shadow_surface = pygame.Surface((self.card_width + 4, self.card_height + 4), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 64), 
                        (0, 0, self.card_width + 4, self.card_height + 4), 
                        border_radius=6)
        self.screen.blit(shadow_surface, (x + 2, y + 2))
        
        # Card background
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
            
    def draw_player_cards(self, x, y, player):
        """Draws all cards in a player's hand with slight rotation"""
        num_cards = len(player.hand)
        angle_step = 5  # degrees between each card
        total_angle = (num_cards - 1) * angle_step
        start_angle = -total_angle / 2
        
        for i, card in enumerate(player.hand):
            # Calculate position with slight arc effect
            angle = math.radians(start_angle + (i * angle_step))
            arc_height = 10  # pixels
            card_x = x + (i * self.card_spacing)
            card_y = y + math.sin(angle) * arc_height
            self.draw_card(int(card_x), int(card_y), card)
            
    def display_game_state(self, players: List[Player]):
        """Displays the current game state with all players' hands"""
        self.screen.fill(self.BACKGROUND)
        self.draw_hexagonal_table()
        
        # Draw players and their cards
        for i, player in enumerate(players):
            angle = i * 60 - 30
            radius = self.table_radius + 80
            
            x = self.center[0] + radius * math.cos(math.radians(angle))
            y = self.center[1] + radius * math.sin(math.radians(angle))
            
            # Adjust position for cards
            x -= (len(player.hand) * self.card_spacing) // 2
            y -= self.card_height // 2
            
            # Draw player's cards
            self.draw_player_cards(x, y, player)
            
            # Draw player name with shadow effect
            name = f"Player {i+1}"
            shadow_text = self.name_font.render(name, True, self.BLACK)
            text = self.name_font.render(name, True, self.WHITE)
            
            text_rect = text.get_rect(center=(
                self.center[0] + (self.table_radius + 160) * math.cos(math.radians(angle)),
                self.center[1] + (self.table_radius + 160) * math.sin(math.radians(angle))
            ))
            
            # Draw shadow slightly offset
            shadow_rect = text_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            self.screen.blit(shadow_text, shadow_rect)
            self.screen.blit(text, text_rect)
        
        pygame.display.flip()
        
    def run(self, players: List[Player]):
        """Main loop for the GUI"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
            self.display_game_state(players)
            pygame.time.wait(100)  # Small delay to prevent high CPU usage
            
        pygame.quit() 