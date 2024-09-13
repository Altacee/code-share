from flask import Flask, render_template, session, make_response, send_from_directory, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_session import Session
from datetime import timedelta
from redis import Redis
import time
import threading
import os
import re
import requests

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'default_secret_key'),
    SESSION_TYPE='redis',
    SESSION_PERMANENT=False,
    SESSION_USE_SIGNER=True,
    SESSION_REDIS=Redis(host='redis', port=6379),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
)
Session(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', ping_interval=25, ping_timeout=60, transports=['websocket', 'polling'])
CODE_DIR = 'room_code_files'
os.makedirs(CODE_DIR, exist_ok=True)
room_creation_times = {}

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/<room_name>')
def room(room_name):
    session.permanent = True
    session['room'] = room_name
    room_creation_times.setdefault(room_name, time.time())
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

@app.route('/suggest_code', methods=['POST'])
def suggest_code():
    prompt = request.json.get('prompt')
    if not prompt:
        return jsonify({"success": False, "error": "No prompt provided"}), 400

    api_url = 'http://100.82.48.118:5005/get_code'
    try:
        response = requests.post(api_url, json={"prompt": prompt})
        response_data = response.json()

        if response.status_code == 200 and response_data.get("success"):
            suggested_code = response_data["result"]["response"]

            # Use regex to remove markdown code block formatting
            suggested_code = re.sub(r'```[a-z]*\n|\n```', '', suggested_code)

            return jsonify({"success": True, "suggested_code": suggested_code})
        else:
            return jsonify({"success": False, "error": response_data.get("errors", "Failed to get code suggestions")}), 500

    except requests.RequestException as e:
        return jsonify({"success": False, "error": str(e)}), 500

@socketio.on('disconnect')
def handle_disconnect():
    pass  # Optional: Add any specific disconnect handling logic here

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
        time.sleep(600)
        current_time = time.time()
        for room, creation_time in list(room_creation_times.items()):
            if current_time - creation_time > 10800:
                file_path = os.path.join(CODE_DIR, f"{room}.txt")
                if os.path.exists(file_path):
                    os.remove(file_path)
                del room_creation_times[room]

if __name__ == '__main__':
    threading.Thread(target=cleanup_files, daemon=True).start()
    socketio.run(app)
