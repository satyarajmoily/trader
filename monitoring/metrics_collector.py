"""
Metrics Collector for Bitcoin Predictor System

Collects and stores performance metrics from both core and agent systems.
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class Metric:
    """Individual metric data point."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags or {}
        }

class MetricsCollector:
    """
    Collects performance metrics from the Bitcoin prediction system.
    
    Metrics include:
    - Prediction latency
    - API response times
    - System resource usage
    - Self-correction success rates
    - GitHub API usage
    """
    
    def __init__(self, max_metrics: int = 10000):
        self.metrics: deque = deque(maxlen=max_metrics)
        self.start_time = datetime.now()
        
        # Metric aggregations
        self.aggregations = defaultdict(list)
        self.counters = defaultdict(int)
        
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric data point."""
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        
        self.metrics.append(metric)
        self.aggregations[name].append(value)
        
        # Keep only recent values for aggregation (last 1000)
        if len(self.aggregations[name]) > 1000:
            self.aggregations[name] = self.aggregations[name][-1000:]
        
        logger.debug(f"Recorded metric: {name}={value} {tags}")
    
    def increment_counter(self, name: str, tags: Dict[str, str] = None):
        """Increment a counter metric."""
        counter_key = f"{name}:{json.dumps(tags or {}, sort_keys=True)}"
        self.counters[counter_key] += 1
        
        self.record_metric(name, self.counters[counter_key], tags)
    
    def record_duration(self, name: str, start_time: float, tags: Dict[str, str] = None):
        """Record a duration metric from start time."""
        duration_ms = (time.time() - start_time) * 1000
        self.record_metric(f"{name}_duration_ms", duration_ms, tags)
        return duration_ms
    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get summary of metrics from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter recent metrics
        recent_metrics = [
            m for m in self.metrics 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": f"No metrics found in last {hours} hours"}
        
        # Group by metric name
        grouped_metrics = defaultdict(list)
        for metric in recent_metrics:
            grouped_metrics[metric.name].append(metric.value)
        
        # Calculate aggregations
        summary = {
            "time_range_hours": hours,
            "total_metrics": len(recent_metrics),
            "unique_metric_types": len(grouped_metrics),
            "timestamp": datetime.now().isoformat(),
            "metrics": {}
        }
        
        for name, values in grouped_metrics.items():
            if values:
                summary["metrics"][name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "latest": values[-1] if values else None
                }
        
        return summary
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """Get performance insights and trends."""
        summary_1h = self.get_metrics_summary(hours=1)
        summary_24h = self.get_metrics_summary(hours=24)
        
        insights = {
            "timestamp": datetime.now().isoformat(),
            "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
            "insights": []
        }
        
        # Analyze prediction performance
        if "prediction_duration_ms" in summary_1h.get("metrics", {}):
            pred_metrics = summary_1h["metrics"]["prediction_duration_ms"]
            if pred_metrics["avg"] > 5000:  # > 5 seconds
                insights["insights"].append({
                    "type": "warning",
                    "message": f"Slow prediction performance: {pred_metrics['avg']:.1f}ms average"
                })
            elif pred_metrics["avg"] < 1000:  # < 1 second
                insights["insights"].append({
                    "type": "good",
                    "message": f"Excellent prediction performance: {pred_metrics['avg']:.1f}ms average"
                })
        
        # Analyze API performance
        api_metrics = [
            name for name in summary_1h.get("metrics", {}).keys()
            if "api_" in name and "duration_ms" in name
        ]
        
        for api_metric in api_metrics:
            api_data = summary_1h["metrics"][api_metric]
            if api_data["avg"] > 10000:  # > 10 seconds
                insights["insights"].append({
                    "type": "warning", 
                    "message": f"Slow API performance for {api_metric}: {api_data['avg']:.1f}ms"
                })
        
        # Analyze error rates
        error_metrics = [
            name for name in summary_1h.get("metrics", {}).keys()
            if "error" in name.lower()
        ]
        
        for error_metric in error_metrics:
            error_data = summary_1h["metrics"][error_metric]
            if error_data["latest"] > 0:
                insights["insights"].append({
                    "type": "error",
                    "message": f"Errors detected in {error_metric}: {error_data['latest']}"
                })
        
        return insights
    
    def export_metrics(self, filename: str = None, hours: int = 24) -> str:
        """Export metrics to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_export_{timestamp}.json"
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter and export metrics
        export_metrics = [
            metric.to_dict() for metric in self.metrics
            if metric.timestamp >= cutoff_time
        ]
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "time_range_hours": hours,
            "total_metrics": len(export_metrics),
            "metrics": export_metrics,
            "summary": self.get_metrics_summary(hours),
            "insights": self.get_performance_insights()
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Metrics exported to {filename}")
        return filename

# Global metrics collector instance
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

# Convenience functions for recording metrics
def record_metric(name: str, value: float, tags: Dict[str, str] = None):
    """Record a metric using the global collector."""
    get_metrics_collector().record_metric(name, value, tags)

def increment_counter(name: str, tags: Dict[str, str] = None):
    """Increment a counter using the global collector."""
    get_metrics_collector().increment_counter(name, tags)

def record_duration(name: str, start_time: float, tags: Dict[str, str] = None) -> float:
    """Record a duration using the global collector."""
    return get_metrics_collector().record_duration(name, start_time, tags)

# Context manager for timing operations
class MetricTimer:
    """Context manager for timing operations."""
    
    def __init__(self, metric_name: str, tags: Dict[str, str] = None):
        self.metric_name = metric_name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            record_duration(self.metric_name, self.start_time, self.tags) 