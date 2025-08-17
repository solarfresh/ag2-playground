import streamlit as st
import socketio
import time
from datetime import datetime
import sys
import os

# Add parent directory to path to import configs
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from configs.settings import settings

# Page configuration
st.set_page_config(
    page_title="TwinRAD Dashboard",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "connected" not in st.session_state:
    st.session_state.connected = False
if "client_socket" not in st.session_state:
    st.session_state.client_socket = None

class StreamlitSocketIOClient:
    def __init__(self):
        self.sio = socketio.Client(
            logger=False,  # Disable logging for cleaner Streamlit output
            engineio_logger=False
        )
        self.setup_events()
    
    def setup_events(self):
        @self.sio.event
        def connect():
            # Don't modify session state from background thread
            print("Socket.IO connected to server")
        
        @self.sio.event
        def disconnect():
            # Don't modify session state from background thread
            print("Socket.IO disconnected from server")
        
        @self.sio.event
        def agent_activity(data):
            """Handle agent activity broadcasts from server"""
            # Store in a thread-safe way - we'll check this in the main thread
            agent_name = data.get("agent", "Unknown")
            activity = data.get("activity", "")
            message_type = data.get("type", "info")
            
            # Store message in a thread-safe buffer
            if not hasattr(self, '_message_buffer'):
                self._message_buffer = []
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            new_message = {
                "timestamp": timestamp,
                "agent": agent_name,
                "message": activity,
                "type": message_type
            }
            self._message_buffer.append(new_message)
            print(f"Received activity: {agent_name} - {activity}")
        
        @self.sio.event
        def response(data):
            """Handle general responses from server"""
            if not hasattr(self, '_message_buffer'):
                self._message_buffer = []
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            new_message = {
                "timestamp": timestamp,
                "agent": "Server",
                "message": str(data),
                "type": "info"
            }
            self._message_buffer.append(new_message)
            print(f"Received server response: {data}")
    
    def add_message(self, agent: str, message: str, msg_type: str = "info"):
        """Add a message to the session state"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        new_message = {
            "timestamp": timestamp,
            "agent": agent,
            "message": message,
            "type": msg_type
        }
        st.session_state.messages.append(new_message)
        # Keep only last 100 messages to prevent memory issues
        if len(st.session_state.messages) > 100:
            st.session_state.messages = st.session_state.messages[-100:]
    
    def connect_to_server(self):
        """Connect to the Socket.IO server"""
        try:
            if not self.sio.connected:
                self.sio.connect(f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}")
                if self.sio.connected:
                    self.add_message("System", "Connected to TwinRAD server", "success")
                    return True
        except Exception as e:
            self.add_message("System", f"Connection failed: {str(e)}", "error")
            return False
        return self.sio.connected
    
    def get_new_messages(self):
        """Get new messages from the buffer and add them to session state"""
        if hasattr(self, '_message_buffer') and self._message_buffer:
            new_messages = self._message_buffer.copy()
            self._message_buffer.clear()
            
            for msg in new_messages:
                st.session_state.messages.append(msg)
                # Keep only last 100 messages to prevent memory issues
                if len(st.session_state.messages) > 100:
                    st.session_state.messages = st.session_state.messages[-100:]
    
    def disconnect_from_server(self):
        """Disconnect from the Socket.IO server"""
        if self.sio.connected:
            self.sio.disconnect()

def get_message_color(msg_type: str) -> str:
    """Get color for message type"""
    colors = {
        "success": "#28a745",
        "error": "#dc3545", 
        "warning": "#ffc107",
        "info": "#17a2b8",
        "attack": "#fd7e14",
        "evaluation": "#6f42c1"
    }
    return colors.get(msg_type, "#6c757d")

def main():
    # Header
    st.title("🔴 TwinRAD Real-time Monitoring Dashboard")
    st.markdown("---")
    
    # Initialize socket client
    if st.session_state.client_socket is None:
        st.session_state.client_socket = StreamlitSocketIOClient()
    
    # Process new messages from the buffer (thread-safe)
    st.session_state.client_socket.get_new_messages()
    
    # Update connection status
    if st.session_state.client_socket.sio.connected:
        st.session_state.connected = True
    else:
        st.session_state.connected = False
    
    # Sidebar
    with st.sidebar:
        st.header("Connection Status")
        
        # Connection status
        if st.session_state.connected:
            st.success("🟢 Connected")
        else:
            st.error("🔴 Disconnected")
        
        # Connection controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Connect", disabled=st.session_state.connected):
                if st.session_state.client_socket.connect_to_server():
                    st.rerun()
        
        with col2:
            if st.button("Disconnect", disabled=not st.session_state.connected):
                st.session_state.client_socket.disconnect_from_server()
                st.rerun()
        
        st.markdown("---")
        
        # Server settings
        st.subheader("Server Settings")
        st.text(f"Host: {settings.SERVER_HOST}")
        st.text(f"Port: {settings.SERVER_PORT}")
        
        st.markdown("---")
        
        # Clear messages
        if st.button("Clear Messages"):
            st.session_state.messages = []
            st.rerun()
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto Refresh", value=True)
        if auto_refresh:
            refresh_rate = st.slider("Refresh Rate (seconds)", 1, 10, 3)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Real-time Activity Log")
        
        # Messages container
        message_container = st.container()
        
        with message_container:
            if not st.session_state.messages:
                st.info("Waiting for messages from TwinRAD system...")
            else:
                # Display messages in reverse order (newest first)
                for msg in reversed(st.session_state.messages[-20:]):  # Show last 20 messages
                    color = get_message_color(msg["type"])
                    
                    # Create message card
                    st.markdown(f"""
                    <div style="
                        border-left: 4px solid {color};
                        padding: 10px;
                        margin: 5px 0;
                        background-color: rgba(128, 128, 128, 0.1);
                        border-radius: 5px;
                    ">
                        <div style="
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            margin-bottom: 5px;
                        ">
                            <strong style="color: {color};">{msg["agent"]}</strong>
                            <small style="color: #666;">{msg["timestamp"]}</small>
                        </div>
                        <div>{msg["message"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("System Statistics")
        
        # Message count by type
        if st.session_state.messages:
            msg_types = {}
            for msg in st.session_state.messages:
                msg_type = msg["type"]
                msg_types[msg_type] = msg_types.get(msg_type, 0) + 1
            
            for msg_type, count in msg_types.items():
                color = get_message_color(msg_type)
                st.markdown(f"""
                <div style="
                    padding: 5px 10px;
                    margin: 2px 0;
                    background-color: {color}20;
                    border-radius: 3px;
                    display: flex;
                    justify-content: space-between;
                ">
                    <span>{msg_type.title()}</span>
                    <strong>{count}</strong>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No statistics available")
        
        st.markdown("---")
        
        # Recent agents
        st.subheader("Active Agents")
        if st.session_state.messages:
            recent_agents = list(set([msg["agent"] for msg in st.session_state.messages[-10:]]))
            for agent in recent_agents:
                if agent != "System":
                    st.markdown(f"• {agent}")
        else:
            st.info("No agent activity")
    
    # Auto-refresh
    if auto_refresh and st.session_state.connected:
        time.sleep(refresh_rate)
        st.rerun()

if __name__ == "__main__":
    main()