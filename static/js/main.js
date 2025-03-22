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
    
    socket.on('game_log', (entry) => {
        if (gameState) {
            addLogEntry(entry);
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
    
    // Set up the main game board layout
    updateMainBoardLayout();
    
    // Update cards grid - this should happen AFTER we create the grid
    updateCardsGrid();
}

// Set up the main board layout with teams on sides and cards in middle
function updateMainBoardLayout() {
    // Get the main content container
    const mainContent = document.querySelector('.main-content');
    mainContent.innerHTML = '';
    
    // Create team columns
    const teamAColumn = document.createElement('div');
    teamAColumn.className = 'team-column team-a-column';
    
    const teamBColumn = document.createElement('div');
    teamBColumn.className = 'team-column team-b-column';
    
    // Add team headers
    const teamAHeader = document.createElement('div');
    teamAHeader.className = 'team-header team-a';
    teamAHeader.textContent = gameState.team_names[0];
    teamAColumn.appendChild(teamAHeader);
    
    const teamBHeader = document.createElement('div');
    teamBHeader.className = 'team-header team-b';
    teamBHeader.textContent = gameState.team_names[1];
    teamBColumn.appendChild(teamBHeader);
    
    // Add players to team columns
    gameState.players.forEach(player => {
        const playerBtn = document.createElement('button');
        playerBtn.textContent = `${player.name}\n${player.card_count} cards`;
        playerBtn.className = 'player-button';
        
        // Process based on team
        if (player.team === 0) {
            playerBtn.classList.add('team-a');
            if (player.is_current) playerBtn.classList.add('current');
            if (player.is_human) playerBtn.classList.add('human');
            playerBtn.disabled = !player.can_request;
            
            if (player.can_request) {
                playerBtn.addEventListener('click', () => {
                    selectedPlayerIdx = player.index;
                    showCardSelectionPopup();
                });
            }
            
            teamAColumn.appendChild(playerBtn);
        } else {
            playerBtn.classList.add('team-b');
            if (player.is_current) playerBtn.classList.add('current');
            if (player.is_human) playerBtn.classList.add('human');
            playerBtn.disabled = !player.can_request;
            
            if (player.can_request) {
                playerBtn.addEventListener('click', () => {
                    selectedPlayerIdx = player.index;
                    showCardSelectionPopup();
                });
            }
            
            teamBColumn.appendChild(playerBtn);
        }
    });
    
    // Create cards container in the middle
    const cardsContainer = document.createElement('div');
    cardsContainer.className = 'cards-container';
    
    const cardsTitle = document.createElement('h3');
    cardsTitle.textContent = 'Your Cards';
    cardsContainer.appendChild(cardsTitle);
    
    const cardsGrid = document.createElement('div');
    cardsGrid.id = 'cards-grid';
    cardsGrid.className = 'cards-grid';
    cardsContainer.appendChild(cardsGrid);
    
    // Add all elements to main content in the correct order
    mainContent.appendChild(teamAColumn);
    mainContent.appendChild(cardsContainer);
    mainContent.appendChild(teamBColumn);
}

// Update the cards grid
function updateCardsGrid() {
    // Get the cards grid that was dynamically created
    const cardsGrid = document.getElementById('cards-grid');
    if (!cardsGrid) return; // Safety check
    
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
        // Determine family (Low or High) - Ace is now part of High
        const isLow = ['2', '3', '4', '5', '6', '7'].includes(card.rank);
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
    // Update the rank arrays - Ace moved to high group
    const ranks = isLow 
        ? ['2', '3', '4', '5', '6', '7']
        : ['A', '8', '9', '10', 'J', 'Q', 'K'];
    
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

// Add a new log entry to the game log
function addLogEntry(entry) {
    const gameLog = document.getElementById('game-log');
    
    // Create log entry element
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    
    // Add timestamp
    const timestamp = document.createElement('span');
    timestamp.className = 'log-timestamp';
    timestamp.textContent = entry.timestamp;
    logEntry.appendChild(timestamp);
    
    // Create message content
    const message = document.createElement('div');
    message.className = 'log-message';
    
    // Format requester name
    const requesterTeamClass = entry.requester.team === 0 ? 'log-team-a' : 'log-team-b';
    const requesterName = document.createElement('span');
    requesterName.className = `log-player-name ${requesterTeamClass}`;
    requesterName.textContent = entry.requester.name;
    
    // Format target name
    const targetTeamClass = entry.target.team === 0 ? 'log-team-a' : 'log-team-b';
    const targetName = document.createElement('span');
    targetName.className = `log-player-name ${targetTeamClass}`;
    targetName.textContent = entry.target.name;
    
    // Create message with visual card
    message.appendChild(requesterName);
    message.appendChild(document.createTextNode(' requested '));
    
    // Add visual card
    const cardImg = document.createElement('img');
    cardImg.className = 'log-card';
    cardImg.src = `/assets/cards/${entry.card.suit.toLowerCase()}_${entry.card.rank.toLowerCase()}.png`;
    cardImg.alt = `${entry.card.rank} of ${entry.card.suit}`;
    cardImg.onerror = () => {
        cardImg.remove();
        message.appendChild(document.createTextNode(`${entry.card.rank} of ${entry.card.suit}`));
    };
    message.appendChild(cardImg);
    
    message.appendChild(document.createTextNode(' from '));
    message.appendChild(targetName);
    
    // Add result
    const resultText = entry.success ? ' and got it!' : ' but failed.';
    message.appendChild(document.createTextNode(resultText));
    
    logEntry.appendChild(message);
    
    // Insert at the beginning (most recent at the top)
    if (gameLog.firstChild) {
        gameLog.insertBefore(logEntry, gameLog.firstChild);
    } else {
        gameLog.appendChild(logEntry);
    }
    
    // Keep only the most recent two entries
    while (gameLog.children.length > 2) {
        gameLog.removeChild(gameLog.lastChild);
    }
}
