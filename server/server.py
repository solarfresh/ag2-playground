import eventlet
import eventlet.wsgi
import socketio
import sys
import os

# Add parent directory to path to import configs
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from configs.settings import settings
from configs.logging_config import setup_logging

# --- Logger Configuration ---
# Set up the logger using the centralized config function
logger = setup_logging(name='[server]')

# --- Socket.IO Server ---

# Create a Socket.IO server instance
sio = socketio.Server(
    async_mode='eventlet',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Create a WSGI application
app = socketio.WSGIApp(sio, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})

# Define event handlers
@sio.event
def connect(sid, environ):
    """
    Handles a new client connection.
    `sid` is the unique session ID for the client.
    `environ` contains connection details.
    """
    print(f"Client connected: {sid}")

@sio.event
def disconnect(sid):
    """
    Handles a client disconnection.
    """
    print(f"Client disconnected: {sid}")

@sio.event
def message(sid, data):
    """
    Handles an incoming 'message' event from a client.
    `sid` is the session ID.
    `data` is the message content.
    """
    print(f"Received message from {sid}: {data}")
    # Here you can add logic to route the message to other agents
    sio.emit('response', f"Server received your message: {data}", room=sid)

@sio.event
def response_event(sid, data):
    """
    Handles response events from clients.
    """
    print(f"Received response_event from {sid} with data: {data}")
    sio.emit('response', f"Server received your message: {data}", room=sid)

@sio.event
def agent_activity(sid, data):
    """
    Handles agent activity messages and broadcasts them to all connected clients.
    Expected data format:
    {
        "agent": "PromptGenerator",
        "activity": "提示生成中...",
        "type": "info"
    }
    """
    print(f"Received agent activity from {sid}: {data}")
    # Broadcast to all connected clients
    sio.emit('agent_activity', data)

def broadcast_agent_activity(agent_name: str, activity: str, activity_type: str = "info"):
    """
    Helper function to broadcast agent activity to all connected clients.
    This can be called from other parts of the system.
    """
    data = {
        "agent": agent_name,
        "activity": activity,
        "type": activity_type
    }
    sio.emit('agent_activity', data)
    print(f"Broadcasting agent activity: {agent_name} - {activity}")

def run_server():
    """
    Runs the Socket.IO server.
    """
    print("Starting Socket.IO server on localhost:5000")
    # Wrap the app in Eventlet's WSGI server
    eventlet.wsgi.server(
        eventlet.listen((settings.SERVER_HOST, settings.SERVER_PORT)), app)

if __name__ == '__main__':
    run_server()