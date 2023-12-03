let socket = io();

// Unique ID for this client
let cursorId = Math.random().toString(36).substr(2, 9);

// milliseconds
const THROTTLE_INTERVAL = 20;
let lastEmit = Date.now();
let cursors = {};

// Track last position of cursor to calculate distance traveled
let lastPosition = { x: null, y: null };
let totalDistance = 0;

document.addEventListener('mousemove', (event) => {
    // Throttle the number of events emitted
    const now = Date.now();
    if (now - lastEmit > THROTTLE_INTERVAL) {
        // Emit cursor position and update cumulative distance traveled to server

        // Check if lastPosition is not null
        if (lastPosition.x !== null && lastPosition.y !== null) {
            // Calculate the distance between the last position and the current position
            const deltaX = Math.abs(event.pageX - lastPosition.x);
            const deltaY = Math.abs(event.pageY - lastPosition.y);

            // Calculate distance traveled
            const distance = Math.sqrt((deltaX * deltaX) + (deltaY * deltaY));

            // Add the distance to the total
            totalDistance += distance;
        }

        // Update the last position
        lastPosition.x = event.pageX;
        lastPosition.y = event.pageY;

        // Emit cursor position and distance traveled
        socket.emit('move_cursor', { x: event.pageX, y: event.pageY, totalDistance: totalDistance });

        // Update last emit time
        lastEmit = now;
    }
});

document.addEventListener('touchmove', function (event) {
    event.preventDefault(); // Prevent scrolling on touch move
    const touch = event.touches[0];
    const now = Date.now();
    if (now - lastEmit > THROTTLE_INTERVAL) {
        socket.emit('cursor_move', { x: touch.pageX, y: touch.pageY });
        lastEmit = now;
    }
}, { passive: false });


socket.on('batch_update', function (activeClients) {
    // Update active cursors
    for (let id in activeClients) {

        // Don't update the cursor of the current client
        if (id !== cursorId) {
            updateCursor(id, activeClients[id]["position"].x, activeClients[id]["position"].y);
        }
    }

    // Update leaderboard
    updateLeaderboard(activeClients);
});

socket.on('client_disconnect', function (activeClients) {
    // Remove cursors of disconnected clients
    removeDisconnectedCursors(activeClients);
});

function updateCursor(id, x, y) {
    if (!cursors[id]) {
        let cursor = document.createElement('div');
        cursor.id = id;
        cursor.classList.add('cursor');
        cursor.style.position = 'absolute';
        cursor.style.height = '20px';
        cursor.style.width = '20px';
        cursor.style.backgroundColor = getRandomColor();
        cursor.style.borderRadius = '50%';
        cursor.style.pointerEvents = 'none';
        document.body.appendChild(cursor);
        cursors[id] = cursor;
    }
    cursors[id].style.transform = `translate3d(${x}px, ${y}px, 0)`;
}

function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

function removeDisconnectedCursors(activeClients) {
    // Remove cursors of disconnected clients

    // Get all active cursors
    const allCursorElements = document.getElementsByClassName('cursor');

    // Remove cursors that are not in the activeClients array
    Array.from(allCursorElements).forEach(cursorElem => {
        if (!(cursorElem.id in activeClients)) {
            cursorElem.remove();
        }
    });
}

function updateLeaderboard(activeClients) {
    const leaderboard = document.getElementById('leaderboard');
    leaderboard.innerHTML = '<h4>Leaderboard (Distance in Pixels)</h4>';

    // Sort active clients by distance traveled and update leaderboard.
    Object.entries(activeClients)
        .sort((a, b) => b[1].distance - a[1].distance)
        .forEach(([id, clientData]) => {
            leaderboard.innerHTML += `<p>${id}: ${Math.round(clientData.distance)}px</p>`;
        });
}