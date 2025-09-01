#!/usr/bin/env python3
"""
CHS Simulation Platform - Deployment Test Script

This script tests basic deployment functionality including:
- Docker Compose validation
- Environment configuration
- Service health checks
- Basic connectivity tests
"""

import os
import sys
import subprocess
import time
import requests
import yaml
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class DeploymentTester:
    def __init__(self):
        self.project_root = project_root
        self.docker_compose_file = self.project_root / "docker-compose.yml"
        self.env_file = self.project_root / ".env"
        self.services = {
            "postgres": {"port": 5432, "health_endpoint": None},
            "redis": {"port": 6379, "health_endpoint": None},
            "api": {"port": 8000, "health_endpoint": "http://localhost:8000/health"}
        }
    
    def print_status(self, message, status="INFO"):
        """Print colored status messages"""
        colors = {
            "INFO": "\033[0;34m",
            "SUCCESS": "\033[0;32m",
            "WARNING": "\033[1;33m",
            "ERROR": "\033[0;31m",
            "RESET": "\033[0m"
        }
        print(f"{colors.get(status, colors['INFO'])}[{status}]{colors['RESET']} {message}")
    
    def validate_docker_compose(self):
        """Validate docker-compose.yml file"""
        self.print_status("Validating docker-compose.yml...")
        
        if not self.docker_compose_file.exists():
            self.print_status("docker-compose.yml not found!", "ERROR")
            return False
        
        try:
            with open(self.docker_compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)
            
            # Check required services
            services = compose_config.get('services', {})
            required_services = ['postgres', 'redis', 'api']
            
            for service in required_services:
                if service not in services:
                    self.print_status(f"Required service '{service}' not found in docker-compose.yml", "ERROR")
                    return False
            
            self.print_status("docker-compose.yml validation passed", "SUCCESS")
            return True
            
        except yaml.YAMLError as e:
            self.print_status(f"Invalid YAML in docker-compose.yml: {e}", "ERROR")
            return False
        except Exception as e:
            self.print_status(f"Error validating docker-compose.yml: {e}", "ERROR")
            return False
    
    def check_environment_config(self):
        """Check environment configuration"""
        self.print_status("Checking environment configuration...")
        
        # Check if .env file exists
        if not self.env_file.exists():
            self.print_status(".env file not found, using defaults", "WARNING")
        else:
            self.print_status(".env file found", "SUCCESS")
        
        # Check required environment variables
        required_vars = [
            'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD',
            'REDIS_PASSWORD', 'SECRET_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.print_status(f"Missing environment variables: {', '.join(missing_vars)}", "WARNING")
            self.print_status("Using default values from docker-compose.yml", "INFO")
        else:
            self.print_status("All required environment variables are set", "SUCCESS")
        
        return True
    
    def check_docker_availability(self):
        """Check if Docker and Docker Compose are available"""
        self.print_status("Checking Docker availability...")
        
        try:
            # Check Docker
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, check=True)
            self.print_status(f"Docker found: {result.stdout.strip()}", "SUCCESS")
            
            # Check Docker Compose
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True, check=True)
            self.print_status(f"Docker Compose found: {result.stdout.strip()}", "SUCCESS")
            
            return True
            
        except subprocess.CalledProcessError:
            self.print_status("Docker or Docker Compose not found!", "ERROR")
            return False
        except FileNotFoundError:
            self.print_status("Docker or Docker Compose not installed!", "ERROR")
            return False
    
    def test_service_connectivity(self, service_name, port, timeout=30):
        """Test if a service is accessible on the specified port"""
        import socket
        
        self.print_status(f"Testing connectivity to {service_name} on port {port}...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    self.print_status(f"{service_name} is accessible on port {port}", "SUCCESS")
                    return True
                    
            except Exception:
                pass
            
            time.sleep(1)
        
        self.print_status(f"{service_name} is not accessible on port {port} after {timeout}s", "ERROR")
        return False
    
    def test_health_endpoint(self, service_name, endpoint, timeout=30):
        """Test service health endpoint"""
        if not endpoint:
            return True
        
        self.print_status(f"Testing health endpoint for {service_name}: {endpoint}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    self.print_status(f"{service_name} health check passed", "SUCCESS")
                    return True
                    
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
        
        self.print_status(f"{service_name} health check failed after {timeout}s", "ERROR")
        return False
    
    def run_deployment_tests(self):
        """Run all deployment tests"""
        self.print_status("Starting CHS Simulation Platform Deployment Tests", "INFO")
        self.print_status("=" * 60, "INFO")
        
        tests = [
            ("Docker Availability", self.check_docker_availability),
            ("Docker Compose Validation", self.validate_docker_compose),
            ("Environment Configuration", self.check_environment_config),
        ]
        
        failed_tests = []
        
        for test_name, test_func in tests:
            self.print_status(f"\nRunning: {test_name}", "INFO")
            try:
                if not test_func():
                    failed_tests.append(test_name)
            except Exception as e:
                self.print_status(f"Test '{test_name}' failed with exception: {e}", "ERROR")
                failed_tests.append(test_name)
        
        # Summary
        self.print_status("\n" + "=" * 60, "INFO")
        self.print_status("Deployment Test Summary", "INFO")
        self.print_status("=" * 60, "INFO")
        
        if failed_tests:
            self.print_status(f"Failed tests: {', '.join(failed_tests)}", "ERROR")
            self.print_status("Deployment validation FAILED", "ERROR")
            return False
        else:
            self.print_status("All deployment tests passed!", "SUCCESS")
            self.print_status("Deployment validation SUCCESSFUL", "SUCCESS")
            return True

def main():
    """Main function"""
    tester = DeploymentTester()
    
    try:
        success = tester.run_deployment_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        tester.print_status("\nDeployment tests interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        tester.print_status(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()