"""
Alerting System for Bitcoin Predictor

Basic alerting capabilities for production monitoring.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Alert data structure."""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    timestamp: datetime
    component: str
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'component': self.component,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

class AlertManager:
    """
    Basic alerting system for production monitoring.
    
    For Phase 5, this provides console-based alerting.
    Future phases could add email, Slack, PagerDuty integration.
    """
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.alert_counter = 0
        
        # Add default console handler
        self.add_alert_handler(self._console_alert_handler)
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler function."""
        self.alert_handlers.append(handler)
    
    def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        component: str
    ) -> Alert:
        """Create and trigger a new alert."""
        self.alert_counter += 1
        
        alert = Alert(
            id=f"alert_{self.alert_counter}_{int(datetime.now().timestamp())}",
            title=title,
            message=message,
            severity=severity,
            timestamp=datetime.now(),
            component=component
        )
        
        self.alerts.append(alert)
        
        # Notify handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
        
        logger.info(f"Alert created: {alert.id} - {title}")
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert by ID."""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"Alert resolved: {alert_id}")
                return True
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all unresolved alerts."""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts by severity level."""
        return [alert for alert in self.alerts if alert.severity == severity]
    
    def get_alerts_by_component(self, component: str) -> List[Alert]:
        """Get alerts for a specific component."""
        return [alert for alert in self.alerts if alert.component == component]
    
    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of alerts from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_alerts = [
            alert for alert in self.alerts
            if alert.timestamp >= cutoff_time
        ]
        
        active_alerts = [alert for alert in recent_alerts if not alert.resolved]
        
        summary = {
            "time_range_hours": hours,
            "total_alerts": len(recent_alerts),
            "active_alerts": len(active_alerts),
            "resolved_alerts": len(recent_alerts) - len(active_alerts),
            "by_severity": {},
            "by_component": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Group by severity
        for severity in AlertSeverity:
            severity_alerts = [
                alert for alert in recent_alerts
                if alert.severity == severity
            ]
            summary["by_severity"][severity.value] = {
                "total": len(severity_alerts),
                "active": len([a for a in severity_alerts if not a.resolved])
            }
        
        # Group by component
        components = set(alert.component for alert in recent_alerts)
        for component in components:
            component_alerts = [
                alert for alert in recent_alerts
                if alert.component == component
            ]
            summary["by_component"][component] = {
                "total": len(component_alerts),
                "active": len([a for a in component_alerts if not a.resolved])
            }
        
        return summary
    
    def _console_alert_handler(self, alert: Alert):
        """Default console alert handler."""
        # Choose emoji based on severity
        emoji_map = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨"
        }
        
        emoji = emoji_map.get(alert.severity, "📢")
        
        print(f"\n{emoji} ALERT [{alert.severity.value.upper()}] - {alert.component}")
        print(f"   Title: {alert.title}")
        print(f"   Message: {alert.message}")
        print(f"   Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   ID: {alert.id}")
        print()

# Convenience functions for common alert types
def alert_system_unhealthy(component: str, details: str):
    """Create system health alert."""
    manager = get_alert_manager()
    return manager.create_alert(
        title=f"{component} System Unhealthy",
        message=f"System component {component} is unhealthy: {details}",
        severity=AlertSeverity.ERROR,
        component=component
    )

def alert_high_error_rate(component: str, error_rate: float):
    """Create high error rate alert."""
    manager = get_alert_manager()
    return manager.create_alert(
        title=f"High Error Rate in {component}",
        message=f"Error rate is {error_rate:.1%} which exceeds threshold",
        severity=AlertSeverity.WARNING,
        component=component
    )

def alert_api_timeout(api_name: str, timeout_duration: float):
    """Create API timeout alert."""
    manager = get_alert_manager()
    return manager.create_alert(
        title=f"{api_name} API Timeout",
        message=f"API request timed out after {timeout_duration:.1f}s",
        severity=AlertSeverity.WARNING,
        component=f"{api_name}_api"
    )

def alert_prediction_failure(prediction_id: str, error: str):
    """Create prediction failure alert."""
    manager = get_alert_manager()
    return manager.create_alert(
        title="Prediction Generation Failed",
        message=f"Prediction {prediction_id} failed: {error}",
        severity=AlertSeverity.ERROR,
        component="core_system"
    )

def alert_self_correction_failure(attempt_count: int, error: str):
    """Create self-correction failure alert."""
    manager = get_alert_manager()
    severity = AlertSeverity.CRITICAL if attempt_count >= 3 else AlertSeverity.WARNING
    
    return manager.create_alert(
        title="Self-Correction Failed",
        message=f"Code self-correction failed after {attempt_count} attempts: {error}",
        severity=severity,
        component="agent_system"
    )

# Global alert manager instance
_alert_manager = None

def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager 