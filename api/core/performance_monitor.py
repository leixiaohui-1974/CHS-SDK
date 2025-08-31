"""性能监控模块

提供系统性能监控、指标收集、告警等功能。
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import json

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""


@dataclass
class SystemMetrics:
    """系统指标"""
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_percent: float
    disk_used: int
    disk_total: int
    network_sent: int
    network_recv: int
    load_average: List[float]
    timestamp: datetime


@dataclass
class ApplicationMetrics:
    """应用指标"""
    request_count: int
    request_duration: float
    error_count: int
    active_connections: int
    database_connections: int
    cache_hit_rate: float
    timestamp: datetime


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics: deque = deque(maxlen=1000)
        self.system_metrics: deque = deque(maxlen=100)
        self.app_metrics: deque = deque(maxlen=100)
        
        # Prometheus指标
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        
        self.active_connections = Gauge(
            'active_connections',
            'Number of active connections'
        )
        
        self.system_cpu = Gauge(
            'system_cpu_percent',
            'System CPU usage percentage'
        )
        
        self.system_memory = Gauge(
            'system_memory_percent',
            'System memory usage percentage'
        )
        
        self.database_connections = Gauge(
            'database_connections_active',
            'Number of active database connections'
        )
        
        self.cache_operations = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'result']
        )
    
    def add_metric(self, metric: PerformanceMetric):
        """添加性能指标"""
        self.metrics.append(metric)
    
    def add_system_metrics(self, metrics: SystemMetrics):
        """添加系统指标"""
        self.system_metrics.append(metrics)
        
        # 更新Prometheus指标
        self.system_cpu.set(metrics.cpu_percent)
        self.system_memory.set(metrics.memory_percent)
    
    def add_app_metrics(self, metrics: ApplicationMetrics):
        """添加应用指标"""
        self.app_metrics.append(metrics)
        
        # 更新Prometheus指标
        self.active_connections.set(metrics.active_connections)
        self.database_connections.set(metrics.database_connections)
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """记录请求指标"""
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_cache_operation(self, operation: str, result: str):
        """记录缓存操作"""
        self.cache_operations.labels(
            operation=operation,
            result=result
        ).inc()
    
    def get_metrics(self, limit: int = 100) -> List[PerformanceMetric]:
        """获取性能指标"""
        return list(self.metrics)[-limit:]
    
    def get_system_metrics(self, limit: int = 10) -> List[SystemMetrics]:
        """获取系统指标"""
        return list(self.system_metrics)[-limit:]
    
    def get_app_metrics(self, limit: int = 10) -> List[ApplicationMetrics]:
        """获取应用指标"""
        return list(self.app_metrics)[-limit:]
    
    def get_prometheus_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        return generate_latest()


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, collector: MetricsCollector, interval: int = 30):
        self.collector = collector
        self.interval = interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_network_stats = None
    
    async def start(self):
        """启动系统监控"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("系统监控器已启动")
    
    async def stop(self):
        """停止系统监控"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("系统监控器已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                metrics = await self._collect_system_metrics()
                self.collector.add_system_metrics(metrics)
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"系统监控错误: {e}")
                await asyncio.sleep(5)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        
        # 网络统计
        network = psutil.net_io_counters()
        
        # 负载平均值
        try:
            load_avg = psutil.getloadavg()
        except AttributeError:
            # Windows系统不支持getloadavg
            load_avg = [0.0, 0.0, 0.0]
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used=memory.used,
            memory_total=memory.total,
            disk_percent=disk.percent,
            disk_used=disk.used,
            disk_total=disk.total,
            network_sent=network.bytes_sent,
            network_recv=network.bytes_recv,
            load_average=list(load_avg),
            timestamp=datetime.utcnow()
        )


class ApplicationMonitor:
    """应用监控器"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.request_stats = defaultdict(int)
        self.error_stats = defaultdict(int)
        self.response_times = deque(maxlen=1000)
        self._active_connections = 0
        self._database_connections = 0
        self._cache_stats = {"hits": 0, "misses": 0}
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """记录请求"""
        self.collector.record_request(method, endpoint, status_code, duration)
        
        # 更新内部统计
        self.request_stats[f"{method}:{endpoint}"] += 1
        if status_code >= 400:
            self.error_stats[f"{method}:{endpoint}"] += 1
        
        self.response_times.append(duration)
    
    def increment_connections(self):
        """增加活跃连接数"""
        self._active_connections += 1
    
    def decrement_connections(self):
        """减少活跃连接数"""
        self._active_connections = max(0, self._active_connections - 1)
    
    def set_database_connections(self, count: int):
        """设置数据库连接数"""
        self._database_connections = count
    
    def record_cache_hit(self):
        """记录缓存命中"""
        self._cache_stats["hits"] += 1
        self.collector.record_cache_operation("get", "hit")
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        self._cache_stats["misses"] += 1
        self.collector.record_cache_operation("get", "miss")
    
    def get_current_metrics(self) -> ApplicationMetrics:
        """获取当前应用指标"""
        total_requests = sum(self.request_stats.values())
        total_errors = sum(self.error_stats.values())
        
        avg_response_time = 0.0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
        
        cache_hit_rate = 0.0
        total_cache_ops = self._cache_stats["hits"] + self._cache_stats["misses"]
        if total_cache_ops > 0:
            cache_hit_rate = self._cache_stats["hits"] / total_cache_ops
        
        return ApplicationMetrics(
            request_count=total_requests,
            request_duration=avg_response_time,
            error_count=total_errors,
            active_connections=self._active_connections,
            database_connections=self._database_connections,
            cache_hit_rate=cache_hit_rate,
            timestamp=datetime.utcnow()
        )


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app, monitor: ApplicationMonitor):
        super().__init__(app)
        self.monitor = monitor
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 增加活跃连接数
        self.monitor.increment_connections()
        
        try:
            response = await call_next(request)
            
            # 记录请求指标
            duration = time.time() - start_time
            self.monitor.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=duration
            )
            
            # 添加性能头
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            return response
        
        except Exception as e:
            # 记录错误
            duration = time.time() - start_time
            self.monitor.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                duration=duration
            )
            raise e
        
        finally:
            # 减少活跃连接数
            self.monitor.decrement_connections()


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.rules: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
        self.alert_handlers: List[Callable] = []
    
    def add_rule(self, name: str, condition: Callable, threshold: float, message: str):
        """添加告警规则"""
        self.rules.append({
            "name": name,
            "condition": condition,
            "threshold": threshold,
            "message": message,
            "triggered": False,
            "last_triggered": None
        })
    
    def add_alert_handler(self, handler: Callable):
        """添加告警处理器"""
        self.alert_handlers.append(handler)
    
    async def check_alerts(self, metrics: Dict[str, Any]):
        """检查告警"""
        for rule in self.rules:
            try:
                if rule["condition"](metrics, rule["threshold"]):
                    if not rule["triggered"]:
                        # 触发告警
                        alert = {
                            "name": rule["name"],
                            "message": rule["message"],
                            "threshold": rule["threshold"],
                            "current_value": self._get_metric_value(metrics, rule["name"]),
                            "timestamp": datetime.utcnow(),
                            "severity": "warning"
                        }
                        
                        self.alerts.append(alert)
                        rule["triggered"] = True
                        rule["last_triggered"] = datetime.utcnow()
                        
                        # 通知告警处理器
                        for handler in self.alert_handlers:
                            try:
                                await handler(alert)
                            except Exception as e:
                                logger.error(f"告警处理器错误: {e}")
                else:
                    # 恢复正常
                    if rule["triggered"]:
                        rule["triggered"] = False
                        logger.info(f"告警 {rule['name']} 已恢复")
            
            except Exception as e:
                logger.error(f"检查告警规则 {rule['name']} 失败: {e}")
    
    def _get_metric_value(self, metrics: Dict[str, Any], metric_name: str) -> float:
        """获取指标值"""
        # 这里可以根据指标名称从metrics中提取对应的值
        if "cpu" in metric_name.lower():
            return metrics.get("system", {}).get("cpu_percent", 0)
        elif "memory" in metric_name.lower():
            return metrics.get("system", {}).get("memory_percent", 0)
        elif "response_time" in metric_name.lower():
            return metrics.get("application", {}).get("request_duration", 0)
        return 0.0
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃告警"""
        return [alert for alert in self.alerts if alert["timestamp"] > datetime.utcnow() - timedelta(hours=24)]


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    def analyze_trends(self, hours: int = 24) -> Dict[str, Any]:
        """分析性能趋势"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 分析系统指标趋势
        system_metrics = [
            m for m in self.collector.get_system_metrics(1000)
            if m.timestamp > cutoff_time
        ]
        
        # 分析应用指标趋势
        app_metrics = [
            m for m in self.collector.get_app_metrics(1000)
            if m.timestamp > cutoff_time
        ]
        
        analysis = {
            "period": f"{hours} hours",
            "system_trends": self._analyze_system_trends(system_metrics),
            "application_trends": self._analyze_app_trends(app_metrics),
            "recommendations": self._generate_recommendations(system_metrics, app_metrics)
        }
        
        return analysis
    
    def _analyze_system_trends(self, metrics: List[SystemMetrics]) -> Dict[str, Any]:
        """分析系统趋势"""
        if not metrics:
            return {}
        
        cpu_values = [m.cpu_percent for m in metrics]
        memory_values = [m.memory_percent for m in metrics]
        
        return {
            "cpu": {
                "average": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
                "trend": "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing"
            },
            "memory": {
                "average": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
                "trend": "increasing" if memory_values[-1] > memory_values[0] else "decreasing"
            }
        }
    
    def _analyze_app_trends(self, metrics: List[ApplicationMetrics]) -> Dict[str, Any]:
        """分析应用趋势"""
        if not metrics:
            return {}
        
        response_times = [m.request_duration for m in metrics]
        error_counts = [m.error_count for m in metrics]
        
        return {
            "response_time": {
                "average": sum(response_times) / len(response_times),
                "max": max(response_times),
                "min": min(response_times),
                "trend": "increasing" if response_times[-1] > response_times[0] else "decreasing"
            },
            "errors": {
                "total": sum(error_counts),
                "trend": "increasing" if error_counts[-1] > error_counts[0] else "decreasing"
            }
        }
    
    def _generate_recommendations(self, system_metrics: List[SystemMetrics], app_metrics: List[ApplicationMetrics]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if system_metrics:
            avg_cpu = sum(m.cpu_percent for m in system_metrics) / len(system_metrics)
            avg_memory = sum(m.memory_percent for m in system_metrics) / len(system_metrics)
            
            if avg_cpu > 80:
                recommendations.append("CPU使用率过高，建议优化计算密集型操作或增加CPU资源")
            
            if avg_memory > 85:
                recommendations.append("内存使用率过高，建议检查内存泄漏或增加内存资源")
        
        if app_metrics:
            avg_response_time = sum(m.request_duration for m in app_metrics) / len(app_metrics)
            
            if avg_response_time > 1.0:
                recommendations.append("响应时间过长，建议优化数据库查询和缓存策略")
        
        return recommendations


# 全局实例
metrics_collector = MetricsCollector()
system_monitor = SystemMonitor(metrics_collector)
app_monitor = ApplicationMonitor(metrics_collector)
alert_manager = AlertManager()
performance_analyzer = PerformanceAnalyzer(metrics_collector)


# 设置默认告警规则
alert_manager.add_rule(
    "high_cpu",
    lambda metrics, threshold: metrics.get("system", {}).get("cpu_percent", 0) > threshold,
    80.0,
    "CPU使用率过高"
)

alert_manager.add_rule(
    "high_memory",
    lambda metrics, threshold: metrics.get("system", {}).get("memory_percent", 0) > threshold,
    85.0,
    "内存使用率过高"
)

alert_manager.add_rule(
    "slow_response",
    lambda metrics, threshold: metrics.get("application", {}).get("request_duration", 0) > threshold,
    2.0,
    "响应时间过长"
)


# 便捷函数
async def start_monitoring():
    """启动监控"""
    await system_monitor.start()
    logger.info("性能监控已启动")


async def stop_monitoring():
    """停止监控"""
    await system_monitor.stop()
    logger.info("性能监控已停止")


async def get_performance_summary() -> Dict[str, Any]:
    """获取性能摘要"""
    system_metrics = system_monitor.collector.get_system_metrics(1)
    app_metrics = app_monitor.get_current_metrics()
    
    current_system = system_metrics[0] if system_metrics else None
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_percent": current_system.cpu_percent if current_system else 0,
            "memory_percent": current_system.memory_percent if current_system else 0,
            "disk_percent": current_system.disk_percent if current_system else 0,
            "load_average": current_system.load_average if current_system else [0, 0, 0]
        } if current_system else {},
        "application": {
            "request_count": app_metrics.request_count,
            "request_duration": app_metrics.request_duration,
            "error_count": app_metrics.error_count,
            "active_connections": app_metrics.active_connections,
            "cache_hit_rate": app_metrics.cache_hit_rate
        },
        "alerts": alert_manager.get_active_alerts()
    }


async def check_system_health() -> Dict[str, Any]:
    """检查系统健康状态"""
    summary = await get_performance_summary()
    
    # 检查告警
    await alert_manager.check_alerts(summary)
    
    # 生成健康状态
    health_status = "healthy"
    issues = []
    
    system = summary.get("system", {})
    if system.get("cpu_percent", 0) > 90:
        health_status = "critical"
        issues.append("CPU使用率过高")
    elif system.get("cpu_percent", 0) > 80:
        health_status = "warning"
        issues.append("CPU使用率较高")
    
    if system.get("memory_percent", 0) > 95:
        health_status = "critical"
        issues.append("内存使用率过高")
    elif system.get("memory_percent", 0) > 85:
        health_status = "warning"
        issues.append("内存使用率较高")
    
    app = summary.get("application", {})
    if app.get("request_duration", 0) > 3.0:
        health_status = "warning"
        issues.append("响应时间过长")
    
    return {
        "status": health_status,
        "issues": issues,
        "metrics": summary,
        "timestamp": datetime.utcnow().isoformat()
    }