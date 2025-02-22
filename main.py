from deck import Deck
from player import Player
from visualization import display_all_hands
from gui_visualization import TableGUI
from startup_ui import StartupUI

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
    
    # Create and run GUI visualization
    gui = TableGUI()
    gui.run(players)

if __name__ == "__main__":
    main()
