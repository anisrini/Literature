from deck import Deck
from player import Player
from visualization import display_all_hands
from gui_visualization import TableGUI
from startup_ui import StartupUI
from game_state import GameState
import pygame

def main():
    # Show startup UI
    startup = StartupUI()
    num_players, player_names = startup.run()
    
    if not num_players or not player_names:  # If user closed the window
        return
    
    # Calculate cards per player based on player count
    cards_per_player = 6 if num_players == 8 else 8
    
    # Initialize game
    deck = Deck()
    deck.shuffle()
    
    # Create players with names from UI
    players = [Player(name) for name in player_names]
    
    # Deal cards
    deck.deal(players, cards_per_player)
    
    # Show ASCII visualization of all hands
    display_all_hands(players)
    
    # Create game state
    game_state = GameState(players)
    
    # Create GUI
    gui = TableGUI()
    
    # Main game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.VIDEORESIZE:
                gui.handle_resize(event)
            else:
                gui.handle_game_events(event, game_state)
        
        gui.display_game_state(game_state)
        pygame.time.wait(100)

if __name__ == "__main__":
    main()
