import os
import subprocess
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from colorama import Fore, Style, init

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Initialize Colorama
init(autoreset=True)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Container Terminal</title>
    </head>
    <body>
        <h1>Docker Container Terminal</h1>
        <textarea id="terminal" rows="20" cols="80" readonly></textarea><br>
        <input id="command" type="text" placeholder="Enter command">
        <button onclick="sendCommand()">Run</button>
        <script>
            const socket = io();
            const terminal = document.getElementById('terminal');
            const commandInput = document.getElementById('command');

            socket.on('output', (data) => {
                terminal.value += data + '\\n';
                terminal.scrollTop = terminal.scrollHeight;
            });

            function sendCommand() {
                const command = commandInput.value;
                socket.emit('command', command);
                commandInput.value = '';
            }
        </script>
        <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    </body>
    </html>
    '''

@socketio.on('command')
def handle_command(command):
    try:
        # Execute the command inside the container
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        emit('output', output)
    except subprocess.CalledProcessError as e:
        emit('output', f"Error: {e.output}")
    except Exception as e:
        emit('output', f"Unexpected Error: {str(e)}")

if __name__ == '__main__':
    # Run the Flask app
    socketio.run(app, host='0.0.0.0', port=8080)