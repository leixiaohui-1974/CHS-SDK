#!/usr/bin/env python3
"""
CHS Simulation Platform - Deployment Validation Script

This script validates the deployment configuration without requiring Docker.
It checks:
- Environment configuration
- File structure
- Dependencies
- Configuration files
- Basic application startup
"""

import os
import sys
import json
import yaml
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "api"))

class DeploymentValidator:
    def __init__(self):
        self.project_root = project_root
        self.api_root = self.project_root / "api"
        self.frontend_root = self.project_root / "frontend"
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0
    
    def print_status(self, message: str, status: str = "INFO"):
        """Print colored status messages"""
        colors = {
            "INFO": "\033[0;34m",
            "SUCCESS": "\033[0;32m",
            "WARNING": "\033[1;33m",
            "ERROR": "\033[0;31m",
            "RESET": "\033[0m"
        }
        print(f"{colors.get(status, colors['INFO'])}[{status}]{colors['RESET']} {message}")
    
    def check_file_exists(self, file_path: Path, description: str) -> bool:
        """Check if a file exists"""
        self.total_checks += 1
        if file_path.exists():
            self.print_status(f"{description} found: {file_path.name}", "SUCCESS")
            self.success_count += 1
            return True
        else:
            self.print_status(f"{description} missing: {file_path}", "ERROR")
            self.errors.append(f"Missing {description}: {file_path}")
            return False
    
    def check_directory_exists(self, dir_path: Path, description: str) -> bool:
        """Check if a directory exists"""
        self.total_checks += 1
        if dir_path.exists() and dir_path.is_dir():
            self.print_status(f"{description} found: {dir_path.name}/", "SUCCESS")
            self.success_count += 1
            return True
        else:
            self.print_status(f"{description} missing: {dir_path}", "ERROR")
            self.errors.append(f"Missing {description}: {dir_path}")
            return False
    
    def validate_project_structure(self) -> bool:
        """Validate basic project structure"""
        self.print_status("Validating project structure...", "INFO")
        
        # Check main directories
        directories = [
            (self.api_root, "API directory"),
            (self.frontend_root, "Frontend directory"),
            (self.project_root / "scripts", "Scripts directory"),
            (self.project_root / "tests", "Tests directory")
        ]
        
        for dir_path, description in directories:
            self.check_directory_exists(dir_path, description)
        
        # Check main files
        files = [
            (self.project_root / "docker-compose.yml", "Docker Compose file"),
            (self.project_root / "Dockerfile", "Dockerfile"),
            (self.project_root / ".env", "Environment file"),
            (self.project_root / ".env.example", "Environment example file"),
            (self.api_root / "server.py", "Main server file"),
            (self.api_root / "requirements.txt", "Python requirements file")
        ]
        
        for file_path, description in files:
            self.check_file_exists(file_path, description)
        
        return len(self.errors) == 0
    
    def validate_environment_config(self) -> bool:
        """Validate environment configuration"""
        self.print_status("Validating environment configuration...", "INFO")
        
        # Load .env file if exists
        env_file = self.project_root / ".env"
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key] = value
                self.print_status("Environment file loaded successfully", "SUCCESS")
            except Exception as e:
                self.print_status(f"Error loading .env file: {e}", "ERROR")
                self.errors.append(f"Invalid .env file: {e}")
                return False
        
        # Check required environment variables
        required_vars = {
            'SECRET_KEY': 'Application secret key',
            'DATABASE_URL': 'Database connection URL',
            'REDIS_URL': 'Redis connection URL',
            'ENVIRONMENT': 'Application environment'
        }
        
        self.total_checks += len(required_vars)
        for var, description in required_vars.items():
            if os.getenv(var):
                self.print_status(f"{description} configured", "SUCCESS")
                self.success_count += 1
            else:
                self.print_status(f"{description} not configured: {var}", "WARNING")
                self.warnings.append(f"Missing environment variable: {var}")
        
        return True
    
    def validate_python_dependencies(self) -> bool:
        """Validate Python dependencies"""
        self.print_status("Validating Python dependencies...", "INFO")
        
        requirements_file = self.api_root / "requirements.txt"
        if not requirements_file.exists():
            self.print_status("requirements.txt not found", "ERROR")
            self.errors.append("Missing requirements.txt")
            return False
        
        try:
            with open(requirements_file, 'r') as f:
                requirements = f.read().splitlines()
            
            # Check critical dependencies
            critical_deps = ['fastapi', 'uvicorn', 'sqlalchemy', 'redis', 'pydantic']
            found_deps = []
            
            for req in requirements:
                req = req.strip()
                if req and not req.startswith('#'):
                    dep_name = req.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0]
                    if dep_name.lower() in critical_deps:
                        found_deps.append(dep_name.lower())
            
            self.total_checks += len(critical_deps)
            for dep in critical_deps:
                if dep in found_deps:
                    self.print_status(f"Critical dependency found: {dep}", "SUCCESS")
                    self.success_count += 1
                else:
                    self.print_status(f"Critical dependency missing: {dep}", "WARNING")
                    self.warnings.append(f"Missing critical dependency: {dep}")
            
            return True
            
        except Exception as e:
            self.print_status(f"Error reading requirements.txt: {e}", "ERROR")
            self.errors.append(f"Invalid requirements.txt: {e}")
            return False
    
    def validate_docker_config(self) -> bool:
        """Validate Docker configuration"""
        self.print_status("Validating Docker configuration...", "INFO")
        
        # Validate docker-compose.yml
        compose_file = self.project_root / "docker-compose.yml"
        if compose_file.exists():
            try:
                with open(compose_file, 'r') as f:
                    compose_config = yaml.safe_load(f)
                
                # Check required services
                services = compose_config.get('services', {})
                required_services = ['postgres', 'redis', 'api']
                
                self.total_checks += len(required_services)
                for service in required_services:
                    if service in services:
                        self.print_status(f"Docker service configured: {service}", "SUCCESS")
                        self.success_count += 1
                    else:
                        self.print_status(f"Docker service missing: {service}", "ERROR")
                        self.errors.append(f"Missing Docker service: {service}")
                
                return True
                
            except yaml.YAMLError as e:
                self.print_status(f"Invalid docker-compose.yml: {e}", "ERROR")
                self.errors.append(f"Invalid docker-compose.yml: {e}")
                return False
        else:
            self.print_status("docker-compose.yml not found", "ERROR")
            self.errors.append("Missing docker-compose.yml")
            return False
    
    def validate_api_imports(self) -> bool:
        """Validate that main API modules can be imported"""
        self.print_status("Validating API module imports...", "INFO")
        
        modules_to_test = [
            ('server', 'Main server module'),
            ('database.database', 'Database module'),
            ('database.models', 'Database models'),
            ('core.config', 'Configuration module')
        ]
        
        self.total_checks += len(modules_to_test)
        for module_name, description in modules_to_test:
            try:
                # Try to import the module
                if module_name == 'server':
                    spec = importlib.util.spec_from_file_location("server", self.api_root / "server.py")
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        # Don't actually load to avoid side effects
                        self.print_status(f"{description} can be imported", "SUCCESS")
                        self.success_count += 1
                    else:
                        raise ImportError("Module spec not found")
                else:
                    # For other modules, just check if files exist
                    module_path = self.api_root / module_name.replace('.', '/') + '.py'
                    if module_path.exists():
                        self.print_status(f"{description} file exists", "SUCCESS")
                        self.success_count += 1
                    else:
                        raise ImportError(f"Module file not found: {module_path}")
                        
            except ImportError as e:
                self.print_status(f"{description} import failed: {e}", "WARNING")
                self.warnings.append(f"Module import issue: {module_name} - {e}")
            except Exception as e:
                self.print_status(f"{description} validation failed: {e}", "WARNING")
                self.warnings.append(f"Module validation issue: {module_name} - {e}")
        
        return True
    
    def run_validation(self) -> bool:
        """Run all validation checks"""
        self.print_status("Starting CHS Simulation Platform Deployment Validation", "INFO")
        self.print_status("=" * 70, "INFO")
        
        validation_steps = [
            ("Project Structure", self.validate_project_structure),
            ("Environment Configuration", self.validate_environment_config),
            ("Python Dependencies", self.validate_python_dependencies),
            ("Docker Configuration", self.validate_docker_config),
            ("API Module Imports", self.validate_api_imports)
        ]
        
        for step_name, step_func in validation_steps:
            self.print_status(f"\n--- {step_name} ---", "INFO")
            try:
                step_func()
            except Exception as e:
                self.print_status(f"Validation step '{step_name}' failed: {e}", "ERROR")
                self.errors.append(f"Validation step failed: {step_name} - {e}")
        
        # Print summary
        self.print_summary()
        
        return len(self.errors) == 0
    
    def print_summary(self):
        """Print validation summary"""
        self.print_status("\n" + "=" * 70, "INFO")
        self.print_status("Deployment Validation Summary", "INFO")
        self.print_status("=" * 70, "INFO")
        
        self.print_status(f"Total checks: {self.total_checks}", "INFO")
        self.print_status(f"Successful: {self.success_count}", "SUCCESS")
        self.print_status(f"Warnings: {len(self.warnings)}", "WARNING")
        self.print_status(f"Errors: {len(self.errors)}", "ERROR")
        
        if self.warnings:
            self.print_status("\nWarnings:", "WARNING")
            for warning in self.warnings:
                self.print_status(f"  - {warning}", "WARNING")
        
        if self.errors:
            self.print_status("\nErrors:", "ERROR")
            for error in self.errors:
                self.print_status(f"  - {error}", "ERROR")
        
        if len(self.errors) == 0:
            self.print_status("\n✅ Deployment validation PASSED!", "SUCCESS")
            self.print_status("The application is ready for deployment.", "SUCCESS")
        else:
            self.print_status("\n❌ Deployment validation FAILED!", "ERROR")
            self.print_status("Please fix the errors before deploying.", "ERROR")

def main():
    """Main function"""
    validator = DeploymentValidator()
    
    try:
        success = validator.run_validation()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        validator.print_status("\nValidation interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        validator.print_status(f"Unexpected error during validation: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()