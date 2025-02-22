import pygame
import pygame_gui
from typing import Tuple, List

class StartupUI:
    def __init__(self, screen_size=(800, 600)):
        pygame.init()
        self.screen_size = screen_size
        self.screen = pygame.display.set_mode(screen_size, pygame.RESIZABLE)
        pygame.display.set_caption("Literature Game Setup")
        
        self.ui_manager = pygame_gui.UIManager(screen_size)
        self.clock = pygame.time.Clock()
        
        # Create UI elements
        self.create_ui_elements()
        
    def create_ui_elements(self):
        # Player count dropdown
        self.player_count_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 50), (200, 30)),
            text="Number of Players:",
            manager=self.ui_manager
        )
        
        self.player_count_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=['6 Players', '8 Players'],
            starting_option='6 Players',
            relative_rect=pygame.Rect((250, 50), (150, 30)),
            manager=self.ui_manager
        )
        
        # Player name inputs
        self.name_inputs = []
        self.default_names = [f"Player {i+1}" for i in range(8)]
        
        for i in range(8):
            y_pos = 120 + i * 50
            label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect((50, y_pos), (100, 30)),
                text=f"Player {i+1}:",
                manager=self.ui_manager
            )
            
            entry = pygame_gui.elements.UITextEntryLine(
                relative_rect=pygame.Rect((160, y_pos), (200, 30)),
                manager=self.ui_manager
            )
            entry.set_text(self.default_names[i])
            self.name_inputs.append(entry)
            
        # Start button
        self.start_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((300, 520), (200, 50)),
            text="Start Game",
            manager=self.ui_manager
        )
        
        self.update_visible_inputs('6 Players')
        
    def update_visible_inputs(self, player_count: str):
        num_players = int(player_count.split()[0])
        for i, input in enumerate(self.name_inputs):
            input.visible = i < num_players
            
    def run(self) -> Tuple[int, List[str]]:
        running = True
        while running:
            time_delta = self.clock.tick(60)/1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None, None
                
                if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    if event.ui_element == self.player_count_dropdown:
                        self.update_visible_inputs(event.text)
                
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.start_button:
                        selected_option = self.player_count_dropdown.selected_option
                        if isinstance(selected_option, tuple):
                            num_players = int(selected_option[0].split()[0])
                        else:
                            num_players = int(selected_option.split()[0])
                        
                        player_names = [
                            input.get_text() for input in self.name_inputs[:num_players]
                        ]
                        return num_players, player_names
                
                self.ui_manager.process_events(event)
            
            self.ui_manager.update(time_delta)
            self.screen.fill((16, 24, 32))  # Dark blue-grey background
            self.ui_manager.draw_ui(self.screen)
            pygame.display.update()
            
        return None, None 