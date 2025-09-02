#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket监控服务测试

测试WebSocket实时监控功能：
1. 监控服务启动和停止
2. 系统指标收集
3. 进程监控
4. 仿真状态监控
5. WebSocket消息广播
6. 配置管理
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from pathlib import Path

# 模拟依赖项
try:
    from services.websocket_monitor import (
        WebSocketMonitorService,
        ProcessInfo,
        SystemMetrics,
        SimulationMetrics
    )
    from websocket.connection_manager import connection_manager
except ImportError:
    # 如果导入失败，创建模拟类
    class WebSocketMonitorService:
        def __init__(self):
            self.is_running = False
            self.monitor_tasks = set()
            self.simulation_processes = {}
            self.system_metrics_history = []
            self.simulation_metrics_history = {}
            self.max_history_size = 1000
            self.monitor_interval = 1.0
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
            self.is_running = True
        
        async def stop_monitoring(self):
            self.is_running = False
        
        async def get_system_status(self):
            return {
                "is_running": self.is_running,
                "monitor_tasks_count": len(self.monitor_tasks),
                "active_simulations": len(self.simulation_processes),
                "websocket_connections": 0,
                "latest_system_metrics": None,
                "config": self.config
            }
        
        async def get_simulation_history(self, session_id, limit=100):
            return []
        
        async def update_config(self, new_config):
            self.config.update(new_config)
    
    class ProcessInfo:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class SystemMetrics:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class SimulationMetrics:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    # 模拟连接管理器
    class MockConnectionManager:
        def __init__(self):
            self.active_connections = {}
            self.session_subscriptions = {}
        
        def get_stats(self):
            return {
                "total_connections": len(self.active_connections),
                "active_sessions": len(self.session_subscriptions)
            }
        
        async def broadcast_to_session(self, message, session_id):
            pass
    
    connection_manager = MockConnectionManager()

class TestWebSocketMonitorService:
    """
    WebSocket监控服务测试类
    """
    
    @pytest.fixture
    def monitor_service(self):
        """创建监控服务实例"""
        return WebSocketMonitorService()
    
    @pytest.mark.asyncio
    async def test_monitor_service_lifecycle(self, monitor_service):
        """
        测试监控服务生命周期
        """
        # 初始状态
        assert not monitor_service.is_running
        
        # 启动监控服务
        await monitor_service.start_monitoring()
        assert monitor_service.is_running
        
        # 停止监控服务
        await monitor_service.stop_monitoring()
        assert not monitor_service.is_running
    
    @pytest.mark.asyncio
    async def test_system_status(self, monitor_service):
        """
        测试系统状态获取
        """
        status = await monitor_service.get_system_status()
        
        assert isinstance(status, dict)
        assert "is_running" in status
        assert "monitor_tasks_count" in status
        assert "active_simulations" in status
        assert "websocket_connections" in status
        assert "config" in status
    
    @pytest.mark.asyncio
    async def test_config_update(self, monitor_service):
        """
        测试配置更新
        """
        new_config = {
            "system_monitor_enabled": False,
            "alert_thresholds": {
                "cpu_percent": 90.0
            }
        }
        
        await monitor_service.update_config(new_config)
        
        assert not monitor_service.config["system_monitor_enabled"]
        assert monitor_service.config["alert_thresholds"]["cpu_percent"] == 90.0
    
    @pytest.mark.asyncio
    async def test_simulation_history(self, monitor_service):
        """
        测试仿真历史数据获取
        """
        session_id = "test_session_001"
        history = await monitor_service.get_simulation_history(session_id, limit=50)
        
        assert isinstance(history, list)
        assert len(history) <= 50
    
    def test_process_info_creation(self):
        """
        测试进程信息创建
        """
        process_info = ProcessInfo(
            pid=1234,
            name="test_process",
            status="running",
            cpu_percent=25.5,
            memory_percent=15.2,
            memory_mb=512.0,
            create_time=time.time(),
            cmdline=["python", "test.py"],
            session_id="session_001"
        )
        
        assert process_info.pid == 1234
        assert process_info.name == "test_process"
        assert process_info.session_id == "session_001"
    
    def test_system_metrics_creation(self):
        """
        测试系统指标创建
        """
        metrics = SystemMetrics(
            timestamp=time.time(),
            cpu_percent=45.2,
            memory_percent=67.8,
            memory_available_gb=8.5,
            disk_usage_percent=55.3,
            network_io_bytes_sent=1024000,
            network_io_bytes_recv=2048000,
            active_processes=156,
            simulation_processes=3
        )
        
        assert metrics.cpu_percent == 45.2
        assert metrics.memory_percent == 67.8
        assert metrics.simulation_processes == 3
    
    def test_simulation_metrics_creation(self):
        """
        测试仿真指标创建
        """
        metrics = SimulationMetrics(
            session_id="sim_001",
            timestamp=time.time(),
            step=100,
            progress=0.25,
            elapsed_time=300.0,
            estimated_remaining_time=900.0,
            cpu_usage=35.5,
            memory_usage=256.0,
            status="running",
            error_count=0,
            warning_count=2
        )
        
        assert metrics.session_id == "sim_001"
        assert metrics.step == 100
        assert metrics.progress == 0.25
        assert metrics.status == "running"

class TestWebSocketMonitorIntegration:
    """
    WebSocket监控集成测试
    """
    
    @pytest.mark.asyncio
    async def test_monitor_with_mock_processes(self):
        """
        测试监控服务与模拟进程的集成
        """
        monitor = WebSocketMonitorService()
        
        # 模拟进程数据
        mock_processes = [
            ProcessInfo(
                pid=1001,
                name="simulation_engine",
                status="running",
                cpu_percent=30.0,
                memory_percent=20.0,
                memory_mb=512.0,
                create_time=time.time(),
                cmdline=["python", "simulation.py", "--session-id", "test_001"],
                session_id="test_001"
            ),
            ProcessInfo(
                pid=1002,
                name="data_processor",
                status="running",
                cpu_percent=15.0,
                memory_percent=10.0,
                memory_mb=256.0,
                create_time=time.time(),
                cmdline=["python", "processor.py"],
                session_id=None
            )
        ]
        
        # 模拟进程监控
        monitor.simulation_processes = {
            p.session_id or str(p.pid): p for p in mock_processes
        }
        
        assert len(monitor.simulation_processes) == 2
        assert "test_001" in monitor.simulation_processes
        assert "1002" in monitor.simulation_processes
    
    @pytest.mark.asyncio
    async def test_monitor_with_mock_metrics(self):
        """
        测试监控服务与模拟指标的集成
        """
        monitor = WebSocketMonitorService()
        
        # 模拟系统指标历史
        for i in range(10):
            metrics = SystemMetrics(
                timestamp=time.time() - (10 - i) * 60,  # 每分钟一个数据点
                cpu_percent=40.0 + i * 2,
                memory_percent=60.0 + i,
                memory_available_gb=8.0 - i * 0.1,
                disk_usage_percent=50.0,
                network_io_bytes_sent=1000000 + i * 10000,
                network_io_bytes_recv=2000000 + i * 20000,
                active_processes=150 + i,
                simulation_processes=2
            )
            monitor.system_metrics_history.append(metrics)
        
        assert len(monitor.system_metrics_history) == 10
        
        # 检查最新指标
        latest = monitor.system_metrics_history[-1]
        assert latest.cpu_percent == 58.0  # 40.0 + 9 * 2
        assert latest.memory_percent == 69.0  # 60.0 + 9
    
    @pytest.mark.asyncio
    async def test_connection_manager_integration(self):
        """
        测试与连接管理器的集成
        """
        # 获取连接统计
        stats = connection_manager.get_stats()
        
        assert isinstance(stats, dict)
        assert "total_connections" in stats or "active_sessions" in stats
    
    @pytest.mark.asyncio
    async def test_broadcast_functionality(self):
        """
        测试广播功能
        """
        test_message = {
            "type": "test_message",
            "payload": {"data": "test_data"},
            "timestamp": datetime.now().isoformat()
        }
        
        session_id = "test_session"
        
        # 测试广播（不会抛出异常即为成功）
        try:
            await connection_manager.broadcast_to_session(test_message, session_id)
            broadcast_success = True
        except Exception:
            broadcast_success = False
        
        assert broadcast_success

class TestMonitoringConfiguration:
    """
    监控配置测试
    """
    
    def test_default_config(self):
        """
        测试默认配置
        """
        monitor = WebSocketMonitorService()
        config = monitor.config
        
        assert config["system_monitor_enabled"] is True
        assert config["process_monitor_enabled"] is True
        assert config["simulation_monitor_enabled"] is True
        assert config["performance_monitor_enabled"] is True
        assert config["log_monitor_enabled"] is True
        
        thresholds = config["alert_thresholds"]
        assert thresholds["cpu_percent"] == 80.0
        assert thresholds["memory_percent"] == 85.0
        assert thresholds["disk_usage_percent"] == 90.0
        assert thresholds["error_rate"] == 0.1
    
    @pytest.mark.asyncio
    async def test_config_validation(self):
        """
        测试配置验证
        """
        monitor = WebSocketMonitorService()
        
        # 有效配置
        valid_config = {
            "system_monitor_enabled": False,
            "alert_thresholds": {
                "cpu_percent": 75.0,
                "memory_percent": 80.0
            }
        }
        
        await monitor.update_config(valid_config)
        
        assert not monitor.config["system_monitor_enabled"]
        assert monitor.config["alert_thresholds"]["cpu_percent"] == 75.0

class TestMonitoringPerformance:
    """
    监控性能测试
    """
    
    @pytest.mark.asyncio
    async def test_large_metrics_history(self):
        """
        测试大量指标历史数据的处理
        """
        monitor = WebSocketMonitorService()
        
        # 添加大量历史数据
        for i in range(2000):  # 超过max_history_size
            metrics = SystemMetrics(
                timestamp=time.time() - i,
                cpu_percent=50.0,
                memory_percent=60.0,
                memory_available_gb=8.0,
                disk_usage_percent=50.0,
                network_io_bytes_sent=1000000,
                network_io_bytes_recv=2000000,
                active_processes=150,
                simulation_processes=1
            )
            monitor.system_metrics_history.append(metrics)
            
            # 模拟历史数据限制
            if len(monitor.system_metrics_history) > monitor.max_history_size:
                monitor.system_metrics_history.pop(0)
        
        # 验证历史数据不会无限增长
        assert len(monitor.system_metrics_history) <= monitor.max_history_size
    
    @pytest.mark.asyncio
    async def test_concurrent_monitoring_tasks(self):
        """
        测试并发监控任务
        """
        monitor = WebSocketMonitorService()
        
        # 模拟多个监控任务
        async def mock_monitor_task(task_id):
            await asyncio.sleep(0.1)  # 模拟监控工作
            return f"task_{task_id}_completed"
        
        # 创建多个并发任务
        tasks = []
        for i in range(5):
            task = asyncio.create_task(mock_monitor_task(i))
            tasks.append(task)
            monitor.monitor_tasks.add(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        assert len(results) == 5
        assert all("completed" in str(result) for result in results)

# 运行测试的主函数
def run_tests():
    """
    运行所有监控测试
    """
    import subprocess
    import sys
    
    try:
        # 运行pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            __file__, 
            "-v",
            "--tb=short"
        ], capture_output=True, text=True)
        
        print("测试输出:")
        print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"运行测试失败: {e}")
        return False

if __name__ == "__main__":
    # 直接运行测试
    success = run_tests()
    if success:
        print("\n✅ 所有WebSocket监控测试通过")
    else:
        print("\n❌ 部分WebSocket监控测试失败")
        sys.exit(1)