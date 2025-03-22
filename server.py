"""
Literature Card Game - Web Server
Runs the game logic and serves the web interface
"""
import os
import random
import logging
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web_server.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
app.config['SECRET_KEY'] = 'literature-game-secret'
socketio = SocketIO(app)

# Import the game logic
from game_logic import Card, Player, Bot, Game

# Store active games
active_games = {}

@app.route('/')
def index():
    """Serve the main game page"""
    return render_template('index.html')

@app.route('/assets/<path:path>')
def send_assets(path):
    """Serve card images and other assets"""
    return send_from_directory('assets', path)

@socketio.on('create_game')
def handle_create_game(data):
    """Create a new game with the specified number of players"""
    try:
        player_count = int(data.get('player_count', 6))
        
        # Create game ID
        game_id = str(uuid.uuid4())
        
        # Create new game
        game = Game(player_count, human_player_idx=0)
        active_games[game_id] = game
        
        # Send initial game state
        game_state = get_game_state(game, game_id)
        emit('game_created', game_state)
        
        log.info(f"Created game {game_id} with {player_count} players")
        return game_state
    except Exception as e:
        log.error(f"Error creating game: {e}")
        emit('error', {'message': f"Failed to create game: {str(e)}"})
        return None

@socketio.on('request_card')
def handle_request_card(data):
    """Handle a card request from the human player"""
    game_id = data.get('game_id')
    target_player_idx = int(data.get('target_player_idx'))
    suit = data.get('suit')
    rank = data.get('rank')
    
    game = active_games.get(game_id)
    if not game:
        emit('error', {'message': 'Game not found'})
        return
    
    # Get players for log
    requester = game.current_player
    target = game.players[target_player_idx]
    
    # Add to action log
    log_entry = {
        'type': 'request',
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'requester': {
            'name': requester.name,
            'team': requester.team,
            'is_human': not requester.is_bot
        },
        'target': {
            'name': target.name,
            'team': target.team
        },
        'card': {
            'suit': suit,
            'rank': rank
        },
        'success': False  # Will be updated after request
    }
    
    # Process the request
    result = game.request_card(target_player_idx, suit, rank)
    
    # Update success status in log
    log_entry['success'] = result
    
    # Send the log entry
    emit('game_log', log_entry)
    
    # Send the updated game state
    emit('game_updated', get_game_state(game, game_id))
    
    # If it's now a bot's turn, handle that after a delay
    if game.current_player.is_bot:
        socketio.sleep(2)  # Wait 2 seconds before bot turn
        handle_bot_turn(game_id)

@socketio.on('next_player')
def handle_next_player(data):
    """Move to the next player's turn"""
    game_id = data.get('game_id')
    game = active_games.get(game_id)
    if not game:
        emit('error', {'message': 'Game not found'})
        return
    
    game.next_player()
    emit('game_updated', get_game_state(game, game_id))
    
    # If it's a bot's turn, handle that after a delay
    if game.current_player.is_bot:
        socketio.sleep(2)  # Wait 2 seconds before bot turn
        handle_bot_turn(game_id)

def handle_bot_turn(game_id):
    """Handle a bot's turn"""
    game = active_games.get(game_id)
    if not game or not game.current_player.is_bot:
        return
    
    # Send thinking message
    socketio.emit('game_message', {
        'game_id': game_id,
        'message': f"{game.current_player.name} is thinking..."
    })
    
    # Wait a bit to simulate thinking
    socketio.sleep(1.5)
    
    # Get the bot to select a target and card (we need to capture these before the action)
    bot = game.current_player
    card = random.choice(bot.hand) if bot.hand else None
    other_team = 1 if bot.team == 0 else 0
    other_team_players = [p for p in game.players if p.team == other_team]
    target = random.choice(other_team_players) if other_team_players else None
    
    if card and target:
        # Create log entry
        log_entry = {
            'type': 'request',
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'requester': {
                'name': bot.name,
                'team': bot.team,
                'is_human': False
            },
            'target': {
                'name': target.name,
                'team': target.team
            },
            'card': {
                'suit': card.suit,
                'rank': card.rank
            },
            'success': False  # Will be updated after request
        }
        
        # Handle bot turn
        result = game.handle_bot_turn()
        
        # Update success status in log
        log_entry['success'] = result
        
        # Send the log entry
        socketio.emit('game_log', log_entry)
    
    # Update game state
    socketio.emit('game_updated', get_game_state(game, game_id))
    
    # Move to next player after a delay
    socketio.sleep(4)
    game.next_player()
    socketio.emit('game_updated', get_game_state(game, game_id))
    
    # If the next player is also a bot and auto-play is on
    if game.current_player.is_bot and game.auto_play:
        handle_bot_turn(game_id)

@socketio.on('toggle_auto_play')
def handle_toggle_auto_play(data):
    """Toggle automatic bot turn processing"""
    game_id = data.get('game_id')
    auto_play = data.get('auto_play')
    
    game = active_games.get(game_id)
    if not game:
        emit('error', {'message': 'Game not found'})
        return
    
    game.auto_play = auto_play
    emit('auto_play_updated', {'game_id': game_id, 'auto_play': auto_play})
    
    # If auto-play is turned on and it's a bot's turn, start processing
    if auto_play and game.current_player.is_bot:
        handle_bot_turn(game_id)

def get_game_state(game, game_id):
    """Get the current game state to send to the client"""
    human = game.human_player
    current = game.current_player
    
    # Get human player's cards
    human_cards = []
    for card in human.hand:
        human_cards.append({
            'suit': card.suit,
            'rank': card.rank,
            'is_new': hasattr(game, 'received_card') and game.received_card and 
                     game.received_card.suit == card.suit and game.received_card.rank == card.rank
        })
    
    # Get player info
    players = []
    for i, player in enumerate(game.players):
        players.append({
            'index': i,
            'name': player.name,
            'is_bot': player.is_bot,
            'team': player.team,
            'card_count': len(player.hand),
            'is_current': player == current,
            'is_human': player == human,
            'can_request': current == human and player != human and 
                         game.can_request_from_player(human, player)
        })
    
    return {
        'game_id': game_id,
        'human_cards': human_cards,
        'players': players,
        'current_player_idx': game.current_player_idx,
        'human_player_idx': game.human_player_idx,
        'game_message': game.game_message,
        'team_names': game.team_names,
        'auto_play': getattr(game, 'auto_play', False)
    }

if __name__ == '__main__':
    # Ensure asset directories exist
    os.makedirs('assets', exist_ok=True)
    os.makedirs('assets/cards', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Download card images if not present
    from utils.card_downloader import download_card_images
    download_card_images()
    
    # Start the server
    log.info("Starting Literature Card Game Web Server")
    socketio.run(app, debug=True) 