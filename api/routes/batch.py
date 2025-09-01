#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS仿真平台批量仿真API路由
提供批量仿真任务的创建、管理和监控功能
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database.database import get_db
from database import crud, models
from auth.dependencies import get_current_user
from ..core.cache import get_redis_client
from core_lib.core_engine.solver.batch_solver import BatchSimulationEngine
from core_lib.models.api_models import SimulationRequest, SimulationResult

router = APIRouter(prefix="/api/batch", tags=["batch"])

# Pydantic模型
class BatchSimulationRequest(BaseModel):
    """批量仿真请求模型"""
    name: str = Field(..., description="批量仿真任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    simulations: List[SimulationRequest] = Field(..., description="仿真任务列表")
    parallel_count: int = Field(default=4, ge=1, le=16, description="并行执行数量")
    priority: int = Field(default=5, ge=1, le=10, description="任务优先级")
    timeout_minutes: int = Field(default=60, ge=1, le=1440, description="超时时间（分钟）")
    auto_retry: bool = Field(default=True, description="是否自动重试失败的任务")
    retry_count: int = Field(default=3, ge=0, le=10, description="重试次数")
    notification_webhook: Optional[str] = Field(None, description="完成通知webhook")
    tags: List[str] = Field(default_factory=list, description="任务标签")

class BatchSimulationResponse(BaseModel):
    """批量仿真响应模型"""
    batch_id: str = Field(..., description="批量任务ID")
    name: str = Field(..., description="任务名称")
    status: str = Field(..., description="任务状态")
    total_simulations: int = Field(..., description="总仿真数量")
    completed_simulations: int = Field(..., description="已完成数量")
    failed_simulations: int = Field(..., description="失败数量")
    progress_percentage: float = Field(..., description="完成百分比")
    created_at: datetime = Field(..., description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    estimated_completion: Optional[datetime] = Field(None, description="预计完成时间")
    results_url: Optional[str] = Field(None, description="结果下载链接")

class BatchSimulationDetail(BatchSimulationResponse):
    """批量仿真详细信息模型"""
    description: Optional[str] = Field(None, description="任务描述")
    parallel_count: int = Field(..., description="并行数量")
    priority: int = Field(..., description="优先级")
    timeout_minutes: int = Field(..., description="超时时间")
    auto_retry: bool = Field(..., description="自动重试")
    retry_count: int = Field(..., description="重试次数")
    tags: List[str] = Field(..., description="标签")
    simulations: List[Dict[str, Any]] = Field(..., description="仿真任务详情")
    error_message: Optional[str] = Field(None, description="错误信息")
    performance_stats: Dict[str, Any] = Field(default_factory=dict, description="性能统计")

class BatchSimulationFilter(BaseModel):
    """批量仿真过滤器"""
    status: Optional[str] = Field(None, description="状态过滤")
    user_id: Optional[str] = Field(None, description="用户ID过滤")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    created_after: Optional[datetime] = Field(None, description="创建时间过滤（之后）")
    created_before: Optional[datetime] = Field(None, description="创建时间过滤（之前）")

# 批量仿真引擎实例
batch_engine = BatchSimulationEngine()

@router.post("/submit", response_model=BatchSimulationResponse)
async def submit_batch_simulation(
    request: BatchSimulationRequest,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    提交批量仿真任务
    
    Args:
        request: 批量仿真请求
        background_tasks: 后台任务
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        BatchSimulationResponse: 批量仿真响应
    """
    try:
        # 生成批量任务ID
        batch_id = str(uuid.uuid4())
        
        # 验证仿真请求
        if not request.simulations:
            raise HTTPException(status_code=400, detail="仿真任务列表不能为空")
        
        if len(request.simulations) > 1000:
            raise HTTPException(status_code=400, detail="单次批量仿真任务不能超过1000个")
        
        # 创建批量任务记录
        batch_task = models.BatchSimulation(
            id=batch_id,
            name=request.name,
            description=request.description,
            user_id=current_user.id,
            status="pending",
            total_simulations=len(request.simulations),
            parallel_count=request.parallel_count,
            priority=request.priority,
            timeout_minutes=request.timeout_minutes,
            auto_retry=request.auto_retry,
            retry_count=request.retry_count,
            notification_webhook=request.notification_webhook,
            tags=request.tags,
            created_at=datetime.utcnow()
        )
        
        db.add(batch_task)
        db.commit()
        
        # 创建子任务记录
        for i, sim_request in enumerate(request.simulations):
            sub_task = models.BatchSimulationTask(
                id=str(uuid.uuid4()),
                batch_id=batch_id,
                task_index=i,
                simulation_config=sim_request.dict(),
                status="pending",
                created_at=datetime.utcnow()
            )
            db.add(sub_task)
        
        db.commit()
        
        # 添加到后台任务队列
        background_tasks.add_task(
            execute_batch_simulation,
            batch_id,
            request.simulations,
            request.parallel_count,
            request.timeout_minutes,
            request.auto_retry,
            request.retry_count
        )
        
        # 返回响应
        return BatchSimulationResponse(
            batch_id=batch_id,
            name=request.name,
            status="pending",
            total_simulations=len(request.simulations),
            completed_simulations=0,
            failed_simulations=0,
            progress_percentage=0.0,
            created_at=batch_task.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"提交批量仿真任务失败: {str(e)}")

@router.get("/list", response_model=List[BatchSimulationResponse])
async def list_batch_simulations(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    status: Optional[str] = Query(None, description="状态过滤"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取批量仿真任务列表
    
    Args:
        skip: 跳过数量
        limit: 返回数量
        status: 状态过滤
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        List[BatchSimulationResponse]: 批量仿真任务列表
    """
    try:
        # 构建查询
        query = db.query(models.BatchSimulation).filter(
            models.BatchSimulation.user_id == current_user.id
        )
        
        if status:
            query = query.filter(models.BatchSimulation.status == status)
        
        # 执行查询
        batch_tasks = query.order_by(
            models.BatchSimulation.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        # 转换为响应模型
        responses = []
        for task in batch_tasks:
            # 计算进度
            completed_count = db.query(models.BatchSimulationTask).filter(
                models.BatchSimulationTask.batch_id == task.id,
                models.BatchSimulationTask.status == "completed"
            ).count()
            
            failed_count = db.query(models.BatchSimulationTask).filter(
                models.BatchSimulationTask.batch_id == task.id,
                models.BatchSimulationTask.status == "failed"
            ).count()
            
            progress = (completed_count / task.total_simulations * 100) if task.total_simulations > 0 else 0
            
            responses.append(BatchSimulationResponse(
                batch_id=task.id,
                name=task.name,
                status=task.status,
                total_simulations=task.total_simulations,
                completed_simulations=completed_count,
                failed_simulations=failed_count,
                progress_percentage=progress,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                estimated_completion=task.estimated_completion,
                results_url=f"/api/batch/{task.id}/results" if task.status == "completed" else None
            ))
        
        return responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取批量仿真任务列表失败: {str(e)}")

@router.get("/{batch_id}", response_model=BatchSimulationDetail)
async def get_batch_simulation(
    batch_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取批量仿真任务详情
    
    Args:
        batch_id: 批量任务ID
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        BatchSimulationDetail: 批量仿真详情
    """
    try:
        # 查询批量任务
        batch_task = db.query(models.BatchSimulation).filter(
            models.BatchSimulation.id == batch_id,
            models.BatchSimulation.user_id == current_user.id
        ).first()
        
        if not batch_task:
            raise HTTPException(status_code=404, detail="批量仿真任务不存在")
        
        # 查询子任务
        sub_tasks = db.query(models.BatchSimulationTask).filter(
            models.BatchSimulationTask.batch_id == batch_id
        ).order_by(models.BatchSimulationTask.task_index).all()
        
        # 统计信息
        completed_count = sum(1 for task in sub_tasks if task.status == "completed")
        failed_count = sum(1 for task in sub_tasks if task.status == "failed")
        progress = (completed_count / len(sub_tasks) * 100) if sub_tasks else 0
        
        # 构建子任务详情
        simulations = []
        for task in sub_tasks:
            sim_detail = {
                "task_id": task.id,
                "task_index": task.task_index,
                "status": task.status,
                "config": task.simulation_config,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "error_message": task.error_message,
                "result_id": task.result_id,
                "execution_time": task.execution_time,
                "retry_count": task.retry_count
            }
            simulations.append(sim_detail)
        
        # 性能统计
        performance_stats = {
            "total_execution_time": sum(task.execution_time or 0 for task in sub_tasks),
            "average_execution_time": sum(task.execution_time or 0 for task in sub_tasks) / len(sub_tasks) if sub_tasks else 0,
            "success_rate": completed_count / len(sub_tasks) if sub_tasks else 0,
            "total_retries": sum(task.retry_count or 0 for task in sub_tasks)
        }
        
        return BatchSimulationDetail(
            batch_id=batch_task.id,
            name=batch_task.name,
            description=batch_task.description,
            status=batch_task.status,
            total_simulations=batch_task.total_simulations,
            completed_simulations=completed_count,
            failed_simulations=failed_count,
            progress_percentage=progress,
            parallel_count=batch_task.parallel_count,
            priority=batch_task.priority,
            timeout_minutes=batch_task.timeout_minutes,
            auto_retry=batch_task.auto_retry,
            retry_count=batch_task.retry_count,
            tags=batch_task.tags or [],
            created_at=batch_task.created_at,
            started_at=batch_task.started_at,
            completed_at=batch_task.completed_at,
            estimated_completion=batch_task.estimated_completion,
            results_url=f"/api/batch/{batch_task.id}/results" if batch_task.status == "completed" else None,
            simulations=simulations,
            error_message=batch_task.error_message,
            performance_stats=performance_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取批量仿真任务详情失败: {str(e)}")

@router.post("/{batch_id}/cancel")
async def cancel_batch_simulation(
    batch_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取消批量仿真任务
    
    Args:
        batch_id: 批量任务ID
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        dict: 取消结果
    """
    try:
        # 查询批量任务
        batch_task = db.query(models.BatchSimulation).filter(
            models.BatchSimulation.id == batch_id,
            models.BatchSimulation.user_id == current_user.id
        ).first()
        
        if not batch_task:
            raise HTTPException(status_code=404, detail="批量仿真任务不存在")
        
        if batch_task.status in ["completed", "failed", "cancelled"]:
            raise HTTPException(status_code=400, detail="任务已完成或已取消，无法取消")
        
        # 更新任务状态
        batch_task.status = "cancelled"
        batch_task.completed_at = datetime.utcnow()
        
        # 取消未开始的子任务
        db.query(models.BatchSimulationTask).filter(
            models.BatchSimulationTask.batch_id == batch_id,
            models.BatchSimulationTask.status.in_(["pending", "running"])
        ).update({"status": "cancelled"})
        
        db.commit()
        
        # 通知批量引擎取消任务
        await batch_engine.cancel_batch(batch_id)
        
        return {"message": "批量仿真任务已取消"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"取消批量仿真任务失败: {str(e)}")

@router.get("/{batch_id}/results")
async def download_batch_results(
    batch_id: str,
    format: str = Query("zip", description="下载格式: zip, json, csv"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    下载批量仿真结果
    
    Args:
        batch_id: 批量任务ID
        format: 下载格式
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        StreamingResponse: 文件下载响应
    """
    try:
        # 查询批量任务
        batch_task = db.query(models.BatchSimulation).filter(
            models.BatchSimulation.id == batch_id,
            models.BatchSimulation.user_id == current_user.id
        ).first()
        
        if not batch_task:
            raise HTTPException(status_code=404, detail="批量仿真任务不存在")
        
        if batch_task.status != "completed":
            raise HTTPException(status_code=400, detail="任务未完成，无法下载结果")
        
        # 生成结果文件
        from ..services.batch_export import BatchResultExporter
        exporter = BatchResultExporter()
        
        if format == "zip":
            file_stream = await exporter.export_zip(batch_id, db)
            media_type = "application/zip"
            filename = f"batch_results_{batch_id}.zip"
        elif format == "json":
            file_stream = await exporter.export_json(batch_id, db)
            media_type = "application/json"
            filename = f"batch_results_{batch_id}.json"
        elif format == "csv":
            file_stream = await exporter.export_csv(batch_id, db)
            media_type = "text/csv"
            filename = f"batch_results_{batch_id}.csv"
        else:
            raise HTTPException(status_code=400, detail="不支持的下载格式")
        
        return StreamingResponse(
            file_stream,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载批量仿真结果失败: {str(e)}")

@router.get("/{batch_id}/progress")
async def get_batch_progress(
    batch_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取批量仿真进度（实时）
    
    Args:
        batch_id: 批量任务ID
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        dict: 进度信息
    """
    try:
        # 查询批量任务
        batch_task = db.query(models.BatchSimulation).filter(
            models.BatchSimulation.id == batch_id,
            models.BatchSimulation.user_id == current_user.id
        ).first()
        
        if not batch_task:
            raise HTTPException(status_code=404, detail="批量仿真任务不存在")
        
        # 统计子任务状态
        task_stats = db.query(
            models.BatchSimulationTask.status,
            db.func.count(models.BatchSimulationTask.id)
        ).filter(
            models.BatchSimulationTask.batch_id == batch_id
        ).group_by(models.BatchSimulationTask.status).all()
        
        status_counts = {status: count for status, count in task_stats}
        
        total = batch_task.total_simulations
        completed = status_counts.get("completed", 0)
        failed = status_counts.get("failed", 0)
        running = status_counts.get("running", 0)
        pending = status_counts.get("pending", 0)
        cancelled = status_counts.get("cancelled", 0)
        
        progress_percentage = (completed / total * 100) if total > 0 else 0
        
        # 估算完成时间
        estimated_completion = None
        if running > 0 and batch_task.started_at:
            elapsed_time = datetime.utcnow() - batch_task.started_at
            avg_time_per_task = elapsed_time.total_seconds() / max(completed, 1)
            remaining_tasks = pending + running
            estimated_seconds = remaining_tasks * avg_time_per_task
            estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_seconds)
        
        return {
            "batch_id": batch_id,
            "status": batch_task.status,
            "progress_percentage": progress_percentage,
            "total_simulations": total,
            "completed_simulations": completed,
            "failed_simulations": failed,
            "running_simulations": running,
            "pending_simulations": pending,
            "cancelled_simulations": cancelled,
            "started_at": batch_task.started_at,
            "estimated_completion": estimated_completion,
            "current_time": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取批量仿真进度失败: {str(e)}")

async def execute_batch_simulation(
    batch_id: str,
    simulations: List[SimulationRequest],
    parallel_count: int,
    timeout_minutes: int,
    auto_retry: bool,
    retry_count: int
):
    """
    执行批量仿真任务（后台任务）
    
    Args:
        batch_id: 批量任务ID
        simulations: 仿真任务列表
        parallel_count: 并行数量
        timeout_minutes: 超时时间
        auto_retry: 自动重试
        retry_count: 重试次数
    """
    try:
        await batch_engine.execute_batch(
            batch_id=batch_id,
            simulations=simulations,
            parallel_count=parallel_count,
            timeout_minutes=timeout_minutes,
            auto_retry=auto_retry,
            retry_count=retry_count
        )
    except Exception as e:
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"批量仿真任务执行失败 {batch_id}: {str(e)}")