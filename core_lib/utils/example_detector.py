# -*- coding: utf-8 -*-
"""
Example Type Detection Utility

This module provides utilities to automatically detect the type of simulation examples
and determine the appropriate way to run them.
"""

import logging
from pathlib import Path
from typing import Literal, Optional, Dict, Any
import yaml

ExampleType = Literal["run_scenario.py", "python_script", "unknown"]

logger = logging.getLogger(__name__)

def detect_example_type(example_path: str | Path) -> ExampleType:
    """
    Automatically detect the type of simulation example and determine how to run it.
    
    Args:
        example_path: Path to the example directory
        
    Returns:
        ExampleType: One of "run_scenario.py", "python_script", or "unknown"
        
    Examples:
        >>> detect_example_type("examples/agent_based/06_centralized_emergency_override")
        "run_scenario.py"
        
        >>> detect_example_type("examples/identification/01_reservoir_storage_curve")
        "python_script"
    """
    path = Path(example_path)
    
    if not path.exists() or not path.is_dir():
        logger.warning(f"Path does not exist or is not a directory: {path}")
        return "unknown"
    
    # Check for scenario config marker file
    scenario_config_file = path / ".scenario_config"
    if scenario_config_file.exists():
        try:
            with open(scenario_config_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if "run_with: run_scenario.py" in content:
                    return "run_scenario.py"
        except Exception as e:
            logger.warning(f"Error reading .scenario_config file: {e}")
    
    # Check metadata in config.yml
    config_file = path / "config.yml"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if isinstance(config, dict):
                    metadata = config.get('metadata', {})
                    if metadata.get('runner') == 'run_scenario.py':
                        return "run_scenario.py"
        except Exception as e:
            logger.warning(f"Error reading config.yml metadata: {e}")
    
    # Check if it has all required YAML configuration files
    required_yamls = ['config.yml', 'components.yml', 'topology.yml', 'agents.yml']
    has_all_yamls = all((path / yaml_file).exists() for yaml_file in required_yamls)
    
    # Check if it has independent run scripts
    python_files = list(path.glob('*.py'))
    has_run_script = any(f.name.startswith('run_') and f.suffix == '.py' 
                        for f in python_files)
    
    # Decision logic
    if has_all_yamls and not has_run_script:
        return "run_scenario.py"
    elif has_run_script:
        return "python_script"
    else:
        return "unknown"

def get_run_command(example_path: str | Path) -> Optional[str]:
    """
    Get the appropriate command to run the example.
    
    Args:
        example_path: Path to the example directory
        
    Returns:
        str: The command to run the example, or None if unknown
        
    Examples:
        >>> get_run_command("examples/agent_based/06_centralized_emergency_override")
        "python run_scenario.py examples/agent_based/06_centralized_emergency_override"
        
        >>> get_run_command("examples/identification/01_reservoir_storage_curve")
        "python run_identification.py"
    """
    path = Path(example_path)
    example_type = detect_example_type(path)
    
    if example_type == "run_scenario.py":
        return f"python run_scenario.py {path}"
    elif example_type == "python_script":
        # Find the run script
        python_files = list(path.glob('run_*.py'))
        if python_files:
            script_name = python_files[0].name
            return f"cd {path} && python {script_name}"
        else:
            # Fallback to any Python file
            python_files = list(path.glob('*.py'))
            if python_files:
                script_name = python_files[0].name
                return f"cd {path} && python {script_name}"
    
    return None

def get_example_info(example_path: str | Path) -> Dict[str, Any]:
    """
    Get comprehensive information about an example.
    
    Args:
        example_path: Path to the example directory
        
    Returns:
        dict: Information about the example including type, command, and files
    """
    path = Path(example_path)
    example_type = detect_example_type(path)
    run_command = get_run_command(path)
    
    # Get list of files
    files = []
    if path.exists():
        files = [f.name for f in path.iterdir() if f.is_file()]
    
    # Check for README
    readme_files = [f for f in files if f.lower().startswith('readme')]
    
    return {
        'path': str(path),
        'type': example_type,
        'run_command': run_command,
        'files': files,
        'has_readme': len(readme_files) > 0,
        'readme_files': readme_files,
        'has_yaml_configs': all(f in files for f in ['config.yml', 'components.yml', 'topology.yml', 'agents.yml']),
        'python_scripts': [f for f in files if f.endswith('.py')]
    }

def scan_examples_directory(examples_root: str | Path = "examples") -> Dict[str, Dict[str, Any]]:
    """
    Scan the entire examples directory and categorize all examples.
    
    Args:
        examples_root: Path to the examples root directory
        
    Returns:
        dict: Mapping of example paths to their information
    """
    examples_path = Path(examples_root)
    results = {}
    
    if not examples_path.exists():
        logger.error(f"Examples directory does not exist: {examples_path}")
        return results
    
    # Recursively find all potential example directories
    for item in examples_path.rglob('*'):
        if item.is_dir():
            # Skip hidden directories and common non-example directories
            if any(part.startswith('.') for part in item.parts):
                continue
            if any(part in ['__pycache__', 'logs', 'output', 'data'] for part in item.parts):
                continue
                
            # Check if this looks like an example directory
            has_config_files = any((item / f).exists() for f in ['config.yml', 'README.md', 'run_*.py'])
            if has_config_files:
                relative_path = item.relative_to(examples_path.parent)
                results[str(relative_path)] = get_example_info(item)
    
    return results

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        example_path = sys.argv[1]
        info = get_example_info(example_path)
        print(f"Example: {info['path']}")
        print(f"Type: {info['type']}")
        print(f"Command: {info['run_command']}")
        print(f"Files: {', '.join(info['files'])}")
    else:
        # Scan all examples
        results = scan_examples_directory()
        for path, info in results.items():
            print(f"{path}: {info['type']} - {info['run_command']}")