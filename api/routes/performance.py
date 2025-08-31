"""性能监控和优化API路由

提供性能指标查询、系统监控、优化建议等接口。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..core.auth import get_current_user, require_permissions
from ..core.performance_monitor import (
    metrics_collector,
    system_monitor,
    app_monitor,
    alert_manager,
    performance_analyzer,
    get_performance_summary,
    check_system_health
)
from ..core.database_optimization import (
    db_optimizer,
    query_optimizer,
    db_monitor,
    get_db_stats,
    suggest_optimizations,
    optimize_database
)
from ..core.load_balancer import (
    load_balancer,
    get_load_balancer_stats
)
from ..core.cache import cache_manager
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/performance", tags=["performance"])


# Pydantic模型
class PerformanceMetricsResponse(BaseModel):
    """性能指标响应"""
    timestamp: datetime
    system: Dict[str, Any]
    application: Dict[str, Any]
    database: Dict[str, Any] = {}
    cache: Dict[str, Any] = {}
    load_balancer: Dict[str, Any] = {}
    alerts: List[Dict[str, Any]] = []


class SystemHealthResponse(BaseModel):
    """系统健康状态响应"""
    status: str = Field(..., description="健康状态: healthy, warning, critical")
    issues: List[str] = Field(default=[], description="发现的问题")
    metrics: Dict[str, Any]
    timestamp: datetime


class OptimizationSuggestion(BaseModel):
    """优化建议"""
    type: str = Field(..., description="建议类型")
    priority: str = Field(..., description="优先级: high, medium, low")
    description: str = Field(..., description="建议描述")
    impact: str = Field(..., description="预期影响")
    implementation: str = Field(..., description="实施方法")


class OptimizationResponse(BaseModel):
    """优化建议响应"""
    database: List[OptimizationSuggestion] = []
    cache: List[OptimizationSuggestion] = []
    performance: List[OptimizationSuggestion] = []
    infrastructure: List[OptimizationSuggestion] = []


class AlertRule(BaseModel):
    """告警规则"""
    name: str = Field(..., description="规则名称")
    metric: str = Field(..., description="监控指标")
    threshold: float = Field(..., description="阈值")
    operator: str = Field(..., description="比较操作符: >, <, >=, <=")
    message: str = Field(..., description="告警消息")
    enabled: bool = Field(default=True, description="是否启用")


@router.get("/metrics", response_model=PerformanceMetricsResponse)
async def get_metrics(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permissions(["performance:read"]))
):
    """获取性能指标"""
    try:
        # 获取基础性能摘要
        summary = await get_performance_summary()
        
        # 获取数据库统计
        db_stats = await get_db_stats()
        
        # 获取缓存统计
        cache_stats = await cache_manager.get_stats()
        
        # 获取负载均衡器统计
        lb_stats = await get_load_balancer_stats()
        
        return PerformanceMetricsResponse(
            timestamp=datetime.utcnow(),
            system=summary.get("system", {}),
            application=summary.get("application", {}),
            database=db_stats,
            cache=cache_stats,
            load_balancer=lb_stats,
            alerts=summary.get("alerts", [])
        )
    
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取性能指标失败")


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permissions(["performance:read"]))
):
    """获取系统健康状态"""
    try:
        health = await check_system_health()
        return SystemHealthResponse(**health)
    
    except Exception as e:
        logger.error(f"获取系统健康状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取系统健康状态失败")


@router.get("/prometheus")
async def get_prometheus_metrics(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permissions(["performance:read"]))
):
    """获取Prometheus格式的指标"""
    try:
        from prometheus_client import CONTENT_TYPE_LATEST
        metrics = metrics_collector.get_prometheus_metrics()
        return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)
    
    except Exception as e:
        logger.error(f"获取Prometheus指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取Prometheus指标失败")


@router.get("/trends")
async def get_performance_trends(
    hours: int = Query(24, ge=1, le=168, description="分析时间范围（小时）"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permissions(["performance:read"]))
):
    """获取性能趋势分析"""
    try:
        trends = performance_analyzer.analyze_trends(hours)
        return trends
    
    except Exception as e:
        logger.error(f"获取性能趋势失败: {e}")
        raise HTTPException(status_code=500, detail="获取性能趋势失败")


@router.get("/optimization/suggestions", response_model=OptimizationResponse)
async def get_optimization_suggestions(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permissions(["performance:read"]))
):
    """获取优化建议"""
    try:
        # 获取数据库优化建议
        db_suggestions = await suggest_optimizations()
        
        # 获取性能趋势分析
        trends = performance_analyzer.analyze_trends(24)
        
        # 生成优化建议
        suggestions = OptimizationResponse()
        
        # 数据库优化建议
        for suggestion in db_suggestions.get("index_suggestions", []):
            suggestions.database.append(OptimizationSuggestion(
                type="index",
                priority=suggestion.get("priority", "medium"),
                description=f"为表 {suggestion.get('table')} 的列 {suggestion.get('column', suggestion.get('constraint', ''))} 创建索引",
                impact="提高查询性能，减少响应时间",
                implementation="CREATE INDEX idx_name ON table_name (column_name)"
            ))
        
        # 缓存优化建议
        cache_stats = await cache_manager.get_stats()
        if cache_stats.get("hit_rate", 1.0) < 0.8:
            suggestions.cache.append(OptimizationSuggestion(
                type="cache_strategy",
                priority="high",
                description="缓存命中率较低，建议优化缓存策略",
                impact="提高缓存命中率，减少数据库查询",
                implementation="调整缓存TTL，增加预热策略，优化缓存键设计"
            ))
        
        # 性能优化建议
        for recommendation in trends.get("recommendations", []):
            suggestions.performance.append(OptimizationSuggestion(
                type="performance",
                priority="medium",
                description=recommendation,
                impact="改善系统性能和稳定性",
                implementation="根据具体情况调整系统配置或代码优化"
            ))
        
        # 基础设施优化建议
        system_trends = trends.get("system_trends", {})
        if system_trends.get("cpu", {}).get("average", 0) > 70:
            suggestions.infrastructure.append(OptimizationSuggestion(
                type="scaling",
                priority="high",
                description="CPU使用率持续较高，建议考虑水平扩展",
                impact="提高系统处理能力，改善响应时间",
                implementation="增加服务器实例或升级CPU配置"
            ))
        
        return suggestions
    
    except Exception as e:
        logger.error(f"获取优化建议失败: {e}")
        raise HTTPException(status_code=500, detail="获取优化建议失败")


@router.post("/optimization/database")
async def optimize_database_performance(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permissions(["performance:write"]))
):
    """优化数据库性能"""
    try:
        # 在后台执行数据库优化
        background_tasks.add_task(optimize_database)
        
        return {
            "message": "数据库优化任务已启动",
            "status": "started",
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"启动数据库优化失败: {e}")
        raise HTTPException(status_code=500, detail="启动数据库优化失败")


@router.post("/optimization/cache")
async def optimize_cache_performance(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permissions(["performance:write"]))
):
    """优化缓存性能"""
    try:
        # 清理过期缓存
        background_tasks.add_task(cache_manager.cleanup_expired)
        
        # 预热常用缓存
        background_tasks.add_task(cache_manager.warmup_cache)
        
        return {
            "message": "缓存优化任务已启动",
            "status": "started",
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"启动缓存优化失败: {e}")
        raise HTTPException(status_code=500, detail="启动缓存优化失败")


@router.get("/alerts")
async def get_alerts(
    active_only: bool = Query(True, description="只返回活跃告警"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permissions(["performance:read"]))
):
    """获取告警列表"""
    try:
        if active_only:
            alerts = alert_manager.get_active_alerts()
        else:
            alerts = alert_manager.alerts
        
        return {
            "alerts": alerts,
            "total": len(alerts),
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"获取告警列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取告警列表失败")


@router.post("/alerts/rules")
async def create_alert_rule(
    rule: AlertRule,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permissions(["performance:write"]))
):
    """创建告警规则"""
    try:
        # 创建条件函数
        def condition(metrics, threshold):
            metric_value = _get_metric_value(metrics, rule.metric)
            if rule.operator == ">":
                return metric_value > threshold
            elif rule.operator == "<":
                return metric_value < threshold
            elif rule.operator == ">=":
                return metric_value >= threshold
            elif rule.operator == "<=":
                return metric_value <= threshold
            return False
        
        alert_manager.add_rule(
            name=rule.name,
            condition=condition,
            threshold=rule.threshold,
            message=rule.message
        )
        
        return {
            "message": "告警规则创建成功",
            "rule_name": rule.name,
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"创建告警规则失败: {e}")
        raise HTTPException(status_code=500, detail="创建告警规则失败")


@router.get("/database/slow-queries")
async def get_slow_queries(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permissions(["performance:read"]))
):
    """获取慢查询列表"""
    try:
        slow_queries = await db_optimizer.analyze_slow_queries(limit)
        return {
            "slow_queries": slow_queries,
            "total": len(slow_queries),
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"获取慢查询列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取慢查询列表失败")


@router.get("/database/connections")
async def get_database_connections(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permissions(["performance:read"]))
):
    """获取数据库连接信息"""
    try:
        connections = await db_monitor.get_active_connections()
        pool_stats = await db_optimizer.get_connection_stats()
        
        return {
            "active_connections": connections,
            "pool_stats": pool_stats,
            "total_active": len(connections),
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"获取数据库连接信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取数据库连接信息失败")


@router.get("/load-balancer/stats")
async def get_load_balancer_statistics(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permissions(["performance:read"]))
):
    """获取负载均衡器统计信息"""
    try:
        stats = await get_load_balancer_stats()
        return {
            "stats": stats,
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"获取负载均衡器统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取负载均衡器统计失败")


@router.post("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="缓存键模式"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permissions(["performance:write"]))
):
    """清理缓存"""
    try:
        if pattern:
            cleared = await cache_manager.clear_pattern(pattern)
        else:
            cleared = await cache_manager.clear_all()
        
        return {
            "message": "缓存清理完成",
            "cleared_keys": cleared,
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"清理缓存失败: {e}")
        raise HTTPException(status_code=500, detail="清理缓存失败")


@router.get("/reports/daily")
async def get_daily_performance_report(
    date: Optional[str] = Query(None, description="日期 (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permissions(["performance:read"]))
):
    """获取日性能报告"""
    try:
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            target_date = datetime.utcnow().date()
        
        # 获取当天的性能数据
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = start_time + timedelta(days=1)
        
        # 生成报告
        report = {
            "date": target_date.isoformat(),
            "summary": {
                "total_requests": 0,
                "average_response_time": 0.0,
                "error_rate": 0.0,
                "peak_cpu": 0.0,
                "peak_memory": 0.0
            },
            "trends": performance_analyzer.analyze_trends(24),
            "alerts": [alert for alert in alert_manager.alerts if start_time <= alert["timestamp"] < end_time],
            "recommendations": []
        }
        
        return report
    
    except Exception as e:
        logger.error(f"生成日性能报告失败: {e}")
        raise HTTPException(status_code=500, detail="生成日性能报告失败")


def _get_metric_value(metrics: Dict[str, Any], metric_name: str) -> float:
    """从指标数据中提取指定指标的值"""
    metric_map = {
        "cpu_percent": lambda m: m.get("system", {}).get("cpu_percent", 0),
        "memory_percent": lambda m: m.get("system", {}).get("memory_percent", 0),
        "disk_percent": lambda m: m.get("system", {}).get("disk_percent", 0),
        "response_time": lambda m: m.get("application", {}).get("request_duration", 0),
        "error_count": lambda m: m.get("application", {}).get("error_count", 0),
        "active_connections": lambda m: m.get("application", {}).get("active_connections", 0),
        "cache_hit_rate": lambda m: m.get("application", {}).get("cache_hit_rate", 1.0)
    }
    
    extractor = metric_map.get(metric_name)
    if extractor:
        return extractor(metrics)
    
    return 0.0