"""安全测试

测试系统的安全性，包括认证、授权、输入验证、SQL注入、XSS等。
"""

import asyncio
import aiohttp
import json
import base64
import hashlib
import time
from typing import Dict, List, Any, Tuple
from urllib.parse import quote, unquote
import re

import pytest
from dataclasses import dataclass

# 安全测试配置
SECURITY_TEST_CONFIG = {
    "api_base_url": "http://localhost:8000",
    "frontend_url": "http://localhost:3000",
    "timeout": 30
}

# 测试用户
TEST_USERS = {
    "admin": {"email": "admin@example.com", "password": "admin123", "role": "admin"},
    "user": {"email": "user@example.com", "password": "user123", "role": "user"},
    "guest": {"email": "guest@example.com", "password": "guest123", "role": "guest"}
}

# SQL注入测试载荷
SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR '1'='1' /*",
    "'; DROP TABLE users; --",
    "' UNION SELECT * FROM users --",
    "1' AND (SELECT COUNT(*) FROM users) > 0 --",
    "' OR 1=1#",
    "' OR 'a'='a",
    "') OR ('1'='1",
    "1' OR '1'='1' AND '1'='1"
]

# XSS测试载荷
XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg onload=alert('XSS')>",
    "javascript:alert('XSS')",
    "<iframe src=javascript:alert('XSS')></iframe>",
    "<body onload=alert('XSS')>",
    "<input onfocus=alert('XSS') autofocus>",
    "<select onfocus=alert('XSS') autofocus>",
    "<textarea onfocus=alert('XSS') autofocus>",
    "<keygen onfocus=alert('XSS') autofocus>"
]

# 路径遍历测试载荷
PATH_TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
    "....//....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%252f..%252f..%252fetc%252fpasswd",
    "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
    "..//..//..//etc//passwd",
    "..\\..\\..\\etc\\passwd"
]

# 命令注入测试载荷
COMMAND_INJECTION_PAYLOADS = [
    "; ls -la",
    "| whoami",
    "& dir",
    "`id`",
    "$(whoami)",
    "; cat /etc/passwd",
    "| type C:\\Windows\\System32\\drivers\\etc\\hosts",
    "&& echo vulnerable",
    "|| echo vulnerable",
    "; sleep 10"
]

# 弱密码列表
WEAK_PASSWORDS = [
    "123456", "password", "123456789", "12345678", "12345",
    "1234567", "1234567890", "qwerty", "abc123", "111111",
    "123123", "admin", "letmein", "welcome", "monkey",
    "password123", "admin123", "root", "test", "guest"
]


@dataclass
class SecurityTestResult:
    """安全测试结果"""
    test_name: str
    endpoint: str
    payload: str
    expected_blocked: bool
    actually_blocked: bool
    response_code: int
    response_body: str
    vulnerability_detected: bool
    severity: str  # low, medium, high, critical
    description: str


class SecurityTester:
    """安全测试器"""
    
    def __init__(self):
        self.session = None
        self.auth_tokens = {}
        self.results: List[SecurityTestResult] = []
    
    async def setup(self):
        """设置测试环境"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=SECURITY_TEST_CONFIG["timeout"])
        )
        
        # 为不同角色的用户获取认证token
        for role, user_data in TEST_USERS.items():
            try:
                token = await self._authenticate_user(user_data)
                if token:
                    self.auth_tokens[role] = token
            except Exception as e:
                print(f"用户 {role} 认证失败: {e}")
    
    async def teardown(self):
        """清理资源"""
        if self.session:
            await self.session.close()
    
    async def _authenticate_user(self, user_data: Dict[str, str]) -> str:
        """用户认证"""
        # 先尝试注册
        try:
            async with self.session.post(
                f"{SECURITY_TEST_CONFIG['api_base_url']}/api/auth/register",
                json=user_data
            ) as response:
                pass  # 忽略注册结果
        except:
            pass
        
        # 登录获取token
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        async with self.session.post(
            f"{SECURITY_TEST_CONFIG['api_base_url']}/api/auth/login",
            json=login_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("access_token")
        
        return None
    
    async def _make_request(self, method: str, endpoint: str, auth_role: str = None, **kwargs) -> Tuple[int, str]:
        """发起请求"""
        headers = kwargs.get("headers", {})
        
        if auth_role and auth_role in self.auth_tokens:
            headers["Authorization"] = f"Bearer {self.auth_tokens[auth_role]}"
            kwargs["headers"] = headers
        
        try:
            async with self.session.request(
                method, 
                f"{SECURITY_TEST_CONFIG['api_base_url']}{endpoint}", 
                **kwargs
            ) as response:
                body = await response.text()
                return response.status, body
        except Exception as e:
            return 0, str(e)
    
    def _is_vulnerability_detected(self, response_code: int, response_body: str, test_type: str) -> bool:
        """检测是否存在漏洞"""
        # 根据不同测试类型检测漏洞
        if test_type == "sql_injection":
            # SQL错误信息
            sql_errors = [
                "sql syntax", "mysql_fetch", "ora-", "postgresql",
                "sqlite_", "sqlstate", "syntax error", "database error",
                "warning: mysql", "valid mysql result", "mysqlclient"
            ]
            return any(error in response_body.lower() for error in sql_errors)
        
        elif test_type == "xss":
            # XSS载荷是否被原样返回
            return "<script>" in response_body or "javascript:" in response_body
        
        elif test_type == "path_traversal":
            # 敏感文件内容
            sensitive_content = [
                "root:x:0:0", "[boot loader]", "# hosts file",
                "windows nt", "/bin/bash", "/bin/sh"
            ]
            return any(content in response_body.lower() for content in sensitive_content)
        
        elif test_type == "command_injection":
            # 命令执行结果
            command_outputs = [
                "uid=", "gid=", "groups=", "volume in drive",
                "directory of", "total ", "drwx", "-rw-"
            ]
            return any(output in response_body.lower() for output in command_outputs)
        
        elif test_type == "authentication":
            # 认证绕过
            return response_code == 200 and "token" in response_body.lower()
        
        elif test_type == "authorization":
            # 授权绕过
            return response_code == 200
        
        return False
    
    async def test_sql_injection(self):
        """SQL注入测试"""
        print("运行SQL注入测试...")
        
        # 测试端点
        test_endpoints = [
            ("/api/auth/login", "POST", {"email": "{payload}", "password": "test"}),
            ("/api/simulation/sessions", "GET", {"search": "{payload}"}),
            ("/api/users", "GET", {"filter": "{payload}"}),
            ("/api/simulation/sessions/{payload}", "GET", {})
        ]
        
        for endpoint, method, data in test_endpoints:
            for payload in SQL_INJECTION_PAYLOADS:
                try:
                    # 替换载荷
                    test_endpoint = endpoint.format(payload=quote(payload))
                    test_data = {}
                    
                    if method == "POST":
                        test_data = {k: v.format(payload=payload) for k, v in data.items()}
                        response_code, response_body = await self._make_request(
                            method, test_endpoint, json=test_data
                        )
                    else:
                        params = {k: v.format(payload=payload) for k, v in data.items()}
                        response_code, response_body = await self._make_request(
                            method, test_endpoint, params=params
                        )
                    
                    # 检测漏洞
                    vulnerability_detected = self._is_vulnerability_detected(
                        response_code, response_body, "sql_injection"
                    )
                    
                    # 期望被阻止（返回4xx或5xx）
                    expected_blocked = True
                    actually_blocked = response_code >= 400
                    
                    severity = "high" if vulnerability_detected else "low"
                    
                    result = SecurityTestResult(
                        test_name="SQL Injection",
                        endpoint=test_endpoint,
                        payload=payload,
                        expected_blocked=expected_blocked,
                        actually_blocked=actually_blocked,
                        response_code=response_code,
                        response_body=response_body[:500],  # 限制长度
                        vulnerability_detected=vulnerability_detected,
                        severity=severity,
                        description=f"SQL注入测试: {payload}"
                    )
                    
                    self.results.append(result)
                    
                    if vulnerability_detected:
                        print(f"⚠️  SQL注入漏洞检测: {endpoint} - {payload}")
                
                except Exception as e:
                    print(f"SQL注入测试异常: {endpoint} - {payload}: {e}")
    
    async def test_xss_vulnerabilities(self):
        """XSS漏洞测试"""
        print("运行XSS漏洞测试...")
        
        # 测试端点
        test_endpoints = [
            ("/api/simulation/sessions", "POST", {"name": "{payload}", "description": "test"}),
            ("/api/users/profile", "PUT", {"username": "{payload}", "bio": "test"}),
            ("/api/comments", "POST", {"content": "{payload}"})
        ]
        
        for endpoint, method, data in test_endpoints:
            for payload in XSS_PAYLOADS:
                try:
                    test_data = {k: v.format(payload=payload) for k, v in data.items()}
                    
                    response_code, response_body = await self._make_request(
                        method, endpoint, auth_role="user", json=test_data
                    )
                    
                    # 检测漏洞
                    vulnerability_detected = self._is_vulnerability_detected(
                        response_code, response_body, "xss"
                    )
                    
                    expected_blocked = True
                    actually_blocked = not vulnerability_detected
                    
                    severity = "medium" if vulnerability_detected else "low"
                    
                    result = SecurityTestResult(
                        test_name="XSS",
                        endpoint=endpoint,
                        payload=payload,
                        expected_blocked=expected_blocked,
                        actually_blocked=actually_blocked,
                        response_code=response_code,
                        response_body=response_body[:500],
                        vulnerability_detected=vulnerability_detected,
                        severity=severity,
                        description=f"XSS测试: {payload}"
                    )
                    
                    self.results.append(result)
                    
                    if vulnerability_detected:
                        print(f"⚠️  XSS漏洞检测: {endpoint} - {payload}")
                
                except Exception as e:
                    print(f"XSS测试异常: {endpoint} - {payload}: {e}")
    
    async def test_path_traversal(self):
        """路径遍历测试"""
        print("运行路径遍历测试...")
        
        # 测试端点
        test_endpoints = [
            "/api/files/{payload}",
            "/api/simulation/export/{payload}",
            "/api/reports/{payload}",
            "/api/static/{payload}"
        ]
        
        for endpoint in test_endpoints:
            for payload in PATH_TRAVERSAL_PAYLOADS:
                try:
                    test_endpoint = endpoint.format(payload=quote(payload))
                    
                    response_code, response_body = await self._make_request(
                        "GET", test_endpoint, auth_role="user"
                    )
                    
                    # 检测漏洞
                    vulnerability_detected = self._is_vulnerability_detected(
                        response_code, response_body, "path_traversal"
                    )
                    
                    expected_blocked = True
                    actually_blocked = response_code >= 400
                    
                    severity = "high" if vulnerability_detected else "low"
                    
                    result = SecurityTestResult(
                        test_name="Path Traversal",
                        endpoint=test_endpoint,
                        payload=payload,
                        expected_blocked=expected_blocked,
                        actually_blocked=actually_blocked,
                        response_code=response_code,
                        response_body=response_body[:500],
                        vulnerability_detected=vulnerability_detected,
                        severity=severity,
                        description=f"路径遍历测试: {payload}"
                    )
                    
                    self.results.append(result)
                    
                    if vulnerability_detected:
                        print(f"⚠️  路径遍历漏洞检测: {test_endpoint} - {payload}")
                
                except Exception as e:
                    print(f"路径遍历测试异常: {test_endpoint} - {payload}: {e}")
    
    async def test_authentication_bypass(self):
        """认证绕过测试"""
        print("运行认证绕过测试...")
        
        # 测试无token访问受保护端点
        protected_endpoints = [
            "/api/simulation/sessions",
            "/api/users/profile",
            "/api/admin/users",
            "/api/performance/metrics"
        ]
        
        for endpoint in protected_endpoints:
            try:
                response_code, response_body = await self._make_request("GET", endpoint)
                
                # 期望返回401或403
                expected_blocked = True
                actually_blocked = response_code in [401, 403]
                vulnerability_detected = response_code == 200
                
                severity = "critical" if vulnerability_detected else "low"
                
                result = SecurityTestResult(
                    test_name="Authentication Bypass",
                    endpoint=endpoint,
                    payload="No Token",
                    expected_blocked=expected_blocked,
                    actually_blocked=actually_blocked,
                    response_code=response_code,
                    response_body=response_body[:500],
                    vulnerability_detected=vulnerability_detected,
                    severity=severity,
                    description="无token访问受保护端点"
                )
                
                self.results.append(result)
                
                if vulnerability_detected:
                    print(f"⚠️  认证绕过漏洞: {endpoint}")
            
            except Exception as e:
                print(f"认证绕过测试异常: {endpoint}: {e}")
        
        # 测试无效token
        invalid_tokens = [
            "invalid_token",
            "Bearer invalid",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "../../../etc/passwd",
            "<script>alert('xss')</script>"
        ]
        
        for token in invalid_tokens:
            for endpoint in protected_endpoints[:2]:  # 测试部分端点
                try:
                    headers = {"Authorization": f"Bearer {token}"}
                    response_code, response_body = await self._make_request(
                        "GET", endpoint, headers=headers
                    )
                    
                    expected_blocked = True
                    actually_blocked = response_code in [401, 403]
                    vulnerability_detected = response_code == 200
                    
                    severity = "high" if vulnerability_detected else "low"
                    
                    result = SecurityTestResult(
                        test_name="Invalid Token",
                        endpoint=endpoint,
                        payload=token,
                        expected_blocked=expected_blocked,
                        actually_blocked=actually_blocked,
                        response_code=response_code,
                        response_body=response_body[:500],
                        vulnerability_detected=vulnerability_detected,
                        severity=severity,
                        description=f"无效token测试: {token}"
                    )
                    
                    self.results.append(result)
                    
                    if vulnerability_detected:
                        print(f"⚠️  无效token绕过: {endpoint} - {token}")
                
                except Exception as e:
                    print(f"无效token测试异常: {endpoint} - {token}: {e}")
    
    async def test_authorization_bypass(self):
        """授权绕过测试"""
        print("运行授权绕过测试...")
        
        # 测试普通用户访问管理员端点
        admin_endpoints = [
            "/api/admin/users",
            "/api/admin/system",
            "/api/admin/logs",
            "/api/admin/config"
        ]
        
        for endpoint in admin_endpoints:
            try:
                # 使用普通用户token访问管理员端点
                response_code, response_body = await self._make_request(
                    "GET", endpoint, auth_role="user"
                )
                
                expected_blocked = True
                actually_blocked = response_code in [401, 403]
                vulnerability_detected = response_code == 200
                
                severity = "high" if vulnerability_detected else "low"
                
                result = SecurityTestResult(
                    test_name="Authorization Bypass",
                    endpoint=endpoint,
                    payload="User Token",
                    expected_blocked=expected_blocked,
                    actually_blocked=actually_blocked,
                    response_code=response_code,
                    response_body=response_body[:500],
                    vulnerability_detected=vulnerability_detected,
                    severity=severity,
                    description="普通用户访问管理员端点"
                )
                
                self.results.append(result)
                
                if vulnerability_detected:
                    print(f"⚠️  授权绕过漏洞: {endpoint}")
            
            except Exception as e:
                print(f"授权绕过测试异常: {endpoint}: {e}")
    
    async def test_weak_passwords(self):
        """弱密码测试"""
        print("运行弱密码测试...")
        
        # 测试是否允许弱密码注册
        for password in WEAK_PASSWORDS[:10]:  # 测试前10个
            try:
                user_data = {
                    "email": f"weakpass_{password}@example.com",
                    "password": password,
                    "username": f"weakuser_{password}"
                }
                
                response_code, response_body = await self._make_request(
                    "POST", "/api/auth/register", json=user_data
                )
                
                # 期望弱密码被拒绝
                expected_blocked = True
                actually_blocked = response_code >= 400
                vulnerability_detected = response_code in [200, 201]
                
                severity = "medium" if vulnerability_detected else "low"
                
                result = SecurityTestResult(
                    test_name="Weak Password",
                    endpoint="/api/auth/register",
                    payload=password,
                    expected_blocked=expected_blocked,
                    actually_blocked=actually_blocked,
                    response_code=response_code,
                    response_body=response_body[:500],
                    vulnerability_detected=vulnerability_detected,
                    severity=severity,
                    description=f"弱密码测试: {password}"
                )
                
                self.results.append(result)
                
                if vulnerability_detected:
                    print(f"⚠️  弱密码被接受: {password}")
            
            except Exception as e:
                print(f"弱密码测试异常: {password}: {e}")
    
    async def test_rate_limiting(self):
        """速率限制测试"""
        print("运行速率限制测试...")
        
        # 快速发送大量请求
        endpoint = "/api/auth/login"
        login_data = {"email": "test@example.com", "password": "wrongpassword"}
        
        rate_limit_triggered = False
        
        for i in range(20):  # 发送20个请求
            try:
                response_code, response_body = await self._make_request(
                    "POST", endpoint, json=login_data
                )
                
                # 检查是否触发速率限制（429状态码）
                if response_code == 429:
                    rate_limit_triggered = True
                    break
            
            except Exception as e:
                print(f"速率限制测试异常: {e}")
        
        # 期望触发速率限制
        expected_blocked = True
        actually_blocked = rate_limit_triggered
        vulnerability_detected = not rate_limit_triggered
        
        severity = "medium" if vulnerability_detected else "low"
        
        result = SecurityTestResult(
            test_name="Rate Limiting",
            endpoint=endpoint,
            payload="20 rapid requests",
            expected_blocked=expected_blocked,
            actually_blocked=actually_blocked,
            response_code=429 if rate_limit_triggered else 200,
            response_body="Rate limit test",
            vulnerability_detected=vulnerability_detected,
            severity=severity,
            description="速率限制测试"
        )
        
        self.results.append(result)
        
        if vulnerability_detected:
            print("⚠️  速率限制未生效")
    
    async def run_all_security_tests(self):
        """运行所有安全测试"""
        print("=== 开始安全测试 ===")
        
        test_methods = [
            self.test_sql_injection,
            self.test_xss_vulnerabilities,
            self.test_path_traversal,
            self.test_authentication_bypass,
            self.test_authorization_bypass,
            self.test_weak_passwords,
            self.test_rate_limiting
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                print(f"测试方法 {test_method.__name__} 执行失败: {e}")
        
        print("=== 安全测试完成 ===")
    
    def generate_security_report(self) -> str:
        """生成安全测试报告"""
        if not self.results:
            return "没有安全测试结果"
        
        # 统计
        total_tests = len(self.results)
        vulnerabilities = [r for r in self.results if r.vulnerability_detected]
        critical_vulns = [r for r in vulnerabilities if r.severity == "critical"]
        high_vulns = [r for r in vulnerabilities if r.severity == "high"]
        medium_vulns = [r for r in vulnerabilities if r.severity == "medium"]
        low_vulns = [r for r in vulnerabilities if r.severity == "low"]
        
        report = f"""
=== 安全测试报告 ===
测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
总测试数: {total_tests}
发现漏洞: {len(vulnerabilities)}

=== 漏洞严重程度分布 ===
严重 (Critical): {len(critical_vulns)}
高危 (High): {len(high_vulns)}
中危 (Medium): {len(medium_vulns)}
低危 (Low): {len(low_vulns)}

=== 测试类型统计 ===
"""
        
        # 按测试类型统计
        test_types = {}
        for result in self.results:
            test_type = result.test_name
            if test_type not in test_types:
                test_types[test_type] = {"total": 0, "vulnerabilities": 0}
            
            test_types[test_type]["total"] += 1
            if result.vulnerability_detected:
                test_types[test_type]["vulnerabilities"] += 1
        
        for test_type, stats in test_types.items():
            vuln_rate = (stats["vulnerabilities"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            report += f"{test_type}: {stats['vulnerabilities']}/{stats['total']} ({vuln_rate:.1f}% 漏洞率)\n"
        
        # 详细漏洞列表
        if vulnerabilities:
            report += "\n=== 发现的漏洞 ===\n"
            for vuln in vulnerabilities:
                report += f"\n[{vuln.severity.upper()}] {vuln.test_name}\n"
                report += f"端点: {vuln.endpoint}\n"
                report += f"载荷: {vuln.payload}\n"
                report += f"描述: {vuln.description}\n"
                report += f"响应码: {vuln.response_code}\n"
                report += "-" * 50 + "\n"
        
        return report
    
    def save_security_report(self, filename: str):
        """保存安全测试报告"""
        report_data = {
            "timestamp": time.time(),
            "summary": {
                "total_tests": len(self.results),
                "vulnerabilities_found": len([r for r in self.results if r.vulnerability_detected]),
                "critical_count": len([r for r in self.results if r.vulnerability_detected and r.severity == "critical"]),
                "high_count": len([r for r in self.results if r.vulnerability_detected and r.severity == "high"]),
                "medium_count": len([r for r in self.results if r.vulnerability_detected and r.severity == "medium"]),
                "low_count": len([r for r in self.results if r.vulnerability_detected and r.severity == "low"])
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "endpoint": r.endpoint,
                    "payload": r.payload,
                    "expected_blocked": r.expected_blocked,
                    "actually_blocked": r.actually_blocked,
                    "response_code": r.response_code,
                    "vulnerability_detected": r.vulnerability_detected,
                    "severity": r.severity,
                    "description": r.description
                }
                for r in self.results
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)


# pytest测试函数
@pytest.mark.asyncio
async def test_sql_injection_protection():
    """SQL注入防护测试"""
    tester = SecurityTester()
    
    try:
        await tester.setup()
        await tester.test_sql_injection()
        
        # 检查是否有SQL注入漏洞
        sql_vulnerabilities = [
            r for r in tester.results 
            if r.test_name == "SQL Injection" and r.vulnerability_detected
        ]
        
        assert len(sql_vulnerabilities) == 0, f"发现 {len(sql_vulnerabilities)} 个SQL注入漏洞"
    
    finally:
        await tester.teardown()


@pytest.mark.asyncio
async def test_authentication_security():
    """认证安全测试"""
    tester = SecurityTester()
    
    try:
        await tester.setup()
        await tester.test_authentication_bypass()
        
        # 检查认证绕过漏洞
        auth_vulnerabilities = [
            r for r in tester.results 
            if r.test_name in ["Authentication Bypass", "Invalid Token"] and r.vulnerability_detected
        ]
        
        assert len(auth_vulnerabilities) == 0, f"发现 {len(auth_vulnerabilities)} 个认证绕过漏洞"
    
    finally:
        await tester.teardown()


@pytest.mark.asyncio
async def test_xss_protection():
    """XSS防护测试"""
    tester = SecurityTester()
    
    try:
        await tester.setup()
        await tester.test_xss_vulnerabilities()
        
        # 检查XSS漏洞
        xss_vulnerabilities = [
            r for r in tester.results 
            if r.test_name == "XSS" and r.vulnerability_detected
        ]
        
        assert len(xss_vulnerabilities) == 0, f"发现 {len(xss_vulnerabilities)} 个XSS漏洞"
    
    finally:
        await tester.teardown()


@pytest.mark.asyncio
async def test_full_security_suite():
    """完整安全测试套件"""
    tester = SecurityTester()
    
    try:
        await tester.setup()
        await tester.run_all_security_tests()
        
        # 生成报告
        report = tester.generate_security_report()
        print(report)
        
        # 保存报告
        tester.save_security_report("security_test_report.json")
        
        # 检查严重漏洞
        critical_vulnerabilities = [
            r for r in tester.results 
            if r.vulnerability_detected and r.severity == "critical"
        ]
        
        assert len(critical_vulnerabilities) == 0, f"发现 {len(critical_vulnerabilities)} 个严重安全漏洞"
    
    finally:
        await tester.teardown()


if __name__ == "__main__":
    async def main():
        tester = SecurityTester()
        
        try:
            await tester.setup()
            await tester.run_all_security_tests()
            
            # 生成并打印报告
            report = tester.generate_security_report()
            print(report)
            
            # 保存报告
            tester.save_security_report("security_test_report.json")
            
            # 返回是否有严重漏洞
            critical_vulns = [
                r for r in tester.results 
                if r.vulnerability_detected and r.severity in ["critical", "high"]
            ]
            
            if critical_vulns:
                print(f"\n⚠️  发现 {len(critical_vulns)} 个严重安全漏洞！")
                return False
            else:
                print("\n✅ 未发现严重安全漏洞")
                return True
        
        finally:
            await tester.teardown()
    
    # 运行安全测试
    success = asyncio.run(main())
    exit(0 if success else 1)