"""
Health Checker for Bitcoin Predictor System

Monitors the health of both core prediction system and autonomous agent
through their clean interfaces without tight coupling.
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import requests
import os

logger = logging.getLogger(__name__)

@dataclass
class HealthStatus:
    """Health status for a system component."""
    component: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    timestamp: datetime
    response_time_ms: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

@dataclass
class SystemHealth:
    """Overall system health status."""
    overall_status: str
    timestamp: datetime
    components: List[HealthStatus]
    uptime_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'overall_status': self.overall_status,
            'timestamp': self.timestamp.isoformat(),
            'components': [asdict(comp) for comp in self.components],
            'uptime_seconds': self.uptime_seconds
        }

class HealthChecker:
    """
    Health monitoring system for Bitcoin Predictor.
    
    Monitors:
    - Core prediction system health
    - Autonomous agent system health  
    - External dependencies (APIs)
    - System resources
    """
    
    def __init__(self):
        self.start_time = datetime.now()
        self.health_history: List[SystemHealth] = []
        self.max_history = 1000  # Keep last 1000 health checks
        
    def check_core_system_health(self) -> HealthStatus:
        """Check health of the core prediction system."""
        start_time = time.time()
        
        try:
            # Try to import core system components (without instantiating abstract classes)
            from bitcoin_predictor import predictor, storage, data_loader
            from bitcoin_predictor.storage import PredictionStorage
            from bitcoin_predictor.data_loader import BitcoinDataLoader
            
            # Test basic component availability
            storage_instance = PredictionStorage()
            data_loader_instance = BitcoinDataLoader()
            
            # Quick functionality test - try to load some data
            test_data = data_loader_instance.load_data(source="mock_bitcoin_data.csv")
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                component="core_system",
                status="healthy",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details={
                    "modules_importable": True,
                    "storage_available": True,
                    "data_loader_available": True,
                    "test_data_available": len(test_data) > 0,
                    "data_points": len(test_data)
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Core system health check failed: {e}")
            
            return HealthStatus(
                component="core_system",
                status="unhealthy",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    def check_agent_system_health(self) -> HealthStatus:
        """Check health of the autonomous agent system."""
        start_time = time.time()
        
        try:
            # Try to import agent system components (without full initialization)
            from autonomous_agent import orchestrator, tools, chains
            from autonomous_agent.tools.bitcoin_api import BitcoinPriceTool
            from autonomous_agent.chains.evaluator import EvaluatorChain
            
            # Test basic component availability
            bitcoin_api = BitcoinPriceTool()
            evaluator = EvaluatorChain()
            
            # Test that key modules are importable
            from autonomous_agent.tools import code_validator, core_system_manager
            from autonomous_agent.chains import code_analyzer, code_improver
                
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                component="agent_system",
                status="healthy",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details={
                    "modules_importable": True,
                    "bitcoin_api_available": True,
                    "evaluator_available": True,
                    "code_tools_available": True,
                    "improvement_chains_available": True
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Agent system health check failed: {e}")
            
            return HealthStatus(
                component="agent_system", 
                status="unhealthy",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    def check_external_apis_health(self) -> List[HealthStatus]:
        """Check health of external API dependencies."""
        apis_to_check = [
            {
                'name': 'coingecko_api',
                'url': 'https://api.coingecko.com/api/v3/ping',
                'timeout': 10
            },
            {
                'name': 'github_api',
                'url': 'https://api.github.com/rate_limit',
                'timeout': 10,
                'headers': {'Authorization': f'token {os.getenv("GITHUB_TOKEN")}'} if os.getenv("GITHUB_TOKEN") else {}
            }
        ]
        
        health_statuses = []
        
        for api in apis_to_check:
            start_time = time.time()
            
            try:
                response = requests.get(
                    api['url'], 
                    timeout=api['timeout'],
                    headers=api.get('headers', {})
                )
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    status = "healthy"
                    details = {
                        "status_code": response.status_code,
                        "response_size": len(response.content)
                    }
                    error_message = None
                else:
                    status = "degraded"
                    details = {"status_code": response.status_code}
                    error_message = f"HTTP {response.status_code}"
                    
            except requests.exceptions.Timeout:
                response_time = (time.time() - start_time) * 1000
                status = "degraded"
                details = None
                error_message = "Request timeout"
                
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                status = "unhealthy"
                details = None
                error_message = str(e)
            
            health_statuses.append(HealthStatus(
                component=api['name'],
                status=status,
                timestamp=datetime.now(),
                response_time_ms=response_time,
                error_message=error_message,
                details=details
            ))
        
        return health_statuses
    
    def check_system_resources(self) -> HealthStatus:
        """Check system resource usage."""
        start_time = time.time()
        
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on resource usage
            status = "healthy"
            warnings = []
            
            if cpu_percent > 80:
                status = "degraded"
                warnings.append(f"High CPU usage: {cpu_percent}%")
                
            if memory.percent > 85:
                status = "degraded" if status == "healthy" else "unhealthy"
                warnings.append(f"High memory usage: {memory.percent}%")
                
            if disk.percent > 90:
                status = "degraded" if status == "healthy" else "unhealthy"
                warnings.append(f"High disk usage: {disk.percent}%")
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                component="system_resources",
                status=status,
                timestamp=datetime.now(),
                response_time_ms=response_time,
                error_message="; ".join(warnings) if warnings else None,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3)
                }
            )
            
        except ImportError:
            # psutil not available, provide basic check
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                component="system_resources",
                status="healthy",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details={"note": "psutil not available for detailed metrics"}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                component="system_resources",
                status="unhealthy", 
                timestamp=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    def perform_comprehensive_health_check(self) -> SystemHealth:
        """Perform a comprehensive health check of all system components."""
        logger.info("Starting comprehensive health check...")
        
        # Collect health status from all components
        health_statuses = []
        
        # Core system health
        health_statuses.append(self.check_core_system_health())
        
        # Agent system health  
        health_statuses.append(self.check_agent_system_health())
        
        # External APIs health
        health_statuses.extend(self.check_external_apis_health())
        
        # System resources health
        health_statuses.append(self.check_system_resources())
        
        # Determine overall system status
        unhealthy_count = sum(1 for status in health_statuses if status.status == "unhealthy")
        degraded_count = sum(1 for status in health_statuses if status.status == "degraded")
        
        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        # Calculate uptime
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        system_health = SystemHealth(
            overall_status=overall_status,
            timestamp=datetime.now(),
            components=health_statuses,
            uptime_seconds=uptime
        )
        
        # Store in history
        self.health_history.append(system_health)
        if len(self.health_history) > self.max_history:
            self.health_history.pop(0)
        
        logger.info(f"Health check completed. Overall status: {overall_status}")
        return system_health
    
    def get_health_summary(self, detailed: bool = False) -> Dict[str, Any]:
        """Get a summary of system health."""
        if not self.health_history:
            return {"error": "No health checks performed yet"}
        
        latest_health = self.health_history[-1]
        
        summary = {
            "overall_status": latest_health.overall_status,
            "timestamp": latest_health.timestamp.isoformat(),
            "uptime_hours": round(latest_health.uptime_seconds / 3600, 2),
            "components_summary": {
                "total": len(latest_health.components),
                "healthy": sum(1 for c in latest_health.components if c.status == "healthy"),
                "degraded": sum(1 for c in latest_health.components if c.status == "degraded"), 
                "unhealthy": sum(1 for c in latest_health.components if c.status == "unhealthy")
            }
        }
        
        if detailed:
            summary["components"] = [asdict(comp) for comp in latest_health.components]
            
            # Add health trends if we have history
            if len(self.health_history) > 1:
                recent_checks = self.health_history[-10:]  # Last 10 checks
                healthy_percentage = sum(
                    1 for check in recent_checks 
                    if check.overall_status == "healthy"
                ) / len(recent_checks) * 100
                
                summary["trends"] = {
                    "recent_healthy_percentage": round(healthy_percentage, 1),
                    "total_checks": len(self.health_history),
                    "recent_checks_analyzed": len(recent_checks)
                }
        
        return summary
    
    def export_health_history(self, filename: str = None) -> str:
        """Export health history to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_history_{timestamp}.json"
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_checks": len(self.health_history),
            "uptime_hours": round((datetime.now() - self.start_time).total_seconds() / 3600, 2),
            "health_history": [health.to_dict() for health in self.health_history]
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Health history exported to {filename}")
        return filename 