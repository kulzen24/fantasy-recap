"""
Natural Language Query System Monitoring
Provides health checks, metrics collection, and performance monitoring
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import asyncio
from statistics import mean, median

logger = logging.getLogger(__name__)

@dataclass
class QueryMetrics:
    """Metrics for a single query execution"""
    query_id: str
    user_id: str
    league_id: str
    query_type: str
    intent: str
    confidence: float
    response_time_ms: int
    success: bool
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class SystemHealth:
    """Overall system health status"""
    status: str  # "healthy", "degraded", "unhealthy"
    components: Dict[str, str]
    metrics: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class NLQMonitor:
    """Monitor for Natural Language Query system performance and health"""
    
    def __init__(self, max_metrics_history: int = 1000):
        self.max_metrics_history = max_metrics_history
        self.query_metrics: deque = deque(maxlen=max_metrics_history)
        self.component_status: Dict[str, str] = {
            "llm_provider": "unknown",
            "fantasy_service": "unknown", 
            "query_parser": "unknown",
            "analytics_service": "unknown"
        }
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.last_health_check = None
    
    def record_query_metrics(self, metrics: QueryMetrics):
        """Record metrics for a query execution"""
        self.query_metrics.append(metrics)
        
        # Update error counts
        if not metrics.success and metrics.error:
            self.error_counts[metrics.error] += 1
        
        logger.info(
            f"Query metrics recorded: {metrics.query_id} "
            f"({metrics.response_time_ms}ms, success={metrics.success})"
        )
    
    def update_component_status(self, component: str, status: str):
        """Update the status of a system component"""
        if component in self.component_status:
            self.component_status[component] = status
            logger.info(f"Component {component} status updated to {status}")
    
    def get_current_metrics(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get current system metrics within a time window"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        recent_metrics = [
            m for m in self.query_metrics 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {
                "total_queries": 0,
                "success_rate": 0.0,
                "avg_response_time_ms": 0,
                "median_response_time_ms": 0,
                "error_rate": 0.0,
                "popular_query_types": [],
                "avg_confidence": 0.0
            }
        
        # Calculate metrics
        total_queries = len(recent_metrics)
        successful_queries = [m for m in recent_metrics if m.success]
        success_rate = len(successful_queries) / total_queries
        
        response_times = [m.response_time_ms for m in recent_metrics]
        avg_response_time = mean(response_times)
        median_response_time = median(response_times)
        
        confidences = [m.confidence for m in recent_metrics if m.success]
        avg_confidence = mean(confidences) if confidences else 0.0
        
        # Query type popularity
        query_type_counts = defaultdict(int)
        for m in recent_metrics:
            query_type_counts[m.query_type] += 1
        
        popular_types = sorted(
            query_type_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_queries": total_queries,
            "success_rate": success_rate,
            "avg_response_time_ms": round(avg_response_time, 2),
            "median_response_time_ms": round(median_response_time, 2),
            "error_rate": 1.0 - success_rate,
            "popular_query_types": [
                {"type": qtype, "count": count, "percentage": round(count/total_queries*100, 1)}
                for qtype, count in popular_types
            ],
            "avg_confidence": round(avg_confidence, 3)
        }
    
    def get_error_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get summary of recent errors"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        recent_errors = [
            m for m in self.query_metrics 
            if not m.success and m.timestamp >= cutoff_time
        ]
        
        error_counts = defaultdict(int)
        for error_metric in recent_errors:
            if error_metric.error:
                error_counts[error_metric.error] += 1
        
        total_errors = len(recent_errors)
        
        return {
            "total_errors": total_errors,
            "error_types": dict(error_counts),
            "most_common_error": max(error_counts.items(), key=lambda x: x[1])[0] if error_counts else None
        }
    
    async def check_component_health(self) -> Dict[str, str]:
        """Check health of all system components"""
        health_status = {}
        
        # Check LLM Provider
        try:
            # This would ping the LLM provider in a real implementation
            await asyncio.sleep(0.1)  # Simulate health check
            health_status["llm_provider"] = "operational"
        except Exception as e:
            logger.error(f"LLM provider health check failed: {e}")
            health_status["llm_provider"] = "error"
        
        # Check Fantasy Service
        try:
            # This would ping the fantasy service in a real implementation
            await asyncio.sleep(0.1)  # Simulate health check
            health_status["fantasy_service"] = "operational"
        except Exception as e:
            logger.error(f"Fantasy service health check failed: {e}")
            health_status["fantasy_service"] = "error"
        
        # Check Query Parser
        try:
            # Query parser is internal, check if it's responsive
            health_status["query_parser"] = "operational"
        except Exception as e:
            logger.error(f"Query parser health check failed: {e}")
            health_status["query_parser"] = "error"
        
        # Check Analytics Service
        try:
            # Analytics service is internal, check if it's responsive
            health_status["analytics_service"] = "operational"
        except Exception as e:
            logger.error(f"Analytics service health check failed: {e}")
            health_status["analytics_service"] = "error"
        
        # Update component status
        for component, status in health_status.items():
            self.update_component_status(component, status)
        
        return health_status
    
    async def get_system_health(self) -> SystemHealth:
        """Get overall system health status"""
        # Check component health
        component_health = await self.check_component_health()
        
        # Get current metrics
        current_metrics = self.get_current_metrics(15)  # Last 15 minutes
        error_summary = self.get_error_summary(15)
        
        # Determine overall status
        if all(status == "operational" for status in component_health.values()):
            if current_metrics["success_rate"] >= 0.95:
                overall_status = "healthy"
            elif current_metrics["success_rate"] >= 0.80:
                overall_status = "degraded"
            else:
                overall_status = "unhealthy"
        else:
            overall_status = "unhealthy"
        
        # Compile health data
        health = SystemHealth(
            status=overall_status,
            components=component_health,
            metrics={
                "performance": current_metrics,
                "errors": error_summary,
                "uptime_status": "operational" if overall_status != "unhealthy" else "degraded"
            }
        )
        
        self.last_health_check = health.timestamp
        return health
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over time"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        metrics_in_window = [
            m for m in self.query_metrics 
            if m.timestamp >= cutoff_time
        ]
        
        if not metrics_in_window:
            return {"trends": "insufficient_data"}
        
        # Group by hour
        hourly_data = defaultdict(list)
        for metric in metrics_in_window:
            hour_key = metric.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_data[hour_key].append(metric)
        
        trends = []
        for hour, hour_metrics in sorted(hourly_data.items()):
            if hour_metrics:
                success_rate = len([m for m in hour_metrics if m.success]) / len(hour_metrics)
                avg_response_time = mean([m.response_time_ms for m in hour_metrics])
                
                trends.append({
                    "hour": hour.isoformat(),
                    "query_count": len(hour_metrics),
                    "success_rate": round(success_rate, 3),
                    "avg_response_time_ms": round(avg_response_time, 2)
                })
        
        return {
            "time_window_hours": hours,
            "trends": trends,
            "total_queries_in_window": len(metrics_in_window)
        }
    
    def get_alert_conditions(self) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        alerts = []
        current_metrics = self.get_current_metrics(10)  # Last 10 minutes
        
        # High error rate alert
        if current_metrics["error_rate"] > 0.20:  # 20% error rate
            alerts.append({
                "type": "high_error_rate",
                "severity": "warning",
                "message": f"Error rate is {current_metrics['error_rate']:.1%} (threshold: 20%)",
                "value": current_metrics["error_rate"]
            })
        
        # Slow response time alert
        if current_metrics["avg_response_time_ms"] > 3000:  # 3 seconds
            alerts.append({
                "type": "slow_response_time",
                "severity": "warning", 
                "message": f"Average response time is {current_metrics['avg_response_time_ms']}ms (threshold: 3000ms)",
                "value": current_metrics["avg_response_time_ms"]
            })
        
        # Low confidence alert
        if current_metrics["avg_confidence"] < 0.6:  # 60% confidence
            alerts.append({
                "type": "low_confidence",
                "severity": "info",
                "message": f"Average confidence is {current_metrics['avg_confidence']:.1%} (threshold: 60%)",
                "value": current_metrics["avg_confidence"]
            })
        
        # Component health alerts
        for component, status in self.component_status.items():
            if status == "error":
                alerts.append({
                    "type": "component_failure",
                    "severity": "critical",
                    "message": f"Component {component} is in error state",
                    "component": component
                })
        
        return alerts


# Global monitor instance
nlq_monitor = NLQMonitor()


def record_query_execution(query_id: str, user_id: str, league_id: str, 
                          query_type: str, intent: str, confidence: float,
                          response_time_ms: int, success: bool, error: str = None):
    """Convenience function to record query execution metrics"""
    metrics = QueryMetrics(
        query_id=query_id,
        user_id=user_id,
        league_id=league_id,
        query_type=query_type,
        intent=intent,
        confidence=confidence,
        response_time_ms=response_time_ms,
        success=success,
        error=error
    )
    nlq_monitor.record_query_metrics(metrics)


async def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system status for monitoring dashboards"""
    health = await nlq_monitor.get_system_health()
    alerts = nlq_monitor.get_alert_conditions()
    trends = nlq_monitor.get_performance_trends(24)
    
    return {
        "health": asdict(health),
        "alerts": alerts,
        "trends": trends,
        "last_updated": datetime.utcnow().isoformat()
    }
