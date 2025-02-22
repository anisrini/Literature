from typing import List
from player import Player

def display_all_hands(players: List[Player]):
    """Displays all players' hands in a grid layout"""
    # Get the visualized hands for all players
    player_hands = [player.visualize_hand() for player in players]
    
    # Print player names
    for i, player in enumerate(players):
        print(f"\nPlayer {i+1}'s hand:")
        
        # Get the cards for this player
        cards = player_hands[i]
        
        # Display cards in rows (2 cards per row)
        for row in range(0, len(cards), 10):  # 5 lines × 2 cards = 10
            for line in range(5):  # Each card has 5 lines
                # Print two cards side by side
                for card_idx in range(0, min(8, len(cards)//5), 2):
                    if row + card_idx*5 < len(cards):
                        print(cards[row + card_idx*5 + line], end=" ")
                print()  # New line after each row of cards
        print("\n" + "="*50)  # Separator between players 