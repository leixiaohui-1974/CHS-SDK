import requests
import json

# Define the server URL
url = "http://0.0.0.0:8000/run_simulation"

# Construct the payload with both old and new field names to handle
# potential hot-reloading issues with the server's Pydantic models.
payload = {
    "components": {
        "reservoirs": [
            {
                "name": "simple_tank",
                "initial_state": {
                    "water_level": 2.0
                },
                "parameters": {
                    "surface_area": 10.0
                },
                "inflow_topic": "inflow_topic"
            }
        ],
        "gates": [],
        "pipes": [],
        "unified_canals": []
    },
    "topology": {
        "connections": []
    },
    "agents": {
        "agents": [
            {
                "id": "inflow_agent_1",
                "class": "core_lib.data_access.csv_inflow_agent.CsvInflowAgent",
                "params": {
                    # Correct, new field names
                    "csv_file_path": "examples/watertank_refactored/01_simple_simulation/inflow.csv",
                    "time_column": "time",
                    "data_column": "inflow_rate",
                    "inflow_topic": "inflow_topic",
                    # Old field names that the stale model might expect
                    "csv_file": "examples/watertank_refactored/01_simple_simulation/inflow.csv",
                    "value_column": "inflow_rate",
                    "output_topic": "inflow_topic"
                }
            }
        ]
    }
}

print("--- Sending simulation request to API ---")
print(json.dumps(payload, indent=2))

try:
    # Send the POST request
    response = requests.post(url, json=payload)

    # Check the response
    print(f"\n--- API Response ---")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("Simulation successful!")
        response_json = response.json()
        print(f"Response message: {response_json.get('message')}")
        history = response_json.get('history', [])
        print(f"Number of history steps returned: {len(history)}")
        if history:
            print("First history step:")
            print(json.dumps(history[0], indent=2))
            print("Last history step:")
            print(json.dumps(history[-1], indent=2))
    else:
        print("Simulation failed!")
        print("Error details:")
        try:
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print(response.text)

except requests.exceptions.ConnectionError as e:
    print("\n--- Connection Error ---")
    print(f"Could not connect to the server at {url}. Is it running?")
    print(f"Error details: {e}")
