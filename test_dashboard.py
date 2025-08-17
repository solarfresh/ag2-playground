#!/usr/bin/env python3
"""
Test script to demonstrate the dashboard functionality.
This script sends mock agent activities to the server.
"""

import socketio
import time
import random
import sys
import os

# Add current directory to path to import configs
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from configs.settings import settings

def test_dashboard():
    """Send test messages to demonstrate dashboard functionality"""
    
    # Create a Socket.IO client with proper configuration
    sio = socketio.Client(
        logger=True,
        engineio_logger=True
    )
    
    # Test activities to send
    test_activities = [
        {"agent": "PromptGenerator", "activity": "Prompt generating...", "type": "info"},
        {"agent": "PromptGenerator", "activity": "Attack prompt created", "type": "attack"},
        {"agent": "GourmetAgent", "activity": "Processing attack prompt...", "type": "info"},
        {"agent": "GourmetAgent", "activity": "Response generated", "type": "info"},
        {"agent": "EvaluatorAgent", "activity": "Evaluating response...", "type": "info"},
        {"agent": "EvaluatorAgent", "activity": "Evaluation result: Attack successful", "type": "evaluation"},
        {"agent": "EvaluatorAgent", "activity": "Evaluation result: Attack failed", "type": "warning"},
        {"agent": "IntrospectionAgent", "activity": "Learning from evaluation...", "type": "info"},
        {"agent": "IntrospectionAgent", "activity": "Strategy updated", "type": "success"},
        {"agent": "PlannerAgent", "activity": "Planning next action...", "type": "info"},
        {"agent": "PlannerAgent", "activity": "Next speaker: PromptGenerator", "type": "info"},
    ]
    
    @sio.event
    def connect():
        print("Connected to server")
    
    @sio.event
    def disconnect():
        print("Disconnected from server")
    
    try:
        # Connect to server
        server_url = f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}"
        print(f"Connecting to server at {server_url}")
        
        # Try to connect with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                sio.connect(server_url, wait_timeout=10)
                print("✅ Connected successfully!")
                break
            except Exception as e:
                print(f"❌ Connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    print("Failed to connect after all retries. Make sure the server is running:")
                    print("cd server && python server.py")
                    return
                time.sleep(2)
        
        print("Starting to send test activities...")
        print("Open the dashboard at: http://localhost:8501")
        print("Press Ctrl+C to stop")
        
        # Send test activities in a loop
        while True:
            activity = random.choice(test_activities)
            print(f"Sending: {activity['agent']} - {activity['activity']}")
            sio.emit('agent_activity', activity)
            time.sleep(random.uniform(2, 5))  # Random delay between 2-5 seconds
            
    except KeyboardInterrupt:
        print("\nStopping test...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    test_dashboard()