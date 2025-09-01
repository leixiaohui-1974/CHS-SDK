#!/usr/bin/env python3
"""
CHS Simulation Platform - Deployment Status Checker

This script checks the status of deployed services and provides
a quick overview of system health.
"""

import os
import sys
import time
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class DeploymentStatusChecker:
    def __init__(self):
        self.project_root = project_root
        self.services = {
            "API": {
                "url": "http://localhost:8000/health",
                "timeout": 5,
                "expected_status": 200
            },
            "API Monitoring": {
                "url": "http://localhost:8000/api/monitoring/health",
                "timeout": 5,
                "expected_status": 200
            },
            "API Examples": {
                "url": "http://localhost:8000/api/examples",
                "timeout": 5,
                "expected_status": 200
            }
        }
        self.docker_services = ["postgres", "redis", "api"]
    
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
    
    def check_docker_services(self) -> Dict[str, bool]:
        """Check Docker services status"""
        self.print_status("Checking Docker services...", "INFO")
        
        service_status = {}
        
        try:
            # Check if docker-compose is available
            result = subprocess.run(
                ["docker-compose", "ps", "--services"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=10
            )
            
            if result.returncode != 0:
                self.print_status("Docker Compose not available or no services running", "WARNING")
                return service_status
            
            # Check individual services
            for service in self.docker_services:
                try:
                    result = subprocess.run(
                        ["docker-compose", "ps", "-q", service],
                        capture_output=True,
                        text=True,
                        cwd=self.project_root,
                        timeout=5
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        # Check if container is running
                        container_id = result.stdout.strip()
                        inspect_result = subprocess.run(
                            ["docker", "inspect", "-f", "{{.State.Running}}", container_id],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        if inspect_result.returncode == 0 and inspect_result.stdout.strip() == "true":
                            service_status[service] = True
                            self.print_status(f"Docker service '{service}' is running", "SUCCESS")
                        else:
                            service_status[service] = False
                            self.print_status(f"Docker service '{service}' is not running", "ERROR")
                    else:
                        service_status[service] = False
                        self.print_status(f"Docker service '{service}' not found", "ERROR")
                        
                except subprocess.TimeoutExpired:
                    service_status[service] = False
                    self.print_status(f"Timeout checking Docker service '{service}'", "ERROR")
                except Exception as e:
                    service_status[service] = False
                    self.print_status(f"Error checking Docker service '{service}': {e}", "ERROR")
            
        except subprocess.TimeoutExpired:
            self.print_status("Timeout checking Docker services", "ERROR")
        except FileNotFoundError:
            self.print_status("Docker or Docker Compose not found", "WARNING")
        except Exception as e:
            self.print_status(f"Error checking Docker services: {e}", "ERROR")
        
        return service_status
    
    def check_http_services(self) -> Dict[str, bool]:
        """Check HTTP services status"""
        self.print_status("Checking HTTP services...", "INFO")
        
        service_status = {}
        
        for service_name, config in self.services.items():
            try:
                response = requests.get(
                    config["url"],
                    timeout=config["timeout"]
                )
                
                if response.status_code == config["expected_status"]:
                    service_status[service_name] = True
                    self.print_status(f"HTTP service '{service_name}' is healthy", "SUCCESS")
                    
                    # Try to parse JSON response for additional info
                    try:
                        data = response.json()
                        if isinstance(data, dict) and "status" in data:
                            status_info = data.get("status", "unknown")
                            self.print_status(f"  Status: {status_info}", "INFO")
                    except:
                        pass
                        
                else:
                    service_status[service_name] = False
                    self.print_status(
                        f"HTTP service '{service_name}' returned status {response.status_code}",
                        "ERROR"
                    )
                    
            except requests.exceptions.ConnectionError:
                service_status[service_name] = False
                self.print_status(f"HTTP service '{service_name}' is not reachable", "ERROR")
            except requests.exceptions.Timeout:
                service_status[service_name] = False
                self.print_status(f"HTTP service '{service_name}' timed out", "ERROR")
            except Exception as e:
                service_status[service_name] = False
                self.print_status(f"Error checking HTTP service '{service_name}': {e}", "ERROR")
        
        return service_status
    
    def check_file_system(self) -> Dict[str, bool]:
        """Check file system status"""
        self.print_status("Checking file system...", "INFO")
        
        checks = {
            "logs_directory": self.project_root / "logs",
            "uploads_directory": self.project_root / "uploads",
            "data_directory": self.project_root / "data",
            "env_file": self.project_root / ".env"
        }
        
        status = {}
        
        for check_name, path in checks.items():
            if path.exists():
                status[check_name] = True
                if path.is_dir():
                    self.print_status(f"Directory '{path.name}' exists", "SUCCESS")
                else:
                    self.print_status(f"File '{path.name}' exists", "SUCCESS")
            else:
                status[check_name] = False
                if check_name == "env_file":
                    self.print_status(f"File '{path.name}' missing (using defaults)", "WARNING")
                else:
                    self.print_status(f"Directory '{path.name}' missing", "WARNING")
        
        return status
    
    def check_process_status(self) -> Dict[str, bool]:
        """Check if API process is running (non-Docker)"""
        self.print_status("Checking process status...", "INFO")
        
        status = {}
        
        try:
            # Check if uvicorn process is running
            if sys.platform == "win32":
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq python.exe"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "python.exe" in result.stdout:
                    status["python_process"] = True
                    self.print_status("Python process found", "SUCCESS")
                else:
                    status["python_process"] = False
                    self.print_status("No Python process found", "WARNING")
            else:
                result = subprocess.run(
                    ["pgrep", "-f", "uvicorn"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    status["uvicorn_process"] = True
                    self.print_status("Uvicorn process found", "SUCCESS")
                else:
                    status["uvicorn_process"] = False
                    self.print_status("No Uvicorn process found", "WARNING")
                    
        except Exception as e:
            self.print_status(f"Error checking processes: {e}", "WARNING")
        
        return status
    
    def run_status_check(self) -> bool:
        """Run comprehensive status check"""
        self.print_status("CHS Simulation Platform - Deployment Status Check", "INFO")
        self.print_status("=" * 60, "INFO")
        
        all_results = {}
        
        # Run all checks
        checks = [
            ("Docker Services", self.check_docker_services),
            ("HTTP Services", self.check_http_services),
            ("File System", self.check_file_system),
            ("Process Status", self.check_process_status)
        ]
        
        for check_name, check_func in checks:
            self.print_status(f"\n--- {check_name} ---", "INFO")
            try:
                results = check_func()
                all_results[check_name] = results
            except Exception as e:
                self.print_status(f"Check '{check_name}' failed: {e}", "ERROR")
                all_results[check_name] = {}
        
        # Print summary
        self.print_summary(all_results)
        
        # Determine overall health
        critical_services = ["API", "API Monitoring"]
        overall_healthy = True
        
        http_results = all_results.get("HTTP Services", {})
        for service in critical_services:
            if not http_results.get(service, False):
                overall_healthy = False
                break
        
        return overall_healthy
    
    def print_summary(self, results: Dict[str, Dict[str, bool]]):
        """Print status summary"""
        self.print_status("\n" + "=" * 60, "INFO")
        self.print_status("Deployment Status Summary", "INFO")
        self.print_status("=" * 60, "INFO")
        
        total_checks = 0
        successful_checks = 0
        
        for category, checks in results.items():
            if checks:
                category_success = sum(1 for status in checks.values() if status)
                category_total = len(checks)
                total_checks += category_total
                successful_checks += category_success
                
                self.print_status(
                    f"{category}: {category_success}/{category_total} checks passed",
                    "SUCCESS" if category_success == category_total else "WARNING"
                )
        
        self.print_status(f"\nOverall: {successful_checks}/{total_checks} checks passed", "INFO")
        
        # Health status
        if successful_checks == total_checks:
            self.print_status("\n🟢 System Status: HEALTHY", "SUCCESS")
        elif successful_checks >= total_checks * 0.8:
            self.print_status("\n🟡 System Status: DEGRADED", "WARNING")
        else:
            self.print_status("\n🔴 System Status: UNHEALTHY", "ERROR")
        
        # Recommendations
        http_results = results.get("HTTP Services", {})
        if not http_results.get("API", False):
            self.print_status("\nRecommendation: Start the API service", "INFO")
        
        docker_results = results.get("Docker Services", {})
        if not any(docker_results.values()):
            self.print_status("Recommendation: Start Docker services with 'docker-compose up -d'", "INFO")

def main():
    """Main function"""
    checker = DeploymentStatusChecker()
    
    try:
        healthy = checker.run_status_check()
        sys.exit(0 if healthy else 1)
        
    except KeyboardInterrupt:
        checker.print_status("\nStatus check interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        checker.print_status(f"Unexpected error during status check: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()