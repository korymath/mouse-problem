from flask import Flask
from flask import render_template
from flask import request
from flask_socketio import SocketIO
from flask_socketio import emit

from math import sqrt


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

cursor_positions = {}
distances = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('move_cursor')
def handle_cursor_move(data):
    id = data['id']
    new_position = {'x': data['x'], 'y': data['y']}

    # Calculate distance traveled
    if id in cursor_positions:
        old_position = cursor_positions[id]
        distance = sqrt((new_position['x'] - old_position['x'])**2 + (new_position['y'] - old_position['y'])**2)
        distances[id] = distances.get(id, 0) + distance

    cursor_positions[id] = new_position
    emit('update_cursors', {'positions': cursor_positions, 'distances': distances}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    # Assuming you have a way to get the client's unique ID on disconnect
    # You need to identify which client has disconnected
    client_id = request.sid
    if client_id in cursor_positions:
        del cursor_positions[client_id]
        del distances[client_id]
        emit('update_cursors', {'positions': cursor_positions, 'distances': distances}, broadcast=True)



if __name__ == '__main__':
    socketio.run(app, debug=True)
