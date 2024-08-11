from flask import Flask, render_template, request, session, make_response, send_from_directory, Response
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_session import Session
from datetime import timedelta
from redis import Redis
import time
import threading
import os
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
app.config['SESSION_TYPE'] = 'redis' 
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = Redis(host='redis', port=6379)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
Session(app)

socketio = SocketIO(app)

# Directory to store code files
CODE_DIR = 'room_code_files'
os.makedirs(CODE_DIR, exist_ok=True)

# A dictionary to store room creation times
room_creation_times = {}

@app.route('/')
def index():
    return render_template('landing.html')
    #return "Welcome to CodeShare! Use a specific room by visiting /room/<room_name>."

@app.route('/<room_name>')
def room(room_name):
    session.permanent = True
    session['room'] = room_name
    if room_name not in room_creation_times:
        room_creation_times[room_name] = time.time()
        file_path = os.path.join(CODE_DIR, f"{room_name}.txt")
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write("")
    response = make_response(render_template('room.html', room_name=room_name))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/static/<path:filename>')
def static_files(filename):
    response = send_from_directory('static', filename)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@socketio.on('join')
def on_join():
    room = session.get('room')
    join_room(room)
    emit('code_update', read_code_from_file(room), room=room)

@socketio.on('code_update')
def handle_code_update(data):
    room = session.get('room')
    save_code_to_file(room, data)
    emit('code_update', data, room=room)

@socketio.on('leave')
def on_leave():
    room = session.get('room')
    leave_room(room)
    print(f"Client left room {room}")

@socketio.on('disconnect')
def handle_disconnect():
    room = session.get('room')
    print(f"Client disconnected from room {room}")

def save_code_to_file(room, code):
    file_path = os.path.join(CODE_DIR, f"{room}.txt")
    with open(file_path, 'w') as f:
        f.write(code)
    room_creation_times[room] = time.time()

def read_code_from_file(room):
    file_path = os.path.join(CODE_DIR, f"{room}.txt")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return f.read()
    return ''

def cleanup_files():
    while True:
        time.sleep(60 * 10)
        current_time = time.time()
        for room, creation_time in list(room_creation_times.items()):
            if current_time - creation_time > 3 * 3600:
                file_path = os.path.join(CODE_DIR, f"{room}.txt")
                if os.path.exists(file_path):
                    os.remove(file_path)
                del room_creation_times[room]

if __name__ == '__main__':
    # Start the cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_files, daemon=True)
    cleanup_thread.start()
    
    # Log errors to stderr in production
    logging.basicConfig(level=logging.INFO)

    # No need to run with Flask's built-in server; Gunicorn will handle it.
