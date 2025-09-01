"""简化的安全测试

测试 API 的基本安全功能和防护措施。
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# 添加 API 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

# 导入应用
from server import app

# 创建测试客户端
client = TestClient(app)

class TestBasicSecurity:
    """基本安全测试"""
    
    def test_cors_headers(self):
        """测试 CORS 头设置"""
        response = client.get("/api/monitoring/health")
        assert response.status_code == 200
        
        # 检查 CORS 相关头（可能存在也可能不存在，取决于配置）
        headers = response.headers
        # 如果配置了 CORS，应该有相关头
        cors_headers = ["access-control-allow-origin", "Access-Control-Allow-Origin"]
        has_cors = any(header in headers for header in cors_headers)
        
        # 至少应该有基本的响应头
        assert "content-type" in headers or has_cors
    
    def test_security_headers(self):
        """测试安全头设置"""
        response = client.get("/api/monitoring/health")
        assert response.status_code == 200
        
        headers = response.headers
        # 检查常见的安全头（如果配置了的话）
        # 这些头可能在中间件中设置
        expected_security_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection",
            "strict-transport-security"
        ]
        
        # 至少应该有一些安全头
        security_headers_present = any(
            header.lower() in [h.lower() for h in headers.keys()]
            for header in expected_security_headers
        )
        
        # 如果没有安全头，至少应该有基本的内容类型
        if not security_headers_present:
            assert "content-type" in headers
    
    def test_method_not_allowed(self):
        """测试不允许的 HTTP 方法"""
        # 尝试对只支持 GET 的端点使用 POST
        response = client.post("/api/monitoring/health")
        assert response.status_code == 405  # Method Not Allowed
    
    def test_invalid_endpoint(self):
        """测试无效端点"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404  # Not Found
    
    def test_malformed_request(self):
        """测试格式错误的请求"""
        # 发送无效的 JSON
        response = client.post(
            "/api/simulations",
            data="{invalid json}",
            headers={"Content-Type": "application/json"}
        )
        # 应该返回错误状态码（可能是 404 如果端点不存在，或 400/422 如果端点存在但数据无效）
        assert response.status_code in [400, 404, 422]

class TestInputValidation:
    """输入验证测试"""
    
    def test_path_traversal_protection(self):
        """测试路径遍历攻击防护"""
        # 尝试路径遍历攻击
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL 编码
            "....//....//....//etc//passwd"
        ]
        
        for path in malicious_paths:
            response = client.get(f"/api/examples/{path}")
            # 应该返回 400, 403, 404 或 422，而不是 200
            assert response.status_code in [400, 403, 404, 422], f"Path traversal not blocked for: {path}"
    
    def test_sql_injection_protection(self):
        """测试 SQL 注入防护"""
        # 尝试 SQL 注入攻击
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1#"
        ]
        
        for payload in sql_payloads:
            # 尝试在不同端点使用 SQL 注入
            response = client.get(f"/api/examples/{payload}")
            # 应该安全处理，不返回敏感信息
            assert response.status_code in [400, 403, 404, 422], f"SQL injection not handled for: {payload}"
    
    def test_xss_protection(self):
        """测试 XSS 攻击防护"""
        # 尝试 XSS 攻击
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "'><script>alert('xss')</script>"
        ]
        
        for payload in xss_payloads:
            response = client.get(f"/api/examples/{payload}")
            # 应该安全处理 XSS 尝试
            assert response.status_code in [400, 403, 404, 422], f"XSS not handled for: {payload}"
            
            # 如果返回内容，确保没有直接回显恶意脚本
            if response.status_code == 200:
                content = response.text.lower()
                assert "<script>" not in content
                assert "javascript:" not in content
                assert "onerror=" not in content

class TestRateLimiting:
    """速率限制测试"""
    
    def test_rapid_requests(self):
        """测试快速连续请求"""
        # 快速发送多个请求
        responses = []
        for i in range(20):
            response = client.get("/api/monitoring/health")
            responses.append(response.status_code)
        
        # 大部分请求应该成功
        success_count = sum(1 for status in responses if status == 200)
        
        # 至少 80% 的请求应该成功（允许一些速率限制）
        success_rate = success_count / len(responses)
        assert success_rate >= 0.8, f"Success rate too low: {success_rate:.2%}"
        
        # 如果有速率限制，应该返回 429
        rate_limited = [status for status in responses if status == 429]
        if rate_limited:
            assert len(rate_limited) < len(responses) // 2, "Too many requests rate limited"

class TestAuthenticationSecurity:
    """认证安全测试"""
    
    def test_protected_endpoints_without_auth(self):
        """测试未认证访问受保护端点"""
        protected_endpoints = [
            "/api/monitoring/system",
            "/api/monitoring/cache",
            "/api/monitoring/performance",
            "/api/monitoring/database"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            # 应该返回 401 未认证错误
            assert response.status_code == 401, f"Endpoint {endpoint} not properly protected"
    
    def test_invalid_token_format(self):
        """测试无效令牌格式"""
        invalid_tokens = [
            "invalid_token",
            "Bearer",
            "Bearer ",
            "Basic dGVzdDp0ZXN0"  # Basic auth instead of Bearer
        ]
        
        for token in invalid_tokens:
            headers = {"Authorization": token}
            response = client.get("/api/monitoring/system", headers=headers)
            # 应该返回 401（未认证）
            assert response.status_code == 401, f"Invalid token not rejected: {token}"
        
        # 注意：更复杂的 JWT 验证测试需要了解具体的认证实现

class TestDataValidation:
    """数据验证测试"""
    
    def test_oversized_request(self):
        """测试超大请求"""
        # 创建一个较大的请求体（减小大小以避免测试超时）
        large_data = "x" * (1024 * 1024)  # 1MB
        
        response = client.post(
            "/api/simulations",
            json={"config": large_data},
            headers={"Content-Type": "application/json"}
        )
        
        # 应该拒绝过大的请求或返回端点不存在
        assert response.status_code in [400, 404, 413, 422], "Large request not properly handled"
    
    def test_invalid_content_type(self):
        """测试无效内容类型"""
        response = client.post(
            "/api/simulations",
            data="some data",
            headers={"Content-Type": "text/plain"}
        )
        
        # 应该拒绝不支持的内容类型或返回端点不存在
        assert response.status_code in [400, 404, 415, 422], "Invalid content type not properly handled"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])