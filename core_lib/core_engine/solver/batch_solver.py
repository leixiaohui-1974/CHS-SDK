#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS仿真平台批量仿真引擎
提供高效的批量仿真执行、任务调度和资源管理功能
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from core_lib.models.api_models import SimulationRequest, SimulationResult
from core_lib.core_engine.solver.simulation_engine import SimulationSolver
from core_lib.database.database import get_db
from core_lib.database.models import BatchSimulation, BatchSimulationTask, SimulationResult as SimulationResultModel

# 配置日志
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

@dataclass
class BatchTask:
    """批量任务数据类"""
    task_id: str
    batch_id: str
    task_index: int
    simulation_request: SimulationRequest
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[SimulationResult] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class BatchJob:
    """批量作业数据类"""
    batch_id: str
    name: str
    user_id: str
    tasks: List[BatchTask]
    parallel_count: int = 4
    timeout_minutes: int = 60
    auto_retry: bool = True
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_callback: Optional[Callable] = None
    notification_webhook: Optional[str] = None

class BatchSimulationEngine:
    """
    批量仿真引擎
    
    提供高效的批量仿真执行功能，支持：
    - 并行任务执行
    - 任务队列管理
    - 自动重试机制
    - 进度监控
    - 资源管理
    - 错误处理
    """
    
    def __init__(self, max_workers: int = 16):
        """
        初始化批量仿真引擎
        
        Args:
            max_workers: 最大工作线程数
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.simulation_solver = SimulationSolver()
        
        # 活跃的批量作业
        self.active_jobs: Dict[str, BatchJob] = {}
        
        # 任务队列
        self.task_queue = asyncio.Queue()
        
        # 统计信息
        self.stats = {
            "total_batches": 0,
            "completed_batches": 0,
            "failed_batches": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_execution_time": 0.0
        }
        
        logger.info(f"批量仿真引擎初始化完成，最大工作线程数: {max_workers}")
    
    async def execute_batch(
        self,
        batch_id: str,
        simulations: List[SimulationRequest],
        parallel_count: int = 4,
        timeout_minutes: int = 60,
        auto_retry: bool = True,
        retry_count: int = 3,
        progress_callback: Optional[Callable] = None,
        notification_webhook: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行批量仿真任务
        
        Args:
            batch_id: 批量任务ID
            simulations: 仿真请求列表
            parallel_count: 并行执行数量
            timeout_minutes: 超时时间（分钟）
            auto_retry: 是否自动重试
            retry_count: 重试次数
            progress_callback: 进度回调函数
            notification_webhook: 通知webhook
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            logger.info(f"开始执行批量仿真任务 {batch_id}，包含 {len(simulations)} 个仿真")
            
            # 创建批量作业
            batch_job = await self._create_batch_job(
                batch_id=batch_id,
                simulations=simulations,
                parallel_count=parallel_count,
                timeout_minutes=timeout_minutes,
                auto_retry=auto_retry,
                max_retries=retry_count,
                progress_callback=progress_callback,
                notification_webhook=notification_webhook
            )
            
            # 更新数据库状态
            await self._update_batch_status(batch_id, TaskStatus.RUNNING)
            
            # 执行批量任务
            result = await self._execute_batch_job(batch_job)
            
            # 更新统计信息
            self._update_stats(batch_job)
            
            # 发送通知
            if notification_webhook:
                await self._send_notification(batch_job, notification_webhook)
            
            logger.info(f"批量仿真任务 {batch_id} 执行完成")
            return result
            
        except Exception as e:
            logger.error(f"批量仿真任务 {batch_id} 执行失败: {str(e)}")
            await self._update_batch_status(batch_id, TaskStatus.FAILED, str(e))
            raise
        finally:
            # 清理资源
            if batch_id in self.active_jobs:
                del self.active_jobs[batch_id]
    
    async def _create_batch_job(
        self,
        batch_id: str,
        simulations: List[SimulationRequest],
        parallel_count: int,
        timeout_minutes: int,
        auto_retry: bool,
        max_retries: int,
        progress_callback: Optional[Callable],
        notification_webhook: Optional[str]
    ) -> BatchJob:
        """
        创建批量作业
        
        Args:
            batch_id: 批量任务ID
            simulations: 仿真请求列表
            parallel_count: 并行数量
            timeout_minutes: 超时时间
            auto_retry: 自动重试
            max_retries: 最大重试次数
            progress_callback: 进度回调
            notification_webhook: 通知webhook
        
        Returns:
            BatchJob: 批量作业对象
        """
        # 创建批量任务
        tasks = []
        for i, sim_request in enumerate(simulations):
            task = BatchTask(
                task_id=str(uuid.uuid4()),
                batch_id=batch_id,
                task_index=i,
                simulation_request=sim_request,
                max_retries=max_retries
            )
            tasks.append(task)
        
        # 创建批量作业
        batch_job = BatchJob(
            batch_id=batch_id,
            name=f"Batch_{batch_id[:8]}",
            user_id="",  # 从数据库获取
            tasks=tasks,
            parallel_count=min(parallel_count, len(tasks)),
            timeout_minutes=timeout_minutes,
            auto_retry=auto_retry,
            max_retries=max_retries,
            created_at=datetime.utcnow(),
            progress_callback=progress_callback,
            notification_webhook=notification_webhook
        )
        
        # 添加到活跃作业列表
        self.active_jobs[batch_id] = batch_job
        
        return batch_job
    
    async def _execute_batch_job(self, batch_job: BatchJob) -> Dict[str, Any]:
        """
        执行批量作业
        
        Args:
            batch_job: 批量作业对象
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        batch_job.started_at = datetime.utcnow()
        batch_job.status = TaskStatus.RUNNING
        
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(batch_job.parallel_count)
        
        # 创建任务协程列表
        task_coroutines = []
        for task in batch_job.tasks:
            coroutine = self._execute_single_task(task, semaphore, batch_job.timeout_minutes)
            task_coroutines.append(coroutine)
        
        # 并发执行所有任务
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # 处理结果
        completed_count = 0
        failed_count = 0
        total_execution_time = 0.0
        
        for i, result in enumerate(results):
            task = batch_job.tasks[i]
            if isinstance(result, Exception):
                task.status = TaskStatus.FAILED
                task.error_message = str(result)
                failed_count += 1
            else:
                if task.status == TaskStatus.COMPLETED:
                    completed_count += 1
                    if task.execution_time:
                        total_execution_time += task.execution_time
                elif task.status == TaskStatus.FAILED:
                    failed_count += 1
        
        # 更新批量作业状态
        batch_job.completed_at = datetime.utcnow()
        if failed_count == 0:
            batch_job.status = TaskStatus.COMPLETED
        elif completed_count == 0:
            batch_job.status = TaskStatus.FAILED
        else:
            batch_job.status = TaskStatus.COMPLETED  # 部分成功也算完成
        
        # 更新数据库
        await self._update_batch_results(batch_job)
        
        # 返回执行结果
        return {
            "batch_id": batch_job.batch_id,
            "status": batch_job.status.value,
            "total_tasks": len(batch_job.tasks),
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "total_execution_time": total_execution_time,
            "average_execution_time": total_execution_time / completed_count if completed_count > 0 else 0,
            "started_at": batch_job.started_at,
            "completed_at": batch_job.completed_at
        }
    
    async def _execute_single_task(
        self,
        task: BatchTask,
        semaphore: asyncio.Semaphore,
        timeout_minutes: int
    ) -> Optional[SimulationResult]:
        """
        执行单个仿真任务
        
        Args:
            task: 批量任务对象
            semaphore: 信号量
            timeout_minutes: 超时时间
        
        Returns:
            Optional[SimulationResult]: 仿真结果
        """
        async with semaphore:
            max_retries = task.max_retries
            
            for attempt in range(max_retries + 1):
                try:
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.utcnow()
                    task.retry_count = attempt
                    
                    # 更新数据库任务状态
                    await self._update_task_status(task)
                    
                    # 执行仿真
                    start_time = time.time()
                    
                    # 使用线程池执行CPU密集型任务
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(
                            self.executor,
                            self._run_simulation,
                            task.simulation_request
                        ),
                        timeout=timeout_minutes * 60
                    )
                    
                    end_time = time.time()
                    task.execution_time = end_time - start_time
                    task.completed_at = datetime.utcnow()
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    
                    # 更新数据库任务结果
                    await self._update_task_result(task)
                    
                    logger.debug(f"任务 {task.task_id} 执行成功，耗时 {task.execution_time:.2f}秒")
                    return result
                    
                except asyncio.TimeoutError:
                    error_msg = f"任务超时（{timeout_minutes}分钟）"
                    logger.warning(f"任务 {task.task_id} 第 {attempt + 1} 次尝试超时")
                    
                except Exception as e:
                    error_msg = f"执行错误: {str(e)}"
                    logger.warning(f"任务 {task.task_id} 第 {attempt + 1} 次尝试失败: {error_msg}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries:
                    task.status = TaskStatus.RETRYING
                    await self._update_task_status(task)
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                else:
                    # 所有重试都失败
                    task.status = TaskStatus.FAILED
                    task.error_message = error_msg
                    task.completed_at = datetime.utcnow()
                    await self._update_task_status(task)
                    logger.error(f"任务 {task.task_id} 执行失败，已重试 {max_retries} 次")
            
            return None
    
    def _run_simulation(self, simulation_request: SimulationRequest) -> SimulationResult:
        """
        运行单个仿真（同步方法，在线程池中执行）
        
        Args:
            simulation_request: 仿真请求
        
        Returns:
            SimulationResult: 仿真结果
        """
        try:
            # 调用仿真求解器
            result = self.simulation_solver.solve(simulation_request)
            return result
        except Exception as e:
            logger.error(f"仿真执行失败: {str(e)}")
            raise
    
    async def _update_batch_status(
        self,
        batch_id: str,
        status: TaskStatus,
        error_message: Optional[str] = None
    ):
        """
        更新批量任务状态
        
        Args:
            batch_id: 批量任务ID
            status: 任务状态
            error_message: 错误信息
        """
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 更新批量任务状态
            batch_task = db.query(BatchSimulation).filter(
                BatchSimulation.id == batch_id
            ).first()
            
            if batch_task:
                batch_task.status = status.value
                if status == TaskStatus.RUNNING and not batch_task.started_at:
                    batch_task.started_at = datetime.utcnow()
                elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    batch_task.completed_at = datetime.utcnow()
                
                if error_message:
                    batch_task.error_message = error_message
                
                db.commit()
            
            db.close()
            
        except Exception as e:
            logger.error(f"更新批量任务状态失败 {batch_id}: {str(e)}")
    
    async def _update_task_status(self, task: BatchTask):
        """
        更新单个任务状态
        
        Args:
            task: 批量任务对象
        """
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 更新任务状态
            db_task = db.query(BatchSimulationTask).filter(
                BatchSimulationTask.id == task.task_id
            ).first()
            
            if db_task:
                db_task.status = task.status.value
                db_task.started_at = task.started_at
                db_task.completed_at = task.completed_at
                db_task.error_message = task.error_message
                db_task.execution_time = task.execution_time
                db_task.retry_count = task.retry_count
                
                db.commit()
            
            db.close()
            
        except Exception as e:
            logger.error(f"更新任务状态失败 {task.task_id}: {str(e)}")
    
    async def _update_task_result(self, task: BatchTask):
        """
        更新任务结果
        
        Args:
            task: 批量任务对象
        """
        try:
            if not task.result:
                return
            
            # 获取数据库会话
            db = next(get_db())
            
            # 保存仿真结果
            result_record = SimulationResultModel(
                id=str(uuid.uuid4()),
                user_id=task.result.user_id if hasattr(task.result, 'user_id') else None,
                simulation_id=task.result.simulation_id if hasattr(task.result, 'simulation_id') else None,
                result_data=task.result.dict() if hasattr(task.result, 'dict') else str(task.result),
                created_at=datetime.utcnow()
            )
            
            db.add(result_record)
            
            # 更新任务结果ID
            db_task = db.query(BatchSimulationTask).filter(
                BatchSimulationTask.id == task.task_id
            ).first()
            
            if db_task:
                db_task.result_id = result_record.id
            
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"更新任务结果失败 {task.task_id}: {str(e)}")
    
    async def _update_batch_results(self, batch_job: BatchJob):
        """
        更新批量任务结果
        
        Args:
            batch_job: 批量作业对象
        """
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 更新批量任务
            batch_task = db.query(BatchSimulation).filter(
                BatchSimulation.id == batch_job.batch_id
            ).first()
            
            if batch_task:
                batch_task.status = batch_job.status.value
                batch_task.started_at = batch_job.started_at
                batch_task.completed_at = batch_job.completed_at
                
                # 计算统计信息
                completed_count = sum(1 for task in batch_job.tasks if task.status == TaskStatus.COMPLETED)
                failed_count = sum(1 for task in batch_job.tasks if task.status == TaskStatus.FAILED)
                
                batch_task.completed_simulations = completed_count
                batch_task.failed_simulations = failed_count
                
                db.commit()
            
            db.close()
            
        except Exception as e:
            logger.error(f"更新批量任务结果失败 {batch_job.batch_id}: {str(e)}")
    
    async def cancel_batch(self, batch_id: str):
        """
        取消批量任务
        
        Args:
            batch_id: 批量任务ID
        """
        try:
            if batch_id in self.active_jobs:
                batch_job = self.active_jobs[batch_id]
                batch_job.status = TaskStatus.CANCELLED
                
                # 取消所有未完成的任务
                for task in batch_job.tasks:
                    if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                        task.status = TaskStatus.CANCELLED
                        task.completed_at = datetime.utcnow()
                
                # 更新数据库
                await self._update_batch_status(batch_id, TaskStatus.CANCELLED)
                
                logger.info(f"批量任务 {batch_id} 已取消")
            
        except Exception as e:
            logger.error(f"取消批量任务失败 {batch_id}: {str(e)}")
    
    async def _send_notification(self, batch_job: BatchJob, webhook_url: str):
        """
        发送完成通知
        
        Args:
            batch_job: 批量作业对象
            webhook_url: Webhook URL
        """
        try:
            import aiohttp
            
            # 构建通知数据
            completed_count = sum(1 for task in batch_job.tasks if task.status == TaskStatus.COMPLETED)
            failed_count = sum(1 for task in batch_job.tasks if task.status == TaskStatus.FAILED)
            
            notification_data = {
                "batch_id": batch_job.batch_id,
                "name": batch_job.name,
                "status": batch_job.status.value,
                "total_tasks": len(batch_job.tasks),
                "completed_tasks": completed_count,
                "failed_tasks": failed_count,
                "started_at": batch_job.started_at.isoformat() if batch_job.started_at else None,
                "completed_at": batch_job.completed_at.isoformat() if batch_job.completed_at else None
            }
            
            # 发送通知
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=notification_data) as response:
                    if response.status == 200:
                        logger.info(f"批量任务 {batch_job.batch_id} 通知发送成功")
                    else:
                        logger.warning(f"批量任务 {batch_job.batch_id} 通知发送失败: {response.status}")
        
        except Exception as e:
            logger.error(f"发送批量任务通知失败 {batch_job.batch_id}: {str(e)}")
    
    def _update_stats(self, batch_job: BatchJob):
        """
        更新统计信息
        
        Args:
            batch_job: 批量作业对象
        """
        self.stats["total_batches"] += 1
        
        if batch_job.status == TaskStatus.COMPLETED:
            self.stats["completed_batches"] += 1
        elif batch_job.status == TaskStatus.FAILED:
            self.stats["failed_batches"] += 1
        
        completed_tasks = sum(1 for task in batch_job.tasks if task.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for task in batch_job.tasks if task.status == TaskStatus.FAILED)
        
        self.stats["total_tasks"] += len(batch_job.tasks)
        self.stats["completed_tasks"] += completed_tasks
        self.stats["failed_tasks"] += failed_tasks
        
        # 计算平均执行时间
        total_execution_time = sum(task.execution_time or 0 for task in batch_job.tasks if task.execution_time)
        if completed_tasks > 0:
            avg_time = total_execution_time / completed_tasks
            current_avg = self.stats["average_execution_time"]
            total_completed = self.stats["completed_tasks"]
            self.stats["average_execution_time"] = (current_avg * (total_completed - completed_tasks) + avg_time * completed_tasks) / total_completed
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return self.stats.copy()
    
    def get_active_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        获取活跃作业信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 活跃作业信息
        """
        active_jobs_info = {}
        
        for batch_id, batch_job in self.active_jobs.items():
            completed_count = sum(1 for task in batch_job.tasks if task.status == TaskStatus.COMPLETED)
            running_count = sum(1 for task in batch_job.tasks if task.status == TaskStatus.RUNNING)
            failed_count = sum(1 for task in batch_job.tasks if task.status == TaskStatus.FAILED)
            
            active_jobs_info[batch_id] = {
                "name": batch_job.name,
                "status": batch_job.status.value,
                "total_tasks": len(batch_job.tasks),
                "completed_tasks": completed_count,
                "running_tasks": running_count,
                "failed_tasks": failed_count,
                "progress_percentage": (completed_count / len(batch_job.tasks) * 100) if batch_job.tasks else 0,
                "started_at": batch_job.started_at.isoformat() if batch_job.started_at else None
            }
        
        return active_jobs_info
    
    def shutdown(self):
        """
        关闭批量仿真引擎
        """
        logger.info("正在关闭批量仿真引擎...")
        
        # 取消所有活跃作业
        for batch_id in list(self.active_jobs.keys()):
            asyncio.create_task(self.cancel_batch(batch_id))
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        logger.info("批量仿真引擎已关闭")