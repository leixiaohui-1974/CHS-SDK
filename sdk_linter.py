import argparse
import os
import yaml
import importlib
import inspect
from pathlib import Path

def main():
    """
    Main function for the SDK Linter.
    Parses command-line arguments and initiates the linting process.
    """
    parser = argparse.ArgumentParser(
        description="A linter to validate scenario configuration files for the Water System SDK."
    )
    parser.add_argument(
        "scenario_dir",
        type=str,
        help="The path to the scenario directory to lint."
    )
    args = parser.parse_args()

    print(f"Starting linting process for scenario: {args.scenario_dir}")

    if not os.path.isdir(args.scenario_dir):
        print(f"Error: Directory not found at '{args.scenario_dir}'")
        return

    # We are only interested in these specific configuration files
    files_to_check = ["agents.yml", "components.yml", "topology.yml"]
    yaml_files = [Path(args.scenario_dir) / f for f in files_to_check if (Path(args.scenario_dir) / f).exists()]

    if not yaml_files:
        print(f"No standard config files (agents.yml, components.yml, topology.yml) found in '{args.scenario_dir}'")
        return

    print(f"Found {len(yaml_files)} config file(s) to lint.")

    all_errors = []
    for yaml_file in yaml_files:
        print(f"  - Linting {yaml_file}...")
        with open(yaml_file, "r") as f:
            try:
                data = yaml.safe_load(f)
                if not data:
                    continue

                # Process components and agents
                for item_type in ["components", "agents"]:
                    if item_type in data:
                        for item in data[item_type]:
                            class_path = item.get("class")
                            item_id = item.get("id", "N/A")
                            if class_path:
                                params = get_class_signature(class_path)
                                if params:
                                    # We have a valid signature, now validate the item config
                                    item_config = item.get("config", {})
                                    errors = validate_item(item_id, item_config, params)
                                    if errors:
                                        all_errors.append(
                                            (yaml_file, item_id, class_path, errors)
                                        )
                                else:
                                    all_errors.append(
                                        (yaml_file, item_id, class_path, ["Could not inspect class signature."])
                                    )


            except yaml.YAMLError as e:
                print(f"    - Error parsing YAML file: {e}")

    # --- Final Report ---
    print("\n" + "=" * 30)
    print("Linting Summary")
    print("=" * 30)
    if not all_errors:
        print("✅ All configurations appear to be valid.")
    else:
        print(f"❌ Found {len(all_errors)} issue(s).")
        for file_path, item_id, class_path, errors in all_errors:
            print(f"\nIn file: {file_path}")
            print(f"  Component/Agent ID: '{item_id}'")
            print(f"  Class: {class_path}")
            for error in errors:
                print(f"    - Error: {error}")
    print("=" * 30)


def get_class_signature(class_path: str) -> dict:
    """
    Dynamically imports a class and inspects its __init__ method to
    determine its signature.

    Args:
        class_path: The full dot-separated path to the class
                    (e.g., 'core_lib.physical_objects.reservoir.Reservoir').

    Returns:
        A dictionary where keys are parameter names and values are their
        inspect.Parameter objects, or an empty dictionary if the class
        or module cannot be found.
    """
    try:
        module_path, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        signature = inspect.signature(cls.__init__)
        return signature.parameters
    except (ImportError, AttributeError, ValueError) as e:
        # Don't print an error here, as the caller will report it.
        return None

def validate_item(item_id: str, config: dict, signature_params: dict) -> list[str]:
    """
    Validates a single item's configuration against its class signature.

    Args:
        item_id: The ID of the item being validated.
        config: The configuration dictionary from the YAML file.
        signature_params: The parameter dictionary from inspect.signature().

    Returns:
        A list of error strings.
    """
    errors = []
    config_keys = set(config.keys())
    sig_keys = set(signature_params.keys())

    # Rule 1: Check for unknown parameters in YAML
    unknown_params = config_keys - sig_keys
    for param in unknown_params:
        # Ignore 'class' and 'id' as they are metadata, not constructor args
        if param not in ['class', 'id']:
            errors.append(f"Unknown parameter '{param}'")

    # Rule 2: Check for missing required parameters in YAML
    # These parameters are known to be injected by the ObjectFactory or are not relevant to config
    factory_injected_params = {'self', 'bus', 'message_bus', 'id', 'agent_id', 'kwargs', 'config'}
    for param_name, param_obj in signature_params.items():
        if param_obj.default == inspect.Parameter.empty and param_name not in factory_injected_params:
            # This is a required parameter that should be in the YAML config
            if param_name not in config_keys:
                errors.append(f"Missing required parameter '{param_name}'")

    return errors

if __name__ == "__main__":
    main()
