"""简化的监控 API 测试

不依赖复杂配置的基本监控功能测试。
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# 添加 API 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

# 导入应用
from server import app
from database.models import UserDB

# 创建测试客户端
client = TestClient(app)

class TestHealthEndpoint:
    """健康检查端点测试"""
    
    def test_health_check_success(self):
        """测试健康检查成功"""
        response = client.get("/api/monitoring/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
        
        # 检查响应头中的性能指标
        assert "x-process-time" in response.headers
        assert "x-cpu-usage" in response.headers
        assert "x-memory-usage" in response.headers
    
    def test_health_check_response_format(self):
        """测试健康检查响应格式"""
        response = client.get("/api/monitoring/health")
        data = response.json()
        
        # 验证状态值
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        
        # 验证服务状态
        services = data["services"]
        assert isinstance(services, dict)
        for service_name, status in services.items():
            assert isinstance(service_name, str)
            assert isinstance(status, str)

class TestSystemMonitoring:
    """系统监控端点测试"""
    
    def test_system_metrics_unauthorized(self):
        """测试未授权访问系统指标"""
        response = client.get("/api/monitoring/system")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_cache_metrics_unauthorized(self):
        """测试未授权访问缓存指标"""
        response = client.get("/api/monitoring/cache")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_performance_metrics_unauthorized(self):
        """测试未授权访问性能指标"""
        response = client.get("/api/monitoring/performance")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

class TestMiddlewareIntegration:
    """中间件集成测试"""
    
    def test_performance_middleware_headers(self):
        """测试性能监控中间件添加的响应头"""
        response = client.get("/api/monitoring/health")
        
        # 检查性能监控中间件添加的头
        assert "x-process-time" in response.headers
        assert "x-cpu-usage" in response.headers
        assert "x-memory-usage" in response.headers
        
        # 验证头值格式
        process_time = float(response.headers["x-process-time"])
        cpu_usage = float(response.headers["x-cpu-usage"])
        memory_usage = float(response.headers["x-memory-usage"])
        
        assert process_time >= 0
        assert 0 <= cpu_usage <= 100
        assert 0 <= memory_usage <= 100
    
    def test_multiple_requests_performance(self):
        """测试多次请求的性能一致性"""
        response_times = []
        
        for _ in range(5):
            response = client.get("/api/monitoring/health")
            assert response.status_code == 200
            
            process_time = float(response.headers["x-process-time"])
            response_times.append(process_time)
        
        # 验证所有响应时间都在合理范围内
        for rt in response_times:
            assert rt < 2.0, f"Response time too high: {rt}s"
        
        # 验证响应时间相对稳定
        avg_time = sum(response_times) / len(response_times)
        for rt in response_times:
            assert abs(rt - avg_time) < avg_time * 2, "Response time variance too high"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])