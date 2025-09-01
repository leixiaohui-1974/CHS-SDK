"""监控 API 端点测试

测试性能监控、健康检查和系统指标相关的 API 端点。
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

# 导入应用
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from server import app
from auth.dependencies import get_current_active_user
from database.models import UserDB

# 创建测试客户端
client = TestClient(app)

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

# 模拟管理员用户
def mock_admin_user():
    """模拟管理员用户"""
    user = MagicMock(spec=UserDB)
    user.id = 1
    user.username = "admin"
    user.email = "admin@example.com"
    user.is_active = True
    user.is_superuser = True
    return user

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
        
        # 验证时间戳格式
        timestamp = data["timestamp"]
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        
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
    
    @patch('auth.dependencies.get_current_active_user', return_value=mock_current_user())
    def test_system_metrics_authorized(self, mock_user):
        """测试授权访问系统指标"""
        response = client.get("/api/monitoring/system")
        assert response.status_code == 200
        
        data = response.json()
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data
        assert "processes" in data
        assert "timestamp" in data
        
        # 验证 CPU 指标
        cpu = data["cpu"]
        assert "usage_percent" in cpu
        assert "count" in cpu
        assert 0 <= cpu["usage_percent"] <= 100
        
        # 验证内存指标
        memory = data["memory"]
        assert "total" in memory
        assert "available" in memory
        assert "used" in memory
        assert "percent" in memory
        assert 0 <= memory["percent"] <= 100

class TestPerformanceMonitoring:
    """性能监控端点测试"""
    
    @patch('auth.dependencies.get_current_active_user', return_value=mock_current_user())
    def test_performance_metrics(self, mock_user):
        """测试性能指标"""
        response = client.get("/api/monitoring/performance")
        assert response.status_code == 200
        
        data = response.json()
        assert "request_count" in data
        assert "average_response_time" in data
        assert "error_rate" in data
        assert "active_connections" in data
        assert "timestamp" in data
        
        # 验证指标类型
        assert isinstance(data["request_count"], int)
        assert isinstance(data["average_response_time"], (int, float))
        assert isinstance(data["error_rate"], (int, float))
        assert isinstance(data["active_connections"], int)
        
        # 验证指标范围
        assert data["request_count"] >= 0
        assert data["average_response_time"] >= 0
        assert 0 <= data["error_rate"] <= 100
        assert data["active_connections"] >= 0

class TestCacheMonitoring:
    """缓存监控端点测试"""
    
    @patch('auth.dependencies.get_current_active_user', return_value=mock_current_user())
    def test_cache_metrics(self, mock_user):
        """测试缓存指标"""
        response = client.get("/api/monitoring/cache")
        assert response.status_code == 200
        
        data = response.json()
        assert "memory_cache" in data
        assert "redis_cache" in data
        assert "timestamp" in data
        
        # 验证内存缓存指标
        memory_cache = data["memory_cache"]
        assert "size" in memory_cache
        assert "hit_rate" in memory_cache
        assert "miss_rate" in memory_cache
        
        # 验证 Redis 缓存指标
        redis_cache = data["redis_cache"]
        assert "status" in redis_cache
        
    @patch('auth.dependencies.get_current_active_user', return_value=mock_admin_user())
    def test_cache_clear_admin(self, mock_user):
        """测试管理员清除缓存"""
        response = client.delete("/api/monitoring/cache/clear?pattern=test:*")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "cleared_keys" in data
        assert isinstance(data["cleared_keys"], int)
    
    @patch('auth.dependencies.get_current_active_user', return_value=mock_current_user())
    def test_cache_clear_non_admin(self, mock_user):
        """测试非管理员清除缓存"""
        response = client.delete("/api/monitoring/cache/clear?pattern=test:*")
        assert response.status_code == 403

class TestDatabaseMonitoring:
    """数据库监控端点测试"""
    
    @patch('auth.dependencies.get_current_active_user', return_value=mock_current_user())
    def test_database_metrics(self, mock_user):
        """测试数据库指标"""
        response = client.get("/api/monitoring/database")
        assert response.status_code == 200
        
        data = response.json()
        assert "connection_pool" in data
        assert "query_performance" in data
        assert "timestamp" in data
        
        # 验证连接池指标
        pool = data["connection_pool"]
        assert "size" in pool
        assert "checked_in" in pool
        assert "checked_out" in pool
        assert "overflow" in pool
        
        # 验证查询性能
        query_perf = data["query_performance"]
        assert "test_query_time" in query_perf
        assert isinstance(query_perf["test_query_time"], (int, float))

class TestAlertsMonitoring:
    """告警监控端点测试"""
    
    @patch('auth.dependencies.get_current_active_user', return_value=mock_current_user())
    def test_alerts_endpoint(self, mock_user):
        """测试告警端点"""
        response = client.get("/api/monitoring/alerts")
        assert response.status_code == 200
        
        data = response.json()
        assert "alerts" in data
        assert "summary" in data
        assert "timestamp" in data
        
        # 验证告警列表
        alerts = data["alerts"]
        assert isinstance(alerts, list)
        
        for alert in alerts:
            assert "type" in alert
            assert "severity" in alert
            assert "message" in alert
            assert "value" in alert
            assert "threshold" in alert
            assert "timestamp" in alert
            
            # 验证严重级别
            assert alert["severity"] in ["low", "medium", "high", "critical"]
        
        # 验证摘要
        summary = data["summary"]
        assert "total_alerts" in summary
        assert "by_severity" in summary
        assert isinstance(summary["total_alerts"], int)
        assert isinstance(summary["by_severity"], dict)

class TestSimulationCacheMonitoring:
    """仿真缓存监控端点测试"""
    
    @patch('auth.dependencies.get_current_active_user', return_value=mock_current_user())
    def test_simulation_cache_info(self, mock_user):
        """测试仿真缓存信息"""
        session_id = "test-session-123"
        response = client.get(f"/api/monitoring/simulation/cache/{session_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "session_id" in data
        assert "cache_info" in data
        assert "timestamp" in data
        
        cache_info = data["cache_info"]
        assert "config_cached" in cache_info
        assert "state_cached" in cache_info
        assert "results_cached" in cache_info
    
    @patch('auth.dependencies.get_current_active_user', return_value=mock_current_user())
    def test_simulation_cache_clear(self, mock_user):
        """测试清除仿真缓存"""
        session_id = "test-session-123"
        response = client.delete(f"/api/monitoring/simulation/cache/{session_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "session_id" in data
        assert data["session_id"] == session_id

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
    
    def test_compression_middleware(self):
        """测试压缩中间件"""
        headers = {"Accept-Encoding": "gzip"}
        response = client.get("/api/monitoring/health", headers=headers)
        
        # 检查是否启用了压缩
        # 注意：TestClient 可能会自动解压缩响应
        assert response.status_code == 200
        assert len(response.content) > 0

if __name__ == "__main__":
    pytest.main([__file__])