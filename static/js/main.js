// Connect to WebSocket server
const socket = io();

// Game state
let gameState = null;
let selectedPlayerIdx = null;

// DOM elements
const menuScreen = document.getElementById('menu-screen');
const gameScreen = document.getElementById('game-screen');
const menuStatus = document.getElementById('menu-status');
const gameMessage = document.getElementById('game-message');
const playerInfo = document.getElementById('player-info');
const teamInfo = document.getElementById('team-info');
const playersGrid = document.getElementById('players-grid');
const cardsGrid = document.getElementById('cards-grid');
const popupEl = document.getElementById('card-selection-popup');
const cardFamilies = document.getElementById('card-families');

// Buttons
const start6PlayersBtn = document.getElementById('start-6-players');
const start8PlayersBtn = document.getElementById('start-8-players');
const playPauseBtn = document.getElementById('play-pause');
const nextBotBtn = document.getElementById('next-bot');
const returnMenuBtn = document.getElementById('return-menu');
const cancelRequestBtn = document.getElementById('cancel-request');

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initEventListeners();
    initSocketListeners();
});

// Initialize event listeners
function initEventListeners() {
    // Menu buttons
    start6PlayersBtn.addEventListener('click', () => createGame(6));
    start8PlayersBtn.addEventListener('click', () => createGame(8));
    
    // Game control buttons
    playPauseBtn.addEventListener('click', toggleAutoPlay);
    nextBotBtn.addEventListener('click', processNextBotTurn);
    returnMenuBtn.addEventListener('click', returnToMenu);
    
    // Popup buttons
    cancelRequestBtn.addEventListener('click', closeCardSelectionPopup);
}

// Socket event listeners
function initSocketListeners() {
    socket.on('connect', () => {
        console.log('Connected to server');
    });
    
    socket.on('game_created', (data) => {
        console.log('Game created:', data);
        gameState = data;
        showGameScreen();
        updateGameDisplay();
    });
    
    socket.on('game_updated', (data) => {
        console.log('Game updated:', data);
        gameState = data;
        updateGameDisplay();
    });
    
    socket.on('error', (data) => {
        console.error('Error:', data.message);
        menuStatus.textContent = data.message;
    });
    
    socket.on('game_message', (data) => {
        if (gameState && gameState.game_id === data.game_id) {
            gameMessage.textContent = data.message;
        }
    });
    
    socket.on('auto_play_updated', (data) => {
        if (gameState && gameState.game_id === data.game_id) {
            updateAutoPlayButton(data.auto_play);
        }
    });
}

// Create a new game
function createGame(playerCount) {
    menuStatus.textContent = `Creating ${playerCount}-player game...`;
    socket.emit('create_game', { player_count: playerCount });
}

// Show game screen (hide menu)
function showGameScreen() {
    menuScreen.classList.remove('active');
    gameScreen.classList.add('active');
}

// Show menu screen (hide game)
function showMenuScreen() {
    gameScreen.classList.remove('active');
    menuScreen.classList.add('active');
}

// Update the game display
function updateGameDisplay() {
    if (!gameState) return;
    
    // Update messages and info
    gameMessage.textContent = gameState.game_message;
    
    const currentPlayer = gameState.players.find(p => p.index === gameState.current_player_idx);
    playerInfo.textContent = `Current Player: ${currentPlayer.name} (${currentPlayer.card_count} cards)`;
    
    teamInfo.textContent = `Teams: ${gameState.team_names[0]} vs ${gameState.team_names[1]}`;
    
    // Update auto-play button
    updateAutoPlayButton(gameState.auto_play);
    
    // Update players grid
    updatePlayersGrid();
    
    // Update cards grid
    updateCardsGrid();
}

// Update the players grid
function updatePlayersGrid() {
    playersGrid.innerHTML = '';
    
    gameState.players.forEach(player => {
        const playerBtn = document.createElement('button');
        playerBtn.textContent = `${player.name}\n${player.card_count} cards\nTeam ${player.team + 1}`;
        playerBtn.className = 'player-button';
        
        // Add classes based on player status
        if (player.team === 0) playerBtn.classList.add('team-a');
        else playerBtn.classList.add('team-b');
        
        if (player.is_current) playerBtn.classList.add('current');
        if (player.is_human) playerBtn.classList.add('human');
        
        // Enable/disable based on can_request
        playerBtn.disabled = !player.can_request;
        
        // Add click handler for requesting cards
        if (player.can_request) {
            playerBtn.addEventListener('click', () => {
                selectedPlayerIdx = player.index;
                showCardSelectionPopup();
            });
        }
        
        playersGrid.appendChild(playerBtn);
    });
}

// Update the cards grid
function updateCardsGrid() {
    cardsGrid.innerHTML = '';
    
    // Sort cards by suit and rank
    const sortedCards = [...gameState.human_cards].sort((a, b) => {
        if (a.suit !== b.suit) return a.suit.localeCompare(b.suit);
        const rankOrder = {
            'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
            '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13
        };
        return rankOrder[a.rank] - rankOrder[b.rank];
    });
    
    sortedCards.forEach(card => {
        const cardDiv = document.createElement('div');
        cardDiv.className = 'card';
        if (card.is_new) cardDiv.classList.add('highlight');
        
        const imgPath = `/assets/cards/${card.suit.toLowerCase()}_${card.rank.toLowerCase()}.png`;
        const img = document.createElement('img');
        img.src = imgPath;
        img.alt = `${card.rank} of ${card.suit}`;
        img.onerror = () => {
            // Fallback to text if image fails to load
            img.remove();
            cardDiv.textContent = `${card.rank} of ${card.suit}`;
            if (card.suit === 'Hearts' || card.suit === 'Diamonds') {
                cardDiv.style.color = 'red';
            }
        };
        
        cardDiv.appendChild(img);
        cardsGrid.appendChild(cardDiv);
    });
}

// Show card selection popup
function showCardSelectionPopup() {
    if (!gameState) return;
    
    // Group cards by family
    const families = {};
    const humanCards = gameState.human_cards;
    
    humanCards.forEach(card => {
        // Determine family (Low or High)
        const isLow = ['A', '2', '3', '4', '5', '6', '7'].includes(card.rank);
        const family = (isLow ? 'Low ' : 'High ') + card.suit;
        
        if (!families[family]) {
            families[family] = {
                title: family,
                cards: []
            };
        }
        families[family].cards.push(card);
    });
    
    // Build the UI for card selection
    cardFamilies.innerHTML = '';
    
    Object.values(families).forEach(family => {
        const familyDiv = document.createElement('div');
        familyDiv.className = 'card-family';
        
        const titleEl = document.createElement('div');
        titleEl.className = 'family-title';
        titleEl.textContent = family.title;
        familyDiv.appendChild(titleEl);
        
        // Add all possible cards of this family
        const familyCards = getAllCardsInFamily(family.title);
        
        familyCards.forEach(card => {
            // Check if player already has this card
            const hasCard = humanCards.some(c => c.suit === card.suit && c.rank === card.rank);
            
            const cardBtn = document.createElement('div');
            cardBtn.className = 'card-option';
            if (hasCard) cardBtn.classList.add('disabled');
            
            cardBtn.textContent = `${card.rank} of ${card.suit}`;
            
            if (!hasCard) {
                cardBtn.addEventListener('click', () => {
                    requestCard(selectedPlayerIdx, card.suit, card.rank);
                    closeCardSelectionPopup();
                });
            }
            
            familyDiv.appendChild(cardBtn);
        });
        
        cardFamilies.appendChild(familyDiv);
    });
    
    // Show the popup
    popupEl.style.display = 'flex';
}

// Get all cards in a specific family
function getAllCardsInFamily(familyTitle) {
    const [type, suit] = familyTitle.split(' ');
    const isLow = type === 'Low';
    const ranks = isLow 
        ? ['A', '2', '3', '4', '5', '6', '7']
        : ['8', '9', '10', 'J', 'Q', 'K'];
    
    return ranks.map(rank => ({ suit, rank }));
}

// Close card selection popup
function closeCardSelectionPopup() {
    popupEl.style.display = 'none';
    selectedPlayerIdx = null;
}

// Request a card from another player
function requestCard(targetPlayerIdx, suit, rank) {
    if (!gameState) return;
    
    socket.emit('request_card', {
        game_id: gameState.game_id,
        target_player_idx: targetPlayerIdx,
        suit,
        rank
    });
}

// Toggle auto-play mode
function toggleAutoPlay() {
    if (!gameState) return;
    
    const newAutoPlay = !gameState.auto_play;
    
    socket.emit('toggle_auto_play', {
        game_id: gameState.game_id,
        auto_play: newAutoPlay
    });
    
    updateAutoPlayButton(newAutoPlay);
}

// Update auto-play button appearance
function updateAutoPlayButton(isActive) {
    if (isActive) {
        playPauseBtn.textContent = 'Auto Play: ON';
        playPauseBtn.classList.add('active');
    } else {
        playPauseBtn.textContent = 'Auto Play: OFF';
        playPauseBtn.classList.remove('active');
    }
}

// Process the next bot turn manually
function processNextBotTurn() {
    if (!gameState || !gameState.game_id) return;
    
    // Only process if current player is a bot
    const currentPlayer = gameState.players.find(p => p.index === gameState.current_player_idx);
    if (!currentPlayer || !currentPlayer.is_bot) {
        gameMessage.textContent = "It's not a bot's turn!";
        return;
    }
    
    // Request the server to process the next bot turn
    socket.emit('next_player', {
        game_id: gameState.game_id
    });
}

// Return to the menu screen
function returnToMenu() {
    showMenuScreen();
    gameState = null;
}
