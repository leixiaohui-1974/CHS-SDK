"""性能测试

测试 API 的负载能力、响应时间和并发处理能力。
"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import requests
import threading
from typing import List, Dict, Any

# 导入应用
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from server import app
from auth.dependencies import get_current_active_user
from database.models import UserDB

# 创建测试客户端
client = TestClient(app)

# 性能测试配置
PERFORMANCE_CONFIG = {
    "light_load": {
        "concurrent_users": 10,
        "requests_per_user": 5,
        "max_response_time": 2.0  # 秒
    },
    "medium_load": {
        "concurrent_users": 50,
        "requests_per_user": 10,
        "max_response_time": 5.0  # 秒
    },
    "heavy_load": {
        "concurrent_users": 100,
        "requests_per_user": 20,
        "max_response_time": 10.0  # 秒
    }
}

# 模拟用户
def mock_current_user():
    """模拟当前用户"""
    user = MagicMock(spec=UserDB)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_active = True
    user.is_superuser = False
    return user

class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.success_count = 0
        self.error_count = 0
        self.status_codes: Dict[int, int] = {}
        self.start_time = None
        self.end_time = None
        self.lock = threading.Lock()
    
    def start_timer(self):
        """开始计时"""
        self.start_time = time.time()
    
    def stop_timer(self):
        """停止计时"""
        self.end_time = time.time()
    
    def add_result(self, response_time: float, status_code: int, success: bool):
        """添加测试结果"""
        with self.lock:
            self.response_times.append(response_time)
            if success:
                self.success_count += 1
            else:
                self.error_count += 1
            
            if status_code in self.status_codes:
                self.status_codes[status_code] += 1
            else:
                self.status_codes[status_code] = 1
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        total_requests = self.success_count + self.error_count
        total_time = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        return {
            "total_requests": total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": (self.success_count / total_requests * 100) if total_requests > 0 else 0,
            "total_time": total_time,
            "requests_per_second": total_requests / total_time if total_time > 0 else 0,
            "avg_response_time": statistics.mean(self.response_times) if self.response_times else 0,
            "min_response_time": min(self.response_times) if self.response_times else 0,
            "max_response_time": max(self.response_times) if self.response_times else 0,
            "median_response_time": statistics.median(self.response_times) if self.response_times else 0,
            "p95_response_time": self._percentile(self.response_times, 95) if self.response_times else 0,
            "p99_response_time": self._percentile(self.response_times, 99) if self.response_times else 0,
            "status_codes": self.status_codes
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

def make_request(endpoint: str, method: str = "GET", headers: Dict = None, data: Dict = None) -> Dict[str, Any]:
    """发送 HTTP 请求"""
    start_time = time.time()
    
    try:
        if method.upper() == "GET":
            response = client.get(endpoint, headers=headers)
        elif method.upper() == "POST":
            response = client.post(endpoint, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = client.put(endpoint, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = client.delete(endpoint, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response_time = time.time() - start_time
        success = 200 <= response.status_code < 400
        
        return {
            "response_time": response_time,
            "status_code": response.status_code,
            "success": success,
            "content_length": len(response.content)
        }
    
    except Exception as e:
        response_time = time.time() - start_time
        return {
            "response_time": response_time,
            "status_code": 500,
            "success": False,
            "error": str(e)
        }

def run_load_test(endpoint: str, concurrent_users: int, requests_per_user: int, 
                 method: str = "GET", headers: Dict = None, data: Dict = None) -> PerformanceMetrics:
    """运行负载测试"""
    metrics = PerformanceMetrics()
    metrics.start_timer()
    
    def user_session(user_id: int):
        """模拟用户会话"""
        for _ in range(requests_per_user):
            result = make_request(endpoint, method, headers, data)
            metrics.add_result(
                result["response_time"],
                result["status_code"],
                result["success"]
            )
    
    # 使用线程池模拟并发用户
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(user_session, i) for i in range(concurrent_users)]
        
        # 等待所有任务完成
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"User session error: {e}")
    
    metrics.stop_timer()
    return metrics

class TestHealthEndpointPerformance:
    """健康检查端点性能测试"""
    
    def test_health_light_load(self):
        """轻负载测试"""
        config = PERFORMANCE_CONFIG["light_load"]
        metrics = run_load_test(
            "/api/monitoring/health",
            config["concurrent_users"],
            config["requests_per_user"]
        )
        
        summary = metrics.get_summary()
        
        # 验证性能指标
        assert summary["success_rate"] >= 95.0, f"Success rate too low: {summary['success_rate']}%"
        assert summary["avg_response_time"] <= config["max_response_time"], f"Average response time too high: {summary['avg_response_time']}s"
        assert summary["p95_response_time"] <= config["max_response_time"] * 2, f"P95 response time too high: {summary['p95_response_time']}s"
        
        print(f"Health endpoint light load test results: {summary}")
    
    def test_health_medium_load(self):
        """中等负载测试"""
        config = PERFORMANCE_CONFIG["medium_load"]
        metrics = run_load_test(
            "/api/monitoring/health",
            config["concurrent_users"],
            config["requests_per_user"]
        )
        
        summary = metrics.get_summary()
        
        # 验证性能指标
        assert summary["success_rate"] >= 90.0, f"Success rate too low: {summary['success_rate']}%"
        assert summary["avg_response_time"] <= config["max_response_time"], f"Average response time too high: {summary['avg_response_time']}s"
        
        print(f"Health endpoint medium load test results: {summary}")
    
    @pytest.mark.slow
    def test_health_heavy_load(self):
        """重负载测试（标记为慢测试）"""
        config = PERFORMANCE_CONFIG["heavy_load"]
        metrics = run_load_test(
            "/api/monitoring/health",
            config["concurrent_users"],
            config["requests_per_user"]
        )
        
        summary = metrics.get_summary()
        
        # 验证性能指标（重负载下要求较低）
        assert summary["success_rate"] >= 85.0, f"Success rate too low: {summary['success_rate']}%"
        assert summary["avg_response_time"] <= config["max_response_time"], f"Average response time too high: {summary['avg_response_time']}s"
        
        print(f"Health endpoint heavy load test results: {summary}")

class TestAuthenticatedEndpointPerformance:
    """认证端点性能测试"""
    
    @patch('auth.dependencies.get_current_active_user', return_value=mock_current_user())
    def test_system_monitoring_performance(self, mock_user):
        """系统监控端点性能测试"""
        config = PERFORMANCE_CONFIG["light_load"]
        
        # 模拟认证头
        headers = {"Authorization": "Bearer fake_token"}
        
        metrics = run_load_test(
            "/api/monitoring/system",
            config["concurrent_users"],
            config["requests_per_user"],
            headers=headers
        )
        
        summary = metrics.get_summary()
        
        # 验证性能指标
        assert summary["success_rate"] >= 95.0, f"Success rate too low: {summary['success_rate']}%"
        assert summary["avg_response_time"] <= config["max_response_time"] * 2, f"Average response time too high: {summary['avg_response_time']}s"
        
        print(f"System monitoring performance test results: {summary}")
    
    @patch('auth.dependencies.get_current_active_user', return_value=mock_current_user())
    def test_cache_monitoring_performance(self, mock_user):
        """缓存监控端点性能测试"""
        config = PERFORMANCE_CONFIG["light_load"]
        
        # 模拟认证头
        headers = {"Authorization": "Bearer fake_token"}
        
        metrics = run_load_test(
            "/api/monitoring/cache",
            config["concurrent_users"],
            config["requests_per_user"],
            headers=headers
        )
        
        summary = metrics.get_summary()
        
        # 验证性能指标
        assert summary["success_rate"] >= 95.0, f"Success rate too low: {summary['success_rate']}%"
        assert summary["avg_response_time"] <= config["max_response_time"] * 2, f"Average response time too high: {summary['avg_response_time']}s"
        
        print(f"Cache monitoring performance test results: {summary}")

class TestSimulationEndpointPerformance:
    """仿真端点性能测试"""
    
    @patch('auth.dependencies.get_current_active_user', return_value=mock_current_user())
    def test_simulation_creation_performance(self, mock_user):
        """仿真创建性能测试"""
        config = PERFORMANCE_CONFIG["light_load"]
        
        # 模拟认证头
        headers = {"Authorization": "Bearer fake_token"}
        
        # 模拟仿真配置
        simulation_data = {
            "name": "Performance Test Simulation",
            "description": "Test simulation for performance testing",
            "config": {
                "duration": 100,
                "time_step": 1,
                "components": []
            }
        }
        
        metrics = run_load_test(
            "/api/simulations",
            min(config["concurrent_users"], 20),  # 限制并发数，避免创建太多仿真
            min(config["requests_per_user"], 3),  # 限制每用户请求数
            method="POST",
            headers=headers,
            data=simulation_data
        )
        
        summary = metrics.get_summary()
        
        # 验证性能指标（创建操作通常较慢）
        assert summary["success_rate"] >= 80.0, f"Success rate too low: {summary['success_rate']}%"
        assert summary["avg_response_time"] <= 10.0, f"Average response time too high: {summary['avg_response_time']}s"
        
        print(f"Simulation creation performance test results: {summary}")

class TestConcurrencyStress:
    """并发压力测试"""
    
    def test_concurrent_health_checks(self):
        """并发健康检查压力测试"""
        # 高并发短时间测试
        concurrent_users = 200
        requests_per_user = 5
        
        metrics = run_load_test(
            "/api/monitoring/health",
            concurrent_users,
            requests_per_user
        )
        
        summary = metrics.get_summary()
        
        # 验证系统在高并发下的稳定性
        assert summary["success_rate"] >= 80.0, f"Success rate too low under stress: {summary['success_rate']}%"
        assert summary["error_count"] < summary["total_requests"] * 0.2, "Too many errors under stress"
        
        print(f"Concurrent stress test results: {summary}")
    
    def test_sustained_load(self):
        """持续负载测试"""
        # 中等并发长时间测试
        concurrent_users = 50
        requests_per_user = 50  # 更多请求模拟持续负载
        
        metrics = run_load_test(
            "/api/monitoring/health",
            concurrent_users,
            requests_per_user
        )
        
        summary = metrics.get_summary()
        
        # 验证系统在持续负载下的稳定性
        assert summary["success_rate"] >= 90.0, f"Success rate degraded under sustained load: {summary['success_rate']}%"
        assert summary["avg_response_time"] <= 3.0, f"Response time degraded under sustained load: {summary['avg_response_time']}s"
        
        # 验证响应时间稳定性（P99 不应该过高）
        assert summary["p99_response_time"] <= summary["avg_response_time"] * 5, "Response time variance too high"
        
        print(f"Sustained load test results: {summary}")

class TestMemoryAndResourceUsage:
    """内存和资源使用测试"""
    
    def test_memory_leak_detection(self):
        """内存泄漏检测测试"""
        import psutil
        import os
        
        # 获取当前进程
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 运行多轮测试
        for round_num in range(5):
            metrics = run_load_test(
                "/api/monitoring/health",
                20,  # 中等并发
                10   # 中等请求数
            )
            
            current_memory = process.memory_info().rss
            memory_increase = (current_memory - initial_memory) / 1024 / 1024  # MB
            
            print(f"Round {round_num + 1}: Memory usage increased by {memory_increase:.2f} MB")
            
            # 验证内存增长不超过合理范围（100MB）
            assert memory_increase < 100, f"Potential memory leak detected: {memory_increase:.2f} MB increase"
    
    def test_response_time_consistency(self):
        """响应时间一致性测试"""
        # 运行多轮测试，检查响应时间是否一致
        response_times = []
        
        for _ in range(10):
            start_time = time.time()
            response = client.get("/api/monitoring/health")
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            response_times.append(response_time)
            
            time.sleep(0.1)  # 短暂间隔
        
        # 计算响应时间统计
        avg_time = statistics.mean(response_times)
        std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
        
        # 验证响应时间一致性（标准差不应该太大）
        assert std_dev < avg_time * 0.5, f"Response time too inconsistent: avg={avg_time:.3f}s, std={std_dev:.3f}s"
        
        print(f"Response time consistency: avg={avg_time:.3f}s, std={std_dev:.3f}s")

if __name__ == "__main__":
    # 运行性能测试
    pytest.main([__file__, "-v", "-s"])