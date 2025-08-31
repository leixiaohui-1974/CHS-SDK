import yaml
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define paths
ROOT_DIR = Path(__file__).parent.parent
EXAMPLES_DIR = ROOT_DIR / 'examples'
OUTPUT_DIR = EXAMPLES_DIR / 'generated_json'

# Define which keys belong to initial_state for each component type.
# This is based on the definitions in core_lib/models/physical_models.py
INITIAL_STATE_KEYS = {
    "Reservoir": {"water_level", "volume", "outflow"},
    "Gate": {"opening", "outflow"},
    "Pipe": {"flow"},
    "UnifiedCanal": {"water_depth", "flow", "water_level"},
    # Add other components as needed
    "Pump": {"flow", "is_on"},
    "Valve": {"opening", "outflow"},
    "WaterTurbine": {"flow", "power"},
}


# Mapping from YAML component 'class' to api_models.py 'ComponentsModel' field name
COMPONENT_TYPE_MAP = {
    "Reservoir": "reservoirs",
    "Gate": "gates",
    "Pipe": "pipes",
    "UnifiedCanal": "unified_canals",
    "Pump": "pumps",
    "Valve": "valves",
    "HydropowerStation": "hydropower_stations",
    "Lake": "lakes",
    "RiverChannel": "river_channels",
    "WaterTurbine": "water_turbines",
    "RainfallRunoff": "rainfall_runoffs",
    "IntegralDelayCanal": "integral_delay_canals",
}

def load_yaml_file(filepath: Path):
    """Safely loads a YAML file, returning None if it doesn't exist."""
    if not filepath.is_file():
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file {filepath}: {e}")
        return None

def transform_components(yaml_data: dict) -> dict:
    """Transforms component data into the nested structure required by Pydantic models."""
    transformed = {key: [] for key in COMPONENT_TYPE_MAP.values()}

    if not yaml_data or 'components' not in yaml_data:
        return transformed

    for component in yaml_data['components']:
        component_class_str = component.get('class')
        if not component_class_str:
            logging.warning(f"Component '{component.get('id')}' has no 'class' defined. Skipping.")
            continue

        simple_class_name = component_class_str.split('.')[-1]
        field_name = COMPONENT_TYPE_MAP.get(simple_class_name)

        if not field_name:
            logging.warning(f"Unknown or unsupported component class '{simple_class_name}' for component '{component.get('id')}'. Skipping.")
            continue

        # Combine all params from YAML
        all_params = {**component.get('initial_state', {}), **component.get('parameters', {})}

        # Get the set of keys that belong in 'initial_state' for this component type
        state_keys = INITIAL_STATE_KEYS.get(simple_class_name, set())

        initial_state_data = {}
        parameters_data = {}

        # Segregate keys into the two sub-dictionaries
        for key, value in all_params.items():
            if key in state_keys:
                initial_state_data[key] = value
            else:
                parameters_data[key] = value

        # Support for 'area' alias for 'surface_area' in reservoirs
        if simple_class_name == "Reservoir" and 'area' in parameters_data:
            parameters_data['surface_area'] = parameters_data.pop('area')


        new_comp = {
            "name": component.get('id'),
            "initial_state": initial_state_data,
            "parameters": parameters_data
        }

        # Add legacy topics if they exist at the top level of the component
        if 'inflow_topic' in component:
            new_comp['inflow_topic'] = component['inflow_topic']
        if 'action_topic' in component:
            new_comp['action_topic'] = component['action_topic']


        transformed[field_name].append(new_comp)

    return {k: v for k, v in transformed.items() if v}

def transform_topology(yaml_data: dict) -> dict:
    """Transforms topology data."""
    if not yaml_data or 'connections' not in yaml_data:
        return {"connections": []}
    return {"connections": yaml_data['connections']}

def transform_agents(yaml_data: dict) -> dict:
    """Transforms agent data."""
    if not yaml_data or 'agents' not in yaml_data:
        return {"agents": []}

    transformed_agents = []
    for agent in yaml_data['agents']:
        # The Pydantic model 'GenericAgentConfig' uses an alias for 'class_name'.
        # The incoming JSON must use the key 'class'.
        new_agent = {
            "id": agent.get('id'),
            "class": agent.get('class'),
            "params": agent.get('config', {})
        }
        transformed_agents.append(new_agent)
    return {"agents": transformed_agents}


def main():
    """Main function to find and process all example scenarios."""
    logging.info(f"Starting preprocessing of examples in: {EXAMPLES_DIR}")
    OUTPUT_DIR.mkdir(exist_ok=True)
    logging.info(f"Outputting generated JSON to: {OUTPUT_DIR}")

    processed_count = 0
    scenario_paths = sorted([p.parent for p in EXAMPLES_DIR.rglob('components.yml')])

    for scenario_path in scenario_paths:
        if any(parent in scenario_path.parents for parent in scenario_paths if parent != scenario_path):
            continue

        relative_path_str = scenario_path.relative_to(EXAMPLES_DIR).as_posix()
        output_filename = relative_path_str.replace('/', '_') + '.json'

        logging.info(f"Processing scenario: {relative_path_str} -> {output_filename}")

        components_data = load_yaml_file(scenario_path / 'components.yml')
        topology_data = load_yaml_file(scenario_path / 'topology.yml')
        agents_data = load_yaml_file(scenario_path / 'agents.yml')

        if components_data is None:
            logging.warning(f"Skipping {relative_path_str} because components.yml could not be loaded.")
            continue

        final_data = {
            "components": transform_components(components_data),
            "topology": transform_topology(topology_data),
            "agents": transform_agents(agents_data)
        }

        output_filepath = OUTPUT_DIR / output_filename
        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=4)
            logging.info(f"Successfully generated {output_filepath.name}")
            processed_count += 1
        except IOError as e:
            logging.error(f"Failed to write JSON for scenario {relative_path_str}: {e}")

    logging.info(f"Preprocessing complete. Processed {processed_count} scenarios.")

if __name__ == "__main__":
    main()
