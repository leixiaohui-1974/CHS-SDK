"""
Main FastAPI application for the CHS-SDK Simulation API.

This server provides an endpoint to run hydraulic simulations based on
a JSON configuration that conforms to the Pydantic models defined
in `core_lib.models`.
"""
import logging
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse

# Configure logging for the application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import the main Pydantic model for the request body and the simulation builder
from core_lib.models.api_models import SimulationRequest
from core_lib.io.api_loader import SimulationBuilderFromModels

# Initialize the FastAPI app
app = FastAPI(
    title="CHS-SDK Simulation API",
    description="An API for running hydraulic simulations using the CHS-SDK.",
    version="1.0.0"
)

@app.get("/", tags=["Status"])
async def read_root():
    """A simple health check endpoint to confirm the API is running."""
    return {"status": "ok", "message": "CHS-SDK Simulation API is running."}

@app.post("/run_simulation", tags=["Simulation"], response_model=dict)
async def run_simulation(request: SimulationRequest):
    """
    Runs a hydraulic simulation based on the provided configuration.

    The request body must conform to the `SimulationRequest` schema, which
    defines all the components, the topology, and the agents for the scenario.
    FastAPI will automatically validate the request body against this schema.
    """
    try:
        logging.info("Received new simulation request. Data has been validated by FastAPI.")

        # A global simulation config can be defined here. In a future version,
        # this could be part of the request model itself.
        default_sim_config = {
            "start_time": 0,
            "end_time": 86400,  # Default to 24 hours
            "dt": 3600         # Default to 1-hour steps
        }

        logging.info("Building simulation from request models...")
        # Use the new builder to create the simulation harness from Pydantic models
        builder = SimulationBuilderFromModels(request_data=request, sim_config=default_sim_config)
        harness = builder.build()

        logging.info("Starting MAS simulation run...")
        harness.run_mas_simulation()
        logging.info("Simulation run complete.")

        history = harness.history
        logging.info(f"Simulation generated {len(history)} steps of history data.")

        # Return the results in a structured response
        return JSONResponse(
            content={"status": "success", "message": "Simulation completed successfully.", "history": history},
            status_code=200
        )

    except ValueError as e:
        # This can catch custom validation errors raised from our root_validator
        logging.error(f"Validation error during simulation setup: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch-all for any other unexpected errors during the simulation process
        logging.error(f"An unexpected error occurred during simulation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")
