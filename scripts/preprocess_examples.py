import sys
import json
import logging
from pathlib import Path

# Add project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from core_lib.io.yaml_loader import SimulationBuilder
from core_lib.models.api_models import SimulationRequest, ComponentsModel, TopologyModel, AgentsModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

EXAMPLES_DIR = project_root / "examples"
OUTPUT_DIR = EXAMPLES_DIR / "generated_json"

def find_example_dirs(base_dir: Path) -> list[Path]:
    """Recursively finds directories containing 'components.yml'."""
    return [entry.parent for entry in base_dir.rglob('components.yml') if entry.is_file()]

def transform_components(components_config: dict) -> dict:
    """Transforms the component list from YAML structure to the Pydantic model structure."""
    components_transformed = {"reservoirs": [], "gates": [], "pipes": [], "unified_canals": []}
    if components_config and 'components' in components_config:
        for comp_conf in components_config['components']:
            class_path = comp_conf.pop('class', '')
            if 'id' in comp_conf:
                comp_conf['name'] = comp_conf.pop('id')

            if 'Reservoir' in class_path:
                components_transformed['reservoirs'].append(comp_conf)
            elif 'Gate' in class_path:
                components_transformed['gates'].append(comp_conf)
            elif 'Pipe' in class_path:
                components_transformed['pipes'].append(comp_conf)
            elif 'UnifiedCanal' in class_path:
                components_transformed['unified_canals'].append(comp_conf)
    return components_transformed

def transform_agents(agents_config: dict, example_path: Path) -> dict:
    """Transforms the agent list from YAML structure to the Pydantic model structure."""
    agents_config_transformed = {"agents": []}
    if agents_config and 'agents' in agents_config:
        for agent_conf in agents_config['agents']:
            if 'config' in agent_conf:
                agent_conf['params'] = agent_conf.pop('config')

            if 'CsvInflowAgent' in agent_conf.get('class', ''):
                if 'params' in agent_conf and 'csv_file' in agent_conf['params']:
                    csv_file = agent_conf['params'].pop('csv_file')
                    # Create a path relative to the project root for consistency
                    full_csv_path = example_path / csv_file
                    agent_conf['params']['csv_file_path'] = str(full_csv_path)

            agents_config_transformed['agents'].append(agent_conf)
    return agents_config_transformed

def main():
    """Main function to preprocess a single example and print its JSON."""
    example_to_process = "watertank_refactored/01_simple_simulation"
    example_path = EXAMPLES_DIR / example_to_process

    if not example_path.is_dir():
        logging.error(f"Example directory not found: {example_path}")
        return

    try:
        # 1. Load config using SimulationBuilder
        loader = SimulationBuilder(scenario_path=str(example_path))

        # 2. Transform the loaded dictionaries
        components_data = transform_components(loader.components_config)
        topology_data = loader.topology_config or {}
        agents_data = transform_agents(loader.agents_config, example_path)

        # 3. Validate and structure the data with Pydantic models
        components_model = ComponentsModel.model_validate(components_data)
        topology_model = TopologyModel.model_validate(topology_data)
        agents_model = AgentsModel.model_validate(agents_data)

        simulation_request = SimulationRequest(
            components=components_model,
            topology=topology_model,
            agents=agents_model
        )

        # 4. Serialize to a dictionary with correct aliases
        output_dict = simulation_request.model_dump(by_alias=True, exclude_none=True)

        # 5. Print JSON to stdout
        print(json.dumps(output_dict, indent=2))

    except Exception as e:
        logging.error(f"Failed to process example {example_to_process}: {e}", exc_info=True)


if __name__ == "__main__":
    main()
