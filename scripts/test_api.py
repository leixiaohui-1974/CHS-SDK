import requests
import json
import time
import websocket
import threading

# Define the server URL
BASE_URL = "http://127.0.0.1:8000"

def load_example_config(example_path):
    """Loads a simulation config from the examples directory."""
    try:
        print(f"Loading example: {example_path}")
        response = requests.get(f"{BASE_URL}/api/examples/{example_path}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error loading example config: {e}")
        return None

def create_simulation(config):
    """Creates a simulation session."""
    try:
        print("Creating simulation session with config:")
        print(json.dumps(config, indent=2))
        response = requests.post(f"{BASE_URL}/api/simulations", json=config)
        response.raise_for_status()
        session_id = response.json()["session_id"]
        print(f"Simulation created with session_id: {session_id}")
        return session_id
    except requests.exceptions.RequestException as e:
        print(f"Error creating simulation: {e}")
        if response:
            print(f"Error details: {response.text}")
        return None

def start_simulation(session_id):
    """Starts the simulation."""
    try:
        print(f"Starting simulation {session_id}...")
        response = requests.post(f"{BASE_URL}/api/simulations/{session_id}/start")
        response.raise_for_status()
        print("Simulation started.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error starting simulation: {e}")
        return False

def pause_simulation(session_id):
    """Pauses the simulation."""
    try:
        print(f"Pausing simulation {session_id}...")
        response = requests.post(f"{BASE_URL}/api/simulations/{session_id}/pause")
        response.raise_for_status()
        print("Simulation paused.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error pausing simulation: {e}")
        return False

def resume_simulation(session_id):
    """Resumes the simulation."""
    try:
        print(f"Resuming simulation {session_id}...")
        response = requests.post(f"{BASE_URL}/api/simulations/{session_id}/resume")
        response.raise_for_status()
        print("Simulation resumed.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error resuming simulation: {e}")
        return False

def stop_simulation(session_id):
    """Stops the simulation."""
    try:
        print(f"Stopping simulation {session_id}...")
        response = requests.post(f"{BASE_URL}/api/simulations/{session_id}/stop")
        response.raise_for_status()
        print("Simulation stopped.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error stopping simulation: {e}")
        return False

def on_message(ws, message):
    print(f"WS Message: {message}")

def on_error(ws, error):
    print(f"WS Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WS Closed")

def on_open(ws):
    print("WS Opened")

def run_websocket(session_id):
    ws_url = f"ws://127.0.0.1:8000/ws/simulations/{session_id}"
    ws = websocket.WebSocketApp(ws_url,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    ws.run_forever()


if __name__ == "__main__":
    # 1. Load example config
    example_path = "watertank_refactored/01_simple_simulation"
    config = load_example_config(example_path)
    if not config:
        exit(1)

    # 2. Create simulation
    session_id = create_simulation(config)
    if not session_id:
        exit(1)

    # 3. Start WebSocket listener in a separate thread
    ws_thread = threading.Thread(target=run_websocket, args=(session_id,))
    ws_thread.daemon = True
    ws_thread.start()
    time.sleep(2) # Give websocket time to connect

    # 4. Start simulation
    if not start_simulation(session_id):
        exit(1)
    time.sleep(2)

    # 5. Pause simulation
    if not pause_simulation(session_id):
        exit(1)
    time.sleep(2)

    # 6. Resume simulation
    if not resume_simulation(session_id):
        exit(1)
    time.sleep(2)

    # 7. Stop simulation
    if not stop_simulation(session_id):
        exit(1)

    print("Test finished successfully!")
    # Allow some time for final messages to be received
    time.sleep(2)
    # The websocket thread is a daemon, so it will exit when the main thread exits.
