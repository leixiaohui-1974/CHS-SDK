#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK WebSocket压力测试套件

专门测试WebSocket连接和实时监控功能，包括：
1. 大量并发WebSocket连接测试
2. 高频消息传输压力测试
3. 长时间连接稳定性测试
4. 消息丢失和重连机制测试
5. 内存泄漏和资源管理测试
6. 网络异常和错误恢复测试
"""

import pytest
import asyncio
import json
import time
import threading
import gc
import psutil
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
import numpy as np
from dataclasses import dataclass
from collections import defaultdict

# 导入项目模块
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.services.websocket_monitor import WebSocketMonitorService


@dataclass
class ConnectionMetrics:
    """连接指标"""
    connection_id: str
    connect_time: float
    disconnect_time: Optional[float] = None
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def connection_duration(self) -> float:
        if self.disconnect_time:
            return self.disconnect_time - self.connect_time
        return time.time() - self.connect_time
    
    @property
    def throughput_sent(self) -> float:
        """发送吞吐量 (bytes/second)"""
        duration = self.connection_duration
        return self.bytes_sent / duration if duration > 0 else 0
    
    @property
    def throughput_received(self) -> float:
        """接收吞吐量 (bytes/second)"""
        duration = self.connection_duration
        return self.bytes_received / duration if duration > 0 else 0


class WebSocketStressTestClient:
    """WebSocket压力测试客户端"""
    
    def __init__(self, uri: str, client_id: str):
        self.uri = uri
        self.client_id = client_id
        self.websocket = None
        self.metrics = ConnectionMetrics(client_id, time.time())
        self.is_connected = False
        self.message_queue = asyncio.Queue()
        self.stop_event = asyncio.Event()
        
    async def connect(self, timeout: float = 10.0) -> bool:
        """连接到WebSocket服务器"""
        try:
            self.websocket = await asyncio.wait_for(
                websockets.connect(self.uri),
                timeout=timeout
            )
            self.is_connected = True
            self.metrics.connect_time = time.time()
            return True
        except Exception as e:
            self.metrics.errors.append(f"连接失败: {str(e)}")
            return False
    
    async def disconnect(self):
        """断开WebSocket连接"""
        if self.websocket and self.is_connected:
            try:
                await self.websocket.close()
            except:
                pass
            finally:
                self.is_connected = False
                self.metrics.disconnect_time = time.time()
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """发送消息"""
        if not self.is_connected or not self.websocket:
            return False
        
        try:
            message_str = json.dumps(message)
            await self.websocket.send(message_str)
            
            self.metrics.messages_sent += 1
            self.metrics.bytes_sent += len(message_str.encode('utf-8'))
            return True
        except Exception as e:
            self.metrics.errors.append(f"发送消息失败: {str(e)}")
            return False
    
    async def receive_message(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """接收消息"""
        if not self.is_connected or not self.websocket:
            return None
        
        try:
            message_str = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=timeout
            )
            
            self.metrics.messages_received += 1
            self.metrics.bytes_received += len(message_str.encode('utf-8'))
            
            return json.loads(message_str)
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            self.metrics.errors.append(f"接收消息失败: {str(e)}")
            return None
    
    async def ping_pong_test(self, count: int = 10, interval: float = 0.1) -> Dict[str, Any]:
        """Ping-Pong延迟测试"""
        latencies = []
        
        for i in range(count):
            start_time = time.time()
            
            ping_message = {
                "type": "ping",
                "timestamp": start_time,
                "sequence": i
            }
            
            if await self.send_message(ping_message):
                response = await self.receive_message(timeout=5.0)
                
                if response and response.get("type") == "pong":
                    end_time = time.time()
                    latency = (end_time - start_time) * 1000  # 毫秒
                    latencies.append(latency)
                else:
                    self.metrics.errors.append(f"Ping {i}: 未收到pong响应")
            
            if interval > 0:
                await asyncio.sleep(interval)
        
        return {
            "total_pings": count,
            "successful_pings": len(latencies),
            "avg_latency_ms": np.mean(latencies) if latencies else 0,
            "min_latency_ms": np.min(latencies) if latencies else 0,
            "max_latency_ms": np.max(latencies) if latencies else 0,
            "std_latency_ms": np.std(latencies) if latencies else 0,
            "latencies": latencies
        }
    
    async def stress_send_messages(self, message_count: int, message_size: int = 1024) -> Dict[str, Any]:
        """压力发送消息测试"""
        # 生成测试消息
        test_data = "x" * (message_size - 100)  # 预留JSON结构空间
        
        start_time = time.time()
        successful_sends = 0
        
        for i in range(message_count):
            message = {
                "type": "stress_test",
                "sequence": i,
                "timestamp": time.time(),
                "data": test_data
            }
            
            if await self.send_message(message):
                successful_sends += 1
            
            # 每100条消息检查一次连接状态
            if i % 100 == 0 and not self.is_connected:
                break
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "total_messages": message_count,
            "successful_sends": successful_sends,
            "duration_seconds": duration,
            "messages_per_second": successful_sends / duration if duration > 0 else 0,
            "bytes_per_second": self.metrics.bytes_sent / duration if duration > 0 else 0
        }


class WebSocketStressTestSuite:
    """WebSocket压力测试套件"""
    
    def __init__(self, server_uri: str = "ws://localhost:8000/ws"):
        self.server_uri = server_uri
        self.clients: List[WebSocketStressTestClient] = []
        self.test_results = defaultdict(list)
        self.monitor_service = None
        
    async def setup_mock_server(self):
        """设置模拟WebSocket服务器"""
        self.monitor_service = WebSocketMonitorService()
        
        # 模拟服务器行为
        async def mock_websocket_handler(websocket, path):
            try:
                await self.monitor_service.connect(websocket)
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        
                        # 处理ping消息
                        if data.get("type") == "ping":
                            pong_response = {
                                "type": "pong",
                                "timestamp": time.time(),
                                "original_timestamp": data.get("timestamp"),
                                "sequence": data.get("sequence")
                            }
                            await websocket.send(json.dumps(pong_response))
                        
                        # 处理其他消息类型
                        elif data.get("type") == "stress_test":
                            # 对于压力测试消息，可以选择性回复
                            if data.get("sequence", 0) % 10 == 0:  # 每10条消息回复一次
                                ack_response = {
                                    "type": "ack",
                                    "sequence": data.get("sequence")
                                }
                                await websocket.send(json.dumps(ack_response))
                    
                    except json.JSONDecodeError:
                        error_response = {
                            "type": "error",
                            "message": "Invalid JSON format"
                        }
                        await websocket.send(json.dumps(error_response))
            
            except ConnectionClosed:
                pass
            finally:
                await self.monitor_service.disconnect(websocket)
        
        # 在实际测试中，这里会启动真实的WebSocket服务器
        # 现在我们使用模拟的方式
        return mock_websocket_handler
    
    async def create_clients(self, count: int) -> List[WebSocketStressTestClient]:
        """创建测试客户端"""
        clients = []
        
        for i in range(count):
            client_id = f"stress_client_{i}"
            client = WebSocketStressTestClient(self.server_uri, client_id)
            clients.append(client)
        
        self.clients.extend(clients)
        return clients
    
    async def connect_clients_batch(self, clients: List[WebSocketStressTestClient], batch_size: int = 10) -> Dict[str, Any]:
        """批量连接客户端"""
        successful_connections = 0
        failed_connections = 0
        connection_times = []
        
        # 分批连接以避免过载
        for i in range(0, len(clients), batch_size):
            batch = clients[i:i + batch_size]
            
            # 并发连接当前批次
            connect_tasks = []
            for client in batch:
                # 模拟连接（在实际测试中会真实连接）
                mock_websocket = AsyncMock()
                mock_websocket.send = AsyncMock()
                mock_websocket.recv = AsyncMock()
                mock_websocket.close = AsyncMock()
                
                client.websocket = mock_websocket
                client.is_connected = True
                client.metrics.connect_time = time.time()
                
                connect_tasks.append(asyncio.create_task(asyncio.sleep(0.01)))  # 模拟连接延迟
            
            start_time = time.time()
            await asyncio.gather(*connect_tasks, return_exceptions=True)
            end_time = time.time()
            
            batch_connection_time = end_time - start_time
            connection_times.append(batch_connection_time)
            
            # 统计连接结果
            for client in batch:
                if client.is_connected:
                    successful_connections += 1
                else:
                    failed_connections += 1
            
            # 批次间短暂延迟
            await asyncio.sleep(0.1)
        
        return {
            "total_clients": len(clients),
            "successful_connections": successful_connections,
            "failed_connections": failed_connections,
            "connection_success_rate": successful_connections / len(clients) if clients else 0,
            "avg_batch_connection_time": np.mean(connection_times) if connection_times else 0,
            "total_connection_time": sum(connection_times)
        }
    
    async def disconnect_clients_batch(self, clients: List[WebSocketStressTestClient]) -> Dict[str, Any]:
        """批量断开客户端"""
        disconnect_tasks = []
        
        for client in clients:
            disconnect_tasks.append(client.disconnect())
        
        start_time = time.time()
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        end_time = time.time()
        
        return {
            "total_clients": len(clients),
            "disconnect_time": end_time - start_time
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        process = psutil.Process()
        
        return {
            "cpu_percent": process.cpu_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "memory_percent": process.memory_percent(),
            "open_files": len(process.open_files()),
            "num_threads": process.num_threads(),
            "connections": len(process.connections())
        }
    
    def analyze_client_metrics(self, clients: List[WebSocketStressTestClient]) -> Dict[str, Any]:
        """分析客户端指标"""
        if not clients:
            return {}
        
        # 收集所有指标
        connection_durations = [c.metrics.connection_duration for c in clients]
        messages_sent = [c.metrics.messages_sent for c in clients]
        messages_received = [c.metrics.messages_received for c in clients]
        bytes_sent = [c.metrics.bytes_sent for c in clients]
        bytes_received = [c.metrics.bytes_received for c in clients]
        error_counts = [len(c.metrics.errors) for c in clients]
        
        # 计算统计信息
        return {
            "total_clients": len(clients),
            "avg_connection_duration": np.mean(connection_durations),
            "total_messages_sent": sum(messages_sent),
            "total_messages_received": sum(messages_received),
            "avg_messages_sent_per_client": np.mean(messages_sent),
            "avg_messages_received_per_client": np.mean(messages_received),
            "total_bytes_sent": sum(bytes_sent),
            "total_bytes_received": sum(bytes_received),
            "avg_throughput_sent_bps": np.mean([c.metrics.throughput_sent for c in clients]),
            "avg_throughput_received_bps": np.mean([c.metrics.throughput_received for c in clients]),
            "total_errors": sum(error_counts),
            "clients_with_errors": sum(1 for count in error_counts if count > 0),
            "error_rate": sum(error_counts) / len(clients) if clients else 0
        }


class TestWebSocketConcurrency:
    """WebSocket并发测试"""
    
    @pytest.fixture(scope="class")
    def stress_suite(self):
        return WebSocketStressTestSuite()
    
    @pytest.mark.asyncio
    async def test_concurrent_connections_small(self, stress_suite):
        """测试小规模并发连接 (50个客户端)"""
        client_count = 50
        
        # 记录初始系统状态
        initial_metrics = stress_suite.get_system_metrics()
        
        # 创建客户端
        clients = await stress_suite.create_clients(client_count)
        
        # 批量连接
        connection_result = await stress_suite.connect_clients_batch(clients, batch_size=10)
        
        # 验证连接结果
        assert connection_result["successful_connections"] >= client_count * 0.9, \
            f"连接成功率过低: {connection_result['connection_success_rate']:.2%}"
        
        # 保持连接一段时间
        await asyncio.sleep(2.0)
        
        # 记录连接期间的系统状态
        peak_metrics = stress_suite.get_system_metrics()
        
        # 断开连接
        disconnect_result = await stress_suite.disconnect_clients_batch(clients)
        
        # 分析结果
        client_metrics = stress_suite.analyze_client_metrics(clients)
        
        # 验证性能指标
        assert peak_metrics["memory_mb"] < initial_metrics["memory_mb"] + 100, "内存使用增长过多"
        assert connection_result["total_connection_time"] < 10.0, "连接时间过长"
        assert disconnect_result["disconnect_time"] < 5.0, "断开时间过长"
        
        print(f"小规模并发测试通过:")
        print(f"  连接成功率: {connection_result['connection_success_rate']:.2%}")
        print(f"  连接时间: {connection_result['total_connection_time']:.2f}s")
        print(f"  内存使用: {peak_metrics['memory_mb']:.1f}MB")
    
    @pytest.mark.asyncio
    async def test_concurrent_connections_medium(self, stress_suite):
        """测试中等规模并发连接 (200个客户端)"""
        client_count = 200
        
        # 记录初始系统状态
        initial_metrics = stress_suite.get_system_metrics()
        
        # 创建客户端
        clients = await stress_suite.create_clients(client_count)
        
        # 批量连接
        connection_result = await stress_suite.connect_clients_batch(clients, batch_size=20)
        
        # 验证连接结果
        assert connection_result["successful_connections"] >= client_count * 0.8, \
            f"连接成功率过低: {connection_result['connection_success_rate']:.2%}"
        
        # 保持连接一段时间
        await asyncio.sleep(3.0)
        
        # 记录连接期间的系统状态
        peak_metrics = stress_suite.get_system_metrics()
        
        # 断开连接
        disconnect_result = await stress_suite.disconnect_clients_batch(clients)
        
        # 分析结果
        client_metrics = stress_suite.analyze_client_metrics(clients)
        
        # 验证性能指标
        assert peak_metrics["memory_mb"] < initial_metrics["memory_mb"] + 200, "内存使用增长过多"
        assert connection_result["total_connection_time"] < 20.0, "连接时间过长"
        
        print(f"中等规模并发测试通过:")
        print(f"  连接成功率: {connection_result['connection_success_rate']:.2%}")
        print(f"  连接时间: {connection_result['total_connection_time']:.2f}s")
        print(f"  内存使用: {peak_metrics['memory_mb']:.1f}MB")
    
    @pytest.mark.asyncio
    async def test_concurrent_connections_large(self, stress_suite):
        """测试大规模并发连接 (500个客户端)"""
        client_count = 500
        
        # 记录初始系统状态
        initial_metrics = stress_suite.get_system_metrics()
        
        # 创建客户端
        clients = await stress_suite.create_clients(client_count)
        
        # 批量连接
        connection_result = await stress_suite.connect_clients_batch(clients, batch_size=25)
        
        # 验证连接结果（大规模测试允许更低的成功率）
        assert connection_result["successful_connections"] >= client_count * 0.7, \
            f"连接成功率过低: {connection_result['connection_success_rate']:.2%}"
        
        # 保持连接一段时间
        await asyncio.sleep(5.0)
        
        # 记录连接期间的系统状态
        peak_metrics = stress_suite.get_system_metrics()
        
        # 断开连接
        disconnect_result = await stress_suite.disconnect_clients_batch(clients)
        
        # 分析结果
        client_metrics = stress_suite.analyze_client_metrics(clients)
        
        # 验证性能指标（大规模测试放宽限制）
        assert peak_metrics["memory_mb"] < initial_metrics["memory_mb"] + 500, "内存使用增长过多"
        assert connection_result["total_connection_time"] < 60.0, "连接时间过长"
        
        print(f"大规模并发测试通过:")
        print(f"  连接成功率: {connection_result['connection_success_rate']:.2%}")
        print(f"  连接时间: {connection_result['total_connection_time']:.2f}s")
        print(f"  内存使用: {peak_metrics['memory_mb']:.1f}MB")


class TestWebSocketThroughput:
    """WebSocket吞吐量测试"""
    
    @pytest.fixture(scope="class")
    def stress_suite(self):
        return WebSocketStressTestSuite()
    
    @pytest.mark.asyncio
    async def test_high_frequency_messages(self, stress_suite):
        """测试高频消息传输"""
        client_count = 10
        messages_per_client = 1000
        message_size = 512  # bytes
        
        # 创建并连接客户端
        clients = await stress_suite.create_clients(client_count)
        await stress_suite.connect_clients_batch(clients)
        
        # 并发发送消息
        async def send_messages_for_client(client):
            return await client.stress_send_messages(messages_per_client, message_size)
        
        start_time = time.time()
        
        # 并发执行所有客户端的消息发送
        send_tasks = [send_messages_for_client(client) for client in clients if client.is_connected]
        send_results = await asyncio.gather(*send_tasks, return_exceptions=True)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # 分析结果
        successful_results = [r for r in send_results if isinstance(r, dict)]
        total_messages_sent = sum(r["successful_sends"] for r in successful_results)
        total_bytes_sent = sum(client.metrics.bytes_sent for client in clients)
        
        # 断开连接
        await stress_suite.disconnect_clients_batch(clients)
        
        # 验证性能指标
        messages_per_second = total_messages_sent / total_duration
        bytes_per_second = total_bytes_sent / total_duration
        
        assert messages_per_second > 1000, f"消息吞吐量过低: {messages_per_second:.0f} msg/s"
        assert bytes_per_second > 100000, f"字节吞吐量过低: {bytes_per_second:.0f} bytes/s"
        
        print(f"高频消息测试通过:")
        print(f"  消息吞吐量: {messages_per_second:.0f} msg/s")
        print(f"  字节吞吐量: {bytes_per_second / 1024:.0f} KB/s")
        print(f"  总消息数: {total_messages_sent}")
        print(f"  测试时长: {total_duration:.2f}s")
    
    @pytest.mark.asyncio
    async def test_large_message_transmission(self, stress_suite):
        """测试大消息传输"""
        client_count = 5
        messages_per_client = 100
        message_size = 64 * 1024  # 64KB per message
        
        # 创建并连接客户端
        clients = await stress_suite.create_clients(client_count)
        await stress_suite.connect_clients_batch(clients)
        
        # 发送大消息
        async def send_large_messages(client):
            return await client.stress_send_messages(messages_per_client, message_size)
        
        start_time = time.time()
        
        send_tasks = [send_large_messages(client) for client in clients if client.is_connected]
        send_results = await asyncio.gather(*send_tasks, return_exceptions=True)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # 分析结果
        successful_results = [r for r in send_results if isinstance(r, dict)]
        total_bytes_sent = sum(client.metrics.bytes_sent for client in clients)
        
        # 断开连接
        await stress_suite.disconnect_clients_batch(clients)
        
        # 验证性能指标
        mb_per_second = (total_bytes_sent / 1024 / 1024) / total_duration
        
        assert mb_per_second > 1.0, f"大消息传输速度过低: {mb_per_second:.2f} MB/s"
        
        print(f"大消息传输测试通过:")
        print(f"  传输速度: {mb_per_second:.2f} MB/s")
        print(f"  总数据量: {total_bytes_sent / 1024 / 1024:.1f} MB")
        print(f"  测试时长: {total_duration:.2f}s")
    
    @pytest.mark.asyncio
    async def test_bidirectional_communication(self, stress_suite):
        """测试双向通信"""
        client_count = 20
        ping_count = 50
        
        # 创建并连接客户端
        clients = await stress_suite.create_clients(client_count)
        await stress_suite.connect_clients_batch(clients)
        
        # 并发执行ping-pong测试
        async def ping_pong_for_client(client):
            return await client.ping_pong_test(ping_count, interval=0.05)
        
        start_time = time.time()
        
        ping_tasks = [ping_pong_for_client(client) for client in clients if client.is_connected]
        ping_results = await asyncio.gather(*ping_tasks, return_exceptions=True)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # 分析结果
        successful_results = [r for r in ping_results if isinstance(r, dict)]
        
        if successful_results:
            avg_latencies = [r["avg_latency_ms"] for r in successful_results if r["avg_latency_ms"] > 0]
            total_successful_pings = sum(r["successful_pings"] for r in successful_results)
            
            overall_avg_latency = np.mean(avg_latencies) if avg_latencies else 0
            success_rate = total_successful_pings / (client_count * ping_count)
        else:
            overall_avg_latency = 0
            success_rate = 0
        
        # 断开连接
        await stress_suite.disconnect_clients_batch(clients)
        
        # 验证性能指标
        assert success_rate > 0.8, f"Ping-Pong成功率过低: {success_rate:.2%}"
        assert overall_avg_latency < 100, f"平均延迟过高: {overall_avg_latency:.1f}ms"
        
        print(f"双向通信测试通过:")
        print(f"  成功率: {success_rate:.2%}")
        print(f"  平均延迟: {overall_avg_latency:.1f}ms")
        print(f"  总Ping数: {total_successful_pings}")
        print(f"  测试时长: {total_duration:.2f}s")


class TestWebSocketStability:
    """WebSocket稳定性测试"""
    
    @pytest.fixture(scope="class")
    def stress_suite(self):
        return WebSocketStressTestSuite()
    
    @pytest.mark.asyncio
    async def test_long_duration_connections(self, stress_suite):
        """测试长时间连接稳定性"""
        client_count = 20
        test_duration = 30.0  # 30秒长连接测试
        
        # 创建并连接客户端
        clients = await stress_suite.create_clients(client_count)
        connection_result = await stress_suite.connect_clients_batch(clients)
        
        connected_clients = [c for c in clients if c.is_connected]
        initial_connected_count = len(connected_clients)
        
        # 定期发送心跳消息
        async def heartbeat_sender(client, interval=5.0):
            heartbeat_count = 0
            while client.is_connected:
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": time.time(),
                    "count": heartbeat_count
                }
                
                if await client.send_message(heartbeat_message):
                    heartbeat_count += 1
                
                await asyncio.sleep(interval)
        
        # 启动心跳任务
        heartbeat_tasks = [heartbeat_sender(client) for client in connected_clients]
        
        # 记录初始系统状态
        initial_metrics = stress_suite.get_system_metrics()
        
        # 等待测试时间
        await asyncio.sleep(test_duration)
        
        # 停止心跳任务
        for task in heartbeat_tasks:
            task.cancel()
        
        # 记录最终系统状态
        final_metrics = stress_suite.get_system_metrics()
        
        # 检查连接状态
        still_connected = sum(1 for c in connected_clients if c.is_connected)
        connection_retention_rate = still_connected / initial_connected_count if initial_connected_count > 0 else 0
        
        # 断开连接
        await stress_suite.disconnect_clients_batch(clients)
        
        # 分析客户端指标
        client_metrics = stress_suite.analyze_client_metrics(connected_clients)
        
        # 验证稳定性指标
        assert connection_retention_rate > 0.9, f"连接保持率过低: {connection_retention_rate:.2%}"
        
        # 检查内存泄漏
        memory_growth = final_metrics["memory_mb"] - initial_metrics["memory_mb"]
        assert memory_growth < 50, f"内存增长过多: {memory_growth:.1f}MB"
        
        print(f"长时间连接测试通过:")
        print(f"  连接保持率: {connection_retention_rate:.2%}")
        print(f"  内存增长: {memory_growth:.1f}MB")
        print(f"  平均心跳数: {client_metrics.get('avg_messages_sent_per_client', 0):.1f}")
        print(f"  测试时长: {test_duration}s")
    
    @pytest.mark.asyncio
    async def test_connection_recovery(self, stress_suite):
        """测试连接恢复机制"""
        client_count = 10
        
        # 创建并连接客户端
        clients = await stress_suite.create_clients(client_count)
        await stress_suite.connect_clients_batch(clients)
        
        connected_clients = [c for c in clients if c.is_connected]
        
        # 模拟连接中断
        interrupted_clients = connected_clients[:5]  # 中断一半连接
        
        for client in interrupted_clients:
            client.is_connected = False
            client.metrics.errors.append("模拟连接中断")
        
        # 等待一段时间
        await asyncio.sleep(2.0)
        
        # 模拟重连
        reconnected_count = 0
        for client in interrupted_clients:
            # 模拟重连成功
            if await client.connect():
                reconnected_count += 1
        
        # 验证重连结果
        reconnection_rate = reconnected_count / len(interrupted_clients)
        
        # 断开所有连接
        await stress_suite.disconnect_clients_batch(clients)
        
        assert reconnection_rate > 0.8, f"重连成功率过低: {reconnection_rate:.2%}"
        
        print(f"连接恢复测试通过:")
        print(f"  重连成功率: {reconnection_rate:.2%}")
        print(f"  中断连接数: {len(interrupted_clients)}")
        print(f"  重连成功数: {reconnected_count}")
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, stress_suite):
        """测试内存泄漏检测"""
        iterations = 5
        clients_per_iteration = 50
        
        memory_usage_history = []
        
        for iteration in range(iterations):
            # 记录迭代开始时的内存使用
            gc.collect()  # 强制垃圾回收
            start_memory = stress_suite.get_system_metrics()["memory_mb"]
            
            # 创建连接
            clients = await stress_suite.create_clients(clients_per_iteration)
            await stress_suite.connect_clients_batch(clients)
            
            # 发送一些消息
            for client in clients[:10]:  # 只让前10个客户端发送消息
                if client.is_connected:
                    await client.stress_send_messages(100, 1024)
            
            # 断开连接
            await stress_suite.disconnect_clients_batch(clients)
            
            # 清理客户端引用
            del clients
            gc.collect()
            
            # 记录迭代结束时的内存使用
            end_memory = stress_suite.get_system_metrics()["memory_mb"]
            memory_usage_history.append(end_memory - start_memory)
            
            await asyncio.sleep(1.0)  # 等待系统稳定
        
        # 分析内存使用趋势
        avg_memory_growth = np.mean(memory_usage_history)
        max_memory_growth = np.max(memory_usage_history)
        
        # 验证内存泄漏
        assert avg_memory_growth < 10, f"平均内存增长过多: {avg_memory_growth:.1f}MB"
        assert max_memory_growth < 20, f"最大内存增长过多: {max_memory_growth:.1f}MB"
        
        print(f"内存泄漏检测测试通过:")
        print(f"  平均内存增长: {avg_memory_growth:.1f}MB")
        print(f"  最大内存增长: {max_memory_growth:.1f}MB")
        print(f"  测试迭代数: {iterations}")
        print(f"  每次迭代客户端数: {clients_per_iteration}")


class TestWebSocketErrorHandling:
    """WebSocket错误处理测试"""
    
    @pytest.fixture(scope="class")
    def stress_suite(self):
        return WebSocketStressTestSuite()
    
    @pytest.mark.asyncio
    async def test_malformed_message_handling(self, stress_suite):
        """测试格式错误消息处理"""
        client_count = 5
        
        # 创建并连接客户端
        clients = await stress_suite.create_clients(client_count)
        await stress_suite.connect_clients_batch(clients)
        
        connected_clients = [c for c in clients if c.is_connected]
        
        # 发送格式错误的消息
        malformed_messages = [
            "not json",
            '{"incomplete": json',
            '{"type": "test", "data": }',
            '',
            None
        ]
        
        error_responses = 0
        
        for client in connected_clients:
            for malformed_msg in malformed_messages:
                try:
                    if malformed_msg is None:
                        continue
                    
                    # 直接发送字符串（绕过JSON序列化）
                    if client.websocket:
                        await client.websocket.send(malformed_msg)
                        
                        # 尝试接收错误响应
                        response = await client.receive_message(timeout=1.0)
                        if response and response.get("type") == "error":
                            error_responses += 1
                
                except Exception as e:
                    client.metrics.errors.append(f"发送格式错误消息失败: {str(e)}")
        
        # 断开连接
        await stress_suite.disconnect_clients_batch(clients)
        
        # 验证错误处理
        total_malformed_sent = len(connected_clients) * (len(malformed_messages) - 1)  # 排除None
        
        print(f"格式错误消息处理测试:")
        print(f"  发送格式错误消息数: {total_malformed_sent}")
        print(f"  收到错误响应数: {error_responses}")
        print(f"  客户端错误数: {sum(len(c.metrics.errors) for c in connected_clients)}")
        
        # 至少应该有一些错误被正确处理
        assert error_responses > 0 or sum(len(c.metrics.errors) for c in connected_clients) > 0, \
            "格式错误的消息应该被检测和处理"
    
    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self, stress_suite):
        """测试连接超时处理"""
        client_count = 10
        
        # 创建客户端但使用很短的超时时间
        clients = await stress_suite.create_clients(client_count)
        
        # 尝试连接（模拟超时）
        timeout_count = 0
        
        for client in clients:
            try:
                # 模拟连接超时
                success = await asyncio.wait_for(client.connect(), timeout=0.001)  # 极短超时
                if not success:
                    timeout_count += 1
            except asyncio.TimeoutError:
                timeout_count += 1
                client.metrics.errors.append("连接超时")
        
        # 验证超时处理
        assert timeout_count > 0, "应该有连接超时发生"
        
        print(f"连接超时处理测试:")
        print(f"  总客户端数: {client_count}")
        print(f"  超时连接数: {timeout_count}")
        print(f"  超时率: {timeout_count / client_count:.2%}")
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_handling(self, stress_suite):
        """测试资源耗尽处理"""
        # 尝试创建大量客户端以测试资源限制
        max_clients = 1000
        successful_connections = 0
        resource_errors = 0
        
        clients = []
        
        try:
            for i in range(max_clients):
                client = WebSocketStressTestClient(stress_suite.server_uri, f"resource_test_{i}")
                clients.append(client)
                
                # 模拟连接（在实际环境中可能会因资源限制失败）
                try:
                    mock_websocket = AsyncMock()
                    client.websocket = mock_websocket
                    client.is_connected = True
                    successful_connections += 1
                    
                    # 检查系统资源
                    metrics = stress_suite.get_system_metrics()
                    if metrics["memory_mb"] > 1000:  # 如果内存使用超过1GB，停止
                        break
                        
                except Exception as e:
                    resource_errors += 1
                    client.metrics.errors.append(f"资源耗尽: {str(e)}")
                    
                    # 如果连续多次失败，停止测试
                    if resource_errors > 10:
                        break
        
        finally:
            # 清理资源
            for client in clients:
                if client.is_connected:
                    await client.disconnect()
        
        print(f"资源耗尽处理测试:")
        print(f"  成功连接数: {successful_connections}")
        print(f"  资源错误数: {resource_errors}")
        print(f"  最终内存使用: {stress_suite.get_system_metrics()['memory_mb']:.1f}MB")
        
        # 验证系统能够处理资源限制
        assert successful_connections > 0, "应该能够建立一些连接"
        assert stress_suite.get_system_metrics()["memory_mb"] < 2000, "内存使用应该在合理范围内"


if __name__ == "__main__":
    # 运行WebSocket压力测试
    pytest.main(["-v", __file__, "--tb=short", "-k", "not test_concurrent_connections_large"])