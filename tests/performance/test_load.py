"""压力测试和负载测试

测试系统在高负载下的性能表现。
"""

import asyncio
import aiohttp
import time
import statistics
import json
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading
import random

import pytest
import websockets
from dataclasses import dataclass

# 测试配置
LOAD_TEST_CONFIG = {
    "api_base_url": "http://localhost:8000",
    "websocket_url": "ws://localhost:8000/ws",
    "test_duration": 300,  # 5分钟
    "ramp_up_time": 60,    # 1分钟渐增
    "concurrent_users": 100,
    "requests_per_second": 50,
    "timeout": 30
}

# 测试用户池
TEST_USERS = [
    {"email": f"loadtest{i}@example.com", "password": "testpass123", "username": f"loaduser{i}"}
    for i in range(1, 101)
]

# 测试仿真配置模板
SIMULATION_TEMPLATES = [
    {
        "name": "Load Test Simulation {}",
        "description": "Load testing simulation",
        "duration": 1800,
        "time_step": 30,
        "config": {
            "nodes": [
                {"id": "reservoir_1", "type": "reservoir", "initial_level": 10.0, "capacity": 100.0},
                {"id": "pump_1", "type": "pump", "max_flow_rate": 5.0, "efficiency": 0.85}
            ],
            "connections": [{"from": "reservoir_1", "to": "pump_1", "type": "pipe"}]
        }
    },
    {
        "name": "Complex Load Test {}",
        "description": "Complex load testing simulation",
        "duration": 3600,
        "time_step": 60,
        "config": {
            "nodes": [
                {"id": f"node_{i}", "type": "reservoir", "initial_level": random.uniform(5, 15), "capacity": random.uniform(50, 150)}
                for i in range(10)
            ],
            "connections": [
                {"from": f"node_{i}", "to": f"node_{i+1}", "type": "pipe"}
                for i in range(9)
            ]
        }
    }
]


@dataclass
class RequestResult:
    """请求结果"""
    timestamp: float
    duration: float
    status_code: int
    success: bool
    error: str = None
    endpoint: str = None
    user_id: str = None


@dataclass
class LoadTestMetrics:
    """负载测试指标"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    error_rate: float
    throughput: float
    concurrent_users: int
    test_duration: float


class LoadTestUser:
    """负载测试用户"""
    
    def __init__(self, user_data: Dict[str, str], user_id: str):
        self.user_data = user_data
        self.user_id = user_id
        self.session = None
        self.auth_token = None
        self.simulation_ids = []
        self.results = []
        self.is_running = False
    
    async def setup(self):
        """用户设置"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=LOAD_TEST_CONFIG["timeout"])
        )
        
        # 注册和登录
        await self._register_and_login()
    
    async def teardown(self):
        """用户清理"""
        if self.session:
            await self.session.close()
    
    async def _register_and_login(self):
        """注册和登录"""
        try:
            # 注册
            async with self.session.post(
                f"{LOAD_TEST_CONFIG['api_base_url']}/api/auth/register",
                json=self.user_data
            ) as response:
                pass  # 忽略注册结果，可能已存在
            
            # 登录
            login_data = {
                "email": self.user_data["email"],
                "password": self.user_data["password"]
            }
            
            start_time = time.time()
            async with self.session.post(
                f"{LOAD_TEST_CONFIG['api_base_url']}/api/auth/login",
                json=login_data
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get("access_token")
                    
                    self.results.append(RequestResult(
                        timestamp=start_time,
                        duration=duration,
                        status_code=response.status,
                        success=True,
                        endpoint="/api/auth/login",
                        user_id=self.user_id
                    ))
                else:
                    self.results.append(RequestResult(
                        timestamp=start_time,
                        duration=duration,
                        status_code=response.status,
                        success=False,
                        error=f"Login failed: {response.status}",
                        endpoint="/api/auth/login",
                        user_id=self.user_id
                    ))
        
        except Exception as e:
            self.results.append(RequestResult(
                timestamp=time.time(),
                duration=0,
                status_code=0,
                success=False,
                error=str(e),
                endpoint="/api/auth/login",
                user_id=self.user_id
            ))
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> RequestResult:
        """发起请求"""
        headers = kwargs.get("headers", {})
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            kwargs["headers"] = headers
        
        start_time = time.time()
        try:
            async with self.session.request(method, f"{LOAD_TEST_CONFIG['api_base_url']}{endpoint}", **kwargs) as response:
                duration = time.time() - start_time
                
                return RequestResult(
                    timestamp=start_time,
                    duration=duration,
                    status_code=response.status,
                    success=200 <= response.status < 400,
                    endpoint=endpoint,
                    user_id=self.user_id
                )
        
        except Exception as e:
            duration = time.time() - start_time
            return RequestResult(
                timestamp=start_time,
                duration=duration,
                status_code=0,
                success=False,
                error=str(e),
                endpoint=endpoint,
                user_id=self.user_id
            )
    
    async def create_simulation(self) -> RequestResult:
        """创建仿真"""
        template = random.choice(SIMULATION_TEMPLATES)
        simulation_data = template.copy()
        simulation_data["name"] = template["name"].format(self.user_id)
        
        result = await self._make_request("POST", "/api/simulation/sessions", json=simulation_data)
        
        if result.success:
            # 这里应该解析响应获取simulation_id，简化处理
            self.simulation_ids.append(f"sim_{self.user_id}_{len(self.simulation_ids)}")
        
        return result
    
    async def start_simulation(self) -> RequestResult:
        """启动仿真"""
        if not self.simulation_ids:
            return RequestResult(
                timestamp=time.time(),
                duration=0,
                status_code=0,
                success=False,
                error="No simulations to start",
                endpoint="/api/simulation/sessions/start",
                user_id=self.user_id
            )
        
        sim_id = random.choice(self.simulation_ids)
        return await self._make_request("POST", f"/api/simulation/sessions/{sim_id}/start")
    
    async def get_simulation_status(self) -> RequestResult:
        """获取仿真状态"""
        if not self.simulation_ids:
            return RequestResult(
                timestamp=time.time(),
                duration=0,
                status_code=0,
                success=False,
                error="No simulations to check",
                endpoint="/api/simulation/sessions/status",
                user_id=self.user_id
            )
        
        sim_id = random.choice(self.simulation_ids)
        return await self._make_request("GET", f"/api/simulation/sessions/{sim_id}")
    
    async def get_simulation_results(self) -> RequestResult:
        """获取仿真结果"""
        if not self.simulation_ids:
            return RequestResult(
                timestamp=time.time(),
                duration=0,
                status_code=0,
                success=False,
                error="No simulations to get results",
                endpoint="/api/simulation/sessions/results",
                user_id=self.user_id
            )
        
        sim_id = random.choice(self.simulation_ids)
        return await self._make_request("GET", f"/api/simulation/sessions/{sim_id}/results")
    
    async def get_performance_metrics(self) -> RequestResult:
        """获取性能指标"""
        return await self._make_request("GET", "/api/performance/metrics")
    
    async def run_user_scenario(self, duration: float):
        """运行用户场景"""
        self.is_running = True
        end_time = time.time() + duration
        
        # 用户行为权重
        actions = [
            (self.create_simulation, 0.2),
            (self.start_simulation, 0.15),
            (self.get_simulation_status, 0.3),
            (self.get_simulation_results, 0.25),
            (self.get_performance_metrics, 0.1)
        ]
        
        while time.time() < end_time and self.is_running:
            # 随机选择动作
            action = random.choices(
                [action for action, _ in actions],
                weights=[weight for _, weight in actions]
            )[0]
            
            try:
                result = await action()
                self.results.append(result)
            except Exception as e:
                self.results.append(RequestResult(
                    timestamp=time.time(),
                    duration=0,
                    status_code=0,
                    success=False,
                    error=str(e),
                    endpoint="unknown",
                    user_id=self.user_id
                ))
            
            # 随机等待时间，模拟真实用户行为
            await asyncio.sleep(random.uniform(0.5, 3.0))
    
    def stop(self):
        """停止用户"""
        self.is_running = False


class LoadTestRunner:
    """负载测试运行器"""
    
    def __init__(self):
        self.users: List[LoadTestUser] = []
        self.all_results: List[RequestResult] = []
        self.start_time = None
        self.end_time = None
        self.is_running = False
    
    async def setup_users(self, num_users: int):
        """设置测试用户"""
        print(f"设置 {num_users} 个测试用户...")
        
        for i in range(num_users):
            user_data = TEST_USERS[i % len(TEST_USERS)]
            user = LoadTestUser(user_data, f"user_{i}")
            
            try:
                await user.setup()
                self.users.append(user)
            except Exception as e:
                print(f"用户 {i} 设置失败: {e}")
        
        print(f"成功设置 {len(self.users)} 个用户")
    
    async def run_load_test(self, duration: float, ramp_up_time: float = 0):
        """运行负载测试"""
        print(f"开始负载测试: {len(self.users)} 用户, {duration}秒, 渐增时间 {ramp_up_time}秒")
        
        self.is_running = True
        self.start_time = time.time()
        
        # 创建用户任务
        tasks = []
        
        for i, user in enumerate(self.users):
            # 计算用户启动延迟（渐增）
            if ramp_up_time > 0:
                delay = (i / len(self.users)) * ramp_up_time
                await asyncio.sleep(delay / len(self.users))  # 分批启动
            
            task = asyncio.create_task(user.run_user_scenario(duration))
            tasks.append(task)
        
        # 等待所有用户完成或超时
        try:
            await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=duration + 60)
        except asyncio.TimeoutError:
            print("负载测试超时，停止所有用户")
            for user in self.users:
                user.stop()
        
        self.end_time = time.time()
        self.is_running = False
        
        # 收集所有结果
        self.all_results = []
        for user in self.users:
            self.all_results.extend(user.results)
        
        print(f"负载测试完成，收集到 {len(self.all_results)} 个请求结果")
    
    async def cleanup(self):
        """清理资源"""
        print("清理测试用户...")
        for user in self.users:
            try:
                await user.teardown()
            except Exception as e:
                print(f"用户清理失败: {e}")
    
    def calculate_metrics(self) -> LoadTestMetrics:
        """计算测试指标"""
        if not self.all_results:
            return LoadTestMetrics(
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                average_response_time=0,
                median_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                min_response_time=0,
                max_response_time=0,
                requests_per_second=0,
                error_rate=0,
                throughput=0,
                concurrent_users=len(self.users),
                test_duration=0
            )
        
        # 基本统计
        total_requests = len(self.all_results)
        successful_requests = sum(1 for r in self.all_results if r.success)
        failed_requests = total_requests - successful_requests
        
        # 响应时间统计
        response_times = [r.duration for r in self.all_results if r.duration > 0]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # 百分位数
            sorted_times = sorted(response_times)
            p95_index = int(0.95 * len(sorted_times))
            p99_index = int(0.99 * len(sorted_times))
            p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_response_time
            p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else max_response_time
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        # 时间相关指标
        test_duration = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        requests_per_second = total_requests / test_duration if test_duration > 0 else 0
        error_rate = (failed_requests / total_requests) * 100 if total_requests > 0 else 0
        throughput = successful_requests / test_duration if test_duration > 0 else 0
        
        return LoadTestMetrics(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            throughput=throughput,
            concurrent_users=len(self.users),
            test_duration=test_duration
        )
    
    def generate_report(self, metrics: LoadTestMetrics) -> str:
        """生成测试报告"""
        report = f"""
=== 负载测试报告 ===
测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
测试持续时间: {metrics.test_duration:.2f} 秒
并发用户数: {metrics.concurrent_users}

=== 请求统计 ===
总请求数: {metrics.total_requests}
成功请求数: {metrics.successful_requests}
失败请求数: {metrics.failed_requests}
错误率: {metrics.error_rate:.2f}%

=== 性能指标 ===
平均响应时间: {metrics.average_response_time:.3f} 秒
中位数响应时间: {metrics.median_response_time:.3f} 秒
95%响应时间: {metrics.p95_response_time:.3f} 秒
99%响应时间: {metrics.p99_response_time:.3f} 秒
最小响应时间: {metrics.min_response_time:.3f} 秒
最大响应时间: {metrics.max_response_time:.3f} 秒

=== 吞吐量 ===
每秒请求数 (RPS): {metrics.requests_per_second:.2f}
每秒成功请求数: {metrics.throughput:.2f}

=== 端点统计 ===
"""
        
        # 按端点统计
        endpoint_stats = {}
        for result in self.all_results:
            endpoint = result.endpoint or "unknown"
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {"total": 0, "success": 0, "avg_time": 0, "times": []}
            
            endpoint_stats[endpoint]["total"] += 1
            if result.success:
                endpoint_stats[endpoint]["success"] += 1
            if result.duration > 0:
                endpoint_stats[endpoint]["times"].append(result.duration)
        
        for endpoint, stats in endpoint_stats.items():
            success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            avg_time = statistics.mean(stats["times"]) if stats["times"] else 0
            
            report += f"{endpoint}: {stats['total']} 请求, {success_rate:.1f}% 成功率, {avg_time:.3f}s 平均响应时间\n"
        
        return report
    
    def save_results(self, filename: str):
        """保存测试结果"""
        results_data = {
            "test_config": LOAD_TEST_CONFIG,
            "metrics": self.calculate_metrics().__dict__,
            "results": [
                {
                    "timestamp": r.timestamp,
                    "duration": r.duration,
                    "status_code": r.status_code,
                    "success": r.success,
                    "error": r.error,
                    "endpoint": r.endpoint,
                    "user_id": r.user_id
                }
                for r in self.all_results
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)


class WebSocketLoadTest:
    """WebSocket负载测试"""
    
    def __init__(self, num_connections: int = 50):
        self.num_connections = num_connections
        self.connections = []
        self.message_count = 0
        self.error_count = 0
        self.start_time = None
        self.end_time = None
    
    async def create_connection(self, user_id: str, auth_token: str):
        """创建WebSocket连接"""
        try:
            uri = f"{LOAD_TEST_CONFIG['websocket_url']}/simulation/test"
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            websocket = await websockets.connect(uri, extra_headers=headers)
            self.connections.append((user_id, websocket))
            return websocket
        
        except Exception as e:
            print(f"WebSocket连接失败 {user_id}: {e}")
            self.error_count += 1
            return None
    
    async def send_messages(self, websocket, user_id: str, duration: float):
        """发送消息"""
        end_time = time.time() + duration
        
        while time.time() < end_time:
            try:
                message = {
                    "type": "subscribe",
                    "data": {"events": ["simulation_update"]},
                    "user_id": user_id,
                    "timestamp": time.time()
                }
                
                await websocket.send(json.dumps(message))
                self.message_count += 1
                
                # 等待响应
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    # 处理响应
                except asyncio.TimeoutError:
                    pass
                
                await asyncio.sleep(random.uniform(1, 5))
            
            except Exception as e:
                print(f"WebSocket消息发送失败 {user_id}: {e}")
                self.error_count += 1
                break
    
    async def run_websocket_load_test(self, duration: float = 300):
        """运行WebSocket负载测试"""
        print(f"开始WebSocket负载测试: {self.num_connections} 连接, {duration}秒")
        
        self.start_time = time.time()
        
        # 创建连接任务
        connection_tasks = []
        for i in range(self.num_connections):
            # 这里需要实际的认证token，简化处理
            auth_token = f"test_token_{i}"
            task = asyncio.create_task(self.create_connection(f"ws_user_{i}", auth_token))
            connection_tasks.append(task)
        
        # 等待连接建立
        await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        print(f"建立了 {len(self.connections)} 个WebSocket连接")
        
        # 发送消息任务
        message_tasks = []
        for user_id, websocket in self.connections:
            if websocket:
                task = asyncio.create_task(self.send_messages(websocket, user_id, duration))
                message_tasks.append(task)
        
        # 等待消息发送完成
        await asyncio.gather(*message_tasks, return_exceptions=True)
        
        self.end_time = time.time()
        
        # 关闭连接
        for user_id, websocket in self.connections:
            if websocket:
                try:
                    await websocket.close()
                except:
                    pass
        
        # 计算统计信息
        test_duration = self.end_time - self.start_time
        messages_per_second = self.message_count / test_duration if test_duration > 0 else 0
        error_rate = (self.error_count / (self.message_count + self.error_count)) * 100 if (self.message_count + self.error_count) > 0 else 0
        
        print(f"WebSocket负载测试完成:")
        print(f"  连接数: {len(self.connections)}")
        print(f"  消息总数: {self.message_count}")
        print(f"  错误数: {self.error_count}")
        print(f"  每秒消息数: {messages_per_second:.2f}")
        print(f"  错误率: {error_rate:.2f}%")


# pytest测试函数
@pytest.mark.asyncio
async def test_api_load():
    """API负载测试"""
    runner = LoadTestRunner()
    
    try:
        # 设置较少的用户进行快速测试
        await runner.setup_users(10)
        
        # 运行短时间负载测试
        await runner.run_load_test(duration=60, ramp_up_time=10)
        
        # 计算指标
        metrics = runner.calculate_metrics()
        
        # 断言
        assert metrics.total_requests > 0, "没有发送任何请求"
        assert metrics.error_rate < 50, f"错误率过高: {metrics.error_rate}%"
        assert metrics.average_response_time < 5, f"平均响应时间过长: {metrics.average_response_time}s"
        
        print(runner.generate_report(metrics))
    
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_websocket_load():
    """WebSocket负载测试"""
    ws_test = WebSocketLoadTest(num_connections=20)
    await ws_test.run_websocket_load_test(duration=60)
    
    # 断言
    assert len(ws_test.connections) > 0, "没有建立WebSocket连接"
    assert ws_test.message_count > 0, "没有发送任何消息"


@pytest.mark.asyncio
async def test_stress_test():
    """压力测试"""
    runner = LoadTestRunner()
    
    try:
        # 高并发用户
        await runner.setup_users(50)
        
        # 运行压力测试
        await runner.run_load_test(duration=120, ramp_up_time=30)
        
        # 计算指标
        metrics = runner.calculate_metrics()
        
        # 压力测试的断言更宽松
        assert metrics.total_requests > 0, "没有发送任何请求"
        assert metrics.error_rate < 80, f"错误率过高: {metrics.error_rate}%"
        
        print(runner.generate_report(metrics))
        
        # 保存结果
        runner.save_results("stress_test_results.json")
    
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    async def main():
        print("=== CHS Simulation Platform 负载测试 ===")
        
        # 1. API负载测试
        print("\n1. 运行API负载测试...")
        api_runner = LoadTestRunner()
        
        try:
            await api_runner.setup_users(LOAD_TEST_CONFIG["concurrent_users"])
            await api_runner.run_load_test(
                duration=LOAD_TEST_CONFIG["test_duration"],
                ramp_up_time=LOAD_TEST_CONFIG["ramp_up_time"]
            )
            
            api_metrics = api_runner.calculate_metrics()
            print(api_runner.generate_report(api_metrics))
            api_runner.save_results("api_load_test_results.json")
        
        finally:
            await api_runner.cleanup()
        
        # 2. WebSocket负载测试
        print("\n2. 运行WebSocket负载测试...")
        ws_test = WebSocketLoadTest(num_connections=50)
        await ws_test.run_websocket_load_test(duration=300)
        
        print("\n=== 负载测试完成 ===")
    
    # 运行测试
    asyncio.run(main())