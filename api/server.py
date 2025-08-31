"""
Main FastAPI application for the CHS-SDK Simulation API.

This server provides an endpoint to run hydraulic simulations based on
a JSON configuration that conforms to the Pydantic models defined
in `core_lib.models`.
"""
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Configure logging for the application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import the main Pydantic model for the request body and the simulation builder
from core_lib.models.api_models import SimulationRequest, ComponentsModel, TopologyModel, AgentsModel
from core_lib.io.api_loader import SimulationBuilderFromModels

# Initialize the FastAPI app
app = FastAPI(
    title="CHS-SDK Simulation API",
    description="An API for running hydraulic simulations using the CHS-SDK.",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests from the frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXAMPLES_DIR = Path("examples")

def find_example_dirs(base_dir: Path) -> List[str]:
    """Recursively finds directories containing 'components.yml' and returns their relative paths."""
    example_dirs = []
    for entry in base_dir.rglob('components.yml'):
        if entry.is_file():
            # Represent the path as a string with forward slashes for consistency
            example_dir = entry.parent.relative_to(base_dir).as_posix()
            example_dirs.append(example_dir)
    return sorted(example_dirs)

@app.get("/api/examples", tags=["Examples"], response_model=List[str])
async def list_examples():
    """Returns a list of available example scenario paths."""
    if not EXAMPLES_DIR.is_dir():
        raise HTTPException(status_code=404, detail="Examples directory not found.")
    try:
        return find_example_dirs(EXAMPLES_DIR)
    except Exception as e:
        logging.error(f"Error scanning examples directory: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan examples directory.")

import json

@app.get("/api/examples/{example_path:path}", tags=["Examples"], response_model=Dict[str, Any])
async def get_example_config(example_path: str):
    """
    Loads a pre-processed example configuration from a generated JSON file.
    """
    # Basic security check
    if ".." in example_path:
        raise HTTPException(status_code=400, detail="Invalid example path.")

    # Construct the path to the pre-generated JSON file
    json_filename = example_path.replace('/', '_') + '.json'
    json_filepath = EXAMPLES_DIR / "generated_json" / json_filename

    if not json_filepath.is_file():
        logging.error(f"Pre-processed JSON file not found: {json_filepath}")
        raise HTTPException(status_code=404, detail=f"Example configuration '{example_path}' not found. Have you run the preprocessing script?")

    try:
        with open(json_filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load or parse JSON file {json_filepath}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load example configuration.")

import uuid
import asyncio
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_json(self, session_id: str, data: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(data)

manager = ConnectionManager()

# In-memory storage for simulation sessions
simulation_sessions: Dict[str, Any] = {}

async def run_simulation_step_by_step(session_id: str, harness: Any):
    """
    Runs the simulation step-by-step and sends data over WebSocket.
    Handles start, pause, and resume.
    """
    # Find the first reservoir to report on. This is a simplification for the demo.
    from core_lib.physical_objects.reservoir import Reservoir
    first_reservoir_id = None
    for comp_id, comp in harness.components.items():
        if isinstance(comp, Reservoir):
            first_reservoir_id = comp_id
            break

    try:
        while harness.is_running and not simulation_sessions.get(session_id, {}).get("stop_flag", False):
            # If pause is activated, wait until it's cleared.
            if harness._is_paused.is_set():
                await manager.send_json(session_id, {"type": "status", "payload": "Simulation paused."})
                # Use asyncio.sleep for non-blocking wait
                while harness._is_paused.is_set():
                    await asyncio.sleep(0.2)
                await manager.send_json(session_id, {"type": "status", "payload": "Simulation resumed."})

            harness.step()

            # Send data point over WebSocket
            if first_reservoir_id:
                try:
                    state = harness.components[first_reservoir_id].get_state()
                    water_level = state.get('water_level', 0)
                    data_to_send = {
                        "timestamp": harness.t,
                        "id": first_reservoir_id,
                        "water_level": water_level
                    }
                    await manager.send_json(session_id, {"type": "data", "payload": data_to_send})
                except KeyError:
                    logging.warning(f"Component {first_reservoir_id} not found in current step.")
                except Exception as e:
                    logging.error(f"Error getting state for {first_reservoir_id}: {e}")


            if not harness.is_running:
                logging.info(f"Simulation {session_id} reached end time or was stopped.")
                break

            await asyncio.sleep(0.1)  # Control simulation speed

        await manager.send_json(session_id, {"type": "status", "payload": "Simulation finished."})
    except Exception as e:
        logging.error(f"Error during simulation for session {session_id}: {e}", exc_info=True)
        await manager.send_json(session_id, {"type": "error", "payload": str(e)})
    finally:
        logging.info(f"Cleaning up session {session_id}")
        manager.disconnect(session_id)
        if session_id in simulation_sessions:
            del simulation_sessions[session_id]


@app.get("/api/status", tags=["Status"])
async def read_root():
    """A simple health check endpoint to confirm the API is running."""
    return {"status": "ok", "message": "CHS-SDK Simulation API is running."}

@app.post("/api/simulations", tags=["Simulation"], status_code=201)
async def create_simulation_session(request: SimulationRequest):
    """Creates a new simulation session and returns the session ID."""
    session_id = str(uuid.uuid4())
    default_sim_config = {"start_time": 0, "end_time": 86400, "dt": 3600}

    try:
        logging.info("Building simulation from request...")
        builder = SimulationBuilderFromModels(request_data=request, sim_config=default_sim_config)
        harness = builder.build()
        simulation_sessions[session_id] = {"harness": harness, "stop_flag": False}
        logging.info(f"Created simulation session: {session_id}")
        return {"session_id": session_id}
    except Exception as e:
        logging.error(f"Failed to create simulation session: {e}", exc_info=True)
        raise HTTPException(status_code=422, detail=str(e))

@app.post("/api/simulations/{session_id}/start", tags=["Simulation"], status_code=202)
async def start_simulation(session_id: str):
    """Starts the simulation for a given session ID."""
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="Simulation session not found.")

    harness = simulation_sessions[session_id]["harness"]
    asyncio.create_task(run_simulation_step_by_step(session_id, harness))
    logging.info(f"Started simulation for session: {session_id}")
    return {"message": "Simulation started."}

@app.post("/api/simulations/{session_id}/stop", tags=["Simulation"], status_code=200)
async def stop_simulation(session_id: str):
    """Stops the simulation for a given session ID."""
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="Simulation session not found.")

    simulation_sessions[session_id]["stop_flag"] = True
    logging.info(f"Stopping simulation for session: {session_id}")
    return {"message": "Simulation stopping."}


@app.post("/api/simulations/{session_id}/pause", tags=["Simulation"], status_code=204)
async def pause_simulation(session_id: str):
    """Pauses the simulation for a given session ID."""
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="Simulation session not found.")

    harness = simulation_sessions[session_id]["harness"]
    if harness._is_paused.is_set():
        raise HTTPException(status_code=409, detail="Simulation is already paused.")

    harness.pause()
    return


@app.post("/api/simulations/{session_id}/resume", tags=["Simulation"], status_code=204)
async def resume_simulation(session_id: str):
    """Resumes the simulation for a given session ID."""
    if session_id not in simulation_sessions:
        raise HTTPException(status_code=404, detail="Simulation session not found.")

    harness = simulation_sessions[session_id]["harness"]
    if not harness._is_paused.is_set():
        raise HTTPException(status_code=409, detail="Simulation is not paused.")

    harness.resume()
    return


@app.websocket("/ws/simulations/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    if session_id not in simulation_sessions:
        await websocket.close(code=1008)
        return

    await manager.connect(session_id, websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        # Also stop the simulation if the client disconnects
        if session_id in simulation_sessions:
            simulation_sessions[session_id]["stop_flag"] = True
        logging.info(f"WebSocket disconnected for session: {session_id}")
