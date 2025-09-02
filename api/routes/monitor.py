#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket监控API路由

提供监控服务的控制和状态查询接口：
1. 启动/停止监控服务
2. 获取系统状态和指标
3. 获取仿真历史数据
4. 配置监控参数
5. 获取实时统计信息
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from services.websocket_monitor import websocket_monitor
from websocket.connection_manager import connection_manager
from auth.auth_handler import get_current_user
from models.user_models import User
from models.response_models import StandardResponse

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/api/monitor",
    tags=["监控服务"],
    responses={404: {"description": "Not found"}}
)

@router.post("/start", response_model=StandardResponse)
async def start_monitoring(
    current_user: User = Depends(get_current_user)
):
    """
    启动WebSocket监控服务
    
    需要管理员权限
    """
    try:
        # 检查用户权限
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="需要管理员权限才能启动监控服务"
            )
        
        # 启动监控服务
        await websocket_monitor.start_monitoring()
        
        logger.info(f"用户 {current_user.username} 启动了WebSocket监控服务")
        
        return StandardResponse(
            success=True,
            message="WebSocket监控服务已启动",
            data={
                "started_at": datetime.now().isoformat(),
                "started_by": current_user.username
            }
        )
        
    except Exception as e:
        logger.error(f"启动监控服务失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"启动监控服务失败: {str(e)}"
        )

@router.post("/stop", response_model=StandardResponse)
async def stop_monitoring(
    current_user: User = Depends(get_current_user)
):
    """
    停止WebSocket监控服务
    
    需要管理员权限
    """
    try:
        # 检查用户权限
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="需要管理员权限才能停止监控服务"
            )
        
        # 停止监控服务
        await websocket_monitor.stop_monitoring()
        
        logger.info(f"用户 {current_user.username} 停止了WebSocket监控服务")
        
        return StandardResponse(
            success=True,
            message="WebSocket监控服务已停止",
            data={
                "stopped_at": datetime.now().isoformat(),
                "stopped_by": current_user.username
            }
        )
        
    except Exception as e:
        logger.error(f"停止监控服务失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"停止监控服务失败: {str(e)}"
        )

@router.get("/status", response_model=StandardResponse)
async def get_monitoring_status(
    current_user: User = Depends(get_current_user)
):
    """
    获取监控服务状态
    """
    try:
        status = await websocket_monitor.get_system_status()
        
        return StandardResponse(
            success=True,
            message="获取监控状态成功",
            data=status
        )
        
    except Exception as e:
        logger.error(f"获取监控状态失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取监控状态失败: {str(e)}"
        )

@router.get("/system-metrics", response_model=StandardResponse)
async def get_system_metrics(
    limit: int = Query(100, ge=1, le=1000, description="返回的数据点数量"),
    current_user: User = Depends(get_current_user)
):
    """
    获取系统指标历史数据
    """
    try:
        # 获取最近的系统指标
        metrics_history = websocket_monitor.system_metrics_history[-limit:]
        
        data = {
            "metrics": [{
                "timestamp": m.timestamp,
                "cpu_percent": m.cpu_percent,
                "memory_percent": m.memory_percent,
                "memory_available_gb": m.memory_available_gb,
                "disk_usage_percent": m.disk_usage_percent,
                "network_io_bytes_sent": m.network_io_bytes_sent,
                "network_io_bytes_recv": m.network_io_bytes_recv,
                "active_processes": m.active_processes,
                "simulation_processes": m.simulation_processes
            } for m in metrics_history],
            "total_count": len(metrics_history),
            "latest_timestamp": metrics_history[-1].timestamp if metrics_history else None
        }
        
        return StandardResponse(
            success=True,
            message="获取系统指标成功",
            data=data
        )
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取系统指标失败: {str(e)}"
        )

@router.get("/simulation-metrics/{session_id}", response_model=StandardResponse)
async def get_simulation_metrics(
    session_id: str,
    limit: int = Query(100, ge=1, le=1000, description="返回的数据点数量"),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定仿真会话的指标历史数据
    """
    try:
        history = await websocket_monitor.get_simulation_history(session_id, limit)
        
        return StandardResponse(
            success=True,
            message=f"获取仿真 {session_id} 指标成功",
            data={
                "session_id": session_id,
                "metrics": history,
                "total_count": len(history)
            }
        )
        
    except Exception as e:
        logger.error(f"获取仿真指标失败 {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取仿真指标失败: {str(e)}"
        )

@router.get("/processes", response_model=StandardResponse)
async def get_simulation_processes(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前运行的仿真进程信息
    """
    try:
        processes = list(websocket_monitor.simulation_processes.values())
        
        data = {
            "processes": [{
                "pid": p.pid,
                "name": p.name,
                "status": p.status,
                "cpu_percent": p.cpu_percent,
                "memory_percent": p.memory_percent,
                "memory_mb": p.memory_mb,
                "create_time": p.create_time,
                "session_id": p.session_id,
                "cmdline": p.cmdline
            } for p in processes],
            "total_count": len(processes)
        }
        
        return StandardResponse(
            success=True,
            message="获取仿真进程信息成功",
            data=data
        )
        
    except Exception as e:
        logger.error(f"获取仿真进程信息失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取仿真进程信息失败: {str(e)}"
        )

@router.get("/websocket-stats", response_model=StandardResponse)
async def get_websocket_stats(
    current_user: User = Depends(get_current_user)
):
    """
    获取WebSocket连接统计信息
    """
    try:
        stats = connection_manager.get_stats()
        
        return StandardResponse(
            success=True,
            message="获取WebSocket统计信息成功",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"获取WebSocket统计信息失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取WebSocket统计信息失败: {str(e)}"
        )

@router.put("/config", response_model=StandardResponse)
async def update_monitoring_config(
    config: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    更新监控配置
    
    需要管理员权限
    """
    try:
        # 检查用户权限
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="需要管理员权限才能更新监控配置"
            )
        
        # 验证配置参数
        valid_keys = {
            "system_monitor_enabled",
            "process_monitor_enabled",
            "simulation_monitor_enabled",
            "performance_monitor_enabled",
            "log_monitor_enabled",
            "alert_thresholds"
        }
        
        invalid_keys = set(config.keys()) - valid_keys
        if invalid_keys:
            raise HTTPException(
                status_code=400,
                detail=f"无效的配置参数: {list(invalid_keys)}"
            )
        
        # 更新配置
        await websocket_monitor.update_config(config)
        
        logger.info(f"用户 {current_user.username} 更新了监控配置: {config}")
        
        return StandardResponse(
            success=True,
            message="监控配置更新成功",
            data={
                "updated_config": config,
                "updated_at": datetime.now().isoformat(),
                "updated_by": current_user.username
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新监控配置失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"更新监控配置失败: {str(e)}"
        )

@router.get("/alerts", response_model=StandardResponse)
async def get_recent_alerts(
    hours: int = Query(24, ge=1, le=168, description="获取最近N小时的告警"),
    alert_type: Optional[str] = Query(None, description="告警类型过滤"),
    current_user: User = Depends(get_current_user)
):
    """
    获取最近的系统告警
    
    注意：这是一个示例接口，实际实现需要告警存储机制
    """
    try:
        # 这里应该从告警存储系统获取数据
        # 目前返回模拟数据
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 模拟告警数据
        alerts = [
            {
                "id": "alert_001",
                "type": "cpu_high",
                "severity": "warning",
                "message": "CPU使用率过高: 85.2%",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "resolved": True
            },
            {
                "id": "alert_002",
                "type": "memory_high",
                "severity": "warning",
                "message": "内存使用率过高: 88.7%",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "resolved": False
            }
        ]
        
        # 应用过滤器
        if alert_type:
            alerts = [a for a in alerts if a["type"] == alert_type]
        
        return StandardResponse(
            success=True,
            message="获取告警信息成功",
            data={
                "alerts": alerts,
                "total_count": len(alerts),
                "time_range_hours": hours,
                "filter_type": alert_type
            }
        )
        
    except Exception as e:
        logger.error(f"获取告警信息失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取告警信息失败: {str(e)}"
        )

@router.get("/health", response_model=StandardResponse)
async def get_monitoring_health():
    """
    获取监控服务健康状态
    
    无需认证的健康检查接口
    """
    try:
        status = await websocket_monitor.get_system_status()
        
        health_status = {
            "status": "healthy" if status["is_running"] else "stopped",
            "monitoring_active": status["is_running"],
            "monitor_tasks": status["monitor_tasks_count"],
            "active_simulations": status["active_simulations"],
            "websocket_connections": status["websocket_connections"],
            "timestamp": datetime.now().isoformat()
        }
        
        return StandardResponse(
            success=True,
            message="监控服务健康检查完成",
            data=health_status
        )
        
    except Exception as e:
        logger.error(f"监控健康检查失败: {e}")
        # 健康检查失败时仍返回状态信息
        return StandardResponse(
            success=False,
            message=f"监控健康检查失败: {str(e)}",
            data={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@router.post("/broadcast-test", response_model=StandardResponse)
async def broadcast_test_message(
    message: Dict[str, Any],
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    发送测试广播消息
    
    用于测试WebSocket广播功能，需要管理员权限
    """
    try:
        # 检查用户权限
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="需要管理员权限才能发送测试消息"
            )
        
        test_message = {
            "type": "test_broadcast",
            "payload": message,
            "timestamp": datetime.now().isoformat(),
            "sent_by": current_user.username
        }
        
        if session_id:
            # 发送给指定会话
            await connection_manager.broadcast_to_session(test_message, session_id)
            target = f"会话 {session_id}"
        else:
            # 发送给所有会话
            for sid in connection_manager.session_subscriptions.keys():
                await connection_manager.broadcast_to_session(test_message, sid)
            target = "所有会话"
        
        logger.info(f"用户 {current_user.username} 发送测试广播消息到 {target}")
        
        return StandardResponse(
            success=True,
            message=f"测试消息已发送到 {target}",
            data={
                "message": test_message,
                "target": target,
                "sent_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"发送测试广播消息失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"发送测试广播消息失败: {str(e)}"
        )