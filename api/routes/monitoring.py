from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from auth.dependencies import get_current_active_user
from database.models import UserDB
from core.cache_manager import cache_manager, simulation_cache
import psutil
import asyncio
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# 全局性能监控实例（将在主应用中设置）
performance_middleware = None

def set_performance_middleware(middleware):
    """
    设置性能监控中间件实例
    """
    global performance_middleware
    performance_middleware = middleware

@router.get("/system")
async def get_system_metrics(
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    获取系统性能指标
    """
    try:
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # 内存信息
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        
        # 网络信息
        network = psutil.net_io_counters()
        
        # 进程信息
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "frequency": {
                    "current": cpu_freq.current if cpu_freq else None,
                    "min": cpu_freq.min if cpu_freq else None,
                    "max": cpu_freq.max if cpu_freq else None
                }
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            },
            "process": {
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统指标失败: {str(e)}")

@router.get("/performance")
async def get_performance_metrics(
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    获取应用性能指标
    """
    try:
        if not performance_middleware:
            raise HTTPException(status_code=503, detail="性能监控未启用")
        
        stats = performance_middleware.get_performance_stats()
        return {
            "timestamp": datetime.now().isoformat(),
            "performance": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")

@router.get("/cache")
async def get_cache_metrics(
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    获取缓存指标
    """
    try:
        cache_stats = await cache_manager.get_stats()
        return {
            "timestamp": datetime.now().isoformat(),
            "cache": cache_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存指标失败: {str(e)}")

@router.get("/database")
async def get_database_metrics(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    获取数据库指标
    """
    try:
        # 获取数据库连接池信息
        engine = db.get_bind()
        pool = engine.pool
        
        # 执行一些基本查询来测试性能
        start_time = datetime.now()
        result = db.execute("SELECT 1").fetchone()
        query_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "database": {
                "connection_pool": {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalid": pool.invalid()
                },
                "query_performance": {
                    "test_query_time": query_time,
                    "status": "healthy" if query_time < 0.1 else "slow"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get database metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据库指标失败: {str(e)}")

@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        # 检查数据库
        try:
            from database.database import engine
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            health_status["services"]["database"] = "healthy"
        except Exception as e:
            health_status["services"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # 检查Redis缓存
        try:
            if cache_manager.redis_client:
                await cache_manager.redis_client.ping()
                health_status["services"]["redis"] = "healthy"
            else:
                health_status["services"]["redis"] = "not_configured"
        except Exception as e:
            health_status["services"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # 检查系统资源
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 90 or memory_percent > 90:
                health_status["services"]["system_resources"] = "high_usage"
                health_status["status"] = "degraded"
            else:
                health_status["services"]["system_resources"] = "healthy"
        except Exception as e:
            health_status["services"]["system_resources"] = f"check_failed: {str(e)}"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.post("/cache/clear")
async def clear_cache(
    pattern: str = "*",
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    清除缓存
    """
    try:
        cleared_count = await cache_manager.clear_pattern(pattern)
        return {
            "success": True,
            "message": f"已清除 {cleared_count} 个缓存项",
            "pattern": pattern,
            "cleared_count": cleared_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")

@router.get("/simulation/cache/{session_id}")
async def get_simulation_cache_info(
    session_id: str,
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    获取特定仿真的缓存信息
    """
    try:
        # 检查各种缓存
        config_cached = await simulation_cache.get_simulation_config(session_id) is not None
        results_cached = await simulation_cache.get_simulation_results(session_id) is not None
        
        return {
            "session_id": session_id,
            "cache_status": {
                "config_cached": config_cached,
                "results_cached": results_cached
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get simulation cache info: {e}")
        raise HTTPException(status_code=500, detail=f"获取仿真缓存信息失败: {str(e)}")

@router.delete("/simulation/cache/{session_id}")
async def clear_simulation_cache(
    session_id: str,
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    清除特定仿真的缓存
    """
    try:
        cleared_count = await simulation_cache.clear_simulation_cache(session_id)
        return {
            "success": True,
            "message": f"已清除仿真 {session_id} 的 {cleared_count} 个缓存项",
            "session_id": session_id,
            "cleared_count": cleared_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear simulation cache: {e}")
        raise HTTPException(status_code=500, detail=f"清除仿真缓存失败: {str(e)}")

@router.get("/alerts")
async def get_system_alerts(
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    获取系统告警信息
    """
    try:
        alerts = []
        
        # CPU使用率告警
        cpu_percent = psutil.cpu_percent()
        if cpu_percent > 80:
            alerts.append({
                "type": "cpu_high",
                "level": "warning" if cpu_percent < 90 else "critical",
                "message": f"CPU使用率过高: {cpu_percent:.1f}%",
                "value": cpu_percent,
                "threshold": 80
            })
        
        # 内存使用率告警
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > 80:
            alerts.append({
                "type": "memory_high",
                "level": "warning" if memory_percent < 90 else "critical",
                "message": f"内存使用率过高: {memory_percent:.1f}%",
                "value": memory_percent,
                "threshold": 80
            })
        
        # 磁盘使用率告警
        disk_percent = (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
        if disk_percent > 85:
            alerts.append({
                "type": "disk_high",
                "level": "warning" if disk_percent < 95 else "critical",
                "message": f"磁盘使用率过高: {disk_percent:.1f}%",
                "value": disk_percent,
                "threshold": 85
            })
        
        # 性能告警（如果有性能监控中间件）
        if performance_middleware:
            stats = performance_middleware.get_performance_stats()
            avg_response_time = stats['requests']['avg_response_time']
            if avg_response_time > 2.0:
                alerts.append({
                    "type": "response_time_high",
                    "level": "warning" if avg_response_time < 5.0 else "critical",
                    "message": f"平均响应时间过长: {avg_response_time:.2f}s",
                    "value": avg_response_time,
                    "threshold": 2.0
                })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "alert_count": len(alerts),
            "alerts": alerts
        }
        
    except Exception as e:
        logger.error(f"Failed to get system alerts: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统告警失败: {str(e)}")