
The game will launch with:
- A graphical window showing the game table
- Console output showing detailed card information
- 6 players with 8 cards each
- Cards displayed in a modern, easy-to-read format

## Project Structure

- `main.py` - Main game entry point
- `card.py` - Card class implementation
- `deck.py` - Deck management and dealing
- `player.py` - Player class and hand management
- `visualization.py` - ASCII-based console visualization
- `gui_visualization.py` - Pygame-based graphical interface

## Class Overview

### Card
- Represents individual playing cards
- Handles suit and rank information
- Provides string representation and symbols

### Deck
- Manages the 48-card deck
- Handles shuffling and dealing
- Supports deck reconstruction

### Player
- Manages player hands
- Handles card addition and display
- Supports hand visualization

### TableGUI
- Provides graphical interface
- Renders hexagonal table
- Displays cards with modern styling
- Handles player positioning

## Graphical Features

- Hexagonal table with golden trim
- Modern card design with shadows
- Suit-colored cards (red for Hearts/Diamonds)
- Player name displays
- Card stacking with arc effect
- Smooth animations

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Pygame community for graphics support
- Literature card game traditional rules