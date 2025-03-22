"""
Literature Card Game - Server Component
Handles game sessions and future network connectivity
"""
import os
import sys
import logging
import random
from literature_core import Game, Card, Player, Bot

# Configure server logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GameServer:
    """Manages game sessions"""
    
    def __init__(self):
        """Initialize the game server"""
        self.active_games = {}
        self.next_game_id = 1
        logger.info("Game server initialized")
    
    def create_game(self, player_count, human_player_idx=0):
        """Create a new game and return its ID"""
        game_id = self.next_game_id
        self.next_game_id += 1
        
        try:
            # Create a new game with human player and bots
            self.active_games[game_id] = Game(player_count, human_player_idx)
            logger.info(f"Created game #{game_id} with {player_count} players (human is player {human_player_idx+1})")
            return game_id
        except Exception as e:
            logger.error(f"Failed to create game: {e}")
            return None
    
    def get_game(self, game_id):
        """Get a game by ID"""
        if game_id in self.active_games:
            return self.active_games[game_id]
        logger.warning(f"Game #{game_id} not found")
        return None
    
    def end_game(self, game_id):
        """End a game session"""
        if game_id in self.active_games:
            del self.active_games[game_id]
            logger.info(f"Game #{game_id} ended")
            return True
        logger.warning(f"Cannot end game #{game_id}: not found")
        return False
    
    def request_card(self, game_id, from_player_idx, to_player_idx, suit, rank):
        """Process a card request"""
        game = self.get_game(game_id)
        if not game:
            return False
            
        # Implement request logic
        return game.request_card(to_player_idx, suit, rank)
    
    def make_declaration(self, game_id, player_idx, family):
        """Process a declaration"""
        game = self.get_game(game_id)
        if not game:
            return False
            
        # Implement declaration logic
        if hasattr(game, 'make_declaration'):
            return game.make_declaration(family)
        return False

# Singleton server instance
_server = None

def get_server():
    """Get the singleton server instance"""
    global _server
    if _server is None:
        _server = GameServer()
    return _server

# Integration with literature_core.py
if __name__ == "__main__":
    try:
        logger.info("Starting Literature Card Game Server")
        
        # Import and run the UI if in standalone mode
        from literature_core import LiteratureGame
        
        # Create necessary directories
        os.makedirs('assets', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Initialize server
        server = get_server()
        
        # Start the UI application
        app = LiteratureGame()
        
        # Modify the app's create_game to use the server
        original_create_game = app.create_game
        
        def server_create_game(player_count):
            game_id = server.create_game(player_count, human_player_idx=0)
            if game_id:
                app.game = server.get_game(game_id)
                app.current_game_id = game_id
                app.game_screen.update_display()
                return True
            return False
        
        app.create_game = server_create_game
        
        # Run the app
        app.run()
        
    except Exception as e:
        logger.critical(f"Server error: {e}")
        sys.exit(1) 