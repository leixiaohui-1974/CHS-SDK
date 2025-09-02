#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 性能压力测试套件

专门用于测试系统在高负载、并发和极限条件下的性能表现，包括：
1. 高并发API请求测试
2. WebSocket连接压力测试
3. 大规模仿真性能测试
4. 内存和CPU压力测试
5. 长时间运行稳定性测试
"""

import pytest
import asyncio
import time
import threading
import multiprocessing
import concurrent.futures
import psutil
import gc
import json
import random
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import requests
from typing import List, Dict, Any

# 导入项目模块
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.server import app
from api.services.websocket_monitor import WebSocketMonitorService
from api.agents.chief_modeling_agent import ChiefModelingAgent
from api.agents.runner_agent import RunnerAgent


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.metrics = {
            'response_times': [],
            'throughput': [],
            'error_rates': [],
            'memory_usage': [],
            'cpu_usage': [],
            'connection_counts': []
        }
        self.start_time = None
        self.end_time = None
    
    def start_monitoring(self):
        """开始监控"""
        self.start_time = time.time()
        self.metrics = {key: [] for key in self.metrics.keys()}
    
    def stop_monitoring(self):
        """停止监控"""
        self.end_time = time.time()
    
    def record_response_time(self, response_time: float):
        """记录响应时间"""
        self.metrics['response_times'].append(response_time)
    
    def record_system_metrics(self):
        """记录系统指标"""
        process = psutil.Process()
        self.metrics['memory_usage'].append(process.memory_info().rss / 1024 / 1024)  # MB
        self.metrics['cpu_usage'].append(process.cpu_percent())
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.metrics['response_times']:
            return {"error": "No data collected"}
        
        response_times = self.metrics['response_times']
        duration = self.end_time - self.start_time if self.end_time else time.time() - self.start_time
        
        return {
            'duration': duration,
            'total_requests': len(response_times),
            'throughput': len(response_times) / duration if duration > 0 else 0,
            'avg_response_time': np.mean(response_times),
            'p95_response_time': np.percentile(response_times, 95),
            'p99_response_time': np.percentile(response_times, 99),
            'max_response_time': np.max(response_times),
            'min_response_time': np.min(response_times),
            'avg_memory_usage': np.mean(self.metrics['memory_usage']) if self.metrics['memory_usage'] else 0,
            'max_memory_usage': np.max(self.metrics['memory_usage']) if self.metrics['memory_usage'] else 0,
            'avg_cpu_usage': np.mean(self.metrics['cpu_usage']) if self.metrics['cpu_usage'] else 0,
            'max_cpu_usage': np.max(self.metrics['cpu_usage']) if self.metrics['cpu_usage'] else 0
        }


class TestHighConcurrencyAPI:
    """高并发API测试"""
    
    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)
    
    def test_concurrent_health_checks(self, client):
        """测试并发健康检查"""
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        def make_health_check():
            start_time = time.time()
            try:
                response = client.get("/api/monitor/health")
                end_time = time.time()
                metrics.record_response_time(end_time - start_time)
                return response.status_code
            except Exception as e:
                end_time = time.time()
                metrics.record_response_time(end_time - start_time)
                return 500
        
        # 并发执行1000个请求
        num_requests = 1000
        max_workers = 50
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(make_health_check) for _ in range(num_requests)]
            results = []
            
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
                if len(results) % 100 == 0:
                    metrics.record_system_metrics()
        
        metrics.stop_monitoring()
        summary = metrics.get_summary()
        
        # 性能断言
        success_rate = sum(1 for status in results if status == 200) / len(results)
        assert success_rate >= 0.95, f"成功率过低: {success_rate:.2%}"
        assert summary['avg_response_time'] < 1.0, f"平均响应时间过长: {summary['avg_response_time']:.3f}s"
        assert summary['p95_response_time'] < 2.0, f"P95响应时间过长: {summary['p95_response_time']:.3f}s"
        
        print(f"并发健康检查测试结果:")
        print(f"  总请求数: {summary['total_requests']}")
        print(f"  吞吐量: {summary['throughput']:.1f} req/s")
        print(f"  平均响应时间: {summary['avg_response_time']:.3f}s")
        print(f"  P95响应时间: {summary['p95_response_time']:.3f}s")
        print(f"  成功率: {success_rate:.2%}")
    
    def test_mixed_endpoint_load(self, client):
        """测试混合端点负载"""
        endpoints = [
            ("/api/monitor/health", "GET", None),
            ("/api/scenarios/", "GET", None),
            ("/api/simulations/status", "GET", None),
            ("/api/validator/diagnose", "POST", {"target": "system", "checks": ["connectivity"]})
        ]
        
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        def make_random_request():
            endpoint, method, data = random.choice(endpoints)
            start_time = time.time()
            
            try:
                if method == "GET":
                    response = client.get(endpoint)
                else:
                    response = client.post(endpoint, json=data)
                
                end_time = time.time()
                metrics.record_response_time(end_time - start_time)
                return response.status_code
            except Exception:
                end_time = time.time()
                metrics.record_response_time(end_time - start_time)
                return 500
        
        # 执行500个随机请求
        num_requests = 500
        max_workers = 20
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(make_random_request) for _ in range(num_requests)]
            results = []
            
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
                if len(results) % 50 == 0:
                    metrics.record_system_metrics()
        
        metrics.stop_monitoring()
        summary = metrics.get_summary()
        
        # 性能断言
        success_rate = sum(1 for status in results if status in [200, 201, 202]) / len(results)
        assert success_rate >= 0.90, f"混合负载成功率过低: {success_rate:.2%}"
        
        print(f"混合端点负载测试结果:")
        print(f"  总请求数: {summary['total_requests']}")
        print(f"  吞吐量: {summary['throughput']:.1f} req/s")
        print(f"  平均响应时间: {summary['avg_response_time']:.3f}s")
        print(f"  成功率: {success_rate:.2%}")
    
    def test_burst_load_handling(self, client):
        """测试突发负载处理"""
        metrics = PerformanceMetrics()
        
        def burst_requests(burst_size: int, delay: float):
            """执行突发请求"""
            def make_request():
                start_time = time.time()
                response = client.get("/api/monitor/health")
                end_time = time.time()
                metrics.record_response_time(end_time - start_time)
                return response.status_code
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=burst_size) as executor:
                futures = [executor.submit(make_request) for _ in range(burst_size)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            time.sleep(delay)
            return results
        
        metrics.start_monitoring()
        
        # 执行多轮突发负载
        all_results = []
        burst_configs = [
            (50, 1.0),   # 50个请求，间隔1秒
            (100, 2.0),  # 100个请求，间隔2秒
            (200, 3.0),  # 200个请求，间隔3秒
            (100, 1.0),  # 100个请求，间隔1秒
            (50, 1.0)    # 50个请求，间隔1秒
        ]
        
        for burst_size, delay in burst_configs:
            print(f"执行突发负载: {burst_size} 个请求")
            results = burst_requests(burst_size, delay)
            all_results.extend(results)
            metrics.record_system_metrics()
        
        metrics.stop_monitoring()
        summary = metrics.get_summary()
        
        # 性能断言
        success_rate = sum(1 for status in all_results if status == 200) / len(all_results)
        assert success_rate >= 0.95, f"突发负载成功率过低: {success_rate:.2%}"
        
        print(f"突发负载测试结果:")
        print(f"  总请求数: {len(all_results)}")
        print(f"  平均响应时间: {summary['avg_response_time']:.3f}s")
        print(f"  P99响应时间: {summary['p99_response_time']:.3f}s")
        print(f"  成功率: {success_rate:.2%}")


class TestWebSocketStress:
    """WebSocket压力测试"""
    
    @pytest.mark.asyncio
    async def test_massive_connections(self):
        """测试大量连接"""
        monitor_service = WebSocketMonitorService()
        connections = []
        
        # 创建1000个模拟连接
        connection_count = 1000
        
        async def create_connection(conn_id):
            mock_ws = AsyncMock()
            mock_ws.send = AsyncMock()
            mock_ws.receive = AsyncMock()
            
            await monitor_service.connect(mock_ws)
            connections.append(mock_ws)
            
            # 模拟连接活动
            await asyncio.sleep(0.01)
            return conn_id
        
        start_time = time.time()
        
        # 批量创建连接
        batch_size = 100
        for i in range(0, connection_count, batch_size):
            batch_tasks = [
                create_connection(j) 
                for j in range(i, min(i + batch_size, connection_count))
            ]
            await asyncio.gather(*batch_tasks)
            
            print(f"已创建 {len(connections)} 个连接")
        
        creation_time = time.time() - start_time
        
        # 测试广播性能
        broadcast_start = time.time()
        test_message = {
            "type": "stress_test",
            "timestamp": time.time(),
            "data": {"test_value": 42}
        }
        
        await monitor_service.broadcast(test_message)
        broadcast_time = time.time() - broadcast_start
        
        # 清理连接
        cleanup_start = time.time()
        for ws in connections:
            await monitor_service.disconnect(ws)
        cleanup_time = time.time() - cleanup_start
        
        # 性能断言
        assert len(connections) == connection_count, f"连接数不匹配: {len(connections)} != {connection_count}"
        assert creation_time < 30.0, f"连接创建时间过长: {creation_time:.2f}s"
        assert broadcast_time < 5.0, f"广播时间过长: {broadcast_time:.2f}s"
        
        print(f"大量连接测试结果:")
        print(f"  连接数: {len(connections)}")
        print(f"  创建时间: {creation_time:.2f}s")
        print(f"  广播时间: {broadcast_time:.2f}s")
        print(f"  清理时间: {cleanup_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_high_frequency_messages(self):
        """测试高频消息"""
        monitor_service = WebSocketMonitorService()
        
        # 创建10个连接
        connections = []
        for i in range(10):
            mock_ws = AsyncMock()
            mock_ws.send = AsyncMock()
            await monitor_service.connect(mock_ws)
            connections.append(mock_ws)
        
        # 高频发送消息
        message_count = 10000
        start_time = time.time()
        
        for i in range(message_count):
            message = {
                "type": "high_frequency_test",
                "id": i,
                "timestamp": time.time(),
                "data": {"value": i * 0.1}
            }
            await monitor_service.broadcast(message)
            
            # 每1000条消息打印进度
            if (i + 1) % 1000 == 0:
                print(f"已发送 {i + 1} 条消息")
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = message_count / duration
        
        # 清理连接
        for ws in connections:
            await monitor_service.disconnect(ws)
        
        # 性能断言
        assert throughput > 1000, f"消息吞吐量过低: {throughput:.1f} msg/s"
        
        print(f"高频消息测试结果:")
        print(f"  消息数: {message_count}")
        print(f"  持续时间: {duration:.2f}s")
        print(f"  吞吐量: {throughput:.1f} msg/s")
    
    @pytest.mark.asyncio
    async def test_connection_churn(self):
        """测试连接频繁建立和断开"""
        monitor_service = WebSocketMonitorService()
        
        async def connection_lifecycle(conn_id):
            """连接生命周期"""
            mock_ws = AsyncMock()
            mock_ws.send = AsyncMock()
            
            # 连接
            await monitor_service.connect(mock_ws)
            
            # 短暂活动
            await asyncio.sleep(random.uniform(0.01, 0.1))
            
            # 断开
            await monitor_service.disconnect(mock_ws)
            
            return conn_id
        
        # 执行1000次连接生命周期
        cycle_count = 1000
        start_time = time.time()
        
        # 批量执行
        batch_size = 50
        for i in range(0, cycle_count, batch_size):
            batch_tasks = [
                connection_lifecycle(j)
                for j in range(i, min(i + batch_size, cycle_count))
            ]
            await asyncio.gather(*batch_tasks)
            
            if (i + batch_size) % 200 == 0:
                print(f"已完成 {i + batch_size} 个连接周期")
        
        end_time = time.time()
        duration = end_time - start_time
        cycles_per_second = cycle_count / duration
        
        # 性能断言
        assert cycles_per_second > 100, f"连接周期频率过低: {cycles_per_second:.1f} cycles/s"
        assert len(monitor_service.active_connections) == 0, "存在未清理的连接"
        
        print(f"连接频繁建立断开测试结果:")
        print(f"  周期数: {cycle_count}")
        print(f"  持续时间: {duration:.2f}s")
        print(f"  频率: {cycles_per_second:.1f} cycles/s")


class TestLargeScaleSimulation:
    """大规模仿真测试"""
    
    def test_multiple_concurrent_simulations(self):
        """测试多个并发仿真"""
        runner = RunnerAgent()
        
        def create_simulation_config(sim_id: int) -> Dict[str, Any]:
            """创建仿真配置"""
            return {
                "scenario_name": f"concurrent_sim_{sim_id}",
                "description": f"并发仿真测试 #{sim_id}",
                "components": {
                    "system": {
                        "type": "TestSystem",
                        "parameters": {
                            "size": random.randint(100, 1000),
                            "complexity": random.uniform(0.1, 1.0)
                        }
                    }
                },
                "simulation": {
                    "duration": random.uniform(10.0, 100.0),
                    "time_step": 0.1,
                    "output_interval": 1.0
                }
            }
        
        async def run_simulation(sim_id: int):
            """运行单个仿真"""
            config = create_simulation_config(sim_id)
            
            with patch.object(runner, '_execute_simulation') as mock_execute:
                # 模拟仿真执行时间
                execution_time = config["simulation"]["duration"] * 0.01  # 缩放时间
                
                async def mock_simulation():
                    await asyncio.sleep(execution_time)
                    return {
                        "status": "completed",
                        "duration": config["simulation"]["duration"],
                        "results": {
                            "time": list(range(int(config["simulation"]["duration"]))),
                            "values": [random.random() for _ in range(int(config["simulation"]["duration"]))]
                        }
                    }
                
                mock_execute.side_effect = mock_simulation
                result = await runner.run_simulation(config)
                return sim_id, result
        
        async def run_concurrent_simulations():
            """运行并发仿真"""
            sim_count = 20
            start_time = time.time()
            
            # 并发执行仿真
            tasks = [run_simulation(i) for i in range(sim_count)]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            
            return results, duration
        
        # 执行测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results, duration = loop.run_until_complete(run_concurrent_simulations())
        loop.close()
        
        # 验证结果
        successful_sims = sum(1 for _, result in results if result["status"] == "completed")
        success_rate = successful_sims / len(results)
        
        assert success_rate >= 0.95, f"并发仿真成功率过低: {success_rate:.2%}"
        assert duration < 60.0, f"并发仿真总时间过长: {duration:.2f}s"
        
        print(f"并发仿真测试结果:")
        print(f"  仿真数量: {len(results)}")
        print(f"  成功数量: {successful_sims}")
        print(f"  成功率: {success_rate:.2%}")
        print(f"  总时间: {duration:.2f}s")
    
    def test_large_dataset_processing(self):
        """测试大数据集处理"""
        from api.agents.analyst_reporter_agent import AnalystAndReporterAgent
        
        analyst = AnalystAndReporterAgent()
        
        # 创建大型数据集
        data_size = 100000
        large_dataset = {
            "time": list(range(data_size)),
            "values": [random.random() * 100 for _ in range(data_size)],
            "secondary": [random.random() * 50 for _ in range(data_size)],
            "categories": [f"cat_{i % 10}" for i in range(data_size)]
        }
        
        async def analyze_large_dataset():
            start_time = time.time()
            
            with patch.object(analyst, '_perform_statistical_analysis') as mock_analysis:
                mock_analysis.return_value = {
                    "mean": np.mean(large_dataset["values"]),
                    "std": np.std(large_dataset["values"]),
                    "min": np.min(large_dataset["values"]),
                    "max": np.max(large_dataset["values"]),
                    "count": len(large_dataset["values"])
                }
                
                result = await analyst.analyze_results(large_dataset)
                
            end_time = time.time()
            processing_time = end_time - start_time
            
            return result, processing_time
        
        # 执行分析
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result, processing_time = loop.run_until_complete(analyze_large_dataset())
        loop.close()
        
        # 性能断言
        assert result is not None, "大数据集分析失败"
        assert processing_time < 30.0, f"大数据集处理时间过长: {processing_time:.2f}s"
        
        throughput = data_size / processing_time
        assert throughput > 1000, f"数据处理吞吐量过低: {throughput:.1f} records/s"
        
        print(f"大数据集处理测试结果:")
        print(f"  数据量: {data_size:,} 条记录")
        print(f"  处理时间: {processing_time:.2f}s")
        print(f"  吞吐量: {throughput:.1f} records/s")


class TestMemoryAndCPUStress:
    """内存和CPU压力测试"""
    
    def test_memory_intensive_operations(self):
        """测试内存密集型操作"""
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建大量智能体实例
        agents = []
        agent_count = 1000
        
        print(f"初始内存使用: {initial_memory:.1f}MB")
        
        for i in range(agent_count):
            agent = ChiefModelingAgent()
            agents.append(agent)
            
            if (i + 1) % 100 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                print(f"创建 {i + 1} 个智能体，内存使用: {current_memory:.1f}MB")
        
        peak_memory = process.memory_info().rss / 1024 / 1024
        memory_per_agent = (peak_memory - initial_memory) / agent_count
        
        # 执行内存密集型操作
        large_data = []
        for i in range(100):
            # 创建大型数据结构
            data_chunk = {
                "id": i,
                "data": [random.random() for _ in range(10000)],
                "metadata": {f"key_{j}": f"value_{j}" for j in range(1000)}
            }
            large_data.append(data_chunk)
        
        operation_memory = process.memory_info().rss / 1024 / 1024
        
        # 清理内存
        del agents
        del large_data
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_cleanup = operation_memory - final_memory
        
        # 性能断言
        assert memory_per_agent < 10.0, f"单个智能体内存使用过多: {memory_per_agent:.2f}MB"
        assert memory_cleanup > 0, "内存清理无效"
        
        cleanup_rate = memory_cleanup / (operation_memory - initial_memory)
        assert cleanup_rate > 0.7, f"内存清理率过低: {cleanup_rate:.2%}"
        
        print(f"内存压力测试结果:")
        print(f"  智能体数量: {agent_count}")
        print(f"  峰值内存: {peak_memory:.1f}MB")
        print(f"  单个智能体内存: {memory_per_agent:.2f}MB")
        print(f"  内存清理: {memory_cleanup:.1f}MB")
        print(f"  清理率: {cleanup_rate:.2%}")
    
    def test_cpu_intensive_operations(self):
        """测试CPU密集型操作"""
        def cpu_intensive_task(task_id: int, duration: float):
            """CPU密集型任务"""
            start_time = time.time()
            result = 0
            
            while time.time() - start_time < duration:
                # 执行计算密集型操作
                for i in range(1000):
                    result += i ** 2
                    result = result % 1000000
            
            return task_id, result
        
        # 测试多进程CPU使用
        cpu_count = multiprocessing.cpu_count()
        task_duration = 2.0  # 每个任务2秒
        
        start_time = time.time()
        
        with multiprocessing.Pool(processes=cpu_count) as pool:
            tasks = [(i, task_duration) for i in range(cpu_count * 2)]
            results = pool.starmap(cpu_intensive_task, tasks)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # 计算CPU利用率
        expected_duration = task_duration * 2  # 两轮任务
        cpu_efficiency = expected_duration / total_duration
        
        # 性能断言
        assert len(results) == cpu_count * 2, "任务执行数量不正确"
        assert cpu_efficiency > 0.8, f"CPU利用率过低: {cpu_efficiency:.2%}"
        
        print(f"CPU压力测试结果:")
        print(f"  CPU核心数: {cpu_count}")
        print(f"  任务数量: {len(results)}")
        print(f"  总时间: {total_duration:.2f}s")
        print(f"  CPU效率: {cpu_efficiency:.2%}")
    
    def test_mixed_resource_stress(self):
        """测试混合资源压力"""
        def mixed_workload(worker_id: int):
            """混合工作负载"""
            # CPU密集型操作
            result = 0
            for i in range(100000):
                result += i ** 2
            
            # 内存密集型操作
            large_list = [random.random() for _ in range(50000)]
            
            # I/O操作模拟
            time.sleep(0.01)
            
            return worker_id, len(large_list), result % 1000
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        start_time = time.time()
        
        # 并发执行混合工作负载
        worker_count = 20
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(mixed_workload, i) for i in range(worker_count * 3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        peak_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = peak_memory - initial_memory
        
        # 性能断言
        assert len(results) == worker_count * 3, "工作负载执行数量不正确"
        assert duration < 30.0, f"混合工作负载时间过长: {duration:.2f}s"
        assert memory_increase < 500, f"内存增长过多: {memory_increase:.1f}MB"
        
        throughput = len(results) / duration
        
        print(f"混合资源压力测试结果:")
        print(f"  工作负载数: {len(results)}")
        print(f"  执行时间: {duration:.2f}s")
        print(f"  吞吐量: {throughput:.1f} tasks/s")
        print(f"  内存增长: {memory_increase:.1f}MB")


class TestLongRunningStability:
    """长时间运行稳定性测试"""
    
    @pytest.mark.slow
    def test_extended_operation_stability(self):
        """测试长时间运行稳定性（标记为慢速测试）"""
        monitor_service = WebSocketMonitorService()
        metrics = PerformanceMetrics()
        
        async def long_running_test():
            # 创建持久连接
            connections = []
            for i in range(10):
                mock_ws = AsyncMock()
                mock_ws.send = AsyncMock()
                await monitor_service.connect(mock_ws)
                connections.append(mock_ws)
            
            metrics.start_monitoring()
            
            # 运行30分钟的测试（在实际环境中）
            # 这里缩短为30秒用于测试
            test_duration = 30.0
            start_time = time.time()
            message_count = 0
            
            while time.time() - start_time < test_duration:
                # 定期发送消息
                message = {
                    "type": "stability_test",
                    "id": message_count,
                    "timestamp": time.time()
                }
                await monitor_service.broadcast(message)
                message_count += 1
                
                # 记录系统指标
                if message_count % 100 == 0:
                    metrics.record_system_metrics()
                
                await asyncio.sleep(0.1)  # 10Hz频率
            
            metrics.stop_monitoring()
            
            # 清理连接
            for ws in connections:
                await monitor_service.disconnect(ws)
            
            return message_count
        
        # 执行长时间测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        message_count = loop.run_until_complete(long_running_test())
        loop.close()
        
        summary = metrics.get_summary()
        
        # 稳定性断言
        assert message_count > 200, f"消息发送数量过少: {message_count}"
        assert summary['avg_memory_usage'] > 0, "内存监控数据缺失"
        
        # 检查内存是否稳定（没有明显泄漏）
        if len(metrics.metrics['memory_usage']) > 10:
            early_memory = np.mean(metrics.metrics['memory_usage'][:5])
            late_memory = np.mean(metrics.metrics['memory_usage'][-5:])
            memory_growth = (late_memory - early_memory) / early_memory
            
            assert memory_growth < 0.5, f"内存增长过快，可能存在泄漏: {memory_growth:.2%}"
        
        print(f"长时间稳定性测试结果:")
        print(f"  运行时间: {summary['duration']:.1f}s")
        print(f"  消息数量: {message_count}")
        print(f"  平均内存: {summary['avg_memory_usage']:.1f}MB")
        print(f"  最大内存: {summary['max_memory_usage']:.1f}MB")
    
    def test_memory_leak_detection(self):
        """测试内存泄漏检测"""
        import gc
        
        def create_and_destroy_agents(count: int):
            """创建并销毁智能体"""
            agents = []
            for i in range(count):
                agent = ChiefModelingAgent()
                agents.append(agent)
            
            # 模拟使用
            for agent in agents:
                # 执行一些操作
                pass
            
            # 销毁
            del agents
            gc.collect()
        
        process = psutil.Process()
        memory_samples = []
        
        # 多轮创建和销毁
        rounds = 10
        agents_per_round = 100
        
        for round_num in range(rounds):
            # 记录轮次开始时的内存
            start_memory = process.memory_info().rss / 1024 / 1024
            
            # 创建和销毁智能体
            create_and_destroy_agents(agents_per_round)
            
            # 记录轮次结束时的内存
            end_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(end_memory)
            
            print(f"轮次 {round_num + 1}: {start_memory:.1f}MB -> {end_memory:.1f}MB")
        
        # 分析内存趋势
        if len(memory_samples) >= 5:
            # 计算内存增长趋势
            x = np.arange(len(memory_samples))
            y = np.array(memory_samples)
            
            # 简单线性回归
            slope = np.polyfit(x, y, 1)[0]
            
            # 内存增长率应该很小
            growth_rate = slope / memory_samples[0] if memory_samples[0] > 0 else 0
            
            assert abs(growth_rate) < 0.1, f"检测到内存泄漏，增长率: {growth_rate:.3f}"
            
            print(f"内存泄漏检测结果:")
            print(f"  测试轮次: {rounds}")
            print(f"  内存增长率: {growth_rate:.3f}")
            print(f"  初始内存: {memory_samples[0]:.1f}MB")
            print(f"  最终内存: {memory_samples[-1]:.1f}MB")


if __name__ == "__main__":
    # 运行性能测试
    # 注意：某些测试可能需要较长时间，可以使用 -m 参数选择性运行
    pytest.main(["-v", __file__, "-m", "not slow", "--tb=short"])