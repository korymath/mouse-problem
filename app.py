import eventlet

eventlet.monkey_patch()

import time
import threading

from flask import Flask
from flask import render_template
from flask import request
from flask_socketio import SocketIO


# Set up the Flask app and SocketIO
app = Flask(__name__)
app.config["SECRET_KEY"] = "i-am-really-secret"
socketio = SocketIO(app)


# Using a class as a singleton to keep track of the cursor positions
class CursorGameManager:
    """Class to keep track of the cursor positions."""

    def __init__(self):
        self.lock = eventlet.semaphore.Semaphore()
        self.active_clients = {}
        self.last_update_time = 0

    def update_client(self, cursor_id, position, total_distance):
        """Add a cursor position to the active clients dictionary."""
        with self.lock:
            if cursor_id not in self.active_clients:
                print(f"client {cursor_id} connected")
                self.active_clients[cursor_id] = {}
                self.active_clients[cursor_id]["position"] = position
                self.active_clients[cursor_id]["distance"] = 0

            else:
                # Add the cursor position to the dictionary
                self.active_clients[cursor_id]["position"] = position

                # Add distance to the active clients dictionary
                self.active_clients[cursor_id]["distance"] = total_distance

                # keep track of the last time a cursor was moved
                # TODO(korymath): this should likely be per client
                # as opposed to shared and global
                self.last_update_time = time.time()

    def remove_position(self, cursor_id):
        """Remove a cursor position from the active clients dictionary."""
        with self.lock:
            self.active_clients.pop(cursor_id, None)
            print(f"client {cursor_id} disconnected")

            # If there are active_clients to broadcast, then emit the event
            if self.active_clients:
                # Broadcast the updated active_clients to everyone
                socketio.emit("client_disconnect", self.active_clients)

    def get_active_clients(self):
        """Return the active clients dictionary."""
        with self.lock:
            print(f"self.active_clients: {self.active_clients}")
            return dict(self.active_clients)


game_manager = CursorGameManager()


def broadcast_positions():
    """Broadcast cursor positions to clients with debouncing and throttling."""

    # Debounce interval in seconds
    debounce_interval = 0.05

    while True:
        eventlet.sleep(debounce_interval)

        # If the last update time is within the debounce interval
        # then skip this update
        current_time = time.time()
        if current_time - game_manager.last_update_time > debounce_interval:
            continue

        # Get the active clients
        try:
            active_clients = game_manager.get_active_clients()
        except Exception as e:
            print(f"Error getting active_clients: {e}")
            active_clients = None

        # If there are active_clients to broadcast, then emit the event
        if active_clients:
            socketio.emit("batch_update", active_clients)


@app.route("/")
def index():
    """Return the index page."""
    return render_template("index.html")


@socketio.on("move_cursor")
def handle_cursor_move(data):
    """Handle cursor move event by handling client update."""
    game_manager.update_client(
        request.sid, {"x": data["x"], "y": data["y"]}, data["totalDistance"]
    )


@socketio.on("disconnect")
def handle_disconnect():
    """Handle disconnect event."""

    # Remove the client from active clients dictionary
    game_manager.remove_position(request.sid)

    # If there are active_clients to broadcast, then emit the event
    active_clients = game_manager.get_active_clients()
    if active_clients:
        socketio.emit("batch_update", active_clients)


if __name__ == "__main__":
    threading.Thread(target=broadcast_positions, daemon=True).start()
    socketio.run(app, debug=True, port=2121)
