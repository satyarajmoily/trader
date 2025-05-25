"""
Docker Management for Bitcoin Predictor System

Provides utilities for managing Docker containers and deployments.
"""

import subprocess
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DockerManager:
    """
    Docker management utilities for Bitcoin Predictor deployment.
    
    Handles container lifecycle, health monitoring, and deployment automation.
    """
    
    def __init__(self, compose_file: str = "deployment/docker/docker-compose.yml"):
        self.compose_file = Path(compose_file)
        self.project_name = "bitcoin-predictor"
        
    def check_docker_availability(self) -> bool:
        """Check if Docker and Docker Compose are available."""
        try:
            # Check Docker
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, check=True)
            logger.info(f"Docker available: {result.stdout.strip()}")
            
            # Check Docker Compose
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True, check=True)
            logger.info(f"Docker Compose available: {result.stdout.strip()}")
            
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Docker not available: {e}")
            return False
    
    def build_images(self, service: Optional[str] = None) -> bool:
        """Build Docker images for services."""
        try:
            cmd = ['docker-compose', '-f', str(self.compose_file), 'build']
            if service:
                cmd.append(service)
            
            logger.info(f"Building Docker images...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info("Docker images built successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to build Docker images: {e.stderr}")
            return False
    
    def start_services(self, detached: bool = True) -> bool:
        """Start all services using Docker Compose."""
        try:
            cmd = ['docker-compose', '-f', str(self.compose_file), 'up']
            if detached:
                cmd.append('-d')
            
            logger.info("Starting services...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info("Services started successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start services: {e.stderr}")
            return False
    
    def stop_services(self) -> bool:
        """Stop all services."""
        try:
            cmd = ['docker-compose', '-f', str(self.compose_file), 'down']
            
            logger.info("Stopping services...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info("Services stopped successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop services: {e.stderr}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services."""
        try:
            cmd = ['docker-compose', '-f', str(self.compose_file), 'ps', '--format', 'json']
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse JSON output
            services = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        service_info = json.loads(line)
                        services.append(service_info)
                    except json.JSONDecodeError:
                        continue
            
            return {
                "timestamp": datetime.now().isoformat(),
                "total_services": len(services),
                "services": services
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get service status: {e.stderr}")
            return {"error": str(e)}
    
    def get_service_logs(self, service: str, lines: int = 100) -> str:
        """Get logs for a specific service."""
        try:
            cmd = ['docker-compose', '-f', str(self.compose_file), 
                   'logs', '--tail', str(lines), service]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get logs for {service}: {e.stderr}")
            return f"Error getting logs: {e.stderr}"
    
    def restart_service(self, service: str) -> bool:
        """Restart a specific service."""
        try:
            cmd = ['docker-compose', '-f', str(self.compose_file), 'restart', service]
            
            logger.info(f"Restarting service: {service}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"Service {service} restarted successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart {service}: {e.stderr}")
            return False
    
    def scale_service(self, service: str, replicas: int) -> bool:
        """Scale a service to specified number of replicas."""
        try:
            cmd = ['docker-compose', '-f', str(self.compose_file), 
                   'up', '-d', '--scale', f"{service}={replicas}"]
            
            logger.info(f"Scaling {service} to {replicas} replicas")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"Service {service} scaled successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to scale {service}: {e.stderr}")
            return False
    
    def cleanup_resources(self, volumes: bool = False) -> bool:
        """Clean up Docker resources."""
        try:
            cmd = ['docker-compose', '-f', str(self.compose_file), 'down']
            if volumes:
                cmd.append('--volumes')
            
            logger.info("Cleaning up Docker resources...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info("Docker resources cleaned up successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to cleanup resources: {e.stderr}")
            return False
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get resource usage statistics for containers."""
        try:
            cmd = ['docker', 'stats', '--no-stream', '--format', 
                   'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}']
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse the output
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return {"containers": []}
            
            headers = lines[0].split('\t')
            containers = []
            
            for line in lines[1:]:
                values = line.split('\t')
                if len(values) == len(headers):
                    container_stats = dict(zip(headers, values))
                    containers.append(container_stats)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "containers": containers
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get resource usage: {e.stderr}")
            return {"error": str(e)}
    
    def deploy_production(self) -> bool:
        """Deploy the full production stack."""
        logger.info("Starting production deployment...")
        
        # Check prerequisites
        if not self.check_docker_availability():
            return False
        
        if not self.compose_file.exists():
            logger.error(f"Compose file not found: {self.compose_file}")
            return False
        
        # Build and start services
        if not self.build_images():
            return False
        
        if not self.start_services():
            return False
        
        logger.info("Production deployment completed successfully")
        return True 