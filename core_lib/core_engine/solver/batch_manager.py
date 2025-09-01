#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS仿真平台批量仿真任务管理器
提供批量仿真任务的创建、管理、监控和调度功能
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy.orm import Session
from core_lib.models.api_models import SimulationRequest, BatchSimulationRequest
from core_lib.core_engine.solver.batch_solver import BatchSimulationEngine, TaskStatus
from api.database.database import get_db
from api.database import models

# 配置日志
logger = logging.getLogger(__name__)

class BatchPriority(Enum):
    """批量任务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class BatchTemplate:
    """批量仿真模板"""
    template_id: str
    name: str
    description: str
    parameter_template: Dict[str, Any]
    default_settings: Dict[str, Any]
    created_by: str
    created_at: datetime
    is_public: bool = False
    tags: List[str] = None

class BatchSimulationManager:
    """
    批量仿真任务管理器
    
    提供批量仿真任务的完整生命周期管理：
    - 任务创建和配置
    - 任务队列管理
    - 优先级调度
    - 资源分配
    - 进度监控
    - 结果管理
    - 模板管理
    """
    
    def __init__(self, max_concurrent_batches: int = 5):
        """
        初始化批量仿真管理器
        
        Args:
            max_concurrent_batches: 最大并发批量任务数
        """
        self.max_concurrent_batches = max_concurrent_batches
        self.batch_engine = BatchSimulationEngine()
        
        # 任务队列（按优先级排序）
        self.pending_queue: List[str] = []
        self.running_batches: Dict[str, Dict[str, Any]] = {}
        
        # 模板管理
        self.templates: Dict[str, BatchTemplate] = {}
        
        # 统计信息
        self.manager_stats = {
            "total_submitted": 0,
            "total_completed": 0,
            "total_failed": 0,
            "queue_length": 0,
            "running_count": 0
        }
        
        # 启动任务调度器
        self._scheduler_task = None
        self._running = False
        
        logger.info(f"批量仿真管理器初始化完成，最大并发数: {max_concurrent_batches}")
    
    async def start(self):
        """
        启动批量仿真管理器
        """
        if self._running:
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        # 加载现有模板
        await self._load_templates()
        
        # 恢复未完成的任务
        await self._recover_pending_tasks()
        
        logger.info("批量仿真管理器已启动")
    
    async def stop(self):
        """
        停止批量仿真管理器
        """
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        # 关闭批量引擎
        self.batch_engine.shutdown()
        
        logger.info("批量仿真管理器已停止")
    
    async def submit_batch(
        self,
        request: BatchSimulationRequest,
        user_id: str,
        priority: BatchPriority = BatchPriority.NORMAL
    ) -> str:
        """
        提交批量仿真任务
        
        Args:
            request: 批量仿真请求
            user_id: 用户ID
            priority: 任务优先级
        
        Returns:
            str: 批量任务ID
        """
        try:
            # 生成批量任务ID
            batch_id = str(uuid.uuid4())
            
            # 验证请求
            await self._validate_batch_request(request)
            
            # 创建数据库记录
            await self._create_batch_record(batch_id, request, user_id, priority)
            
            # 添加到队列
            await self._add_to_queue(batch_id, priority)
            
            # 更新统计
            self.manager_stats["total_submitted"] += 1
            self.manager_stats["queue_length"] = len(self.pending_queue)
            
            logger.info(f"批量仿真任务 {batch_id} 已提交到队列，优先级: {priority.value}")
            return batch_id
            
        except Exception as e:
            logger.error(f"提交批量仿真任务失败: {str(e)}")
            raise
    
    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        获取批量任务状态
        
        Args:
            batch_id: 批量任务ID
        
        Returns:
            Dict[str, Any]: 任务状态信息
        """
        try:
            # 从数据库获取任务信息
            db = next(get_db())
            
            batch_record = db.query(models.BatchSimulation).filter(
                models.BatchSimulation.id == batch_id
            ).first()
            
            if not batch_record:
                raise ValueError(f"批量任务 {batch_id} 不存在")
            
            # 获取任务列表
            tasks = db.query(models.BatchSimulationTask).filter(
                models.BatchSimulationTask.batch_id == batch_id
            ).all()
            
            db.close()
            
            # 统计任务状态
            task_stats = {
                "total": len(tasks),
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0
            }
            
            for task in tasks:
                if task.status in task_stats:
                    task_stats[task.status] += 1
            
            # 计算进度
            progress = 0
            if task_stats["total"] > 0:
                completed = task_stats["completed"] + task_stats["failed"] + task_stats["cancelled"]
                progress = (completed / task_stats["total"]) * 100
            
            # 构建状态信息
            status_info = {
                "batch_id": batch_id,
                "name": batch_record.name,
                "status": batch_record.status,
                "priority": batch_record.priority,
                "progress_percentage": round(progress, 2),
                "task_statistics": task_stats,
                "created_at": batch_record.created_at.isoformat() if batch_record.created_at else None,
                "started_at": batch_record.started_at.isoformat() if batch_record.started_at else None,
                "completed_at": batch_record.completed_at.isoformat() if batch_record.completed_at else None,
                "estimated_completion": await self._estimate_completion_time(batch_record, task_stats),
                "error_message": batch_record.error_message
            }
            
            # 如果任务正在运行，获取实时信息
            if batch_id in self.running_batches:
                runtime_info = self.batch_engine.get_active_jobs().get(batch_id, {})
                status_info.update(runtime_info)
            
            return status_info
            
        except Exception as e:
            logger.error(f"获取批量任务状态失败 {batch_id}: {str(e)}")
            raise
    
    async def get_batch_results(
        self,
        batch_id: str,
        include_failed: bool = False,
        format_type: str = "json"
    ) -> Dict[str, Any]:
        """
        获取批量任务结果
        
        Args:
            batch_id: 批量任务ID
            include_failed: 是否包含失败的任务
            format_type: 结果格式（json, csv, excel）
        
        Returns:
            Dict[str, Any]: 任务结果
        """
        try:
            # 从数据库获取结果
            db = next(get_db())
            
            # 获取批量任务信息
            batch_record = db.query(models.BatchSimulation).filter(
                models.BatchSimulation.id == batch_id
            ).first()
            
            if not batch_record:
                raise ValueError(f"批量任务 {batch_id} 不存在")
            
            # 获取任务结果
            query = db.query(models.BatchSimulationTask).filter(
                models.BatchSimulationTask.batch_id == batch_id
            )
            
            if not include_failed:
                query = query.filter(models.BatchSimulationTask.status == "completed")
            
            tasks = query.all()
            
            # 获取仿真结果
            results = []
            for task in tasks:
                if task.result_id:
                    result_record = db.query(models.SimulationResult).filter(
                        models.SimulationResult.id == task.result_id
                    ).first()
                    
                    if result_record:
                        task_result = {
                            "task_id": task.id,
                            "task_index": task.task_index,
                            "status": task.status,
                            "execution_time": task.execution_time,
                            "result_data": json.loads(result_record.result_data) if result_record.result_data else None,
                            "completed_at": task.completed_at.isoformat() if task.completed_at else None
                        }
                        
                        if include_failed and task.error_message:
                            task_result["error_message"] = task.error_message
                        
                        results.append(task_result)
            
            db.close()
            
            # 格式化结果
            formatted_results = await self._format_results(results, format_type)
            
            return {
                "batch_id": batch_id,
                "batch_name": batch_record.name,
                "total_tasks": len(tasks),
                "successful_tasks": len([r for r in results if r["status"] == "completed"]),
                "format": format_type,
                "results": formatted_results,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取批量任务结果失败 {batch_id}: {str(e)}")
            raise
    
    async def cancel_batch(self, batch_id: str, user_id: str) -> bool:
        """
        取消批量任务
        
        Args:
            batch_id: 批量任务ID
            user_id: 用户ID
        
        Returns:
            bool: 是否成功取消
        """
        try:
            # 验证权限
            if not await self._check_batch_permission(batch_id, user_id):
                raise PermissionError("没有权限取消此批量任务")
            
            # 从队列中移除
            if batch_id in self.pending_queue:
                self.pending_queue.remove(batch_id)
                self.manager_stats["queue_length"] = len(self.pending_queue)
            
            # 如果正在运行，取消执行
            if batch_id in self.running_batches:
                await self.batch_engine.cancel_batch(batch_id)
                del self.running_batches[batch_id]
                self.manager_stats["running_count"] = len(self.running_batches)
            
            # 更新数据库状态
            db = next(get_db())
            
            batch_record = db.query(models.BatchSimulation).filter(
                models.BatchSimulation.id == batch_id
            ).first()
            
            if batch_record:
                batch_record.status = TaskStatus.CANCELLED.value
                batch_record.completed_at = datetime.utcnow()
                db.commit()
            
            db.close()
            
            logger.info(f"批量任务 {batch_id} 已取消")
            return True
            
        except Exception as e:
            logger.error(f"取消批量任务失败 {batch_id}: {str(e)}")
            return False
    
    async def create_template(
        self,
        name: str,
        description: str,
        parameter_template: Dict[str, Any],
        default_settings: Dict[str, Any],
        user_id: str,
        is_public: bool = False,
        tags: List[str] = None
    ) -> str:
        """
        创建批量仿真模板
        
        Args:
            name: 模板名称
            description: 模板描述
            parameter_template: 参数模板
            default_settings: 默认设置
            user_id: 创建者ID
            is_public: 是否公开
            tags: 标签列表
        
        Returns:
            str: 模板ID
        """
        try:
            template_id = str(uuid.uuid4())
            
            # 创建模板对象
            template = BatchTemplate(
                template_id=template_id,
                name=name,
                description=description,
                parameter_template=parameter_template,
                default_settings=default_settings,
                created_by=user_id,
                created_at=datetime.utcnow(),
                is_public=is_public,
                tags=tags or []
            )
            
            # 保存到数据库
            db = next(get_db())
            
            template_record = models.BatchTemplate(
                id=template_id,
                name=name,
                description=description,
                parameter_template=json.dumps(parameter_template),
                default_settings=json.dumps(default_settings),
                created_by=user_id,
                created_at=datetime.utcnow(),
                is_public=is_public,
                tags=json.dumps(tags or [])
            )
            
            db.add(template_record)
            db.commit()
            db.close()
            
            # 添加到内存缓存
            self.templates[template_id] = template
            
            logger.info(f"批量仿真模板 {template_id} 创建成功")
            return template_id
            
        except Exception as e:
            logger.error(f"创建批量仿真模板失败: {str(e)}")
            raise
    
    async def get_templates(
        self,
        user_id: str,
        include_public: bool = True,
        tags: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取批量仿真模板列表
        
        Args:
            user_id: 用户ID
            include_public: 是否包含公开模板
            tags: 标签过滤
        
        Returns:
            List[Dict[str, Any]]: 模板列表
        """
        try:
            db = next(get_db())
            
            query = db.query(models.BatchTemplate)
            
            # 权限过滤
            if include_public:
                query = query.filter(
                    (models.BatchTemplate.created_by == user_id) |
                    (models.BatchTemplate.is_public == True)
                )
            else:
                query = query.filter(models.BatchTemplate.created_by == user_id)
            
            templates = query.all()
            db.close()
            
            # 转换为字典格式
            template_list = []
            for template in templates:
                template_dict = {
                    "template_id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "parameter_template": json.loads(template.parameter_template),
                    "default_settings": json.loads(template.default_settings),
                    "created_by": template.created_by,
                    "created_at": template.created_at.isoformat(),
                    "is_public": template.is_public,
                    "tags": json.loads(template.tags) if template.tags else []
                }
                
                # 标签过滤
                if tags:
                    template_tags = template_dict["tags"]
                    if not any(tag in template_tags for tag in tags):
                        continue
                
                template_list.append(template_dict)
            
            return template_list
            
        except Exception as e:
            logger.error(f"获取批量仿真模板失败: {str(e)}")
            raise
    
    async def apply_template(
        self,
        template_id: str,
        parameter_values: Dict[str, Any],
        user_id: str
    ) -> BatchSimulationRequest:
        """
        应用批量仿真模板
        
        Args:
            template_id: 模板ID
            parameter_values: 参数值
            user_id: 用户ID
        
        Returns:
            BatchSimulationRequest: 批量仿真请求
        """
        try:
            # 获取模板
            template = await self._get_template(template_id)
            
            if not template:
                raise ValueError(f"模板 {template_id} 不存在")
            
            # 验证权限
            if not template.is_public and template.created_by != user_id:
                raise PermissionError("没有权限使用此模板")
            
            # 生成仿真请求列表
            simulations = await self._generate_simulations_from_template(
                template, parameter_values
            )
            
            # 创建批量仿真请求
            batch_request = BatchSimulationRequest(
                name=f"{template.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                description=f"基于模板 {template.name} 生成的批量仿真",
                simulations=simulations,
                parallel_count=template.default_settings.get("parallel_count", 4),
                timeout_minutes=template.default_settings.get("timeout_minutes", 60),
                auto_retry=template.default_settings.get("auto_retry", True),
                retry_count=template.default_settings.get("retry_count", 3),
                notification_webhook=template.default_settings.get("notification_webhook")
            )
            
            return batch_request
            
        except Exception as e:
            logger.error(f"应用批量仿真模板失败 {template_id}: {str(e)}")
            raise
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """
        获取队列状态
        
        Returns:
            Dict[str, Any]: 队列状态信息
        """
        try:
            # 获取队列中的任务信息
            queue_info = []
            
            db = next(get_db())
            
            for batch_id in self.pending_queue:
                batch_record = db.query(models.BatchSimulation).filter(
                    models.BatchSimulation.id == batch_id
                ).first()
                
                if batch_record:
                    queue_info.append({
                        "batch_id": batch_id,
                        "name": batch_record.name,
                        "priority": batch_record.priority,
                        "total_simulations": batch_record.total_simulations,
                        "created_at": batch_record.created_at.isoformat(),
                        "estimated_start_time": await self._estimate_start_time(batch_id)
                    })
            
            db.close()
            
            # 获取运行中的任务信息
            running_info = []
            for batch_id, batch_info in self.running_batches.items():
                running_info.append({
                    "batch_id": batch_id,
                    "name": batch_info.get("name", ""),
                    "progress_percentage": batch_info.get("progress_percentage", 0),
                    "started_at": batch_info.get("started_at")
                })
            
            return {
                "queue_length": len(self.pending_queue),
                "running_count": len(self.running_batches),
                "max_concurrent": self.max_concurrent_batches,
                "queue_items": queue_info,
                "running_items": running_info,
                "statistics": self.manager_stats
            }
            
        except Exception as e:
            logger.error(f"获取队列状态失败: {str(e)}")
            raise
    
    async def _scheduler_loop(self):
        """
        任务调度循环
        """
        while self._running:
            try:
                # 检查是否可以启动新任务
                if (len(self.running_batches) < self.max_concurrent_batches and 
                    len(self.pending_queue) > 0):
                    
                    # 获取下一个任务
                    batch_id = self.pending_queue.pop(0)
                    
                    # 启动任务
                    await self._start_batch_execution(batch_id)
                
                # 检查完成的任务
                await self._check_completed_batches()
                
                # 更新统计信息
                self.manager_stats["queue_length"] = len(self.pending_queue)
                self.manager_stats["running_count"] = len(self.running_batches)
                
                # 等待一段时间再检查
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"任务调度循环错误: {str(e)}")
                await asyncio.sleep(10)
    
    async def _start_batch_execution(self, batch_id: str):
        """
        启动批量任务执行
        
        Args:
            batch_id: 批量任务ID
        """
        try:
            # 从数据库获取任务信息
            db = next(get_db())
            
            batch_record = db.query(models.BatchSimulation).filter(
                models.BatchSimulation.id == batch_id
            ).first()
            
            if not batch_record:
                logger.error(f"批量任务 {batch_id} 不存在")
                return
            
            # 获取仿真请求列表
            simulations = json.loads(batch_record.simulation_requests)
            
            db.close()
            
            # 转换为SimulationRequest对象
            simulation_requests = [
                SimulationRequest(**sim) for sim in simulations
            ]
            
            # 添加到运行列表
            self.running_batches[batch_id] = {
                "name": batch_record.name,
                "started_at": datetime.utcnow().isoformat(),
                "progress_percentage": 0
            }
            
            # 启动批量执行
            asyncio.create_task(
                self._execute_batch_with_monitoring(batch_id, batch_record, simulation_requests)
            )
            
            logger.info(f"批量任务 {batch_id} 开始执行")
            
        except Exception as e:
            logger.error(f"启动批量任务执行失败 {batch_id}: {str(e)}")
    
    async def _execute_batch_with_monitoring(
        self,
        batch_id: str,
        batch_record: models.BatchSimulation,
        simulation_requests: List[SimulationRequest]
    ):
        """
        执行批量任务并监控进度
        
        Args:
            batch_id: 批量任务ID
            batch_record: 批量任务记录
            simulation_requests: 仿真请求列表
        """
        try:
            # 执行批量仿真
            result = await self.batch_engine.execute_batch(
                batch_id=batch_id,
                simulations=simulation_requests,
                parallel_count=batch_record.parallel_count,
                timeout_minutes=batch_record.timeout_minutes,
                auto_retry=batch_record.auto_retry,
                retry_count=batch_record.max_retries,
                progress_callback=lambda progress: self._update_progress(batch_id, progress),
                notification_webhook=batch_record.notification_webhook
            )
            
            # 更新统计
            if result["status"] == TaskStatus.COMPLETED.value:
                self.manager_stats["total_completed"] += 1
            else:
                self.manager_stats["total_failed"] += 1
            
            logger.info(f"批量任务 {batch_id} 执行完成: {result['status']}")
            
        except Exception as e:
            logger.error(f"批量任务执行失败 {batch_id}: {str(e)}")
            self.manager_stats["total_failed"] += 1
        finally:
            # 从运行列表中移除
            if batch_id in self.running_batches:
                del self.running_batches[batch_id]
    
    def _update_progress(self, batch_id: str, progress: float):
        """
        更新任务进度
        
        Args:
            batch_id: 批量任务ID
            progress: 进度百分比
        """
        if batch_id in self.running_batches:
            self.running_batches[batch_id]["progress_percentage"] = progress
    
    async def _check_completed_batches(self):
        """
        检查已完成的批量任务
        """
        # 这个方法在实际实现中可能需要检查数据库状态
        # 或者从batch_engine获取完成状态
        pass
    
    # 其他辅助方法的实现...
    async def _validate_batch_request(self, request: BatchSimulationRequest):
        """验证批量仿真请求"""
        if not request.simulations:
            raise ValueError("仿真列表不能为空")
        
        if len(request.simulations) > 1000:  # 限制最大任务数
            raise ValueError("单次批量仿真任务数量不能超过1000个")
    
    async def _create_batch_record(
        self,
        batch_id: str,
        request: BatchSimulationRequest,
        user_id: str,
        priority: BatchPriority
    ):
        """创建批量任务数据库记录"""
        db = next(get_db())
        
        batch_record = models.BatchSimulation(
            id=batch_id,
            name=request.name,
            description=request.description,
            user_id=user_id,
            status=TaskStatus.PENDING.value,
            priority=priority.value,
            total_simulations=len(request.simulations),
            parallel_count=request.parallel_count,
            timeout_minutes=request.timeout_minutes,
            auto_retry=request.auto_retry,
            max_retries=request.retry_count,
            simulation_requests=json.dumps([sim.dict() for sim in request.simulations]),
            notification_webhook=request.notification_webhook,
            created_at=datetime.utcnow()
        )
        
        db.add(batch_record)
        
        # 创建子任务记录
        for i, sim_request in enumerate(request.simulations):
            task_record = models.BatchSimulationTask(
                id=str(uuid.uuid4()),
                batch_id=batch_id,
                task_index=i,
                status=TaskStatus.PENDING.value,
                simulation_request=json.dumps(sim_request.dict()),
                created_at=datetime.utcnow()
            )
            db.add(task_record)
        
        db.commit()
        db.close()
    
    async def _add_to_queue(self, batch_id: str, priority: BatchPriority):
        """添加任务到队列（按优先级排序）"""
        # 根据优先级插入到合适位置
        priority_order = {
            BatchPriority.URGENT: 0,
            BatchPriority.HIGH: 1,
            BatchPriority.NORMAL: 2,
            BatchPriority.LOW: 3
        }
        
        insert_index = len(self.pending_queue)
        for i, existing_batch_id in enumerate(self.pending_queue):
            # 这里需要从数据库获取现有任务的优先级进行比较
            # 简化实现，直接添加到末尾
            pass
        
        self.pending_queue.append(batch_id)
    
    async def _load_templates(self):
        """加载现有模板"""
        try:
            db = next(get_db())
            templates = db.query(models.BatchTemplate).all()
            
            for template in templates:
                self.templates[template.id] = BatchTemplate(
                    template_id=template.id,
                    name=template.name,
                    description=template.description,
                    parameter_template=json.loads(template.parameter_template),
                    default_settings=json.loads(template.default_settings),
                    created_by=template.created_by,
                    created_at=template.created_at,
                    is_public=template.is_public,
                    tags=json.loads(template.tags) if template.tags else []
                )
            
            db.close()
            logger.info(f"加载了 {len(self.templates)} 个批量仿真模板")
            
        except Exception as e:
            logger.error(f"加载模板失败: {str(e)}")
    
    async def _recover_pending_tasks(self):
        """恢复未完成的任务"""
        try:
            db = next(get_db())
            
            # 查找状态为pending的批量任务
            pending_batches = db.query(models.BatchSimulation).filter(
                models.BatchSimulation.status == TaskStatus.PENDING.value
            ).all()
            
            for batch in pending_batches:
                self.pending_queue.append(batch.id)
            
            db.close()
            
            if pending_batches:
                logger.info(f"恢复了 {len(pending_batches)} 个待处理的批量任务")
            
        except Exception as e:
            logger.error(f"恢复待处理任务失败: {str(e)}")
    
    # 其他辅助方法的占位符实现
    async def _estimate_completion_time(self, batch_record, task_stats):
        """估算完成时间"""
        return None
    
    async def _format_results(self, results, format_type):
        """格式化结果"""
        return results
    
    async def _check_batch_permission(self, batch_id, user_id):
        """检查批量任务权限"""
        return True
    
    async def _get_template(self, template_id):
        """获取模板"""
        return self.templates.get(template_id)
    
    async def _generate_simulations_from_template(self, template, parameter_values):
        """从模板生成仿真请求"""
        return []
    
    async def _estimate_start_time(self, batch_id):
        """估算开始时间"""
        return None