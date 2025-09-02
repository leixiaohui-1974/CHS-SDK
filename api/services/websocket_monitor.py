#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket实时监控服务

提供仿真进程状态监控和数据转发功能：
1. 仿真进程状态实时监控
2. 仿真数据实时推送
3. 系统性能指标监控
4. 错误和异常实时通知
5. 客户端连接管理
"""

import asyncio
import json
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import aiofiles
import subprocess
from concurrent.futures import ThreadPoolExecutor

from websocket.connection_manager import connection_manager
from models.websocket_models import SimulationData, WebSocketMessage
from database.database import get_db
from database.models import SimulationSessionDB
from sqlalchemy.orm import Session

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class ProcessInfo:
    """进程信息"""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    create_time: float
    cmdline: List[str]
    session_id: Optional[str] = None

@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    network_io_bytes_sent: int
    network_io_bytes_recv: int
    active_processes: int
    simulation_processes: int

@dataclass
class SimulationMetrics:
    """仿真指标"""
    session_id: str
    timestamp: float
    step: int
    progress: float
    elapsed_time: float
    estimated_remaining_time: float
    cpu_usage: float
    memory_usage: float
    status: str
    error_count: int
    warning_count: int

class WebSocketMonitorService:
    """
    WebSocket实时监控服务
    """
    
    def __init__(self):
        self.is_running = False
        self.monitor_tasks: Set[asyncio.Task] = set()
        self.simulation_processes: Dict[str, ProcessInfo] = {}
        self.system_metrics_history: List[SystemMetrics] = []
        self.simulation_metrics_history: Dict[str, List[SimulationMetrics]] = {}
        self.max_history_size = 1000
        self.monitor_interval = 1.0  # 监控间隔（秒）
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 监控配置
        self.config = {
            "system_monitor_enabled": True,
            "process_monitor_enabled": True,
            "simulation_monitor_enabled": True,
            "performance_monitor_enabled": True,
            "log_monitor_enabled": True,
            "alert_thresholds": {
                "cpu_percent": 80.0,
                "memory_percent": 85.0,
                "disk_usage_percent": 90.0,
                "error_rate": 0.1
            }
        }
    
    async def start_monitoring(self):
        """启动监控服务"""
        if self.is_running:
            logger.warning("WebSocket监控服务已在运行")
            return
        
        self.is_running = True
        logger.info("启动WebSocket实时监控服务...")
        
        # 启动各种监控任务
        if self.config["system_monitor_enabled"]:
            task = asyncio.create_task(self._monitor_system_metrics())
            self.monitor_tasks.add(task)
        
        if self.config["process_monitor_enabled"]:
            task = asyncio.create_task(self._monitor_simulation_processes())
            self.monitor_tasks.add(task)
        
        if self.config["simulation_monitor_enabled"]:
            task = asyncio.create_task(self._monitor_simulation_status())
            self.monitor_tasks.add(task)
        
        if self.config["performance_monitor_enabled"]:
            task = asyncio.create_task(self._monitor_performance())
            self.monitor_tasks.add(task)
        
        if self.config["log_monitor_enabled"]:
            task = asyncio.create_task(self._monitor_logs())
            self.monitor_tasks.add(task)
        
        # 启动数据清理任务
        task = asyncio.create_task(self._cleanup_old_data())
        self.monitor_tasks.add(task)
        
        logger.info(f"WebSocket监控服务已启动，运行 {len(self.monitor_tasks)} 个监控任务")
    
    async def stop_monitoring(self):
        """停止监控服务"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("停止WebSocket监控服务...")
        
        # 取消所有监控任务
        for task in self.monitor_tasks:
            if not task.done():
                task.cancel()
        
        # 等待任务完成
        if self.monitor_tasks:
            await asyncio.gather(*self.monitor_tasks, return_exceptions=True)
        
        self.monitor_tasks.clear()
        self.executor.shutdown(wait=True)
        
        logger.info("WebSocket监控服务已停止")
    
    async def _monitor_system_metrics(self):
        """监控系统指标"""
        logger.info("启动系统指标监控")
        
        while self.is_running:
            try:
                # 获取系统指标
                metrics = await self._get_system_metrics()
                
                # 存储历史数据
                self.system_metrics_history.append(metrics)
                if len(self.system_metrics_history) > self.max_history_size:
                    self.system_metrics_history.pop(0)
                
                # 检查告警阈值
                await self._check_system_alerts(metrics)
                
                # 广播系统指标
                await self._broadcast_system_metrics(metrics)
                
                await asyncio.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"系统指标监控错误: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_simulation_processes(self):
        """监控仿真进程"""
        logger.info("启动仿真进程监控")
        
        while self.is_running:
            try:
                # 获取仿真进程信息
                processes = await self._get_simulation_processes()
                
                # 检测进程变化
                await self._detect_process_changes(processes)
                
                # 更新进程信息
                self.simulation_processes = {p.session_id or str(p.pid): p for p in processes}
                
                # 广播进程状态
                await self._broadcast_process_status(processes)
                
                await asyncio.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"仿真进程监控错误: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_simulation_status(self):
        """监控仿真状态"""
        logger.info("启动仿真状态监控")
        
        while self.is_running:
            try:
                # 获取活跃的仿真会话
                active_sessions = await self._get_active_simulation_sessions()
                
                for session_id in active_sessions:
                    # 获取仿真指标
                    metrics = await self._get_simulation_metrics(session_id)
                    if metrics:
                        # 存储历史数据
                        if session_id not in self.simulation_metrics_history:
                            self.simulation_metrics_history[session_id] = []
                        
                        self.simulation_metrics_history[session_id].append(metrics)
                        if len(self.simulation_metrics_history[session_id]) > self.max_history_size:
                            self.simulation_metrics_history[session_id].pop(0)
                        
                        # 广播仿真指标
                        await self._broadcast_simulation_metrics(metrics)
                
                await asyncio.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"仿真状态监控错误: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_performance(self):
        """监控性能指标"""
        logger.info("启动性能监控")
        
        while self.is_running:
            try:
                # 获取性能数据
                performance_data = await self._get_performance_data()
                
                # 广播性能数据
                await self._broadcast_performance_data(performance_data)
                
                await asyncio.sleep(5)  # 性能监控间隔较长
                
            except Exception as e:
                logger.error(f"性能监控错误: {e}")
                await asyncio.sleep(10)
    
    async def _monitor_logs(self):
        """监控日志文件"""
        logger.info("启动日志监控")
        
        log_files = [
            "logs/simulation.log",
            "logs/api.log",
            "logs/websocket.log"
        ]
        
        file_positions = {}
        
        while self.is_running:
            try:
                for log_file in log_files:
                    if Path(log_file).exists():
                        await self._monitor_log_file(log_file, file_positions)
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"日志监控错误: {e}")
                await asyncio.sleep(5)
    
    async def _get_system_metrics(self) -> SystemMetrics:
        """获取系统指标"""
        def get_metrics():
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_gb=memory.available / (1024**3),
                disk_usage_percent=disk.percent,
                network_io_bytes_sent=network.bytes_sent,
                network_io_bytes_recv=network.bytes_recv,
                active_processes=len(psutil.pids()),
                simulation_processes=len(self.simulation_processes)
            )
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, get_metrics)
    
    async def _get_simulation_processes(self) -> List[ProcessInfo]:
        """获取仿真进程信息"""
        def get_processes():
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'memory_info', 'create_time', 'cmdline']):
                try:
                    info = proc.info
                    
                    # 检查是否为仿真进程
                    if self._is_simulation_process(info):
                        process_info = ProcessInfo(
                            pid=info['pid'],
                            name=info['name'],
                            status=info['status'],
                            cpu_percent=info['cpu_percent'] or 0.0,
                            memory_percent=info['memory_percent'] or 0.0,
                            memory_mb=info['memory_info'].rss / (1024*1024) if info['memory_info'] else 0.0,
                            create_time=info['create_time'],
                            cmdline=info['cmdline'] or [],
                            session_id=self._extract_session_id(info['cmdline'] or [])
                        )
                        processes.append(process_info)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return processes
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, get_processes)
    
    def _is_simulation_process(self, proc_info: Dict) -> bool:
        """判断是否为仿真进程"""
        name = proc_info.get('name', '').lower()
        cmdline = ' '.join(proc_info.get('cmdline', [])).lower()
        
        # 检查进程名称和命令行
        simulation_keywords = [
            'python', 'simulation', 'chs', 'runner',
            'simulate', 'model', 'engine'
        ]
        
        return any(keyword in name or keyword in cmdline for keyword in simulation_keywords)
    
    def _extract_session_id(self, cmdline: List[str]) -> Optional[str]:
        """从命令行参数中提取会话ID"""
        for i, arg in enumerate(cmdline):
            if arg in ['--session-id', '--session', '-s'] and i + 1 < len(cmdline):
                return cmdline[i + 1]
            if arg.startswith('--session-id='):
                return arg.split('=', 1)[1]
        return None
    
    async def _get_active_simulation_sessions(self) -> List[str]:
        """获取活跃的仿真会话ID列表"""
        try:
            # 从数据库获取运行中的仿真会话
            db = next(get_db())
            sessions = db.query(SimulationSessionDB).filter(
                SimulationSessionDB.status.in_(['running', 'paused'])
            ).all()
            
            return [session.session_id for session in sessions]
            
        except Exception as e:
            logger.error(f"获取活跃仿真会话失败: {e}")
            return []
    
    async def _get_simulation_metrics(self, session_id: str) -> Optional[SimulationMetrics]:
        """获取仿真指标"""
        try:
            # 从进程信息获取资源使用情况
            process_info = self.simulation_processes.get(session_id)
            cpu_usage = process_info.cpu_percent if process_info else 0.0
            memory_usage = process_info.memory_mb if process_info else 0.0
            
            # 从仿真状态文件或API获取进度信息
            # 这里需要根据实际的仿真引擎实现
            status_data = await self._get_simulation_status_data(session_id)
            
            if status_data:
                return SimulationMetrics(
                    session_id=session_id,
                    timestamp=time.time(),
                    step=status_data.get('step', 0),
                    progress=status_data.get('progress', 0.0),
                    elapsed_time=status_data.get('elapsed_time', 0.0),
                    estimated_remaining_time=status_data.get('estimated_remaining_time', 0.0),
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    status=status_data.get('status', 'unknown'),
                    error_count=status_data.get('error_count', 0),
                    warning_count=status_data.get('warning_count', 0)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"获取仿真指标失败 {session_id}: {e}")
            return None
    
    async def _get_simulation_status_data(self, session_id: str) -> Optional[Dict]:
        """获取仿真状态数据"""
        try:
            # 尝试从状态文件读取
            status_file = Path(f"temp/simulation_status_{session_id}.json")
            if status_file.exists():
                async with aiofiles.open(status_file, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            
            # 如果没有状态文件，返回默认值
            return {
                'step': 0,
                'progress': 0.0,
                'elapsed_time': 0.0,
                'estimated_remaining_time': 0.0,
                'status': 'unknown',
                'error_count': 0,
                'warning_count': 0
            }
            
        except Exception as e:
            logger.error(f"读取仿真状态数据失败 {session_id}: {e}")
            return None
    
    async def _get_performance_data(self) -> Dict[str, Any]:
        """获取性能数据"""
        try:
            # 计算最近的系统指标平均值
            recent_metrics = self.system_metrics_history[-60:]  # 最近60个数据点
            
            if recent_metrics:
                avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
                avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
                
                return {
                    'timestamp': time.time(),
                    'average_cpu_percent': avg_cpu,
                    'average_memory_percent': avg_memory,
                    'active_simulations': len(self.simulation_processes),
                    'total_websocket_connections': len(connection_manager.active_connections),
                    'system_load': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"获取性能数据失败: {e}")
            return {}
    
    async def _monitor_log_file(self, log_file: str, file_positions: Dict[str, int]):
        """监控日志文件"""
        try:
            file_path = Path(log_file)
            if not file_path.exists():
                return
            
            # 获取文件当前位置
            current_pos = file_positions.get(log_file, 0)
            file_size = file_path.stat().st_size
            
            if file_size < current_pos:
                # 文件被重置，从头开始
                current_pos = 0
            
            if file_size > current_pos:
                # 读取新内容
                async with aiofiles.open(file_path, 'r') as f:
                    await f.seek(current_pos)
                    new_content = await f.read()
                    
                    if new_content:
                        # 处理新的日志内容
                        await self._process_log_content(log_file, new_content)
                        
                        # 更新文件位置
                        file_positions[log_file] = file_size
        
        except Exception as e:
            logger.error(f"监控日志文件失败 {log_file}: {e}")
    
    async def _process_log_content(self, log_file: str, content: str):
        """处理日志内容"""
        lines = content.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
            
            # 检查错误和警告
            if 'ERROR' in line.upper() or 'CRITICAL' in line.upper():
                await self._broadcast_log_alert('error', log_file, line)
            elif 'WARNING' in line.upper() or 'WARN' in line.upper():
                await self._broadcast_log_alert('warning', log_file, line)
    
    async def _detect_process_changes(self, current_processes: List[ProcessInfo]):
        """检测进程变化"""
        current_pids = {p.pid for p in current_processes}
        previous_pids = {p.pid for p in self.simulation_processes.values()}
        
        # 新启动的进程
        new_pids = current_pids - previous_pids
        for process in current_processes:
            if process.pid in new_pids:
                await self._broadcast_process_event('started', process)
        
        # 已停止的进程
        stopped_pids = previous_pids - current_pids
        for pid in stopped_pids:
            old_process = next((p for p in self.simulation_processes.values() if p.pid == pid), None)
            if old_process:
                await self._broadcast_process_event('stopped', old_process)
    
    async def _check_system_alerts(self, metrics: SystemMetrics):
        """检查系统告警"""
        thresholds = self.config["alert_thresholds"]
        
        alerts = []
        
        if metrics.cpu_percent > thresholds["cpu_percent"]:
            alerts.append({
                'type': 'cpu_high',
                'message': f'CPU使用率过高: {metrics.cpu_percent:.1f}%',
                'severity': 'warning'
            })
        
        if metrics.memory_percent > thresholds["memory_percent"]:
            alerts.append({
                'type': 'memory_high',
                'message': f'内存使用率过高: {metrics.memory_percent:.1f}%',
                'severity': 'warning'
            })
        
        if metrics.disk_usage_percent > thresholds["disk_usage_percent"]:
            alerts.append({
                'type': 'disk_high',
                'message': f'磁盘使用率过高: {metrics.disk_usage_percent:.1f}%',
                'severity': 'critical'
            })
        
        for alert in alerts:
            await self._broadcast_system_alert(alert)
    
    async def _cleanup_old_data(self):
        """清理旧数据"""
        while self.is_running:
            try:
                # 清理超过24小时的历史数据
                cutoff_time = time.time() - 24 * 3600
                
                # 清理系统指标历史
                self.system_metrics_history = [
                    m for m in self.system_metrics_history 
                    if m.timestamp > cutoff_time
                ]
                
                # 清理仿真指标历史
                for session_id in list(self.simulation_metrics_history.keys()):
                    self.simulation_metrics_history[session_id] = [
                        m for m in self.simulation_metrics_history[session_id]
                        if m.timestamp > cutoff_time
                    ]
                    
                    # 如果会话没有数据，删除记录
                    if not self.simulation_metrics_history[session_id]:
                        del self.simulation_metrics_history[session_id]
                
                await asyncio.sleep(3600)  # 每小时清理一次
                
            except Exception as e:
                logger.error(f"数据清理错误: {e}")
                await asyncio.sleep(3600)
    
    # 广播方法
    async def _broadcast_system_metrics(self, metrics: SystemMetrics):
        """广播系统指标"""
        message = {
            "type": "system_metrics",
            "payload": asdict(metrics),
            "timestamp": datetime.now().isoformat()
        }
        
        # 广播给所有连接的客户端
        for session_id in connection_manager.session_subscriptions.keys():
            await connection_manager.broadcast_to_session(message, session_id)
    
    async def _broadcast_process_status(self, processes: List[ProcessInfo]):
        """广播进程状态"""
        message = {
            "type": "process_status",
            "payload": {
                "processes": [asdict(p) for p in processes],
                "total_count": len(processes)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        for session_id in connection_manager.session_subscriptions.keys():
            await connection_manager.broadcast_to_session(message, session_id)
    
    async def _broadcast_simulation_metrics(self, metrics: SimulationMetrics):
        """广播仿真指标"""
        message = {
            "type": "simulation_metrics",
            "payload": asdict(metrics),
            "timestamp": datetime.now().isoformat()
        }
        
        await connection_manager.broadcast_to_session(message, metrics.session_id)
    
    async def _broadcast_performance_data(self, data: Dict[str, Any]):
        """广播性能数据"""
        message = {
            "type": "performance_data",
            "payload": data,
            "timestamp": datetime.now().isoformat()
        }
        
        for session_id in connection_manager.session_subscriptions.keys():
            await connection_manager.broadcast_to_session(message, session_id)
    
    async def _broadcast_process_event(self, event_type: str, process: ProcessInfo):
        """广播进程事件"""
        message = {
            "type": "process_event",
            "payload": {
                "event": event_type,
                "process": asdict(process)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 如果有会话ID，广播给该会话
        if process.session_id:
            await connection_manager.broadcast_to_session(message, process.session_id)
        else:
            # 否则广播给所有会话
            for session_id in connection_manager.session_subscriptions.keys():
                await connection_manager.broadcast_to_session(message, session_id)
    
    async def _broadcast_system_alert(self, alert: Dict[str, Any]):
        """广播系统告警"""
        message = {
            "type": "system_alert",
            "payload": alert,
            "timestamp": datetime.now().isoformat()
        }
        
        for session_id in connection_manager.session_subscriptions.keys():
            await connection_manager.broadcast_to_session(message, session_id)
    
    async def _broadcast_log_alert(self, level: str, log_file: str, content: str):
        """广播日志告警"""
        message = {
            "type": "log_alert",
            "payload": {
                "level": level,
                "file": log_file,
                "content": content.strip(),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        for session_id in connection_manager.session_subscriptions.keys():
            await connection_manager.broadcast_to_session(message, session_id)
    
    # 公共API方法
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        latest_metrics = self.system_metrics_history[-1] if self.system_metrics_history else None
        
        return {
            "is_running": self.is_running,
            "monitor_tasks_count": len(self.monitor_tasks),
            "active_simulations": len(self.simulation_processes),
            "websocket_connections": len(connection_manager.active_connections),
            "latest_system_metrics": asdict(latest_metrics) if latest_metrics else None,
            "config": self.config
        }
    
    async def get_simulation_history(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取仿真历史数据"""
        history = self.simulation_metrics_history.get(session_id, [])
        return [asdict(m) for m in history[-limit:]]
    
    async def update_config(self, new_config: Dict[str, Any]):
        """更新监控配置"""
        self.config.update(new_config)
        logger.info(f"监控配置已更新: {new_config}")

# 全局监控服务实例
websocket_monitor = WebSocketMonitorService()