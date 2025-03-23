"""
Literature Card Game - Core Game Logic
Separated from the web interface for clean architecture
"""
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

class Card:
    """A simple playing card"""
    SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
    
    def __str__(self):
        return f"{self.rank} of {self.suit}"
    
    def get_family(self):
        """Get the card family (used for Literature game rules)"""
        # Move Ace to high set, only 2-7 are in low sets now
        if self.rank in ['2', '3', '4', '5', '6', '7']:
            return f"Low {self.suit}"
        else:
            return f"High {self.suit}"

class Player:
    """A player with a hand of cards"""
    def __init__(self, name, is_bot=True, team=0):
        self.name = name
        self.hand = []
        self.is_bot = is_bot
        self.team = team  # 0 for first team, 1 for second team
        
    def add_card(self, card):
        self.hand.append(card)
        
    def remove_card(self, suit, rank):
        """Remove a card from player's hand if it exists"""
        for i, card in enumerate(self.hand):
            if card.suit == suit and card.rank == rank:
                return self.hand.pop(i)
        return None
    
    def has_card(self, suit, rank):
        """Check if player has the specified card"""
        for card in self.hand:
            if card.suit == suit and card.rank == rank:
                return True
        return False
    
    def has_card_of_family(self, family):
        """Check if player has any card of a specific family"""
        for card in self.hand:
            if card.get_family() == family:
                return True
        return False

class Bot(Player):
    """AI player that makes automatic moves"""
    def __init__(self, name, team=0):
        super().__init__(name, is_bot=True, team=team)
    
    def take_turn(self, game):
        """Bot takes its turn automatically"""
        # Simple strategy: randomly ask another player for a card the bot has
        if not self.hand:
            message = f"{self.name} has no cards, skipping turn"
            game.game_message = message
            log.info(message)
            return False
            
        # Choose a random card from hand
        card = random.choice(self.hand)
        
        # Choose a random player from the other team
        other_team = 1 if self.team == 0 else 0
        other_team_players = [p for p in game.players if p.team == other_team]
        
        if not other_team_players:
            return False
            
        target_player = random.choice(other_team_players)
        
        # Store the current request info for logging
        game.last_request = {
            'requester': self,
            'target': target_player,
            'card': card
        }
        
        # Find the target player's index for turn management
        target_player_idx = game.players.index(target_player)
        
        # Create detailed message about the request
        request_message = f"{self.name} asks {target_player.name} for the {card.rank} of {card.suit}"
        game.game_message = request_message
        log.info(request_message)
        
        # Check if target has the card
        if target_player.has_card(card.suit, card.rank):
            # Success! Get the card
            target_card = target_player.remove_card(card.suit, card.rank)
            if target_card:
                self.add_card(target_card)
                result_message = f"SUCCESS! {self.name} got the {card.rank} of {card.suit} from {target_player.name}"
                game.game_message = result_message
                log.info(result_message)
                # Bot gets another turn on success
                return True
        
        fail_message = f"{target_player.name} doesn't have the {card.rank} of {card.suit}"
        game.game_message = fail_message
        log.info(fail_message)
        
        # On failure, turn passes to the target player
        game.current_player_idx = target_player_idx
        return False

class Game:
    """Core game logic"""
    def __init__(self, num_players=6, human_player_idx=0):
        log.info(f"Creating new game with {num_players} players (human is player {human_player_idx+1})")
        
        # Create players - one human, rest bots, split into teams
        self.players = []
        half = num_players // 2
        
        for i in range(num_players):
            team = 0 if i < half else 1
            if i == human_player_idx:
                self.players.append(Player(f"Player {i+1} (You)", is_bot=False, team=team))
            else:
                self.players.append(Bot(f"Bot {i+1}", team=team))
                
        self.human_player_idx = human_player_idx
        self.current_player_idx = 0
        self.auto_play = False
        
        # Team names
        self.team_names = ["Team A", "Team B"]
        
        # Create and deal cards
        self.create_deck()
        self.deal_cards()
        
        # Game state
        self.game_message = "Game started. It's your turn!"
        
        # Print game setup info
        for player in self.players:
            log.info(f"{player.name} has {len(player.hand)} cards (Team {player.team+1})")
    
    def create_deck(self):
        """Create a standard deck of cards"""
        self.deck = []
        for suit in Card.SUITS:
            for rank in Card.RANKS:
                self.deck.append(Card(suit, rank))
        
        random.shuffle(self.deck)
        log.info(f"Created and shuffled deck with {len(self.deck)} cards")
    
    def deal_cards(self):
        """Deal cards to all players"""
        cards_per_player = 6 if len(self.players) == 8 else 8
        log.info(f"Dealing {cards_per_player} cards per player")
        
        for _ in range(cards_per_player):
            for player in self.players:
                if self.deck:
                    card = self.deck.pop()
                    player.add_card(card)
    
    @property
    def current_player(self):
        return self.players[self.current_player_idx]
    
    @property
    def human_player(self):
        return self.players[self.human_player_idx]
    
    def next_player(self):
        """Move to the next player's turn"""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        player = self.current_player
        
        if player.is_bot:
            self.game_message = f"It's {player.name}'s turn"
        else:
            self.game_message = f"It's your turn! Select a player to request a card."
            
        log.info(f"Next player: {player.name}")
        return player
    
    def can_request_from_player(self, from_player, to_player):
        """Check if a player can request a card from another player"""
        # Can only request from players on the other team
        return from_player.team != to_player.team
    
    def can_request_card(self, player, suit, rank):
        """Check if player can request a specific card"""
        # Player can't request a card they already have
        if player.has_card(suit, rank):
            return False
            
        # Player must have at least one card from the same family
        card = Card(suit, rank)
        family = card.get_family()
        return player.has_card_of_family(family)
    
    def handle_bot_turn(self):
        """Handle a bot's turn"""
        if not self.current_player or not self.current_player.is_bot:
            return False
        
        bot = self.current_player
        result = bot.take_turn(self)
        
        # If the bot's turn was successful, don't change players
        # Otherwise, handle in the Bot.take_turn method
        return result
    
    def request_card(self, target_player_idx, suit, rank):
        """Human player requests a card from another player"""
        # Verify it's the human's turn
        if self.current_player_idx != self.human_player_idx:
            self.game_message = "It's not your turn!"
            return False
        
        human = self.human_player
        target = self.players[target_player_idx]
        
        # Verify the target is valid (different team)
        if not self.can_request_from_player(human, target):
            self.game_message = f"You can only request cards from the other team!"
            return False
            
        # Verify the card request is valid (same family, don't have it)
        if not self.can_request_card(human, suit, rank):
            self.game_message = f"You can only request cards from families you already have!"
            return False
            
        # Create a detailed message about the request
        request_message = f"YOU asked {target.name} for the {rank} of {suit}"
        self.game_message = request_message
        log.info(f"{human.name} asks {target.name} for {rank} of {suit}")
        
        # Check if target has the card
        if target.has_card(suit, rank):
            # Success! Get the card
            card = target.remove_card(suit, rank)
            if card:
                human.add_card(card)
                result_message = f"SUCCESS! You got the {rank} of {suit} from {target.name}"
                self.game_message = result_message
                
                # Add a visual indicator for the new card
                self.received_card = card
                
                # Don't change turn on success - player gets another turn
                return True
        
        fail_message = f"{target.name} doesn't have the {rank} of {suit}"
        self.game_message = fail_message
        
        # On failure, the turn passes to the player who was asked
        self.current_player_idx = target_player_idx
        return False
    
    def make_declaration(self, family):
        """Make a declaration for a complete family of cards"""
        # TODO: Implement in a future update
        pass 