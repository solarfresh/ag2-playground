"""
Dashboard client utility for broadcasting agent activities to the monitoring dashboard.
"""

import socketio
import sys
import os
from typing import Optional

# Add parent directories to path to import configs
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from configs.settings import settings
from configs.logging_config import setup_logging

logger = setup_logging(name='[DashboardClient]')


class DashboardClient:
    """Client for sending agent activities to the dashboard via Socket.IO"""
    
    def __init__(self):
        self.sio: Optional[socketio.Client] = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to the Socket.IO server"""
        try:
            if self.sio is None:
                self.sio = socketio.Client()
                self.setup_events()
            
            if not self.connected:
                self.sio.connect(f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}")
                self.connected = True
                logger.info("Connected to dashboard server")
                return True
        except Exception as e:
            logger.error(f"Failed to connect to dashboard server: {e}")
            self.connected = False
            return False
        
        return self.connected
    
    def setup_events(self):
        """Setup Socket.IO event handlers"""
        if self.sio is None:
            return
            
        @self.sio.event
        def connect():
            self.connected = True
            logger.info("Socket.IO connection established")
        
        @self.sio.event
        def disconnect():
            self.connected = False
            logger.info("Socket.IO connection lost")
    
    def broadcast_activity(self, agent_name: str, activity: str, activity_type: str = "info"):
        """
        Broadcast an agent activity to the dashboard
        
        Args:
            agent_name: Name of the agent
            activity: Description of the activity
            activity_type: Type of activity (info, success, error, warning, attack, evaluation)
        """
        if not self.connected:
            if not self.connect():
                return
        
        try:
            data = {
                "agent": agent_name,
                "activity": activity,
                "type": activity_type
            }
            
            if self.sio and self.connected:
                self.sio.emit('agent_activity', data)
                logger.debug(f"Broadcasted activity: {agent_name} - {activity}")
        except Exception as e:
            logger.error(f"Failed to broadcast activity: {e}")
            self.connected = False
    
    def disconnect(self):
        """Disconnect from the Socket.IO server"""
        if self.sio and self.connected:
            self.sio.disconnect()
            self.connected = False
            logger.info("Disconnected from dashboard server")


# Global dashboard client instance
dashboard_client = DashboardClient()


def broadcast_agent_activity(agent_name: str, activity: str, activity_type: str = "info"):
    """
    Convenience function to broadcast agent activity
    
    Args:
        agent_name: Name of the agent
        activity: Description of the activity  
        activity_type: Type of activity (info, success, error, warning, attack, evaluation)
    """
    dashboard_client.broadcast_activity(agent_name, activity, activity_type)