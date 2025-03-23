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

// Add notification system functions
let activeNotifications = [];

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initEventListeners();
    initSocketListeners();
    setTimeout(debugCardImageLoading, 2000); // Wait 2 seconds before testing
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
    
    // Add keyboard navigation
    document.addEventListener('keydown', handleKeyPress);
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
            showNotification(entry);
            
            // If this was a successful card transfer, animate it
            if (entry.success) {
                // Find the player objects
                const fromPlayer = gameState.players.find(p => p.index === gameState.players.findIndex(p => p.name === entry.target.name));
                const toPlayer = gameState.players.find(p => p.index === gameState.players.findIndex(p => p.name === entry.requester.name));
                
                // Animate the transfer
                animateCardTransfer(fromPlayer, toPlayer, entry.card);
            }
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
    
    // Determine current team and highlight that column
    const currentPlayer = gameState.players.find(p => p.index === gameState.current_player_idx);
    if (currentPlayer.team === 0) {
        teamAColumn.classList.add('active');
    } else {
        teamBColumn.classList.add('active');
    }
    
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
            
            playerBtn.dataset.playerIndex = player.index;
            
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
            
            playerBtn.dataset.playerIndex = player.index;
            
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
    if (!cardsGrid) return;
    
    cardsGrid.innerHTML = '';
    
    // Sort cards
    const sortedCards = [...gameState.human_cards].sort((a, b) => {
        // Sort by suit first
        const suitOrder = {'Hearts': 1, 'Diamonds': 2, 'Clubs': 3, 'Spades': 4};
        const suitDiff = suitOrder[a.suit] - suitOrder[b.suit];
        if (suitDiff !== 0) return suitDiff;
        
        // Then by rank
        const rankOrder = {
            'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
            '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13
        };
        return rankOrder[a.rank] - rankOrder[b.rank];
    });
    
    sortedCards.forEach(card => {
        const cardEl = document.createElement('div');
        cardEl.className = 'card';
        if (card.is_new) cardEl.classList.add('highlight');
        
        const img = document.createElement('img');
        img.alt = `${card.rank} of ${card.suit}`;
        
        // Use our robust image loading function
        loadCardImageWithFallbacks(img, card.suit, card.rank, () => {
            // Fallback callback
            img.remove();
            cardEl.textContent = `${card.rank} of ${card.suit}`;
            // Add red color for hearts/diamonds
            if (card.suit === 'Hearts' || card.suit === 'Diamonds') {
                cardEl.style.color = 'red';
            }
        });
        
        cardEl.appendChild(img);
        cardsGrid.appendChild(cardEl);
    });
}

// Special handling for card image paths - try multiple potential filename patterns
function getCardImagePath(suit, rank) {
    const suitText = suit.toLowerCase();
    const rankText = rank.toLowerCase();
    
    // Return an array of possible paths to try in order
    return [
        `/assets/cards/${suitText}_${rankText}.png`,          // standard: hearts_10.png
        `/assets/cards/${rankText}_of_${suitText}.png`,       // alternate: 10_of_hearts.png
        `/assets/cards/${suitText}_${rank}.png`,              // case sensitive: hearts_10.png
        `/assets/cards/${rankText}${suitText[0]}.png`         // api style: 10h.png
    ];
}

// Update card image loading with fallback paths
function loadCardImageWithFallbacks(imgElement, suit, rank, fallbackCallback) {
    const paths = getCardImagePath(suit, rank);
    let pathIndex = 0;
    
    // Try loading image from first path
    imgElement.src = paths[pathIndex];
    
    // Handle error by trying next path or falling back to text
    imgElement.onerror = function() {
        pathIndex++;
        if (pathIndex < paths.length) {
            // Try next path
            imgElement.src = paths[pathIndex];
        } else {
            // All paths failed, use fallback
            fallbackCallback();
        }
    };
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
        game_id: gameState.game_id,
        force_bot_turn: true  // Add this parameter to force bot turn
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
    cardImg.alt = `${entry.card.rank} of ${entry.card.suit}`;
    
    // Use our robust image loading function
    loadCardImageWithFallbacks(
        cardImg, 
        entry.card.suit, 
        entry.card.rank, 
        () => {
            cardImg.remove();
            message.appendChild(document.createTextNode(`${entry.card.rank} of ${entry.card.suit}`));
        }
    );
    
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

// Add this function to help debug the card image loading
function debugCardImageLoading() {
    // Log all the card image loading attempts
    console.log("Debugging card images...");
    
    const suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades'];
    const ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'];
    
    suits.forEach(suit => {
        ranks.forEach(rank => {
            const paths = getCardImagePath(suit, rank);
            console.log(`Card: ${rank} of ${suit}, Paths:`, paths);
            
            // Create a test image to check if it loads
            const testImg = new Image();
            testImg.onload = () => console.log(`SUCCESS: ${testImg.src} loaded`);
            testImg.onerror = () => console.log(`FAILED: ${testImg.src} not found`);
            testImg.src = paths[0];
        });
    });
}

// Add a notification for an action
function showNotification(entry) {
    // Create notification container if it doesn't exist
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.classList.add(entry.success ? 'success' : 'failure');
    
    // Create timer bar
    const timer = document.createElement('div');
    timer.className = 'notification-timer';
    notification.appendChild(timer);
    
    // Create close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'notification-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('click', () => {
        removeNotification(notification);
    });
    notification.appendChild(closeBtn);
    
    // Create notification content by cloning log entry format
    const content = document.createElement('div');
    
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
    content.appendChild(requesterName);
    content.appendChild(document.createTextNode(' requested '));
    
    // Add visual card
    const cardImg = document.createElement('img');
    cardImg.className = 'notification-card';
    cardImg.alt = `${entry.card.rank} of ${entry.card.suit}`;
    
    // Use our robust image loading function
    loadCardImageWithFallbacks(
        cardImg, 
        entry.card.suit, 
        entry.card.rank, 
        () => {
            cardImg.remove();
            content.appendChild(document.createTextNode(`${entry.card.rank} of ${entry.card.suit}`));
        }
    );
    
    content.appendChild(cardImg);
    
    content.appendChild(document.createTextNode(' from '));
    content.appendChild(targetName);
    
    // Add result
    const resultText = entry.success ? ' and got it!' : ' but failed.';
    content.appendChild(document.createTextNode(resultText));
    
    notification.appendChild(content);
    
    // Add to container
    container.appendChild(notification);
    
    // Track this notification
    const notificationId = Date.now();
    notification.dataset.id = notificationId;
    activeNotifications.push(notificationId);
    
    // Trigger animation after a small delay (for browser to process)
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Auto dismiss after 4 seconds
    const timeoutId = setTimeout(() => {
        removeNotification(notification);
    }, 4000);
    
    notification.dataset.timeoutId = timeoutId;
    
    return notification;
}

// Remove a notification
function removeNotification(notification) {
    // Clear the timeout if it exists
    if (notification.dataset.timeoutId) {
        clearTimeout(parseInt(notification.dataset.timeoutId, 10));
    }
    
    // Remove show class to trigger fade out
    notification.classList.remove('show');
    
    // Remove from DOM after animation completes
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
        
        // Remove from active notifications
        const index = activeNotifications.indexOf(parseInt(notification.dataset.id, 10));
        if (index > -1) {
            activeNotifications.splice(index, 1);
        }
    }, 300);
}

// Remove all active notifications
function clearAllNotifications() {
    const container = document.getElementById('notification-container');
    if (container) {
        const notifications = container.querySelectorAll('.notification');
        notifications.forEach(removeNotification);
    }
}

// Handle keyboard navigation
function handleKeyPress(event) {
    // Only process when game is active
    if (!gameState || !document.getElementById('game-screen').classList.contains('active')) {
        return;
    }
    
    // Right arrow key - process next bot turn and clear notifications
    if (event.key === 'ArrowRight') {
        clearAllNotifications();
        processNextBotTurn();
        event.preventDefault(); // Prevent default browser behavior (like scrolling)
    }
    
    // Escape key - close popup if open
    if (event.key === 'Escape') {
        closeCardSelectionPopup();
        event.preventDefault();
    }
}

// Card transfer animation
function animateCardTransfer(fromPlayer, toPlayer, card) {
    // Only animate on successful transfers
    if (!fromPlayer || !toPlayer || !card) return;
    
    // Find player elements
    const fromPlayerEl = document.querySelector(`.player-button[data-player-index="${fromPlayer.index}"]`);
    const toPlayerEl = document.querySelector(`.player-button[data-player-index="${toPlayer.index}"]`);
    
    if (!fromPlayerEl || !toPlayerEl) return;
    
    // Get positions
    const fromRect = fromPlayerEl.getBoundingClientRect();
    const toRect = toPlayerEl.getBoundingClientRect();
    
    // Create moving card element
    const cardEl = document.createElement('img');
    cardEl.className = 'transfer-card';
    cardEl.alt = `${card.rank} of ${card.suit}`;
    
    // Load card image using our helper
    loadCardImageWithFallbacks(
        cardEl, 
        card.suit, 
        card.rank, 
        () => {
            // If image fails to load, use a generic card back
            cardEl.src = '/assets/cards/card_back.png';
        }
    );
    
    // Position at start point
    cardEl.style.left = `${fromRect.left + fromRect.width/2 - 35}px`;
    cardEl.style.top = `${fromRect.top + fromRect.height/2 - 49}px`;
    
    // Add to DOM
    document.body.appendChild(cardEl);
    
    // Calculate animation path
    const endX = toRect.left + toRect.width/2 - 35;
    const endY = toRect.top + toRect.height/2 - 49;
    const startX = parseFloat(cardEl.style.left);
    const startY = parseFloat(cardEl.style.top);
    const distance = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
    
    // Set animation duration based on distance (faster for shorter distances)
    const duration = Math.min(1.5, Math.max(0.8, distance / 800));
    
    // Apply animation
    cardEl.style.animation = `transferCard ${duration}s forwards`;
    
    // Create sparkle trail effect
    let sparkleCount = 0;
    const maxSparkles = 15;
    const sparkleInterval = setInterval(() => {
        if (sparkleCount >= maxSparkles) {
            clearInterval(sparkleInterval);
            return;
        }
        
        // Create sparkle element
        const sparkle = document.createElement('div');
        sparkle.className = 'sparkle';
        
        // Position along the path (with randomness)
        const progress = sparkleCount / maxSparkles;
        const posX = startX + (endX - startX) * progress + (Math.random() * 40 - 20);
        const posY = startY + (endY - startY) * progress + (Math.random() * 40 - 20);
        
        sparkle.style.left = `${posX}px`;
        sparkle.style.top = `${posY}px`;
        sparkle.style.animation = `sparkle ${0.5 + Math.random() * 0.5}s forwards`;
        
        // Add to DOM
        document.body.appendChild(sparkle);
        
        // Remove after animation
        setTimeout(() => {
            if (sparkle.parentNode) {
                sparkle.parentNode.removeChild(sparkle);
            }
        }, 1000);
        
        sparkleCount++;
    }, duration * 1000 / maxSparkles);
    
    // Move card
    const animationFrames = 60;
    let frame = 0;
    
    const moveCard = () => {
        if (frame >= animationFrames) {
            // Animation complete, remove card
            if (cardEl.parentNode) {
                cardEl.parentNode.removeChild(cardEl);
            }
            return;
        }
        
        const progress = frame / animationFrames;
        const newX = startX + (endX - startX) * progress;
        const newY = startY + (endY - startY) * progress;
        
        cardEl.style.left = `${newX}px`;
        cardEl.style.top = `${newY}px`;
        
        frame++;
        requestAnimationFrame(moveCard);
    };
    
    requestAnimationFrame(moveCard);
    
    // Clean up after animation
    setTimeout(() => {
        if (cardEl.parentNode) {
            cardEl.parentNode.removeChild(cardEl);
        }
    }, duration * 1000 + 100);
}
