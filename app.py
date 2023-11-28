from flask import Flask
from flask import render_template
from flask import request
from flask_socketio import SocketIO
from flask_socketio import emit


app = Flask(__name__)
app.config["SECRET_KEY"] = "i-am-really-secret"
socketio = SocketIO(app)


# Keep track of the cursor positions and distances traveled
active_clients = {}


@app.route("/")
def index():
    """Return the index page."""
    return render_template("index.html")


@socketio.on("move_cursor")
def handle_cursor_move(data):
    """Handle cursor move event."""

    # Get the client id and new position
    client_id = request.sid
    position = {"x": data["x"], "y": data["y"]}

    # print(f'cursor {client_id} moved to {position["x"]}, {position["y"]}')
    # print(f'active_clients: {active_clients}')

    # If the client already exists in the active clients, then update the entry
    if client_id in active_clients:
        
        # If the client has a previous position, calculate the distance
        old_position = active_clients[client_id]['position']

        # Calculate the distance traveled as a delta from the previous position
        delta = (
            abs((position["x"] - old_position["x"]))
            + abs((position["y"] - old_position["y"]))
        )

        # If the client had a previous distance, add the new distance
        active_clients[client_id]['distance'] = active_clients[client_id]['distance'] + delta
    
        # Update the cursor position
        active_clients[client_id]['position'] = position

    else:
        # Add the client to the active clients
        active_clients[client_id] = {
            "position": position,
            "distance": 0,
        }

    # Broadcast the updated cursor positions and distances
    emit(
        "update_cursors",
        {"active_clients": active_clients},
        broadcast=True,
    )


@socketio.on("disconnect")
def handle_disconnect():
    """Handle disconnect event."""

    # Get the client id
    client_id = request.sid
    print(f'client {client_id} disconnected')

    # Remove the client from active clients dictionary
    if client_id in active_clients:
        del active_clients[client_id]

    # Broadcast the updated cursor positions and distances
    emit(
        "update_cursors",
        {"active_clients": active_clients},
        broadcast=True,
    )


if __name__ == "__main__":
    socketio.run(app, debug=True)
