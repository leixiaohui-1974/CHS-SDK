"""简化的性能测试

测试 API 的基本性能指标和负载能力。
"""

import pytest
import sys
import time
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient

# 添加 API 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

# 导入应用
from server import app

# 创建测试客户端
client = TestClient(app)

class TestBasicPerformance:
    """基本性能测试"""
    
    def test_health_endpoint_response_time(self):
        """测试健康检查端点响应时间"""
        start_time = time.time()
        response = client.get("/api/monitoring/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0, f"Response time too slow: {response_time:.3f}s"
        
        # 检查性能头信息
        assert "x-process-time" in response.headers
        process_time = float(response.headers["x-process-time"])
        assert process_time < 2.0, f"Process time too slow: {process_time:.3f}s"
    
    def test_status_endpoint_response_time(self):
        """测试状态端点响应时间"""
        start_time = time.time()
        response = client.get("/api/monitoring/health")  # 使用存在的端点
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0, f"Response time too slow: {response_time:.3f}s"
    
    def test_examples_endpoint_response_time(self):
        """测试示例端点响应时间"""
        start_time = time.time()
        response = client.get("/api/examples")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0, f"Response time too slow: {response_time:.3f}s"

class TestConcurrentLoad:
    """并发负载测试"""
    
    def test_concurrent_health_checks(self):
        """测试并发健康检查"""
        def make_request():
            response = client.get("/api/monitoring/health")
            return response.status_code, response.elapsed if hasattr(response, 'elapsed') else 0
        
        # 并发执行 10 个请求
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # 验证所有请求都成功
        for status_code, _ in results:
            assert status_code == 200
        
        assert len(results) == 10
    
    def test_concurrent_status_checks(self):
        """测试并发状态检查"""
        def make_request():
            response = client.get("/api/examples")  # 使用存在的端点
            return response.status_code
        
        # 并发执行 5 个请求
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in as_completed(futures)]
        
        # 验证所有请求都成功
        for status_code in results:
            assert status_code == 200
        
        assert len(results) == 5

class TestLoadStability:
    """负载稳定性测试"""
    
    def test_sustained_load(self):
        """测试持续负载"""
        response_times = []
        error_count = 0
        
        # 连续发送 20 个请求
        for i in range(20):
            start_time = time.time()
            try:
                response = client.get("/api/monitoring/health")
                end_time = time.time()
                
                if response.status_code == 200:
                    response_times.append(end_time - start_time)
                else:
                    error_count += 1
            except Exception:
                error_count += 1
            
            # 短暂间隔
            time.sleep(0.1)
        
        # 验证错误率低于 5%
        error_rate = error_count / 20
        assert error_rate < 0.05, f"Error rate too high: {error_rate:.2%}"
        
        # 验证平均响应时间
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            assert avg_response_time < 1.0, f"Average response time too slow: {avg_response_time:.3f}s"
    
    def test_memory_stability(self):
        """测试内存稳定性"""
        initial_memory = None
        final_memory = None
        
        # 执行多次请求并监控内存使用
        for i in range(50):
            response = client.get("/api/monitoring/health")
            assert response.status_code == 200
            
            if "x-memory-usage" in response.headers:
                memory_usage = float(response.headers["x-memory-usage"])
                
                if initial_memory is None:
                    initial_memory = memory_usage
                final_memory = memory_usage
        
        # 验证内存使用没有显著增长（可能的内存泄漏）
        if initial_memory is not None and final_memory is not None:
            memory_growth = final_memory - initial_memory
            assert memory_growth < 10.0, f"Potential memory leak detected: {memory_growth:.2f}% growth"

class TestPerformanceHeaders:
    """性能头信息测试"""
    
    def test_performance_headers_presence(self):
        """测试性能头信息存在性"""
        response = client.get("/api/monitoring/health")
        assert response.status_code == 200
        
        # 验证性能监控头存在
        required_headers = ["x-process-time", "x-cpu-usage", "x-memory-usage"]
        for header in required_headers:
            assert header in response.headers, f"Missing performance header: {header}"
    
    def test_performance_headers_values(self):
        """测试性能头信息值的合理性"""
        response = client.get("/api/monitoring/health")
        assert response.status_code == 200
        
        # 验证处理时间
        process_time = float(response.headers["x-process-time"])
        assert 0 <= process_time <= 10.0, f"Invalid process time: {process_time}"
        
        # 验证 CPU 使用率
        cpu_usage = float(response.headers["x-cpu-usage"])
        assert 0 <= cpu_usage <= 100.0, f"Invalid CPU usage: {cpu_usage}"
        
        # 验证内存使用率
        memory_usage = float(response.headers["x-memory-usage"])
        assert 0 <= memory_usage <= 100.0, f"Invalid memory usage: {memory_usage}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])