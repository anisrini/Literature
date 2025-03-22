// Connect to Socket.IO server
const socket = io();

// Add connection diagnostics
socket.on('connect', function() {
    console.log('✅ Socket connected successfully! Socket ID:', socket.id);
    showNotification('Connected to server', 'success');
});

socket.on('connect_error', function(error) {
    console.error('❌ Socket connection error:', error);
    showNotification('Connection error: ' + error.message, 'error');
});

socket.on('disconnect', function(reason) {
    console.warn('⚠️ Socket disconnected:', reason);
    showNotification('Disconnected from server: ' + reason, 'warning');
});

// Game state variables
let myPlayerId = null;
let currentTurn = null;
let myHand = [];
let gameStarted = false;
let availableSets = [];
let selectedCards = [];
let selectedSet = null;
let declareMode = false;
let opponentData = [];

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Checking game configuration');
    
    // Check if GAME_ID is properly defined
    if (typeof GAME_ID === 'undefined') {
        console.error('❌ GAME_ID is not defined!');
        alert('Error: Game ID is not properly set. Please check the page configuration.');
    } else {
        console.log('✅ GAME_ID is defined:', GAME_ID);
    }
    
    // Get DOM elements
    const gameId = document.getElementById('game-id');
    const copyBtn = document.getElementById('copy-game-id');
    const joinBtn = document.getElementById('join-game-btn');
    const playerNameInput = document.getElementById('player-name');
    const waitingScreen = document.getElementById('waiting-screen');
    const gameScreen = document.getElementById('game-screen');
    const playersJoined = document.getElementById('players-joined');
    const playerCount = document.getElementById('player-count');
    const playerTarget = document.getElementById('player-target');
    const turnStatus = document.getElementById('turn-status');
    const botGameControls = document.getElementById('bot-game-controls');
    const forceStartBtn = document.getElementById('force-start-game');
    const playerHand = document.getElementById('player-hand');
    const requestPanel = document.getElementById('request-panel');
    const declarePanel = document.getElementById('declare-panel');
    const waitingPanel = document.getElementById('waiting-panel');
    const targetPlayerSelect = document.getElementById('target-player');
    const cardRankSelect = document.getElementById('card-rank');
    const cardSuitSelect = document.getElementById('card-suit');
    const setNameSelect = document.getElementById('set-name');
    const cardAssignments = document.getElementById('card-assignments');
    const sendRequestBtn = document.getElementById('send-request');
    const sendDeclarationBtn = document.getElementById('send-declaration');
    const logContainer = document.getElementById('log-container');
    const team1Score = document.getElementById('team1-score');
    const team2Score = document.getElementById('team2-score');
    const opponentsArea = document.getElementById('opponents-area');
    
    // Add this here to ensure everything's properly defined first
    setupGameEvents();
    
    // Auto-switch to game screen after a delay as a fallback
    setTimeout(function() {
        if (gameStarted && waitingScreen && waitingScreen.style.display !== 'none') {
            console.log('Fallback: Switching to game screen after timeout');
            switchToGameScreen();
        }
    }, 5000);  // 5 second fallback
    
    // Function to setup all game-related events
    function setupGameEvents() {
        // Set up event listeners
        copyBtn.addEventListener('click', function() {
            navigator.clipboard.writeText(gameId.textContent);
            alert('Game ID copied to clipboard!');
        });
        
        // Replace the existing join button event listener with this enhanced version
        joinBtn.addEventListener('click', function() {
            console.log('🖱️ Join button clicked');
            
            try {
                const playerName = playerNameInput.value.trim() || 'Player';
                console.log('📝 Player name:', playerName, 'Game ID:', GAME_ID);
                
                // Show feedback to user
                showNotification('Attempting to join game...', 'info');
                
                // Validate game ID
                if (!GAME_ID) {
                    console.error('❌ Game ID is missing or invalid');
                    showNotification('Error: Game ID is missing', 'error');
                    return;
                }
                
                // Disable button to prevent multiple clicks
                joinBtn.disabled = true;
                joinBtn.textContent = 'Joining...';
                
                // Join the game with a timeout for better UX
                setTimeout(() => {
                    // Check socket connection before emitting
                    if (!socket.connected) {
                        console.error('❌ Socket not connected when trying to join game');
                        showNotification('Error: Not connected to server', 'error');
                        joinBtn.disabled = false;
                        joinBtn.textContent = 'Join Game';
                        return;
                    }
                    
                    console.log('🚀 Emitting join_game event:', {
                        game_id: GAME_ID,
                        player_name: playerName
                    });
                    
                    // Emit the join event
                    socket.emit('join_game', {
                        game_id: GAME_ID,
                        player_name: playerName
                    });
                    
                    // Set a timeout to re-enable button if no response
                    setTimeout(() => {
                        if (joinBtn.disabled) {
                            joinBtn.disabled = false;
                            joinBtn.textContent = 'Join Game';
                            showNotification('Server didn\'t respond. Try again.', 'warning');
                        }
                    }, 5000);
                }, 100);
            } catch (err) {
                console.error('❌ Error in join button handler:', err);
                showNotification('Error joining game: ' + err.message, 'error');
                
                // Re-enable button
                joinBtn.disabled = false;
                joinBtn.textContent = 'Join Game';
            }
        });
        
        // Add event listener for force start
        if (forceStartBtn) {
            forceStartBtn.addEventListener('click', function() {
                socket.emit('force_start_game', { game_id: GAME_ID });
            });
        }
        
        // Socket event handlers
        socket.on('player_joined', function(data) {
            console.log('👤 Player joined event received:', data);
            
            try {
                // Update player list
                const playerCount = document.getElementById('player-count');
                const playerTarget = document.getElementById('player-target');
                const playersJoined = document.getElementById('players-joined');
                const botGameControls = document.getElementById('bot-game-controls');
                
                if (!playerCount || !playerTarget || !playersJoined) {
                    console.error('❌ Required DOM elements not found for player_joined handler');
                    return;
                }
                
                // Update counts
                playerCount.textContent = data.players.length;
                playerTarget.textContent = data.player_count;
                
                // Show bot controls if real_player_count is set (meaning bots are enabled)
                if (data.real_player_count && botGameControls) {
                    botGameControls.style.display = 'block';
                }
                
                // Update players joined list
                playersJoined.innerHTML = '';
                
                if (!data.players || !Array.isArray(data.players)) {
                    console.warn('⚠️ Invalid players array in player_joined event');
                    playersJoined.innerHTML = '<li>Error loading player list</li>';
                    return;
                }
                
                data.players.forEach(player => {
                    const li = document.createElement('li');
                    li.textContent = player.name || 'Unnamed Player';
                    
                    // Add special styling for bot players
                    if (player.is_bot) {
                        li.classList.add('bot-player');
                        li.textContent += ' (Bot)';
                    }
                    
                    playersJoined.appendChild(li);
                });
                
                // Re-enable join button if it was disabled
                const joinBtn = document.getElementById('join-game-btn');
                if (joinBtn && joinBtn.disabled) {
                    joinBtn.disabled = false;
                    joinBtn.textContent = 'Join Game';
                }
                
                // Show notification
                const latestPlayer = data.players[data.players.length - 1];
                if (latestPlayer) {
                    showNotification(`${latestPlayer.name} joined the game`, 'info');
                }
            } catch (err) {
                console.error('❌ Error handling player_joined event:', err);
            }
        });
        
        socket.on('game_started', function(data) {
            console.log('Game started received!', data);
            
            // Fix screen transition
            try {
                // Get fresh references to these elements
                const waitingScreen = document.getElementById('waiting-screen');
                const gameScreen = document.getElementById('game-screen');
                
                if (waitingScreen && gameScreen) {
                    console.log('Found screen elements, switching views');
                    
                    // First add a class instead of setting style directly
                    waitingScreen.classList.add('hidden');
                    gameScreen.classList.remove('hidden');
                    gameScreen.classList.add('active');
                    
                    // Also set style directly as backup
                    waitingScreen.style.display = 'none';
                    gameScreen.style.display = 'flex';
                    
                    gameStarted = true;
                    console.log('Switched to game screen successfully');
                    
                    // Force a redraw
                    setTimeout(function() {
                        window.dispatchEvent(new Event('resize'));
                    }, 100);
                } else {
                    console.error('Screen elements not found');
                    alert('Error: Could not find game screen elements. Try refreshing the page.');
                }
            } catch (err) {
                console.error('Error switching screens:', err);
                alert('Error switching screens: ' + err.message);
            }
            
            // Set up our enhanced UI components
            setupCardRequestWizard();
            setupSetDeclarationWizard();
            
            // Add this to ensure we have refresh controls
            setupRefreshControls();
        }
        
        socket.on('game_state_update', function(data) {
            console.log('🔄 Received game state update');
            
            try {
                // CRITICAL: Store all state data immediately and properly
                if (data.my_id !== undefined) {
                    myPlayerId = data.my_id;
                    sessionStorage.setItem('myPlayerId', data.my_id);
                    console.log('👤 Player ID set to:', myPlayerId);
                }
                
                if (data.current_turn !== undefined) {
                    currentTurn = data.current_turn;
                }
                
                if (data.my_hand !== undefined) {
                    myHand = data.my_hand;
                }
                
                if (data.available_sets !== undefined) {
                    availableSets = data.available_sets;
                }
                
                // IMPORTANT: Always update opponent data if available
                if (data.opponents && Array.isArray(data.opponents)) {
                    // Store a deep copy to avoid reference issues
                    opponentData = JSON.parse(JSON.stringify(data.opponents));
                    console.log('👥 Updated opponent data with', opponentData.length, 'players');
                    
                    // Store in sessionStorage for recovery
                    sessionStorage.setItem('lastOpponentData', JSON.stringify(opponentData));
                } else {
                    console.warn('⚠️ No opponent data in game state update');
                    
                    // Try to recover from session storage
                    const storedData = sessionStorage.getItem('lastOpponentData');
                    if (storedData && (!opponentData || opponentData.length === 0)) {
                        opponentData = JSON.parse(storedData);
                        console.log('🔄 Recovered opponent data from session storage:', opponentData.length, 'players');
                    }
                }
                
                // Ensure game started flag is set
                gameStarted = true;
                
                // Now update all UI elements in the correct order
                updatePlayerHand(myHand);
                
                // IMPORTANT: Explicitly force opponent display update
                if (opponentData && opponentData.length > 0) {
                    forceOpponentDisplay(); // Use our robust display function
                } else {
                    console.warn('⚠️ Cannot update opponents - no data available');
                }
                
                updateTurnStatus(currentTurn);
                updateActionPanels(); // New function to ensure action panels are properly set up
                
                // Update game log if available
                if (data.game_log && data.game_log.length > 0) {
                    updateGameLog(data.game_log);
                }
                
                // Update scores if available
                if (data.team1_sets !== undefined && data.team2_sets !== undefined) {
                    updateScores(data.team1_sets, data.team2_sets);
                }
                
                // Run diagnostic check after updates
                const diagnostics = debugFullGameState();
                
                // If we still don't have opponent elements but should, try one more time
                if (diagnostics.hasOpponentData && !diagnostics.hasOpponentElements) {
                    console.warn('⚠️ Opponent data exists but no elements rendered - forcing second update');
                    setTimeout(forceOpponentDisplay, 300);
                }
            } catch (err) {
                console.error('❌ Error processing game state:', err);
                showNotification('Error updating game state. Try refreshing.', 'error');
            }
        });
        
        socket.on('error', function(data) {
            alert('Error: ' + data.message);
        });

        // Add this after your other socket events
        socket.on('connect', function() {
            console.log('Connected to server!');
            
            // Reattach to game if we were already playing
            if (GAME_ID) {
                console.log('Attempting to rejoin game:', GAME_ID);
                attemptRejoin();
            }
        });

        socket.on('connect_error', function(err) {
            console.error('Connection error:', err);
            alert('Connection error. Please refresh the page.');
        });

        socket.on('disconnect', function() {
            console.warn('Disconnected from server. Attempting reconnect...');
            // The socket.io client will automatically try to reconnect
        });

        // Add this to help debug
        window.debugGame = function() {
            console.log({
                waitingScreen: document.getElementById('waiting-screen'),
                gameScreen: document.getElementById('game-screen'),
                gameStarted: gameStarted,
                myPlayerId: myPlayerId,
                socketConnected: socket.connected
            });
        };

        // Add handlers for card request results
        socket.on('card_request_result', function(data) {
            console.log('Card request result:', data);
            
            const requestingPlayer = data.requesting_player;
            const targetPlayer = data.target_player;
            const card = data.card;
            const success = data.success;
            
            // Create message
            let message = '';
            let messageClass = '';
            
            if (requestingPlayer === myPlayerId) {
                // I was the requester
                if (success) {
                    message = `You received the ${card.rank} of ${card.suit} from ${targetPlayer.name}!`;
                    messageClass = 'success';
                } else {
                    message = `${targetPlayer.name} didn't have the ${card.rank} of ${card.suit}.`;
                    messageClass = 'failure';
                }
            } else if (targetPlayer.id === myPlayerId) {
                // I was the target
                if (success) {
                    message = `You gave the ${card.rank} of ${card.suit} to ${requestingPlayer.name}.`;
                    messageClass = 'neutral';
                } else {
                    message = `${requestingPlayer.name} asked for the ${card.rank} of ${card.suit}, but you don't have it.`;
                    messageClass = 'neutral';
                }
            } else {
                // I was neither
                if (success) {
                    message = `${requestingPlayer.name} received a card from ${targetPlayer.name}.`;
                } else {
                    message = `${requestingPlayer.name} asked ${targetPlayer.name} for a card but didn't get it.`;
                }
                messageClass = 'other-player';
            }
            
            // Display notification
            showNotification(message, messageClass);
            
            // We'll automatically get a game state update after this
        });

        // Add handlers for set declaration results
        socket.on('set_declaration_result', function(data) {
            console.log('Set declaration result:', data);
            
            const declaringPlayer = data.declaring_player;
            const setName = data.set_name;
            const success = data.success;
            const teamThatWon = data.team_that_won;
            
            // Create message
            let message = '';
            let messageClass = '';
            
            if (declaringPlayer === myPlayerId) {
                // I was the declarer
                if (success) {
                    message = `Your set declaration for ${setName} was successful!`;
                    messageClass = 'success';
                } else {
                    message = `Your set declaration for ${setName} failed. The opposing team gets a point.`;
                    messageClass = 'failure';
                }
            } else {
                const playerName = opponentData.find(p => p.id === declaringPlayer)?.name || `Player ${declaringPlayer}`;
                if (success) {
                    message = `${playerName} successfully declared the ${setName} set.`;
                } else {
                    message = `${playerName} tried to declare the ${setName} set but failed.`;
                }
                messageClass = 'other-player';
            }
            
            // Display notification
            showNotification(message, messageClass, 5000); // Show for 5 seconds
            
            // We'll automatically get a game state update after this
        });

        // Add handler for game over
        socket.on('game_over', function(data) {
            const winningTeam = data.team1_sets > data.team2_sets ? 1 : 2;
            const myTeam = myPlayerId % 2 === 0 ? 1 : 2;
            const iWon = winningTeam === myTeam;
            
            showGameOver(iWon, data.team1_sets, data.team2_sets);
        });

        // Add this to setupGameEvents()
        document.getElementById('debug-show-request')?.addEventListener('click', function() {
            document.getElementById('request-panel').style.display = 'block';
            document.getElementById('declare-panel').style.display = 'none';
            document.getElementById('waiting-panel').style.display = 'none';
            document.getElementById('request-tab').classList.add('active');
            document.getElementById('declare-tab').classList.remove('active');
            setupBasicActionUI();
            
            // Create mock opponents when showing the request panel
            createMockOpponents();
        });

        document.getElementById('debug-show-declare')?.addEventListener('click', function() {
            document.getElementById('request-panel').style.display = 'none';
            document.getElementById('declare-panel').style.display = 'block';
            document.getElementById('waiting-panel').style.display = 'none';
            document.getElementById('request-tab').classList.remove('active');
            document.getElementById('declare-tab').classList.add('active');
            setupBasicActionUI();
        });

        document.getElementById('debug-show-waiting')?.addEventListener('click', function() {
            document.getElementById('request-panel').style.display = 'none';
            document.getElementById('declare-panel').style.display = 'none';
            document.getElementById('waiting-panel').style.display = 'block';
        });

        // Add this function to check and report the state of the opponent area
        function debugOpponentPanel() {
            const opponentsArea = document.getElementById('opponents-area');
            console.log("Debugging Opponent Panel");
            
            if (!opponentsArea) {
                console.error("Opponents area element not found in DOM");
                return;
            }
            
            console.log("Opponent area dimensions:", {
                width: opponentsArea.offsetWidth,
                height: opponentsArea.offsetHeight,
                visible: opponentsArea.offsetWidth > 0 && opponentsArea.offsetHeight > 0
            });
            
            console.log("Current opponent area contents:", opponentsArea.innerHTML);
            console.log("Current opponentData:", JSON.stringify(opponentData));
            console.log("Number of opponent elements:", opponentsArea.querySelectorAll('.opponent').length);
            
            // Force a re-render
            if (opponentData && opponentData.length > 0) {
                console.log("Forcing opponent re-render...");
                updateOpponents(opponentData);
            } else {
                console.warn("No opponent data available to re-render");
            }
        }

        // Add a call to this in your debug button handler
        document.getElementById('debug-refresh-ui')?.addEventListener('click', function() {
            console.log("Debug UI refresh clicked");
            debugOpponentPanel();
            setupBasicActionUI();
            updateTurnStatus(currentTurn);
        });

        // Add these handlers to better track game joining
        socket.on('join_success', function(data) {
            console.log('✅ Successfully joined game:', data);
            
            // Re-enable button
            const joinBtn = document.getElementById('join-game-btn');
            if (joinBtn) {
                joinBtn.disabled = false;
                joinBtn.textContent = 'Join Game';
            }
            
            // Store player ID
            if (data.player_id !== undefined) {
                myPlayerId = data.player_id;
                sessionStorage.setItem('myPlayerId', data.player_id);
            }
            
            showNotification('Successfully joined the game!', 'success');
        });

        socket.on('join_error', function(data) {
            console.error('❌ Error joining game:', data);
            
            // Re-enable button
            const joinBtn = document.getElementById('join-game-btn');
            if (joinBtn) {
                joinBtn.disabled = false;
                joinBtn.textContent = 'Join Game';
            }
            
            showNotification('Error: ' + (data.message || 'Could not join game'), 'error');
        });
    }
    
    // Check if we already have opponent data (from session storage or previous load)
    const storedPlayerID = sessionStorage.getItem('myPlayerId');
    if (storedPlayerID) {
        console.log("Found stored player ID:", storedPlayerID);
        
        // Request a game state update to refresh visualization
        socket.emit('rejoin_game', {
            game_id: GAME_ID,
            player_id: parseInt(storedPlayerID)
        });
    }
    
    // Call this to make sure players are visualized properly
    setTimeout(ensureAllPlayersVisualized, 1000);
    
    // Add a refresh button specifically for player visualization
    const debugControls = document.querySelector('.debug-controls');
    if (debugControls) {
        const refreshPlayerBtn = document.createElement('button');
        refreshPlayerBtn.className = 'btn btn-sm btn-success';
        refreshPlayerBtn.textContent = 'Refresh Players';
        refreshPlayerBtn.addEventListener('click', ensureAllPlayersVisualized);
        debugControls.appendChild(refreshPlayerBtn);
    }
    
    // Add this at the END of the DOMContentLoaded handler
    // Ensure initialization after a short delay to allow everything to load
    setTimeout(ensureGameInitialization, 500);
    
    // Also add periodic refresh for long-running games
    setInterval(function() {
        if (gameStarted && (!opponentData || opponentData.length === 0)) {
            console.log('🔄 Periodic check - no opponent data, requesting refresh');
            socket.emit('get_game_state', { game_id: GAME_ID });
        }
    }, 10000); // Check every 10 seconds
    
    // Add this function for manual controls
    function setupManualControls() {
        // Create a container for manual controls
        const container = document.createElement('div');
        container.className = 'manual-controls';
        container.style.padding = '10px';
        container.style.margin = '15px 0';
        container.style.backgroundColor = '#e9ecef';
        container.style.borderRadius = '8px';
        
        // Create heading
        const heading = document.createElement('h4');
        heading.textContent = 'Manual Controls';
        heading.style.marginBottom = '10px';
        
        // Create buttons
        const refreshBtn = document.createElement('button');
        refreshBtn.className = 'btn btn-small';
        refreshBtn.textContent = '🔄 Refresh Game State';
        refreshBtn.addEventListener('click', function() {
            socket.emit('get_game_state', { game_id: GAME_ID });
            showNotification('Requesting fresh game state...', 'info');
        });
        
        const forcePlayerDisplayBtn = document.createElement('button');
        forcePlayerDisplayBtn.className = 'btn btn-small';
        forcePlayerDisplayBtn.style.marginLeft = '10px';
        forcePlayerDisplayBtn.textContent = '👥 Show Players';
        forcePlayerDisplayBtn.addEventListener('click', function() {
            forceOpponentDisplay();
            showNotification('Forcing player display...', 'info');
        });
        
        const debugStateBtn = document.createElement('button');
        debugStateBtn.className = 'btn btn-small btn-warning';
        debugStateBtn.style.marginLeft = '10px';
        debugStateBtn.textContent = '🐞 Debug State';
        debugStateBtn.addEventListener('click', function() {
            debugFullGameState();
            showNotification('Check console for debug info', 'info');
        });
        
        // Assemble container
        container.appendChild(heading);
        container.appendChild(refreshBtn);
        container.appendChild(forcePlayerDisplayBtn);
        container.appendChild(debugStateBtn);
        
        // Add to game board
        const gameBoard = document.querySelector('.game-board');
        if (gameBoard) {
            gameBoard.appendChild(container);
        }
    }

    // Call this at the end of your setupGameEvents function
    setupManualControls();

    // Add this function to your code to create a fallback manual join option
    function createFallbackJoinControls() {
        // Create container
        const fallbackContainer = document.createElement('div');
        fallbackContainer.className = 'fallback-join';
        fallbackContainer.style.marginTop = '20px';
        fallbackContainer.style.padding = '15px';
        fallbackContainer.style.backgroundColor = '#f8d7da';
        fallbackContainer.style.border = '1px solid #f5c6cb';
        fallbackContainer.style.borderRadius = '4px';
        
        // Add heading
        const heading = document.createElement('h4');
        heading.textContent = 'Join Game (Fallback Method)';
        heading.style.marginBottom = '10px';
        
        // Add description
        const desc = document.createElement('p');
        desc.textContent = 'If the normal join button doesn\'t work, try this alternative method:';
        desc.style.marginBottom = '10px';
        
        // Create name input
        const nameInput = document.createElement('input');
        nameInput.type = 'text';
        nameInput.placeholder = 'Your Name';
        nameInput.style.marginBottom = '10px';
        nameInput.style.padding = '8px';
        nameInput.style.width = '100%';
        nameInput.value = document.getElementById('player-name')?.value || '';
        
        // Create button
        const joinBtn = document.createElement('button');
        joinBtn.className = 'btn';
        joinBtn.textContent = 'Manual Join';
        joinBtn.style.backgroundColor = '#dc3545';
        joinBtn.style.color = 'white';
        
        // Add event listener
        joinBtn.addEventListener('click', function() {
            const playerName = nameInput.value.trim() || 'Player';
            console.log('🚀 Manual join attempt with name:', playerName);
            
            // Show feedback
            showNotification('Attempting manual join...', 'info');
            
            // Send direct socket event
            socket.emit('join_game', {
                game_id: GAME_ID,
                player_name: playerName
            });
            
            // Provide console instructions for debugging
            console.log('📝 Debug instructions:');
            console.log('1. Check if socket is connected:', socket.connected);
            console.log('2. Check socket ID:', socket.id);
            console.log('3. Check game ID:', GAME_ID);
        });
        
        // Assemble container
        fallbackContainer.appendChild(heading);
        fallbackContainer.appendChild(desc);
        fallbackContainer.appendChild(nameInput);
        fallbackContainer.appendChild(joinBtn);
        
        // Add to page
        const waitingScreen = document.getElementById('waiting-screen');
        if (waitingScreen) {
            waitingScreen.appendChild(fallbackContainer);
        }
    }

    // Call this function at the end of your DOMContentLoaded handler
    createFallbackJoinControls();
});

// Add utility functions to update the UI

function updatePlayerHand(cards) {
    const handElem = document.getElementById('player-hand');
    if (!handElem) return;
    
    handElem.innerHTML = '';
    
    // Group cards by suit
    const suitGroups = {};
    for (const card of cards) {
        if (!suitGroups[card.suit]) {
            suitGroups[card.suit] = [];
        }
        suitGroups[card.suit].push(card);
    }
    
    // Sort suits alphabetically
    const suits = Object.keys(suitGroups).sort();
    
    // Display cards grouped by suit
    for (const suit of suits) {
        // Add suit divider
        const divider = document.createElement('div');
        divider.className = 'suit-divider';
        divider.textContent = suit;
        handElem.appendChild(divider);
        
        // Sort cards within suit by rank
        const rankOrder = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
            '9': 9, '10': 10, 'Jack': 11, 'Queen': 12, 'King': 13, 'Ace': 14
        };
        
        suitGroups[suit].sort((a, b) => rankOrder[a.rank] - rankOrder[b.rank]);
        
        // Create container for this suit's cards
        const suitContainer = document.createElement('div');
        suitContainer.className = 'card-suit-group';
        
        // Add cards
        for (const card of suitGroups[suit]) {
            const cardElem = document.createElement('div');
            cardElem.className = 'card';
            cardElem.dataset.rank = card.rank;
            cardElem.dataset.suit = card.suit;
            
            // Add card content
            cardElem.innerHTML = `
                <div class="card-content ${suit === 'Hearts' || suit === 'Diamonds' ? 'red' : 'black'}">
                    <div class="card-rank">${card.rank}</div>
                    <div class="card-suit-symbol">${getSuitSymbol(card.suit)}</div>
                </div>
            `;
            
            cardElem.addEventListener('click', function() {
                // For card selection in future
                console.log('Selected card:', card.rank, 'of', card.suit);
            });
            
            suitContainer.appendChild(cardElem);
        }
        
        handElem.appendChild(suitContainer);
    }
}

// Helper function to get suit symbol
function getSuitSymbol(suit) {
    switch(suit) {
        case 'Hearts': return '♥';
        case 'Diamonds': return '♦';
        case 'Clubs': return '♣';
        case 'Spades': return '♠';
        default: return '';
    }
}

// Add this function to ensure all players (including bots) are properly visualized
function ensureAllPlayersVisualized() {
    console.log("Ensuring all players are visualized properly");
    
    // Create notification container if it doesn't exist
    if (!document.querySelector('.notifications-container')) {
        const notificationsContainer = document.createElement('div');
        notificationsContainer.className = 'notifications-container';
        document.body.appendChild(notificationsContainer);
    }
    
    // Get the opponents area
    const opponentsArea = document.getElementById('opponents-area');
    if (!opponentsArea) {
        showNotification("Cannot find opponents area!", "failure");
        return;
    }
    
    // If we have opponent data but no visualized opponents, force a re-render
    if (opponentData && opponentData.length > 0) {
        const opponentElements = opponentsArea.querySelectorAll('.opponent');
        if (opponentElements.length < opponentData.length) {
            console.log(`Found ${opponentElements.length} opponent elements but should have ${opponentData.length}`);
            showNotification("Refreshing player visualization", "info");
            updateOpponents(opponentData);
        }
    } else {
        // If we don't have opponent data but should, try to get it from the server
        console.log("No opponent data found, requesting game state update");
        socket.emit('get_game_state', { game_id: GAME_ID });
    }
}

// Modify the updateOpponents function to ensure bots are properly displayed
function updateOpponents(opponents) {
    console.log("updateOpponents called with data:", JSON.stringify(opponents));
    
    const opponentsArea = document.getElementById('opponents-area');
    if (!opponentsArea) {
        console.error("Opponents area element not found!");
        return;
    }
    
    // Always clear existing content first
    opponentsArea.innerHTML = '';
    
    if (!opponents || opponents.length === 0) {
        console.warn("No opponent data received or empty array");
        opponentsArea.innerHTML = '<div class="no-opponents">No other players yet</div>';
        return;
    }
    
    // Group opponents by team
    const team1 = opponents.filter(opp => opp.team === 0);
    const team2 = opponents.filter(opp => opp.team === 1);
    
    // Create team containers
    const team1Container = document.createElement('div');
    team1Container.className = 'team-container team1-container';
    team1Container.innerHTML = '<h3>Team 1</h3>';
    
    const team2Container = document.createElement('div');
    team2Container.className = 'team-container team2-container';
    team2Container.innerHTML = '<h3>Team 2</h3>';
    
    // Add myself to the appropriate team if not already included
    if (myPlayerId !== null) {
        const myTeam = myPlayerId % 2;
        let foundSelf = false;
        
        for (const opp of opponents) {
            if (opp.id === myPlayerId) {
                foundSelf = true;
                break;
            }
        }
        
        if (!foundSelf) {
            const myPlayerObj = {
                id: myPlayerId,
                name: 'You',
                team: myTeam,
                card_count: myHand ? myHand.length : 0,
                is_bot: false
            };
            
            if (myTeam === 0) {
                team1.push(myPlayerObj);
            } else {
                team2.push(myPlayerObj);
            }
        }
    }
    
    // Add opponents to their team containers
    team1.forEach(opp => {
        const oppElem = createOpponentElement(opp);
        team1Container.appendChild(oppElem);
    });
    
    team2.forEach(opp => {
        const oppElem = createOpponentElement(opp);
        team2Container.appendChild(oppElem);
    });
    
    // Only append containers that have players
    if (team1.length > 0) {
        opponentsArea.appendChild(team1Container);
    }
    
    if (team2.length > 0) {
        opponentsArea.appendChild(team2Container);
    }
    
    // Add a timestamp to show when last updated
    const timestamp = document.createElement('div');
    timestamp.className = 'update-timestamp';
    timestamp.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    timestamp.style.fontSize = '10px';
    timestamp.style.color = '#999';
    timestamp.style.textAlign = 'right';
    opponentsArea.appendChild(timestamp);
    
    // Add a player count summary
    const playerCountSummary = document.createElement('div');
    playerCountSummary.className = 'player-count-summary';
    playerCountSummary.innerHTML = `
        <strong>Players (${opponents.length + (myPlayerId !== null ? 1 : 0)}):</strong> 
        Team 1: ${team1.length}, Team 2: ${team2.length}
    `;
    opponentsArea.insertBefore(playerCountSummary, opponentsArea.firstChild);
}

// Update the createOpponentElement function to better display bots
function createOpponentElement(opponent) {
    const oppElem = document.createElement('div');
    oppElem.className = 'opponent';
    oppElem.dataset.id = opponent.id;
    oppElem.dataset.team = opponent.team;
    
    // Add more visible indicators
    if (opponent.is_bot) {
        oppElem.classList.add('bot-player');
    }
    
    if (opponent.id === myPlayerId) {
        oppElem.classList.add('self');
    }
    
    if (opponent.id === currentTurn) {
        oppElem.classList.add('current-turn');
    }
    
    // Format the display name
    let displayName = opponent.id === myPlayerId ? 'You' : opponent.name;
    
    // Enhanced display for the opponent element
    oppElem.innerHTML = `
        <div class="opponent-name">${displayName}${opponent.is_bot ? ' <span class="bot-indicator">(Bot)</span>' : ''}</div>
        <div class="opponent-cards"><i class="card-icon">🃏</i> ${opponent.card_count}</div>
        <div class="opponent-team team${opponent.team + 1}">Team ${opponent.team + 1}</div>
        ${opponent.id === currentTurn ? '<div class="turn-marker">Current Turn</div>' : ''}
    `;
    
    // Add interactivity for opponents you can request cards from
    if (opponent.id !== myPlayerId && opponent.team !== myPlayerId % 2 && currentTurn === myPlayerId) {
        oppElem.classList.add('clickable');
        
        // Add a visual indicator that you can click
        const actionIndicator = document.createElement('div');
        actionIndicator.className = 'action-indicator';
        actionIndicator.innerHTML = '👆 Ask for card';
        oppElem.appendChild(actionIndicator);
        
        oppElem.addEventListener('click', function() {
            // Select this player in the request form
            const targetSelect = document.getElementById('basic-target-player');
            if (targetSelect) {
                targetSelect.value = opponent.id;
                targetSelect.dispatchEvent(new Event('change'));
            }
            
            // Show request panel
            document.getElementById('request-panel').style.display = 'block';
            document.getElementById('declare-panel').style.display = 'none';
            
            // Activate request tab
            document.getElementById('request-tab').classList.add('active');
            document.getElementById('declare-tab').classList.remove('active');
            
            // Scroll to the action panel
            document.getElementById('action-panel').scrollIntoView({ behavior: 'smooth' });
        });
    }
    
    return oppElem;
}

function updateTargetOptions(opponents, myTeam) {
    targetPlayerSelect.innerHTML = '';
    
    // Filter opponents from the other team
    const otherTeamOpponents = opponents.filter(o => o.team !== myTeam);
    
    otherTeamOpponents.forEach(opponent => {
        const option = document.createElement('option');
        option.value = opponent.id;
        option.textContent = opponent.name + (opponent.is_bot ? ' (Bot)' : '');
        targetPlayerSelect.appendChild(option);
    });
}

function updateCardOptions() {
    cardRankSelect.innerHTML = '';
    cardSuitSelect.innerHTML = '';
    
    // Add rank options
    const ranks = ['2', '3', '4', '5', '6', '7', '9', '10', 'Jack', 'Queen', 'King', 'Ace'];
    ranks.forEach(rank => {
        const option = document.createElement('option');
        option.value = rank;
        option.textContent = rank;
        cardRankSelect.appendChild(option);
    });
    
    // Add suit options
    const suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades'];
    suits.forEach(suit => {
        const option = document.createElement('option');
        option.value = suit;
        option.textContent = suit;
        cardSuitSelect.appendChild(option);
    });
    
    // Default to a card in hand if possible
    if (myHand.length > 0) {
        cardRankSelect.value = myHand[0].rank;
        cardSuitSelect.value = myHand[0].suit;
    }
}

function updateSetOptions(sets) {
    setNameSelect.innerHTML = '';
    
    sets.forEach(set => {
        const option = document.createElement('option');
        option.value = set;
        option.textContent = set;
        setNameSelect.appendChild(option);
    });
    
    // Set up change handler to update card assignments
    setNameSelect.addEventListener('change', function() {
        selectedSet = setNameSelect.value;
        updateCardAssignments();
    });
    
    // Trigger once to initialize
    if (sets.length > 0) {
        selectedSet = sets[0];
        updateCardAssignments();
    }
}

function updateCardAssignments() {
    const cardAssignments = document.getElementById('card-assignments');
    if (!cardAssignments || !selectedSet) return;
    
    cardAssignments.innerHTML = '';
    
    // Add helper text
    const helpText = document.createElement('p');
    helpText.className = 'helper-text';
    helpText.textContent = 'Assign each card to the player who has it:';
    cardAssignments.appendChild(helpText);
    
    // Determine which cards are in the selected set
    const [setType, setSuit] = selectedSet.split(' ');
    let ranks = [];
    
    if (setType === 'Low') {
        ranks = ['2', '3', '4', '5', '6', '7'];
    } else if (setType === 'High') {
        ranks = ['9', '10', 'Jack', 'Queen', 'King', 'Ace'];
    }
    
    // Create assignment inputs for each card
    ranks.forEach(rank => {
        const cardName = `${rank} of ${setSuit}`;
        const assignmentDiv = document.createElement('div');
        assignmentDiv.className = 'card-assignment';
        
        // Create card visual
        const cardVisual = document.createElement('div');
        cardVisual.className = 'mini-card';
        cardVisual.innerHTML = `
            <div class="mini-card-content ${setSuit === 'Hearts' || setSuit === 'Diamonds' ? 'red' : 'black'}">
                <span class="mini-card-rank">${rank}</span>
                <span class="mini-card-suit">${getSuitSymbol(setSuit)}</span>
            </div>
        `;
        
        const label = document.createElement('label');
        label.textContent = cardName;
        
        const select = document.createElement('select');
        select.name = `card_${rank}_${setSuit}`;
        select.dataset.rank = rank;
        select.dataset.suit = setSuit;
        
        // Add option for each player on my team
        const myTeam = myPlayerId % 2;
        
        // Add all players from my team
        const teamPlayers = opponentData
            .filter(player => player.team === myTeam)
            .map(player => player.id);
        
        // Add myself
        if (!teamPlayers.includes(myPlayerId)) {
            teamPlayers.push(myPlayerId);
        }
        
        // Sort by ID
        teamPlayers.sort();
        
        // Add options
        teamPlayers.forEach(playerId => {
            const option = document.createElement('option');
            option.value = playerId;
            
            // Find player name
            let playerName = playerId === myPlayerId ? 'Me' : `Player ${playerId}`;
            const playerObj = opponentData.find(p => p.id === playerId);
            if (playerObj) {
                playerName = playerObj.name;
            }
            
            option.textContent = playerName;
            
            // Preselect if I have the card
            if (playerId === myPlayerId && haveCardInHand(rank, setSuit)) {
                option.selected = true;
            }
            
            select.appendChild(option);
        });
        
        assignmentDiv.appendChild(cardVisual);
        assignmentDiv.appendChild(label);
        assignmentDiv.appendChild(select);
        cardAssignments.appendChild(assignmentDiv);
    });
}

function haveCardInHand(rank, suit) {
    return myHand.some(card => card.rank === rank && card.suit === suit);
}

function showPanel(panelName) {
    const requestPanel = document.getElementById('request-panel');
    const declarePanel = document.getElementById('declare-panel');
    const waitingPanel = document.getElementById('waiting-panel');
    
    // Hide all panels first
    requestPanel.style.display = 'none';
    declarePanel.style.display = 'none';
    waitingPanel.style.display = 'none';
    
    // Show the selected panel
    if (panelName === 'request') {
        requestPanel.style.display = 'block';
    } else if (panelName === 'declare') {
        declarePanel.style.display = 'block';
    } else if (panelName === 'waiting') {
        waitingPanel.style.display = 'block';
    }
}

function addLogEntry(action) {
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    
    let message = '';
    
    if (action.action === 'CARD_REQUEST') {
        const details = action.details;
        const botTag = details.is_bot ? ' (Bot)' : '';
        message = details.success ? 
            `Player ${details.requester}${botTag} got ${details.card.rank} of ${details.card.suit} from Player ${details.target}` :
            `Player ${details.requester}${botTag} asked Player ${details.target} for ${details.card.rank} of ${details.card.suit} - GO FISH!`;
    } else if (action.action === 'SET_DECLARATION') {
        const details = action.details;
        const botTag = details.is_bot ? ' (Bot)' : '';
        message = details.success ? 
            `Player ${details.player}${botTag} correctly declared ${details.set} for Team ${details.team_that_won + 1}` :
            `Player ${details.player}${botTag} incorrectly declared ${details.set}. Point to Team ${details.team_that_won + 1}`;
    } else if (action.action === 'GAME_START') {
        message = `Game started with ${action.details.player_count} players. Player ${action.details.first_player} goes first.`;
    }
    
    logEntry.textContent = message;
    
    // Prepend to log (newest entries at top)
    logContainer.insertBefore(logEntry, logContainer.firstChild);
    
    // Limit log entries to avoid performance issues
    if (logContainer.children.length > 50) {
        logContainer.removeChild(logContainer.lastChild);
    }
}

function showGameOver(iWon, team1Sets, team2Sets) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'game-over-overlay';
    
    const modal = document.createElement('div');
    modal.className = 'game-over-modal';
    
    const resultText = iWon ? 'Your Team Won!' : 'Your Team Lost!';
    const scoreText = `Final Score - Team 1: ${team1Sets}, Team 2: ${team2Sets}`;
    
    // Determine winner
    const winningTeam = team1Sets > team2Sets ? 1 : 2;
    const myTeam = (myPlayerId % 2) + 1; // Convert 0/1 to 1/2
    
    modal.innerHTML = `
        <h2>${resultText}</h2>
        <div class="game-over-details">
            <p>${scoreText}</p>
            <p>Team ${winningTeam} has won the game!</p>
            ${iWon ? 
                '<p class="win-message">Congratulations on your victory!</p>' : 
                '<p class="loss-message">Better luck next time!</p>'
            }
        </div>
        <div class="game-over-actions">
            <button id="new-game-btn" class="btn btn-primary">Play Again</button>
            <button id="back-to-lobby-btn" class="btn btn-secondary">Back to Lobby</button>
        </div>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Add event listeners for buttons
    document.getElementById('new-game-btn').addEventListener('click', function() {
        window.location.reload();
    });
    
    document.getElementById('back-to-lobby-btn').addEventListener('click', function() {
        window.location.href = '/';
    });
}

// Move switchToGameScreen outside the DOMContentLoaded function so it's globally available
function switchToGameScreen() {
    console.log('Manual switch to game screen triggered');
    const waitingScreen = document.getElementById('waiting-screen');
    const gameScreen = document.getElementById('game-screen');
    
    if (waitingScreen && gameScreen) {
        // Try multiple approaches for maximum compatibility
        waitingScreen.classList.add('hidden');
        gameScreen.classList.remove('hidden');
        
        waitingScreen.style.display = 'none';
        gameScreen.style.display = 'flex';
        
        // For debugging
        console.log('Screen switch complete');
        console.log('Waiting screen display:', waitingScreen.style.display);
        console.log('Game screen display:', gameScreen.style.display);
    }
}

// Update the rejoin_game function to send player ID
function attemptRejoin() {
    const storedPlayerId = sessionStorage.getItem('myPlayerId');
    
    socket.emit('rejoin_game', { 
        game_id: GAME_ID,
        player_id: storedPlayerId ? parseInt(storedPlayerId) : undefined
    });
}

// Modify the debug button event listener to be in a dedicated script tag in the HTML
// This ensures it's correctly defined

// Simplified turn status update
function updateTurnStatus(currentTurn) {
    console.log("Updating turn status, current turn:", currentTurn, "my ID:", myPlayerId);
    
    const turnStatus = document.getElementById('turn-status');
    const requestPanel = document.getElementById('request-panel');
    const declarePanel = document.getElementById('declare-panel');
    const waitingPanel = document.getElementById('waiting-panel');
    
    if (!turnStatus || !requestPanel || !declarePanel || !waitingPanel) {
        console.error("Cannot find turn status or panel elements");
        return;
    }
    
    const isMyTurn = currentTurn === myPlayerId;
    
    // Update turn status message
    if (isMyTurn) {
        turnStatus.innerHTML = '<strong>🎮 It\'s YOUR turn! 🎮</strong>';
        turnStatus.classList.add('my-turn');
    } else {
        let playerName = "Player " + currentTurn;
        const currentPlayer = opponentData.find(p => p.id === currentTurn);
        if (currentPlayer) {
            playerName = currentPlayer.name;
        }
        
        turnStatus.innerHTML = `Waiting for <strong>${playerName}</strong>...`;
        turnStatus.classList.remove('my-turn');
    }
    
    // Show/hide panels based on turn
    if (isMyTurn) {
        // It's my turn, show action panels
        waitingPanel.style.display = 'none';
        
        // Show the appropriate action panel
        if (document.getElementById('declare-tab').classList.contains('active')) {
            declarePanel.style.display = 'block';
            requestPanel.style.display = 'none';
        } else {
            requestPanel.style.display = 'block';
            declarePanel.style.display = 'none';
        }
        
        // Setup the action forms
        setupBasicActionUI();
        
        // Show a notification
        showNotification("It's your turn! Make a move.", 'info');
    } else {
        // Not my turn, show waiting panel
        waitingPanel.style.display = 'block';
        requestPanel.style.display = 'none';
        declarePanel.style.display = 'none';
    }
    
    // Highlight the current player
    document.querySelectorAll('.opponent').forEach(opp => {
        opp.classList.remove('current-turn');
        
        const oppId = parseInt(opp.dataset.id);
        if (oppId === currentTurn) {
            opp.classList.add('current-turn');
        }
    });
}

function updateOpponentHighlighting(currentTurn) {
    // Remove current-turn class from all opponents
    document.querySelectorAll('.opponent').forEach(opp => {
        opp.classList.remove('current-turn');
    });
    
    // Add current-turn class to the current player
    const currentPlayerElem = document.querySelector(`.opponent[data-id="${currentTurn}"]`);
    if (currentPlayerElem) {
        currentPlayerElem.classList.add('current-turn');
    }
}

// Update initializeCardRequestOptions function
function initializeCardRequestOptions() {
    const targetPlayerSelect = document.getElementById('target-player');
    const cardRankSelect = document.getElementById('card-rank');
    const cardSuitSelect = document.getElementById('card-suit');
    
    if (!targetPlayerSelect || !cardRankSelect || !cardSuitSelect) return;
    
    // Clear existing options
    targetPlayerSelect.innerHTML = '';
    cardRankSelect.innerHTML = '';
    cardSuitSelect.innerHTML = '';
    
    // Populate target player options (only opponents on the other team)
    const myTeam = myPlayerId % 2;
    
    // First add a placeholder
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = '-- Select a player --';
    placeholder.disabled = true;
    placeholder.selected = true;
    targetPlayerSelect.appendChild(placeholder);
    
    // Add actual opponents
    opponentData.forEach(opponent => {
        // Only include opponents on the opposite team
        if (opponent.team !== myTeam && opponent.id !== myPlayerId) {
            const option = document.createElement('option');
            option.value = opponent.id;
            option.textContent = opponent.name;
            targetPlayerSelect.appendChild(option);
        }
    });
    
    // Populate card rank options
    const rankPlaceholder = document.createElement('option');
    rankPlaceholder.value = '';
    rankPlaceholder.textContent = '-- Select a rank --';
    rankPlaceholder.disabled = true;
    rankPlaceholder.selected = true;
    cardRankSelect.appendChild(rankPlaceholder);
    
    // Show ranks we have in our hand
    const rankOrder = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
        '9': 9, '10': 10, 'Jack': 11, 'Queen': 12, 'King': 13, 'Ace': 14
    };
    
    const seenRanks = new Set(); // Track ranks we already have in our hand
    myHand.forEach(card => {
        seenRanks.add(card.rank);
    });
    
    // Sort ranks by their numeric order
    Array.from(seenRanks).sort((a, b) => rankOrder[a] - rankOrder[b]).forEach(rank => {
        const option = document.createElement('option');
        option.value = rank;
        option.textContent = rank;
        cardRankSelect.appendChild(option);
    });
    
    // Update suit options based on selected rank
    cardRankSelect.addEventListener('change', updateSuitOptions);
    
    // Add a visual help for the card request
    const requestHelp = document.createElement('div');
    requestHelp.className = 'request-help';
    requestHelp.innerHTML = `
        <p>Ask an opponent from the other team for a card that matches the rank of a card you already have.</p>
        <div class="tip">Tip: You can only ask for cards where you already have at least one of that rank.</div>
    `;
    
    const existingHelp = requestPanel.querySelector('.request-help');
    if (existingHelp) {
        existingHelp.remove();
    }
    
    requestPanel.insertBefore(requestHelp, requestPanel.firstChild);
    
    function updateSuitOptions() {
        const selectedRank = cardRankSelect.value;
        
        // Clear current options
        cardSuitSelect.innerHTML = '';
        
        // Add placeholder
        const suitPlaceholder = document.createElement('option');
        suitPlaceholder.value = '';
        suitPlaceholder.textContent = '-- Select a suit --';
        suitPlaceholder.disabled = true;
        suitPlaceholder.selected = true;
        cardSuitSelect.appendChild(suitPlaceholder);
        
        if (!selectedRank) return;
        
        // Get all suits for the selected rank
        const suits = new Set();
        myHand.forEach(card => {
            if (card.rank === selectedRank) {
                suits.add(card.suit);
            }
        });
        
        // Add options for each suit
        Array.from(suits).sort().forEach(suit => {
            const option = document.createElement('option');
            option.value = suit;
            option.textContent = suit;
            cardSuitSelect.appendChild(option);
        });
    }
}

// Update initializeSetDeclarationOptions function
function initializeSetDeclarationOptions() {
    const setNameSelect = document.getElementById('set-name');
    const cardAssignments = document.getElementById('card-assignments');
    
    if (!setNameSelect || !cardAssignments) return;
    
    // Clear existing options
    setNameSelect.innerHTML = '';
    
    // Add available sets
    availableSets.forEach(set => {
        const option = document.createElement('option');
        option.value = set;
        option.textContent = set;
        setNameSelect.appendChild(option);
    });
    
    // Update card assignments when set changes
    setNameSelect.addEventListener('change', function() {
        selectedSet = this.value;
        updateCardAssignments();
    });
    
    // Initialize card assignments
    if (availableSets.length > 0) {
        selectedSet = availableSets[0];
        updateCardAssignments();
    }
}

// Update updateScores function
function updateScores(team1Sets, team2Sets) {
    const team1Score = document.getElementById('team1-score');
    const team2Score = document.getElementById('team2-score');
    
    if (team1Score) team1Score.textContent = team1Sets;
    if (team2Score) team2Score.textContent = team2Sets;
    
    // Highlight my team's score
    const myTeam = myPlayerId % 2;
    const myTeamScore = myTeam === 0 ? team1Score : team2Score;
    const otherTeamScore = myTeam === 0 ? team2Score : team1Score;
    
    if (myTeamScore) {
        myTeamScore.parentElement.classList.add('my-team');
        otherTeamScore.parentElement.classList.remove('my-team');
    }
    
    // Show sets remaining
    const totalSets = 8; // Total sets in the game
    const setsClaimed = team1Sets + team2Sets;
    const setsRemaining = totalSets - setsClaimed;
    
    const gameStatus = document.querySelector('.game-status');
    if (gameStatus) {
        let statusElem = gameStatus.querySelector('.sets-remaining');
        if (!statusElem) {
            statusElem = document.createElement('div');
            statusElem.className = 'sets-remaining';
            gameStatus.appendChild(statusElem);
        }
        statusElem.textContent = `Sets remaining: ${setsRemaining}`;
    }
}

// Add this function to handle card request submission
function setupCardRequestForm() {
    const sendRequestBtn = document.getElementById('send-request');
    const targetPlayerSelect = document.getElementById('target-player');
    const cardRankSelect = document.getElementById('card-rank');
    const cardSuitSelect = document.getElementById('card-suit');
    
    if (!sendRequestBtn) return;
    
    // Remove any existing event listeners
    sendRequestBtn.replaceWith(sendRequestBtn.cloneNode(true));
    
    // Get the fresh reference
    const newSendRequestBtn = document.getElementById('send-request');
    
    // Add event listener
    newSendRequestBtn.addEventListener('click', function() {
        if (currentTurn !== myPlayerId) {
            alert("It's not your turn!");
            return;
        }
        
        const targetId = parseInt(targetPlayerSelect.value);
        const rank = cardRankSelect.value;
        const suit = cardSuitSelect.value;
        
        if (!targetId || !rank || !suit) {
            alert("Please select a player, rank, and suit.");
            return;
        }
        
        console.log(`Requesting ${rank} of ${suit} from player ${targetId}`);
        
        // Disable button to prevent double-clicks
        newSendRequestBtn.disabled = true;
        
        // Send the request
        socket.emit('request_card', {
            game_id: GAME_ID,
            player_id: myPlayerId,
            target_id: targetId,
            card_rank: rank,
            card_suit: suit
        });
        
        // Re-enable after 1 second
        setTimeout(() => {
            newSendRequestBtn.disabled = false;
        }, 1000);
    });
}

// Add this function to handle set declaration submission
function setupSetDeclarationForm() {
    const sendDeclarationBtn = document.getElementById('send-declaration');
    const setNameSelect = document.getElementById('set-name');
    
    if (!sendDeclarationBtn) return;
    
    // Remove any existing event listeners
    sendDeclarationBtn.replaceWith(sendDeclarationBtn.cloneNode(true));
    
    // Get the fresh reference
    const newSendDeclarationBtn = document.getElementById('send-declaration');
    
    // Add event listener
    newSendDeclarationBtn.addEventListener('click', function() {
        if (currentTurn !== myPlayerId) {
            alert("It's not your turn!");
            return;
        }
        
        const set = setNameSelect.value;
        
        if (!set) {
            alert("Please select a set to declare.");
            return;
        }
        
        // Gather card assignments
        const assignments = {};
        const cardSelects = document.querySelectorAll('#card-assignments select');
        
        cardSelects.forEach(select => {
            const { rank, suit } = select.dataset;
            const playerId = parseInt(select.value);
            
            assignments[`${rank}_${suit}`] = playerId;
        });
        
        console.log(`Declaring set: ${set}`, assignments);
        
        // Disable button to prevent double-clicks
        newSendDeclarationBtn.disabled = true;
        
        // Send the declaration
        socket.emit('declare_set', {
            game_id: GAME_ID,
            player_id: myPlayerId,
            set_name: set,
            card_assignments: assignments
        });
        
        // Re-enable after 1 second
        setTimeout(() => {
            newSendDeclarationBtn.disabled = false;
        }, 1000);
    });
}

// Improved notification function
function showNotification(message, type = 'info') {
    // Make sure we have a container
    let container = document.querySelector('.notifications-container');
    
    if (!container) {
        container = document.createElement('div');
        container.className = 'notifications-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '1000';
        document.body.appendChild(container);
    }
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.backgroundColor = type === 'error' ? '#f44336' : 
                                        type === 'success' ? '#4CAF50' : 
                                        type === 'warning' ? '#ff9800' : '#2196F3';
    notification.style.color = 'white';
    notification.style.padding = '10px 15px';
    notification.style.marginBottom = '10px';
    notification.style.borderRadius = '4px';
    notification.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
    notification.style.minWidth = '250px';
    notification.style.position = 'relative';
    notification.style.animation = 'slideIn 0.3s forwards';
    
    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
    `;
    document.head.appendChild(style);
    
    // Add icon based on type
    const iconMap = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌'
    };
    
    // Add content
    notification.innerHTML = `
        <span style="margin-right:8px;">${iconMap[type] || '🔔'}</span>
        <span>${message}</span>
        <span style="position:absolute;right:8px;top:8px;cursor:pointer;" 
              onclick="this.parentElement.style.animation='fadeOut 0.3s forwards';
                      setTimeout(() => this.parentElement.remove(), 300);">
            ✖
        </span>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.3s forwards';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Update the game log function
function updateGameLog(gameLog) {
    const logContainer = document.getElementById('log-container');
    if (!logContainer) return;
    
    // Clear existing log if we're starting fresh
    if (gameLog.length > 0 && logContainer.children.length === 0) {
        logContainer.innerHTML = '';
    }
    
    // Only add entries that aren't already in the log
    const existingEntries = logContainer.children.length;
    const newEntries = gameLog.slice(existingEntries);
    
    newEntries.forEach(entry => {
        // Create log entry
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        // Format message based on action type
        let message = '';
        
        switch(entry.action) {
            case 'GAME_START':
                message = `Game started with ${entry.details.player_count} players.`;
                break;
                
            case 'CARD_REQUEST':
                const requestSuccess = entry.details.success ? 'successfully' : 'unsuccessfully';
                message = `Player ${entry.details.requester} ${requestSuccess} requested the ${entry.details.card.rank} of ${entry.details.card.suit} from Player ${entry.details.target}.`;
                break;
                
            case 'SET_DECLARATION':
                const declarationSuccess = entry.details.success ? 'successfully' : 'unsuccessfully';
                message = `Player ${entry.details.player} ${declarationSuccess} declared the ${entry.details.set} set.`;
                break;
                
            case 'GAME_OVER':
                message = `Game over! Team 1: ${entry.details.team1_sets} sets, Team 2: ${entry.details.team2_sets} sets. Team ${entry.details.winning_team} wins!`;
                logEntry.classList.add('game-over-entry');
                break;
                
            default:
                message = `${entry.action}: ${JSON.stringify(entry.details)}`;
        }
        
        logEntry.textContent = message;
        
        // Add to log container
        logContainer.appendChild(logEntry);
    });
    
    // Scroll to bottom
    logContainer.scrollTop = logContainer.scrollHeight;
}

// Function to update the UI when turn changes
function updateTurnIndicators() {
    const isMyTurn = currentTurn === myPlayerId;
    const actionPanel = document.getElementById('action-panel');
    
    if (!actionPanel) return;
    
    // Reset existing indicators
    document.querySelectorAll('.turn-indicator').forEach(el => el.remove());
    
    if (isMyTurn) {
        // Create a prominent turn indicator
        const turnIndicator = document.createElement('div');
        turnIndicator.className = 'turn-indicator';
        turnIndicator.innerHTML = `
            <div class="turn-indicator-icon">🎯</div>
            <div class="turn-indicator-text">
                <h3>Your Turn!</h3>
                <p>Take an action below to continue the game.</p>
            </div>
        `;
        
        // Insert at the top of the action panel
        actionPanel.insertBefore(turnIndicator, actionPanel.firstChild);
        
        // Show proper panels
        const requestPanel = document.getElementById('request-panel');
        const declarePanel = document.getElementById('declare-panel');
        const waitingPanel = document.getElementById('waiting-panel');
        
        if (waitingPanel) waitingPanel.style.display = 'none';
        
        // Show default action panel
        if (requestPanel) requestPanel.style.display = 'block';
        if (declarePanel) declarePanel.style.display = 'none';
        
        // Set up the action tabs
        const requestTab = document.getElementById('request-tab');
        const declareTab = document.getElementById('declare-tab');
        
        if (requestTab && declareTab) {
            requestTab.classList.add('active');
            declareTab.classList.remove('active');
            
            // Make tabs work properly
            requestTab.addEventListener('click', function() {
                this.classList.add('active');
                declareTab.classList.remove('active');
                requestPanel.style.display = 'block';
                declarePanel.style.display = 'none';
            });
            
            declareTab.addEventListener('click', function() {
                this.classList.add('active');
                requestTab.classList.remove('active');
                declarePanel.style.display = 'block';
                requestPanel.style.display = 'none';
            });
        }
        
        // Set up enhanced UI components for actions
        setupCardRequestWizard();
        setupSetDeclarationWizard();
    }
}

// Highlight opponents that can be interacted with
function highlightActionableOpponents() {
    // First remove any existing highlights
    document.querySelectorAll('.opponent-action-hint').forEach(el => el.remove());
    
    // Add visual indicators to opposing team members
    const myTeam = myPlayerId % 2;
    document.querySelectorAll(`.opponent[data-team="${myTeam === 0 ? '1' : '0'}"]`).forEach(opp => {
        const actionHint = document.createElement('div');
        actionHint.className = 'opponent-action-hint';
        actionHint.innerHTML = '<span class="hint-icon">🎯</span> Ask for card';
        
        opp.appendChild(actionHint);
        opp.classList.add('actionable');
    });
}

// Update the setupCardRequestWizard function to include a set selection step
function setupCardRequestWizard() {
    const requestPanel = document.getElementById('request-panel');
    if (!requestPanel) return;
    
    // First clear existing content
    const existingWizard = requestPanel.querySelector('.request-wizard');
    if (existingWizard) existingWizard.remove();
    
    // Create wizard container
    const wizard = document.createElement('div');
    wizard.className = 'request-wizard';
    
    // Create steps - add a new step for set selection
    const steps = [
        {
            id: 'step1',
            title: 'Step 1: Choose a Player',
            content: `
                <p>Select an opponent from the other team to ask for a card.</p>
                <div class="tip">You can also click directly on an opponent above!</div>
                <div class="wizard-select-container">
                    <select id="wizard-target-player"></select>
                </div>
            `
        },
        {
            id: 'step2',
            title: 'Step 2: Choose a Set',
            content: `
                <p>Select a set that you have at least one card from:</p>
                <div class="set-options">
                    <!-- Will be filled dynamically -->
                </div>
            `
        },
        {
            id: 'step3',
            title: 'Step 3: Choose a Card',
            content: `
                <p>Select the card you want to ask for:</p>
                <div class="rank-options">
                    <!-- Will be filled dynamically -->
                </div>
            `
        },
        {
            id: 'step4',
            title: 'Review and Submit',
            content: `
                <div class="request-summary">
                    <p>You're asking <span id="summary-player">___</span> for:</p>
                    <div class="requested-card">
                        <span id="summary-rank">___</span> of <span id="summary-suit">___</span>
                    </div>
                    <div class="set-info">
                        From the set: <span id="summary-set">___</span>
                    </div>
                </div>
                <button id="wizard-submit-request" class="btn btn-primary">Ask for Card</button>
            `
        }
    ];
    
    // Create step navigation
    const stepsNav = document.createElement('div');
    stepsNav.className = 'wizard-steps';
    
    // Create step buttons
    steps.forEach(step => {
        const stepBtn = document.createElement('button');
        stepBtn.className = 'wizard-step-btn';
        stepBtn.dataset.step = step.id;
        stepBtn.textContent = step.id.replace('step', 'Step ');
        
        stepBtn.addEventListener('click', function() {
            showWizardStep(step.id);
        });
        
        stepsNav.appendChild(stepBtn);
    });
    
    // Create content area
    const contentArea = document.createElement('div');
    contentArea.className = 'wizard-content';
    
    // Assemble wizard
    wizard.appendChild(stepsNav);
    wizard.appendChild(contentArea);
    
    // Add to the panel
    requestPanel.appendChild(wizard);
    
    // Show the first step
    showWizardStep('step1');
}

// Add this function to populate set options
function populateWizardSetOptions() {
    const setOptions = document.querySelector('.set-options');
    if (!setOptions) return;
    
    setOptions.innerHTML = '';
    
    // Define which ranks belong to which set
    const lowRanks = ['2', '3', '4', '5', '6', '7'];
    const highRanks = ['9', '10', 'Jack', 'Queen', 'King', 'Ace'];
    
    // Find which sets (half-suits) the player has cards in
    const lowSets = new Set();  // e.g., "Low Hearts"
    const highSets = new Set(); // e.g., "High Spades"
    
    // Analyze player's hand
    myHand.forEach(card => {
        if (lowRanks.includes(card.rank)) {
            lowSets.add(`Low ${card.suit}`);
        } else if (highRanks.includes(card.rank)) {
            highSets.add(`High ${card.suit}`);
        }
    });
    
    // Combine all sets
    const allSets = [...lowSets, ...highSets].sort();
    
    if (allSets.length === 0) {
        setOptions.innerHTML = '<p>You don\'t have cards from any sets yet.</p>';
        return;
    }
    
    // Create set options
    allSets.forEach(set => {
        const setOption = document.createElement('div');
        setOption.className = 'set-option';
        setOption.dataset.set = set;
        
        // Parse the set name
        const [setType, setSuit] = set.split(' ');
        const isRed = setSuit === 'Hearts' || setSuit === 'Diamonds';
        
        // Show a visual representation of the set
        setOption.innerHTML = `
            <div class="set-name">${set}</div>
            <div class="set-cards ${isRed ? 'red' : 'black'}">
                ${setType === 'Low' ? '2-7' : '9-A'} of ${setSuit}
            </div>
        `;
        
        setOption.addEventListener('click', function() {
            // Remove selected class from all options
            document.querySelectorAll('.set-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            
            // Add selected class to this option
            this.classList.add('selected');
            
            // Store selected set in session storage for next step
            sessionStorage.setItem('selectedSet', set);
            
            // Update summary
            const summarySet = document.getElementById('summary-set');
            if (summarySet) {
                summarySet.textContent = set;
            }
            
            // Enable next button
            const nextBtn = document.querySelector('.wizard-navigation .btn-next');
            if (nextBtn) {
                nextBtn.classList.remove('disabled');
            }
        });
        
        setOptions.appendChild(setOption);
    });
}

// Add function to show wizard steps
function showWizardStep(stepId) {
    // Update step buttons
    document.querySelectorAll('.wizard-step-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.step === stepId);
    });
    
    // Get step content
    const steps = [
        {
            id: 'step1',
            title: 'Step 1: Choose a Player',
            content: `
                <p>Select an opponent from the other team to ask for a card.</p>
                <div class="tip">You can also click directly on an opponent above!</div>
                <div class="wizard-select-container">
                    <select id="wizard-target-player"></select>
                </div>
            `
        },
        {
            id: 'step2',
            title: 'Step 2: Choose a Set',
            content: `
                <p>Select a set that you have at least one card from:</p>
                <div class="set-options">
                    <!-- Will be filled dynamically -->
                </div>
            `
        },
        {
            id: 'step3',
            title: 'Step 3: Choose a Card',
            content: `
                <p>Select the card you want to ask for:</p>
                <div class="rank-options">
                    <!-- Will be filled dynamically -->
                </div>
            `
        },
        {
            id: 'step4',
            title: 'Review and Submit',
            content: `
                <div class="request-summary">
                    <p>You're asking <span id="summary-player">___</span> for:</p>
                    <div class="requested-card">
                        <span id="summary-rank">___</span> of <span id="summary-suit">___</span>
                    </div>
                    <div class="set-info">
                        From the set: <span id="summary-set">___</span>
                    </div>
                </div>
                <button id="wizard-submit-request" class="btn btn-primary">Ask for Card</button>
            `
        }
    ];
    
    const step = steps.find(s => s.id === stepId);
    if (!step) return;
    
    // Update content area
    const contentArea = document.querySelector('.wizard-content');
    if (!contentArea) return;
    
    contentArea.innerHTML = `
        <h3>${step.title}</h3>
        <div class="step-content">${step.content}</div>
        <div class="wizard-navigation">
            <button class="btn-prev ${stepId === 'step1' ? 'disabled' : ''}">Previous</button>
            <button class="btn-next ${stepId === 'step4' ? 'disabled' : ''}">Continue</button>
        </div>
    `;
    
    // Populate the step based on which one it is
    if (stepId === 'step1') {
        populateWizardPlayerSelect();
    } else if (stepId === 'step2') {
        populateWizardSetOptions();
    } else if (stepId === 'step3') {
        populateWizardRankOptions();
    } else if (stepId === 'step4') {
        updateRequestSummary();
    }
    
    // Navigation event handlers...
}

// Set up the set declaration wizard
function setupSetDeclarationWizard() {
    const declarePanel = document.getElementById('declare-panel');
    if (!declarePanel) return;
    
    // First clear existing content
    const existingWizard = declarePanel.querySelector('.declare-wizard');
    if (existingWizard) existingWizard.remove();
    
    // Create instruction and help
    const helpPanel = document.createElement('div');
    helpPanel.className = 'declare-help';
    helpPanel.innerHTML = `
        <h3>Declaring a Set</h3>
        <p>When your team knows where all the cards in a set are, you can declare that set to score a point.</p>
        <div class="warning">Be careful! If your declaration is incorrect, the other team gets the point instead.</div>
        
        <div class="set-example">
            <p><strong>Example:</strong> A "Low Hearts" set contains these 6 cards:</p>
            <div class="example-cards">
                <div class="mini-card"><div class="mini-card-content red"><span>2♥</span></div></div>
                <div class="mini-card"><div class="mini-card-content red"><span>3♥</span></div></div>
                <div class="mini-card"><div class="mini-card-content red"><span>4♥</span></div></div>
                <div class="mini-card"><div class="mini-card-content red"><span>5♥</span></div></div>
                <div class="mini-card"><div class="mini-card-content red"><span>6♥</span></div></div>
                <div class="mini-card"><div class="mini-card-content red"><span>7♥</span></div></div>
            </div>
        </div>
    `;
    
    declarePanel.innerHTML = ''; // Clear existing content
    declarePanel.appendChild(helpPanel);
    
    // Create the main form with visual enhancements
    const setSelector = document.createElement('div');
    setSelector.className = 'set-selector';
    setSelector.innerHTML = `
        <label for="selected-set">Choose a set to declare:</label>
        <select id="selected-set" class="enhanced-select"></select>
    `;
    
    declarePanel.appendChild(setSelector);
    
    // Create the card assignments with visual representation
    const assignmentContainer = document.createElement('div');
    assignmentContainer.className = 'assignment-container';
    assignmentContainer.innerHTML = `
        <h4>Assign each card to the player who has it:</h4>
        <div id="card-assignment-grid"></div>
    `;
    
    declarePanel.appendChild(assignmentContainer);
    
    // Add submit button with confirmation
    const submitContainer = document.createElement('div');
    submitContainer.className = 'submit-container';
    submitContainer.innerHTML = `
        <button id="declare-submit-btn" class="btn btn-warning">Declare This Set</button>
        <div class="tip">Make sure your assignments are correct before declaring!</div>
    `;
    
    declarePanel.appendChild(submitContainer);
    
    // Populate sets
    populateSetOptions();
    
    // Event listener for set selection
    const setSelect = document.getElementById('selected-set');
    if (setSelect) {
        setSelect.addEventListener('change', function() {
            updateCardAssignmentGrid(this.value);
        });
    }
    
    // Event listener for declaration submission
    const declareBtn = document.getElementById('declare-submit-btn');
    if (declareBtn) {
        declareBtn.addEventListener('click', function() {
            const selectedSet = document.getElementById('selected-set').value;
            
            if (!selectedSet) {
                showNotification("Please select a set first", "info");
                return;
            }
            
            // Gather assignments from the UI
            const assignments = {};
            document.querySelectorAll('.card-assignment-row select').forEach(select => {
                const cardId = select.dataset.cardId;
                const playerId = parseInt(select.value);
                assignments[cardId] = playerId;
            });
            
            // Check if all assignments are made
            const allAssigned = Object.values(assignments).every(id => !isNaN(id));
            
            if (!allAssigned) {
                showNotification("Please assign all cards before declaring", "info");
                return;
            }
            
            // Show confirmation
            if (confirm(`Are you sure you want to declare the "${selectedSet}" set? If incorrect, the other team will get the point instead.`)) {
                // Submit the declaration
                socket.emit('declare_set', {
                    game_id: GAME_ID,
                    player_id: myPlayerId,
                    set_name: selectedSet,
                    card_assignments: assignments
                });
                
                showNotification("Declaration submitted!", "info");
            }
        });
    }
}

// Helper to populate set options
function populateSetOptions() {
    const setSelect = document.getElementById('selected-set');
    if (!setSelect) return;
    
    setSelect.innerHTML = '<option value="">-- Select a set --</option>';
    
    if (!availableSets || availableSets.length === 0) {
        const option = document.createElement('option');
        option.value = "";
        option.textContent = "No sets available to declare";
        option.disabled = true;
        setSelect.appendChild(option);
        return;
    }
    
    availableSets.forEach(set => {
        const option = document.createElement('option');
        option.value = set;
        option.textContent = set;
        setSelect.appendChild(option);
    });
}

// Helper to update card assignment grid
function updateCardAssignmentGrid(setName) {
    const grid = document.getElementById('card-assignment-grid');
    if (!grid || !setName) return;
    
    grid.innerHTML = '';
    
    // Determine cards in the set
    const [setType, setSuit] = setName.split(' ');
    let ranks = [];
    
    if (setType === 'Low') {
        ranks = ['2', '3', '4', '5', '6', '7'];
    } else if (setType === 'High') {
        ranks = ['9', '10', 'Jack', 'Queen', 'King', 'Ace'];
    }
    
    // Get all players on my team
    const myTeam = myPlayerId % 2;
    const teamPlayers = opponentData
        .filter(player => player.team === myTeam)
        .concat([{id: myPlayerId, name: 'You (Me)', team: myTeam}])
        .sort((a, b) => a.id - b.id);
    
    // Create assignment rows
    ranks.forEach(rank => {
        const row = document.createElement('div');
        row.className = 'card-assignment-row';
        
        const isRed = setSuit === 'Hearts' || setSuit === 'Diamonds';
        const cardId = `${rank}_${setSuit}`;
        
        row.innerHTML = `
            <div class="assignment-card ${isRed ? 'red' : 'black'}">
                <span class="card-text">${rank} of ${setSuit}</span>
                <span class="card-symbol">${rank}${getSuitSymbol(setSuit)}</span>
            </div>
            <div class="assignment-select-wrapper">
                <select data-card-id="${cardId}" class="player-assignment">
                    <option value="">Who has this card?</option>
                    ${teamPlayers.map(player => 
                        `<option value="${player.id}" ${
                            (player.id === myPlayerId && haveCardInHand(rank, setSuit)) 
                                ? 'selected' 
                                : ''
                        }>${player.name}</option>`
                    ).join('')}
                </select>
            </div>
        `;
        
        grid.appendChild(row);
    });
}

// Add these helper functions for the card request wizard

// Helper function to populate player select in the wizard
function populateWizardPlayerSelect() {
    const playerSelect = document.getElementById('wizard-target-player');
    if (!playerSelect) return;
    
    playerSelect.innerHTML = '<option value="">-- Select a player --</option>';
    
    // Debug current opponent data
    console.log("Populating wizard with opponent data:", opponentData);
    
    // First verify we have opponent data
    if (!opponentData || opponentData.length === 0) {
        playerSelect.innerHTML += '<option value="" disabled>No opponents available</option>';
        
        // Show a message and try to refresh data
        showNotification("No players found. Refreshing data...", "info");
        socket.emit('get_game_state', { game_id: GAME_ID });
        return;
    }
    
    // Populate target player options (only opponents on the other team)
    const myTeam = myPlayerId % 2;
    
    // Filter for opponents on the other team
    const otherTeamPlayers = opponentData.filter(player => 
        player.team !== myTeam && player.id !== myPlayerId
    );
    
    if (otherTeamPlayers.length === 0) {
        playerSelect.innerHTML += '<option value="" disabled>No opponents on other team</option>';
    } else {
        otherTeamPlayers.forEach(player => {
            const option = document.createElement('option');
            option.value = player.id;
            // Add visual indicator for bots
            option.textContent = player.name + (player.is_bot ? ' (Bot)' : '');
            playerSelect.appendChild(option);
        });
    }
    
    // Add event listener for selection
    playerSelect.addEventListener('change', function() {
        // Update summary
        const summaryPlayer = document.getElementById('summary-player');
        if (summaryPlayer) {
            const selectedPlayer = opponentData.find(p => p.id == this.value);
            summaryPlayer.textContent = selectedPlayer ? selectedPlayer.name : '___';
        }
        
        // Enable next step if a player is selected
        const nextBtn = document.querySelector('.wizard-navigation .btn-next');
        if (nextBtn) {
            nextBtn.classList.toggle('disabled', !this.value);
        }
    });
}

// Helper function to populate rank options in the wizard
function populateWizardRankOptions() {
    const rankOptions = document.querySelector('.rank-options');
    if (!rankOptions) return;
    
    rankOptions.innerHTML = '';
    
    // Get the selected set from session storage
    const selectedSet = sessionStorage.getItem('selectedSet');
    if (!selectedSet) {
        rankOptions.innerHTML = '<p>Please select a set first</p>';
        return;
    }
    
    // Parse the selected set
    const [setType, setSuit] = selectedSet.split(' ');
    
    // Define which ranks belong to which set
    const lowRanks = ['2', '3', '4', '5', '6', '7'];
    const highRanks = ['9', '10', 'Jack', 'Queen', 'King', 'Ace'];
    
    // Determine which ranks are in this set
    const setRanks = setType === 'Low' ? lowRanks : highRanks;
    
    // Find which cards in this set I already have
    const myCardsInSet = myHand.filter(card => 
        card.suit === setSuit && setRanks.includes(card.rank)
    );
    
    // Create rank options
    setRanks.forEach(rank => {
        const rankOption = document.createElement('div');
        rankOption.className = 'rank-option';
        rankOption.dataset.rank = rank;
        
        // Check if I already have this card
        const haveThisCard = myCardsInSet.some(card => card.rank === rank);
        
        // Add visual indicator if I already have this card
        if (haveThisCard) {
            rankOption.classList.add('in-hand');
            rankOption.innerHTML = `${rank} <span class="in-hand-marker">(in hand)</span>`;
        } else {
            rankOption.textContent = rank;
        }
        
        rankOption.addEventListener('click', function() {
            // If I already have this card, don't allow selecting it
            if (haveThisCard) {
                showNotification("You already have this card", "info");
                return;
            }
            
            // Remove selected class from all options
            document.querySelectorAll('.rank-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            
            // Add selected class to this option
            this.classList.add('selected');
            
            // Update the summary
            const summaryRank = document.getElementById('summary-rank');
            if (summaryRank) {
                summaryRank.textContent = rank;
            }
            
            // Store selected rank in session storage for next step
            sessionStorage.setItem('selectedRank', rank);
            sessionStorage.setItem('selectedSuit', setSuit);
            
            // Enable next button
            const nextBtn = document.querySelector('.wizard-navigation .btn-next');
            if (nextBtn) {
                nextBtn.classList.remove('disabled');
            }
        });
        
        rankOptions.appendChild(rankOption);
    });
}

// Helper function to populate suit options in the wizard
function populateWizardSuitOptions() {
    const suitOptions = document.querySelector('.suit-options');
    if (!suitOptions) return;
    
    suitOptions.innerHTML = '';
    
    // Get selected rank from session storage
    const selectedRank = sessionStorage.getItem('selectedRank');
    if (!selectedRank) {
        suitOptions.innerHTML = '<p>Please select a rank first</p>';
        return;
    }
    
    // Get all suits for the selected rank
    const suits = new Set();
    myHand.forEach(card => {
        if (card.rank === selectedRank) {
            suits.add(card.suit);
        }
    });
    
    // Create suit options
    Array.from(suits).sort().forEach(suit => {
        const suitOption = document.createElement('div');
        suitOption.className = 'suit-option';
        suitOption.dataset.suit = suit;
        
        const isRed = suit === 'Hearts' || suit === 'Diamonds';
        
        suitOption.innerHTML = `
            <span class="suit-symbol ${isRed ? 'red' : 'black'}">${getSuitSymbol(suit)}</span>
            <span>${suit}</span>
        `;
        
        suitOption.addEventListener('click', function() {
            // Remove selected class from all options
            document.querySelectorAll('.suit-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            
            // Add selected class to this option
            this.classList.add('selected');
            
            // Update the summary
            const summarySuit = document.getElementById('summary-suit');
            if (summarySuit) {
                summarySuit.textContent = suit;
            }
            
            // Store selected suit in session storage
            sessionStorage.setItem('selectedSuit', suit);
            
            // Enable next button
            const nextBtn = document.querySelector('.wizard-navigation .btn-next');
            if (nextBtn) {
                nextBtn.classList.remove('disabled');
            }
        });
        
        suitOptions.appendChild(suitOption);
    });
}

// Update the request summary in the wizard
function updateRequestSummary() {
    const summaryPlayer = document.getElementById('summary-player');
    const summaryRank = document.getElementById('summary-rank');
    const summarySuit = document.getElementById('summary-suit');
    
    if (!summaryPlayer || !summaryRank || !summarySuit) return;
    
    // Get values from session storage
    const playerSelect = document.getElementById('wizard-target-player');
    const selectedPlayerId = playerSelect ? playerSelect.value : sessionStorage.getItem('selectedPlayerId');
    const selectedRank = sessionStorage.getItem('selectedRank');
    const selectedSuit = sessionStorage.getItem('selectedSuit');
    
    // Update summary text
    if (selectedPlayerId) {
        const selectedPlayer = opponentData.find(p => p.id == selectedPlayerId);
        summaryPlayer.textContent = selectedPlayer ? selectedPlayer.name : '___';
    } else {
        summaryPlayer.textContent = '___';
    }
    
    summaryRank.textContent = selectedRank || '___';
    summarySuit.textContent = selectedSuit || '___';
    
    // Enable/disable submit button
    const submitBtn = document.getElementById('wizard-submit-request');
    if (submitBtn) {
        const isComplete = selectedPlayerId && selectedRank && selectedSuit;
        submitBtn.disabled = !isComplete;
    }
}

// Handle card request submission from the wizard
function submitCardRequest() {
    // Get values from session storage or form elements
    const playerSelect = document.getElementById('wizard-target-player');
    const selectedPlayerId = playerSelect ? playerSelect.value : sessionStorage.getItem('selectedPlayerId');
    const selectedRank = sessionStorage.getItem('selectedRank');
    const selectedSuit = sessionStorage.getItem('selectedSuit');
    
    // Validate
    if (!selectedPlayerId || !selectedRank || !selectedSuit) {
        showNotification('Please complete all steps before submitting', 'info');
        return;
    }
    
    // Submit request
    console.log(`Requesting ${selectedRank} of ${selectedSuit} from player ${selectedPlayerId}`);
    
    // Emit the socket event
    socket.emit('request_card', {
        game_id: GAME_ID,
        player_id: myPlayerId,
        target_id: parseInt(selectedPlayerId),
        card_rank: selectedRank,
        card_suit: selectedSuit
    });
    
    // Show notification
    showNotification(`Requesting ${selectedRank} of ${selectedSuit}...`, 'info');
    
    // Clean up
    sessionStorage.removeItem('selectedPlayerId');
    sessionStorage.removeItem('selectedRank');
    sessionStorage.removeItem('selectedSuit');
    
    // Close wizard or reset to first step
    const wizardSteps = document.querySelectorAll('.wizard-step-btn');
    if (wizardSteps.length > 0) {
        wizardSteps[0].click();
    }
}

// A simpler way to setup basic action UI that will definitely work
function setupBasicActionUI() {
    console.log("Setting up basic action UI");
    
    // Find panels
    const requestPanel = document.getElementById('request-panel');
    const declarePanel = document.getElementById('declare-panel');
    const waitingPanel = document.getElementById('waiting-panel');
    
    if (!requestPanel || !declarePanel || !waitingPanel) {
        console.error("Cannot find action panels - they may not exist in the HTML");
        return;
    }
    
    // Clear existing content
    requestPanel.innerHTML = '';
    declarePanel.innerHTML = '';
    
    // Create basic request form
    requestPanel.innerHTML = `
        <div class="basic-form">
            <h3>Request a Card</h3>
            <p>Ask an opponent from the other team for a card that matches the rank of a card you already have.</p>
            
            <div class="form-group">
                <label for="basic-target-player">Choose a player:</label>
                <select id="basic-target-player" class="form-control"></select>
            </div>
            
            <div class="form-group">
                <label for="basic-card-rank">Choose a rank:</label>
                <select id="basic-card-rank" class="form-control"></select>
            </div>
            
            <div class="form-group">
                <label for="basic-card-suit">Choose a suit:</label>
                <select id="basic-card-suit" class="form-control"></select>
            </div>
            
            <button id="basic-send-request" class="btn btn-primary">Ask for Card</button>
        </div>
    `;
    
    // Create basic declare form
    declarePanel.innerHTML = `
        <div class="basic-form">
            <h3>Declare a Set</h3>
            <p>When your team knows where all the cards in a set are, you can declare that set to score a point.</p>
            
            <div class="form-group">
                <label for="basic-set-name">Choose a set:</label>
                <select id="basic-set-name" class="form-control"></select>
            </div>
            
            <div id="basic-card-assignments">
                <!-- Will be populated when a set is selected -->
            </div>
            
            <button id="basic-send-declaration" class="btn btn-warning">Declare Set</button>
        </div>
    `;
    
    // Populate the basic forms
    populateBasicRequestForm();
    populateBasicDeclareForm();
    
    // Setup tab functionality
    const requestTab = document.getElementById('request-tab');
    const declareTab = document.getElementById('declare-tab');
    
    if (requestTab && declareTab) {
        requestTab.addEventListener('click', function() {
            requestTab.classList.add('active');
            declareTab.classList.remove('active');
            requestPanel.style.display = 'block';
            declarePanel.style.display = 'none';
        });
        
        declareTab.addEventListener('click', function() {
            declareTab.classList.add('active');
            requestTab.classList.remove('active');
            declarePanel.style.display = 'block';
            requestPanel.style.display = 'none';
        });
    }
}

// Populate the basic request form
function populateBasicRequestForm() {
    console.log("Populating basic request form with correct game rules");
    
    const targetSelect = document.getElementById('basic-target-player');
    const rankSelect = document.getElementById('basic-card-rank');
    const suitSelect = document.getElementById('basic-card-suit');
    const sendBtn = document.getElementById('basic-send-request');
    
    if (!targetSelect || !rankSelect || !suitSelect || !sendBtn) {
        console.error("Cannot find basic request form elements");
        return;
    }
    
    // Clear existing options
    targetSelect.innerHTML = '';
    rankSelect.innerHTML = '';
    suitSelect.innerHTML = '';
    
    // Debug opponent data
    console.log("Populating target dropdown with opponent data:", opponentData);
    
    // FIXED: Better player dropdown population
    targetSelect.innerHTML = '<option value="">-- Select a player --</option>';
    const myTeam = myPlayerId % 2;
    
    // First check if we have opponent data
    if (!opponentData || opponentData.length === 0) {
        console.warn("No opponent data available for populating dropdown");
        targetSelect.innerHTML += '<option value="" disabled>No opponents available</option>';
        
        // Try to refresh opponent data
        socket.emit('get_game_state', { game_id: GAME_ID });
        return;
    }
    
    // Filter and add opponents from the other team (including bots)
    const otherTeamPlayers = opponentData.filter(player => 
        player.team !== myTeam && player.id !== myPlayerId
    );
    
    console.log("Filtered other team players:", otherTeamPlayers);
    
    if (otherTeamPlayers.length === 0) {
        targetSelect.innerHTML += '<option value="" disabled>No opponents on other team</option>';
    } else {
        otherTeamPlayers.forEach(player => {
            const option = document.createElement('option');
            option.value = player.id;
            option.textContent = player.name + (player.is_bot ? ' (Bot)' : '');
            targetSelect.appendChild(option);
            console.log("Added player to dropdown:", player.name);
        });
    }
    
    // Rest of function for rank and suit selection...
}

// Populate the basic declare form
function populateBasicDeclareForm() {
    console.log("Populating basic declare form");
    
    const setSelect = document.getElementById('basic-set-name');
    const cardAssignments = document.getElementById('basic-card-assignments');
    const sendBtn = document.getElementById('basic-send-declaration');
    
    if (!setSelect || !cardAssignments || !sendBtn) {
        console.error("Cannot find basic declare form elements");
        return;
    }
    
    // Clear existing options
    setSelect.innerHTML = '';
    cardAssignments.innerHTML = '';
    
    // Add default option
    setSelect.innerHTML = '<option value="">-- Select a set --</option>';
    
    // Populate set dropdown
    if (availableSets && availableSets.length === 0) {
        const option = document.createElement('option');
        option.value = "";
        option.textContent = "No sets available";
        option.disabled = true;
        setSelect.appendChild(option);
        return;
    }
    
    availableSets.forEach(set => {
        const option = document.createElement('option');
        option.value = set;
        option.textContent = set;
        setSelect.appendChild(option);
    });
}

// Add this function to create mock opponents for testing
function createMockOpponents() {
    console.log("Creating mock opponents for testing");
    
    const mockOpponents = [
        { id: 1, name: "Player 1", team: 0, card_count: 8, is_bot: false },
        { id: 2, name: "Player 2", team: 1, card_count: 7, is_bot: false },
        { id: 3, name: "Bot 1", team: 0, card_count: 9, is_bot: true },
        { id: 4, name: "Bot 2", team: 1, card_count: 6, is_bot: true }
    ];
    
    // Set global opponent data
    opponentData = mockOpponents;
    
    // Force visualization update
    updateOpponents(mockOpponents);
    
    // Show a notification
    showNotification("Created mock opponents for testing", "info");
    
    return mockOpponents;
}

// Add this debug helper function
function debugGameState() {
    console.log("=== GAME STATE DEBUG ===");
    console.log("My Player ID:", myPlayerId);
    console.log("Current Turn:", currentTurn);
    console.log("Game Started:", gameStarted);
    console.log("My Hand:", myHand);
    console.log("Opponent Data:", opponentData);
    console.log("=== END DEBUG ===");
}

// Add this function to ensure opponents are properly displayed
function forceOpponentDisplay() {
    console.log("Forcing opponent display refresh");
    
    // Get the opponents area
    const opponentsArea = document.getElementById('opponents-area');
    if (!opponentsArea) {
        console.error("Cannot find opponents area element");
        return;
    }
    
    // Clear current content
    opponentsArea.innerHTML = '';
    
    // Check if we have opponent data
    if (!opponentData || opponentData.length === 0) {
        console.warn("No opponent data to display");
        opponentsArea.innerHTML = `
            <div class="no-opponents-message">
                <p>No other players found.</p>
                <button id="refresh-opponents" class="btn btn-small">Refresh</button>
            </div>
        `;
        
        // Add refresh button functionality
        const refreshBtn = opponentsArea.querySelector('#refresh-opponents');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', function() {
                socket.emit('get_game_state', { game_id: GAME_ID });
                showNotification("Refreshing game state...", "info");
            });
        }
        return;
    }
    
    // Add a small header to make it clearer
    const header = document.createElement('div');
    header.className = 'opponents-header';
    header.innerHTML = `<h3>Players (${opponentData.length + 1})</h3>`;
    opponentsArea.appendChild(header);
    
    // Create temporary player groups to ensure correct grouping
    const team1 = [];
    const team2 = [];
    
    // First, categorize all opponents
    opponentData.forEach(player => {
        if (player.team === 0) {
            team1.push(player);
        } else {
            team2.push(player);
        }
    });
    
    // Add myself to the appropriate team if not already included
    if (myPlayerId !== null) {
        const myTeam = myPlayerId % 2;
        let foundSelf = false;
        
        // Check if I'm already in the opponent data
        opponentData.forEach(player => {
            if (player.id === myPlayerId) {
                foundSelf = true;
            }
        });
        
        // If I'm not in the opponent data, add myself
        if (!foundSelf) {
            const myPlayerObj = {
                id: myPlayerId,
                name: 'You (Me)',
                team: myTeam,
                card_count: myHand ? myHand.length : 0,
                is_bot: false
            };
            
            if (myTeam === 0) {
                team1.push(myPlayerObj);
            } else {
                team2.push(myPlayerObj);
            }
        }
    }
    
    // Create team containers with clear visual distinction
    const team1Container = document.createElement('div');
    team1Container.className = 'team-container team1-container';
    team1Container.innerHTML = '<h3>Team 1</h3>';
    team1Container.style.border = '3px solid var(--team1-color)';
    
    const team2Container = document.createElement('div');
    team2Container.className = 'team-container team2-container';
    team2Container.innerHTML = '<h3>Team 2</h3>';
    team2Container.style.border = '3px solid var(--team2-color)';
    
    // Add players to team containers
    team1.forEach(player => {
        const playerElem = createPlayerElement(player);
        team1Container.appendChild(playerElem);
    });
    
    team2.forEach(player => {
        const playerElem = createPlayerElement(player);
        team2Container.appendChild(playerElem);
    });
    
    // Add team containers to the opponents area
    if (team1.length > 0) {
        opponentsArea.appendChild(team1Container);
    }
    
    if (team2.length > 0) {
        opponentsArea.appendChild(team2Container);
    }
    
    // Log the final result
    console.log(`Displayed ${team1.length} Team 1 players and ${team2.length} Team 2 players`);
}

// Helper function to create a player element
function createPlayerElement(player) {
    // Create player element with enhanced styling
    const playerElem = document.createElement('div');
    playerElem.className = 'opponent';
    playerElem.dataset.id = player.id;
    playerElem.dataset.team = player.team;
    
    // Add appropriate classes
    if (player.id === myPlayerId) {
        playerElem.classList.add('self');
    }
    
    if (player.is_bot) {
        playerElem.classList.add('bot-player');
    }
    
    if (player.id === currentTurn) {
        playerElem.classList.add('current-turn');
    }
    
    // Create enhanced display with clear visual indicators
    playerElem.innerHTML = `
        <div class="opponent-avatar">${player.id === myPlayerId ? '👤' : player.is_bot ? '🤖' : '👨‍💼'}</div>
        <div class="opponent-name">${player.id === myPlayerId ? 'YOU' : player.name}${player.is_bot ? ' <span class="bot-tag">BOT</span>' : ''}</div>
        <div class="opponent-cards"><i class="card-icon">🃏</i> ${player.card_count || 0}</div>
        <div class="opponent-team team${player.team + 1}" style="color: var(--team${player.team + 1}-color);">Team ${player.team + 1}</div>
        ${player.id === currentTurn ? '<div class="turn-indicator">CURRENT TURN</div>' : ''}
    `;
    
    // Add interactive elements for requesting cards
    if (player.id !== myPlayerId && player.team !== myPlayerId % 2 && currentTurn === myPlayerId) {
        playerElem.classList.add('clickable');
        
        const actionButton = document.createElement('button');
        actionButton.className = 'request-card-btn';
        actionButton.textContent = 'Ask for Card';
        playerElem.appendChild(actionButton);
        
        actionButton.addEventListener('click', function(e) {
            e.stopPropagation();  // Prevent double triggering
            selectPlayerInRequestForm(player.id);
        });
        
        // Make the whole player card clickable too
        playerElem.addEventListener('click', function() {
            selectPlayerInRequestForm(player.id);
        });
    }
    
    return playerElem;
}

// Helper to select a player in the request form
function selectPlayerInRequestForm(playerId) {
    // Show request panel
    document.getElementById('request-panel').style.display = 'block';
    document.getElementById('declare-panel').style.display = 'none';
    
    // Activate request tab
    document.getElementById('request-tab').classList.add('active');
    document.getElementById('declare-tab').classList.remove('active');
    
    // Select the player in the dropdown
    const targetSelect = document.getElementById('basic-target-player');
    if (targetSelect) {
        targetSelect.value = playerId;
        targetSelect.dispatchEvent(new Event('change'));
    }
    
    // Scroll to the action panel
    document.getElementById('action-panel').scrollIntoView({ behavior: 'smooth' });
}

// Add this to your setupGameEvents function
function setupRefreshControls() {
    // Create a refresh button specifically for opponent visualization
    const gameBoard = document.querySelector('.game-board');
    if (gameBoard) {
        const refreshContainer = document.createElement('div');
        refreshContainer.className = 'refresh-controls';
        refreshContainer.style.textAlign = 'right';
        refreshContainer.style.padding = '5px';
        
        const refreshBtn = document.createElement('button');
        refreshBtn.className = 'btn btn-small';
        refreshBtn.innerHTML = '🔄 Refresh Game';
        refreshBtn.addEventListener('click', function() {
            // Force a complete UI refresh
            socket.emit('get_game_state', { game_id: GAME_ID });
            showNotification("Refreshing game state...", "info");
            
            // Force update all UI components directly
            setTimeout(() => {
                if (opponentData && opponentData.length > 0) {
                    forceOpponentDisplay();
                }
                setupBasicActionUI();
            }, 500);
        });
        
        refreshContainer.appendChild(refreshBtn);
        gameBoard.insertBefore(refreshContainer, gameBoard.firstChild);
    }
}

// Call this when the game starts
socket.on('game_started', function(data) {
    // Existing code...
    
    // Add this to ensure we have refresh controls
    setupRefreshControls();
    
    // Existing code...
});

// Add this at the end of your setupGameEvents function
// Special handling for bot games
socket.on('bot_added', function(data) {
    console.log("Bot player added:", data);
    
    // Request a fresh game state to make sure we have all players including bots
    socket.emit('get_game_state', { game_id: GAME_ID });
    
    showNotification(`Bot player ${data.bot_name} added to the game`, "info");
});

// Add this to DOMContentLoaded handler after setupGameEvents()
// Try to force refresh if we detect we're in a game with bots
if (GAME_ID) {
    setTimeout(() => {
        if (opponentData.length === 0) {
            console.log("No opponent data detected, requesting game state");
            socket.emit('get_game_state', { game_id: GAME_ID });
        }
    }, 2000);
}

// Add this at the top of your file
let DEBUG_MODE = true; // Set to false for production

// Add this comprehensive debug function
function debugFullGameState() {
    if (!DEBUG_MODE) return;
    
    console.group("=== FULL GAME STATE DIAGNOSTIC ===");
    console.log("🎮 Game ID:", GAME_ID);
    console.log("🧩 Game Started:", gameStarted);
    console.log("👤 My Player ID:", myPlayerId);
    console.log("🎯 Current Turn:", currentTurn);
    console.log("🃏 My Hand:", myHand);
    console.log("👥 Opponent Data:", opponentData);
    
    // DOM element checks
    const opponentsArea = document.getElementById('opponents-area');
    console.log("📋 Opponents Area Exists:", !!opponentsArea);
    if (opponentsArea) {
        console.log("📋 Opponents Area Content:", opponentsArea.innerHTML);
        console.log("📋 Number of Opponent Elements:", opponentsArea.querySelectorAll('.opponent').length);
    }
    
    const actionPanel = document.getElementById('action-panel');
    console.log("🔘 Action Panel Exists:", !!actionPanel);
    
    const requestPanel = document.getElementById('request-panel');
    console.log("📝 Request Panel Exists:", !!requestPanel);
    if (requestPanel) {
        console.log("📝 Request Panel Display:", requestPanel.style.display);
    }
    
    // Check player drop-down
    const playerSelect = document.getElementById('basic-target-player');
    if (playerSelect) {
        console.log("🔽 Player Select Options:", playerSelect.options.length);
        console.log("🔽 Player Select HTML:", playerSelect.innerHTML);
    }
    
    console.groupEnd();
    
    // Return diagnostics for notifications
    return {
        hasOpponentData: opponentData && opponentData.length > 0,
        hasOpponentsArea: !!opponentsArea,
        hasOpponentElements: opponentsArea ? opponentsArea.querySelectorAll('.opponent').length > 0 : false,
        hasActionPanel: !!actionPanel,
        hasPlayerSelect: !!playerSelect
    };
}

// New function to ensure action panels are properly initialized and updated
function updateActionPanels() {
    const actionPanel = document.getElementById('action-panel');
    const requestPanel = document.getElementById('request-panel');
    const declarePanel = document.getElementById('declare-panel');
    const waitingPanel = document.getElementById('waiting-panel');
    
    if (!actionPanel || !requestPanel || !declarePanel || !waitingPanel) {
        console.error('❌ Action panels not found in DOM');
        return;
    }
    
    // Set up the request form if it's my turn
    if (currentTurn === myPlayerId) {
        console.log('🎯 It\'s my turn, setting up action panels');
        
        // Hide waiting panel, show appropriate action panel
        waitingPanel.style.display = 'none';
        
        // Default to request panel
        requestPanel.style.display = 'block';
        declarePanel.style.display = 'none';
        
        // Update tabs if they exist
        const requestTab = document.getElementById('request-tab');
        const declareTab = document.getElementById('declare-tab');
        
        if (requestTab && declareTab) {
            requestTab.classList.add('active');
            declareTab.classList.remove('active');
        }
        
        // Populate the request form
        setupBasicRequestForm();
        
        // Show a notification
        showNotification("It's your turn to play!", 'success');
    } else {
        // Not my turn, show waiting panel
        waitingPanel.style.display = 'block';
        requestPanel.style.display = 'none';
        declarePanel.style.display = 'none';
    }
}

// Completely rewrite this function to be more robust
function setupBasicRequestForm() {
    console.log('🔄 Setting up basic request form');
    
    // Get form elements
    const requestPanel = document.getElementById('request-panel');
    
    if (!requestPanel) {
        console.error('❌ Request panel not found');
        return;
    }
    
    // Clear existing content
    requestPanel.innerHTML = '';
    
    // Create a new basic form
    const formHtml = `
        <div class="basic-form">
            <h3>Request a Card</h3>
            <p>Ask an opponent from the other team for a card.</p>
            
            <div class="form-group">
                <label for="basic-target-player">Choose a player:</label>
                <select id="basic-target-player" class="form-control">
                    <option value="">-- Select a player --</option>
                </select>
                <div class="player-count-info"></div>
            </div>
            
            <div class="form-group">
                <label for="basic-set-select">Choose a set:</label>
                <select id="basic-set-select" class="form-control">
                    <option value="">-- Select a set --</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="basic-card-rank">Choose a card:</label>
                <select id="basic-card-rank" class="form-control" disabled>
                    <option value="">-- Select a set first --</option>
                </select>
            </div>
            
            <div class="form-group" style="display:none;">
                <label for="basic-card-suit">Suit:</label>
                <select id="basic-card-suit" class="form-control">
                    <option value="">-- Auto-selected --</option>
                </select>
            </div>
            
            <button id="basic-send-request" class="btn btn-primary" disabled>Ask for Card</button>
        </div>
    `;
    
    // Add form to panel
    requestPanel.innerHTML = formHtml;
    
    // Now populate the player dropdown
    populatePlayerDropdown();
    
    // Set up event listeners
    const setSelect = document.getElementById('basic-set-select');
    const rankSelect = document.getElementById('basic-card-rank');
    const suitSelect = document.getElementById('basic-card-suit');
    const sendBtn = document.getElementById('basic-send-request');
    
    if (setSelect) {
        setSelect.addEventListener('change', function() {
            populateRankOptions(this.value);
        });
    }
    
    if (rankSelect) {
        rankSelect.addEventListener('change', updateSendButtonState);
    }
    
    if (sendBtn) {
        sendBtn.addEventListener('click', sendCardRequest);
    }
    
    // Populate set options
    populateSetOptions();
}

// Function to populate player dropdown
function populatePlayerDropdown() {
    const playerSelect = document.getElementById('basic-target-player');
    const playerCountInfo = document.querySelector('.player-count-info');
    
    if (!playerSelect || !playerCountInfo) {
        console.error('❌ Player select elements not found');
        return;
    }
    
    // Clear and initialize
    playerSelect.innerHTML = '<option value="">-- Select a player --</option>';
    
    console.log('👥 Populating player dropdown with opponent data:', opponentData);
    
    // First check if we have data
    if (!opponentData || opponentData.length === 0) {
        playerSelect.innerHTML += '<option value="" disabled>No opponents found</option>';
        playerCountInfo.textContent = 'No opponents available - try refreshing';
        playerCountInfo.style.color = 'red';
        
        // Try to reload data
        socket.emit('get_game_state', { game_id: GAME_ID });
        return;
    }
    
    // Filter for opponents on other team
    const myTeam = myPlayerId % 2;
    const otherTeamPlayers = opponentData.filter(player => 
        player.team !== myTeam && player.id !== myPlayerId
    );
    
    if (otherTeamPlayers.length === 0) {
        playerSelect.innerHTML += '<option value="" disabled>No opponents on other team</option>';
        playerCountInfo.textContent = 'No opponents on other team';
    } else {
        // Add each player as an option
        otherTeamPlayers.forEach(player => {
            const option = document.createElement('option');
            option.value = player.id;
            option.textContent = `${player.name}${player.is_bot ? ' (Bot)' : ''}`;
            playerSelect.appendChild(option);
        });
        
        playerCountInfo.textContent = `${otherTeamPlayers.length} opponents available`;
        playerCountInfo.style.color = 'green';
    }
    
    // Add change listener
    playerSelect.addEventListener('change', updateSendButtonState);
}

// Function to populate set options
function populateSetOptions() {
    const setSelect = document.getElementById('basic-set-select');
    if (!setSelect) return;
    
    // Clear options
    setSelect.innerHTML = '<option value="">-- Select a set --</option>';
    
    // Define sets
    const lowRanks = ['2', '3', '4', '5', '6', '7'];
    const highRanks = ['9', '10', 'Jack', 'Queen', 'King', 'Ace'];
    const suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades'];
    
    // Determine which sets the player has cards in
    const playerSets = new Set();
    
    if (!myHand || myHand.length === 0) {
        setSelect.innerHTML += '<option value="" disabled>You have no cards</option>';
        return;
    }
    
    // Find which sets the player has at least one card in
    myHand.forEach(card => {
        if (lowRanks.includes(card.rank)) {
            playerSets.add(`Low ${card.suit}`);
        } else if (highRanks.includes(card.rank)) {
            playerSets.add(`High ${card.suit}`);
        }
    });
    
    // Add each set as an option
    [...playerSets].sort().forEach(set => {
        const option = document.createElement('option');
        option.value = set;
        option.textContent = set;
        setSelect.appendChild(option);
    });
    
    if (playerSets.size === 0) {
        setSelect.innerHTML += '<option value="" disabled>No valid sets in your hand</option>';
    }
}

// Function to populate rank options based on selected set
function populateRankOptions(selectedSet) {
    const rankSelect = document.getElementById('basic-card-rank');
    const suitSelect = document.getElementById('basic-card-suit');
    
    if (!rankSelect || !suitSelect || !selectedSet) return;
    
    // Parse the set
    const [setType, setSuit] = selectedSet.split(' ');
    
    // Define ranks in set
    const lowRanks = ['2', '3', '4', '5', '6', '7'];
    const highRanks = ['9', '10', 'Jack', 'Queen', 'King', 'Ace'];
    
    // Determine which ranks are in this set
    const setRanks = setType === 'Low' ? lowRanks : highRanks;
    
    // Clear rank select
    rankSelect.innerHTML = '<option value="">-- Select a card --</option>';
    rankSelect.disabled = false;
    
    // Find which cards in this set I already have
    const myCardsInSet = myHand.filter(card => 
        card.suit === setSuit && setRanks.includes(card.rank)
    );
    
    // Create rank options
    setRanks.forEach(rank => {
        const haveCard = myCardsInSet.some(card => card.rank === rank);
        
        const option = document.createElement('option');
        option.value = rank;
        option.textContent = `${rank}${haveCard ? ' (in hand)' : ''}`;
        option.disabled = haveCard; // Disable cards I already have
        
        rankSelect.appendChild(option);
    });
    
    // Set suit automatically
    suitSelect.innerHTML = `<option value="${setSuit}" selected>${setSuit}</option>`;
    
    // Update button state
    updateSendButtonState();
}

// Function to update send button state
function updateSendButtonState() {
    const playerSelect = document.getElementById('basic-target-player');
    const rankSelect = document.getElementById('basic-card-rank');
    const sendBtn = document.getElementById('basic-send-request');
    
    if (!playerSelect || !rankSelect || !sendBtn) return;
    
    // Enable button if both player and rank are selected
    const isValid = playerSelect.value && rankSelect.value;
    sendBtn.disabled = !isValid;
}

// Function to send card request
function sendCardRequest() {
    const playerSelect = document.getElementById('basic-target-player');
    const rankSelect = document.getElementById('basic-card-rank');
    const suitSelect = document.getElementById('basic-card-suit');
    
    if (!playerSelect || !rankSelect || !suitSelect) return;
    
    const targetId = parseInt(playerSelect.value);
    const rank = rankSelect.value;
    const suit = suitSelect.value;
    
    if (!targetId || !rank || !suit) {
        showNotification('Please complete all fields', 'error');
        return;
    }
    
    // Find target player name
    const targetPlayer = opponentData.find(p => p.id === targetId);
    const targetName = targetPlayer ? targetPlayer.name : 'opponent';
    
    // Send request to server
    socket.emit('request_card', {
        game_id: GAME_ID,
        player_id: myPlayerId,
        target_id: targetId,
        card_rank: rank,
        card_suit: suit
    });
    
    // Show user feedback
    showNotification(`Requesting ${rank} of ${suit} from ${targetName}...`, 'info');
    
    // Disable form to prevent double submission
    const sendBtn = document.getElementById('basic-send-request');
    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.textContent = 'Request Sent...';
    }
}

// Add this to ensure the game is properly initialized
function ensureGameInitialization() {
    console.log('🔍 Checking game initialization status');
    
    // First check if we have a stored player ID
    const storedPlayerId = sessionStorage.getItem('myPlayerId');
    if (storedPlayerId) {
        console.log('🔄 Recovered player ID from storage:', storedPlayerId);
        myPlayerId = parseInt(storedPlayerId);
    }
    
    // Check if we need to request a game state update
    const needsUpdate = !gameStarted || !opponentData || opponentData.length === 0;
    
    if (needsUpdate && GAME_ID) {
        console.log('🔄 Game needs initialization, requesting state update');
        socket.emit('get_game_state', { 
            game_id: GAME_ID,
            player_id: myPlayerId || undefined
        });
        
        // Add UI notification
        const gameBoard = document.querySelector('.game-board');
        if (gameBoard) {
            const loadingMsg = document.createElement('div');
            loadingMsg.className = 'loading-message';
            loadingMsg.textContent = 'Loading game data...';
            loadingMsg.style.textAlign = 'center';
            loadingMsg.style.padding = '20px';
            loadingMsg.style.backgroundColor = '#f8f9fa';
            loadingMsg.style.borderRadius = '8px';
            loadingMsg.style.margin = '20px 0';
            
            // Add a spinner
            const spinner = document.createElement('div');
            spinner.className = 'spinner';
            spinner.style.border = '4px solid #f3f3f3';
            spinner.style.borderTop = '4px solid var(--primary-color)';
            spinner.style.borderRadius = '50%';
            spinner.style.width = '30px';
            spinner.style.height = '30px';
            spinner.style.margin = '10px auto';
            spinner.style.animation = 'spin 2s linear infinite';
            
            // Add keyframes for spinner
            const style = document.createElement('style');
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
            
            loadingMsg.insertBefore(spinner, loadingMsg.firstChild);
            gameBoard.insertBefore(loadingMsg, gameBoard.firstChild);
            
            // Remove after success or timeout
            setTimeout(() => {
                if (loadingMsg.parentNode) {
                    loadingMsg.parentNode.removeChild(loadingMsg);
                }
            }, 5000);
        }
    } else {
        console.log('✅ Game already initialized');
    }
}

// Add this at the beginning of the file to ensure we can reconnect
window.addEventListener('load', function() {
    // Try to reconnect if we have stored game information
    const storedGameId = GAME_ID;
    const storedPlayerId = sessionStorage.getItem('myPlayerId');
    
    if (storedGameId && storedPlayerId) {
        console.log('🔄 Attempting to reconnect to game:', storedGameId, 'as player:', storedPlayerId);
        
        setTimeout(() => {
            socket.emit('rejoin_game', {
                game_id: storedGameId,
                player_id: parseInt(storedPlayerId)
            });
            
            showNotification('Reconnecting to game...', 'info');
        }, 1000);
    }
});

// Add a visible reconnect button in case of issues
function addReconnectButton() {
    const gameHeader = document.querySelector('.game-header');
    
    if (gameHeader) {
        const reconnectBtn = document.createElement('button');
        reconnectBtn.className = 'btn btn-small btn-warning';
        reconnectBtn.innerHTML = '🔄 Reconnect';
        reconnectBtn.addEventListener('click', function() {
            const storedPlayerId = sessionStorage.getItem('myPlayerId');
            
            if (storedPlayerId) {
                socket.emit('rejoin_game', {
                    game_id: GAME_ID,
                    player_id: parseInt(storedPlayerId)
                });
                
                showNotification('Attempting to reconnect...', 'info');
            } else {
                showNotification('No player ID found. Try refreshing the page.', 'error');
            }
        });
        
        gameHeader.appendChild(reconnectBtn);
    }
}

// Call this in your setupGameEvents function
addReconnectButton();

// Add this code to monitor socket events
(function setupSocketMonitoring() {
    const originalEmit = socket.emit;
    
    // Override emit to add logging
    socket.emit = function(event, ...args) {
        console.log(`📡 SOCKET EMIT: ${event}`, ...args);
        return originalEmit.apply(this, [event, ...args]);
    };
    
    // Listen for all incoming events
    const onevent = socket.onevent;
    socket.onevent = function(packet) {
        const [event, ...args] = packet.data || [];
        if (event !== 'disconnect') { // Avoid logging frequent disconnect checks
            console.log(`📡 SOCKET RECEIVE: ${event}`, ...args);
        }
        return onevent.apply(this, arguments);
    };
    
    console.log('📡 Socket monitoring enabled');
})();