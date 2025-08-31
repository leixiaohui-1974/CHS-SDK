import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Adjust the path to import the app from the parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.server import app

# Create a TestClient instance
client = TestClient(app)

# Define the path to the generated examples for use in tests
EXAMPLES_JSON_DIR = Path(__file__).parent.parent / "examples" / "generated_json"
KNOWN_EXAMPLE_PATH = "agent_based/06_centralized_emergency_override"
KNOWN_EXAMPLE_JSON_FILENAME = "agent_based_06_centralized_emergency_override.json"

def test_read_status():
    """Tests the health check endpoint."""
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "CHS-SDK Simulation API is running."}

def test_list_examples():
    """Tests the endpoint for listing available example scenarios."""
    response = client.get("/api/examples")
    assert response.status_code == 200

    examples_list = response.json()
    assert isinstance(examples_list, list)
    assert KNOWN_EXAMPLE_PATH in examples_list

def test_get_valid_example_config():
    """Tests fetching a valid, pre-processed example configuration."""
    response = client.get(f"/api/examples/{KNOWN_EXAMPLE_PATH}")
    assert response.status_code == 200

    config = response.json()
    assert "components" in config
    assert "topology" in config
    assert "agents" in config
    assert "reservoirs" in config["components"]
    assert len(config["components"]["reservoirs"]) > 0

def test_get_invalid_example_config():
    """Tests fetching a non-existent example configuration, expecting a 404."""
    response = client.get("/api/examples/this/path/does/not/exist")
    assert response.status_code == 404

def test_get_example_config_path_traversal():
    """Tests for path traversal attempts."""
    response = client.get("/api/examples/../..")
    # A 404 is a reasonable response for a path that doesn't resolve to a valid resource
    # after normalization. The main goal is to ensure it doesn't lead to a 200 OK on an
    # unexpected resource.
    assert response.status_code == 404

@pytest.fixture(scope="module")
def simulation_request_body():
    """
    A pytest fixture to load a valid simulation request body from a generated JSON file.
    It also injects any necessary parameters required by tests that may be missing
    from the base example file.
    """
    json_path = EXAMPLES_JSON_DIR / KNOWN_EXAMPLE_JSON_FILENAME
    with open(json_path, 'r') as f:
        data = json.load(f)

    # FIX: The CentralDispatcherAgent in this example requires 'mode' and
    # 'emergency_flood_level' parameters to be explicitly set. We inject them
    # here to make the test data valid as the source YAML is outdated.
    for agent_config in data.get("agents", {}).get("agents", []):
        if agent_config.get("id") == "central_dispatcher":
            if "params" not in agent_config:
                agent_config["params"] = {}
            agent_config["params"]["mode"] = "emergency"
            # The agent's __init__ now requires this parameter for emergency mode.
            agent_config["params"]["emergency_flood_level"] = 100.0
            break

    return data

def test_create_simulation_session(simulation_request_body):
    """Tests the creation of a new simulation session."""
    response = client.post("/api/simulations", json=simulation_request_body)
    assert response.status_code == 201

    data = response.json()
    assert "session_id" in data
    assert isinstance(data["session_id"], str)

def test_create_simulation_with_invalid_body():
    """Tests creating a simulation with a malformed request body."""
    invalid_body = {"components": "not_a_valid_model"}
    response = client.post("/api/simulations", json=invalid_body)
    assert response.status_code == 422  # Unprocessable Entity

def test_pause_resume_workflow(simulation_request_body):
    """
    Tests the full pause/resume workflow for a simulation session.
    """
    # 1. Create a simulation session
    create_response = client.post("/api/simulations", json=simulation_request_body)
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]

    # 2. Pause the simulation (it's not running yet, but should still be pausable)
    pause_response_1 = client.post(f"/api/simulations/{session_id}/pause")
    assert pause_response_1.status_code == 204

    # 3. Pausing again should fail
    pause_response_2 = client.post(f"/api/simulations/{session_id}/pause")
    assert pause_response_2.status_code == 409  # Conflict - already paused
    assert "already paused" in pause_response_2.json()["detail"]

    # 4. Resume the simulation
    resume_response_1 = client.post(f"/api/simulations/{session_id}/resume")
    assert resume_response_1.status_code == 204

    # 5. Resuming again should fail
    resume_response_2 = client.post(f"/api/simulations/{session_id}/resume")
    assert resume_response_2.status_code == 409 # Conflict - not paused
    assert "not paused" in resume_response_2.json()["detail"]

def test_workflow_for_non_existent_session():
    """Tests that pause/resume/stop endpoints return 404 for a bad session ID."""
    bad_session_id = "this-session-does-not-exist"

    pause_response = client.post(f"/api/simulations/{bad_session_id}/pause")
    assert pause_response.status_code == 404

    resume_response = client.post(f"/api/simulations/{bad_session_id}/resume")
    assert resume_response.status_code == 404

    stop_response = client.post(f"/api/simulations/{bad_session_id}/stop")
    assert stop_response.status_code == 404
