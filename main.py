from deck import Deck
from player import Player
from visualization import display_all_hands
from gui_visualization import TableGUI
import threading

def main():
    # Example usage
    deck = Deck()
    deck.shuffle()
    
    # Create 6 players
    players = [Player(f"Player {i+1}") for i in range(6)]
    
    # Deal 8 cards to each player
    deck.deal(players, 8)
    
    # Show ASCII visualization of all hands
    display_all_hands(players)
    
    # Create and run GUI visualization in a separate thread
    gui = TableGUI()
    gui.run(players)

if __name__ == "__main__":
    main()
