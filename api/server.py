import os
import json
from flask import Flask, jsonify, abort
from flask_cors import CORS

app = Flask(__name__)
# Allow CORS for all domains on all routes, which is fine for development.
CORS(app)

# The directory where simulation case JSON files are stored.
# We assume the server is run from the root of the repository.
CASES_DIRECTORY = 'data/simulation_cases'

@app.route('/api/examples', methods=['GET'])
def get_examples():
    """
    Scans the CASES_DIRECTORY for .json files and returns a list of their
    metadata (name and description).
    """
    examples = []
    if not os.path.exists(CASES_DIRECTORY):
        print(f"Warning: Cases directory '{CASES_DIRECTORY}' not found.")
        return jsonify([])

    for filename in os.listdir(CASES_DIRECTORY):
        if filename.endswith('.json'):
            example_name = filename.replace('.json', '')
            filepath = os.path.join(CASES_DIRECTORY, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    metadata = data.get('metadata', {})
                    examples.append({
                        'id': example_name,
                        'name': metadata.get('name', 'Unnamed Example'),
                        'description': metadata.get('description', '')
                    })
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading or parsing {filename}: {e}")
                continue
    return jsonify(examples)

@app.route('/api/examples/<string:example_name>', methods=['GET'])
def get_example_details(example_name):
    """
    Returns the full JSON configuration for a given example name.
    The example_name corresponds to the filename without the .json extension.
    """
    filename = f"{example_name}.json"
    filepath = os.path.join(CASES_DIRECTORY, filename)

    if not os.path.exists(filepath):
        abort(404, description=f"Example '{example_name}' not found.")

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return jsonify(data)
    except (IOError, json.JSONDecodeError) as e:
        abort(500, description=f"Could not read or parse file for example '{example_name}'.")


if __name__ == '__main__':
    # Running on port 5001 to avoid potential conflicts.
    # Debug mode is on for development.
    app.run(host='0.0.0.0', port=5001, debug=True)
