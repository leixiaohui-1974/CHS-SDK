# CHS-SDK 测试指南

## 概述

CHS-SDK 采用多层次测试策略，确保系统的可靠性、性能和安全性。测试套件包括单元测试、集成测试、端到端测试、性能测试和安全测试。

## 测试目录结构

```
tests/
├── e2e/                     # 端到端测试
│   └── test_e2e.py
├── performance/             # 性能测试
│   └── test_load.py
├── security/                # 安全测试
│   └── test_security.py
├── test_*.py                # 单元和集成测试
├── conftest.py.bak          # pytest 配置备份
└── test_data/               # 测试数据
    └── test_inflow.csv
```

## 测试分类

### 1. 单元测试

#### 智能体测试
- `test_central_dispatcher_agent.py`: 中央调度智能体测试
- `test_central_mpc_agent.py`: 中央MPC智能体测试
- `test_central_perception_agent.py`: 中央感知智能体测试
- `test_csv_inflow_agent.py`: CSV流入智能体测试
- `test_emergency_agent.py`: 应急智能体测试
- `test_reservoir_perception_agent.py`: 水库感知智能体测试
- `test_valve_control_agent.py`: 阀门控制智能体测试

#### 核心组件测试
- `test_reservoir.py`: 水库组件测试
- `test_simulation_builder.py`: 仿真构建器测试

### 2. 集成测试

#### API 集成测试
- `test_api_endpoints.py`: 基础API端点测试
- `test_api_endpoints_comprehensive.py`: 全面API端点测试
- `test_api_auth.py`: API认证测试
- `test_api_monitoring.py`: API监控测试

#### 智能体集成测试
- `test_agents_integration.py`: 智能体集成测试
- `test_integration_workflow.py`: 集成工作流测试

#### 后端集成测试
- `test_backend_comprehensive.py`: 后端综合测试
- `test_batch_simulation.py`: 批处理仿真测试

### 3. 工作流测试

- `test_simulation_workflow.py`: 仿真工作流测试
- `test_cloud_deployment.py`: 云部署测试

### 4. 性能测试

#### 基础性能测试
- `test_performance.py`: 基础性能测试
- `test_simple_performance.py`: 简单性能测试

#### 压力测试
- `test_performance_stress.py`: 性能压力测试
- `test_performance_benchmark.py`: 性能基准测试
- `performance/test_load.py`: 负载测试

#### WebSocket 测试
- `test_websocket_monitor.py`: WebSocket监控测试
- `test_websocket_stress.py`: WebSocket压力测试

### 5. 端到端测试

- `e2e/test_e2e.py`: 端到端功能测试

### 6. 安全测试

- `security/test_security.py`: 安全功能测试
- `test_simple_security.py`: 简单安全测试

### 7. 监控测试

- `test_simple_monitoring.py`: 简单监控测试
- `test_simple_scenario.py`: 简单场景测试

## 测试策略

### 1. 测试金字塔

```
    ┌─────────────┐
    │   E2E Tests │  # 少量，关键路径
    └─────────────┘
  ┌─────────────────┐
  │ Integration Tests│  # 中等数量，组件交互
  └─────────────────┘
┌─────────────────────┐
│    Unit Tests       │  # 大量，单个组件
└─────────────────────┘
```

### 2. 测试覆盖率目标

- **单元测试**: 90%+ 代码覆盖率
- **集成测试**: 80%+ 功能覆盖率
- **端到端测试**: 100% 关键路径覆盖

### 3. 测试环境

#### 开发环境
- 本地SQLite数据库
- Mock外部服务
- 快速反馈循环

#### 测试环境
- 独立测试数据库
- 真实外部服务
- 完整功能验证

#### 生产环境
- 生产数据副本
- 真实负载测试
- 性能基准验证

## 测试工具和框架

### 1. 核心测试框架

```python
# pytest - 主要测试框架
pytest>=7.0.0

# pytest插件
pytest-asyncio>=0.21.0      # 异步测试支持
pytest-cov>=4.0.0           # 代码覆盖率
pytest-mock>=3.10.0         # Mock支持
pytest-xdist>=3.2.0         # 并行测试
```

### 2. 性能测试工具

```python
# locust - 负载测试
locust>=2.14.0

# memory-profiler - 内存分析
memory-profiler>=0.60.0

# psutil - 系统监控
psutil>=5.9.0
```

### 3. 安全测试工具

```python
# bandit - 安全漏洞扫描
bandit>=1.7.0

# safety - 依赖安全检查
safety>=2.3.0
```

## 测试配置

### pytest.ini 配置

```ini
[tool:pytest]
addopts = 
    --strict-markers
    --strict-config
    --cov=api
    --cov=core_lib
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    -v

testpaths = tests

markers =
    unit: 单元测试
    integration: 集成测试
    e2e: 端到端测试
    performance: 性能测试
    security: 安全测试
    slow: 慢速测试
    smoke: 冒烟测试
```

### conftest.py 配置

```python
import pytest
import asyncio
from fastapi.testclient import TestClient
from api.server import app
from api.database.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """创建测试客户端"""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine(TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
```

## 测试数据管理

### 1. 测试数据策略

#### 固定测试数据
- 存储在 `test_data/` 目录
- 版本控制管理
- 数据一致性保证

#### 动态测试数据
- 使用 Factory Boy 生成
- 随机数据生成
- 边界值测试

### 2. 数据清理策略

```python
@pytest.fixture(autouse=True)
def cleanup_database():
    """自动清理测试数据"""
    yield
    # 测试后清理
    cleanup_test_data()
```

## 测试执行

### 1. 本地测试执行

```bash
# 运行所有测试
pytest

# 运行特定类型测试
pytest -m unit                    # 单元测试
pytest -m integration             # 集成测试
pytest -m "not slow"              # 排除慢速测试

# 运行特定文件
pytest tests/test_api_endpoints.py

# 运行特定测试方法
pytest tests/test_api_endpoints.py::test_health_check

# 并行执行
pytest -n auto                    # 自动检测CPU核心数
pytest -n 4                       # 使用4个进程

# 生成覆盖率报告
pytest --cov-report=html
```

### 2. CI/CD 测试执行

```yaml
# GitHub Actions 配置示例
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: |
        pytest --cov=api --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 性能测试详解

### 1. 负载测试

```python
# 使用 locust 进行负载测试
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def test_simulation_endpoint(self):
        self.client.post("/api/simulation/run", json={
            "scenario_id": "test_scenario",
            "duration": 100
        })
    
    @task(1)
    def test_monitoring_endpoint(self):
        self.client.get("/api/monitoring/status")
```

### 2. 压力测试

```python
# 压力测试示例
import asyncio
import aiohttp
import time

async def stress_test():
    """API压力测试"""
    concurrent_requests = 100
    total_requests = 1000
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(total_requests):
            task = asyncio.create_task(
                make_request(session, f"/api/test/{i}")
            )
            tasks.append(task)
            
            if len(tasks) >= concurrent_requests:
                await asyncio.gather(*tasks)
                tasks = []
        
        if tasks:
            await asyncio.gather(*tasks)
```

### 3. 内存和CPU监控

```python
import psutil
import memory_profiler

@memory_profiler.profile
def test_memory_usage():
    """内存使用测试"""
    # 执行内存密集型操作
    large_data = [i for i in range(1000000)]
    return len(large_data)

def test_cpu_usage():
    """CPU使用测试"""
    start_cpu = psutil.cpu_percent()
    # 执行CPU密集型操作
    result = sum(i**2 for i in range(100000))
    end_cpu = psutil.cpu_percent()
    
    assert end_cpu - start_cpu < 80  # CPU使用率不超过80%
```

## 安全测试详解

### 1. 认证测试

```python
def test_unauthorized_access():
    """未授权访问测试"""
    response = client.get("/api/protected")
    assert response.status_code == 401

def test_invalid_token():
    """无效Token测试"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/protected", headers=headers)
    assert response.status_code == 401
```

### 2. 输入验证测试

```python
def test_sql_injection():
    """SQL注入测试"""
    malicious_input = "'; DROP TABLE users; --"
    response = client.post("/api/search", json={
        "query": malicious_input
    })
    assert response.status_code == 400

def test_xss_protection():
    """XSS攻击测试"""
    xss_payload = "<script>alert('xss')</script>"
    response = client.post("/api/comment", json={
        "content": xss_payload
    })
    assert "<script>" not in response.json()["content"]
```

## 测试最佳实践

### 1. 测试命名规范

```python
# 好的测试命名
def test_user_login_with_valid_credentials_returns_token():
    pass

def test_user_login_with_invalid_password_returns_401():
    pass

# 避免的命名
def test_login():
    pass

def test_user_stuff():
    pass
```

### 2. 测试结构 (AAA模式)

```python
def test_create_user_success():
    # Arrange - 准备测试数据
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword"
    }
    
    # Act - 执行被测试的操作
    response = client.post("/api/users", json=user_data)
    
    # Assert - 验证结果
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"
    assert "password" not in response.json()
```

### 3. Mock 使用

```python
from unittest.mock import patch, MagicMock

@patch('api.services.external_service.call_api')
def test_external_service_integration(mock_call_api):
    # 配置Mock
    mock_call_api.return_value = {"status": "success"}
    
    # 执行测试
    result = service.process_data()
    
    # 验证Mock调用
    mock_call_api.assert_called_once_with(expected_params)
    assert result["status"] == "success"
```

### 4. 参数化测试

```python
import pytest

@pytest.mark.parametrize("input_value,expected", [
    ("valid_email@example.com", True),
    ("invalid_email", False),
    ("", False),
    (None, False),
])
def test_email_validation(input_value, expected):
    result = validate_email(input_value)
    assert result == expected
```

## 持续集成测试

### 1. 测试阶段

```yaml
stages:
  - lint          # 代码质量检查
  - unit-test     # 单元测试
  - integration   # 集成测试
  - security      # 安全测试
  - performance   # 性能测试
  - e2e          # 端到端测试
```

### 2. 测试报告

- **覆盖率报告**: HTML格式，详细展示代码覆盖情况
- **性能报告**: 响应时间、吞吐量等指标
- **安全报告**: 漏洞扫描结果
- **测试结果**: JUnit XML格式，集成到CI/CD

## 故障排查

### 1. 常见测试问题

#### 测试不稳定
- 检查异步操作
- 验证测试数据隔离
- 确认外部依赖Mock

#### 性能测试失败
- 检查系统资源
- 验证测试环境配置
- 分析性能瓶颈

#### 集成测试失败
- 检查服务依赖
- 验证网络连接
- 确认配置正确

### 2. 调试技巧

```python
# 使用pytest调试
pytest --pdb                    # 失败时进入调试器
pytest --pdbcls=IPython.terminal.debugger:Pdb  # 使用IPython调试器

# 详细输出
pytest -v -s                   # 显示详细信息和print输出

# 只运行失败的测试
pytest --lf                     # last failed
pytest --ff                     # failed first
```

## 测试维护

### 1. 定期维护任务

- 更新测试数据
- 清理过时测试
- 优化测试性能
- 更新测试文档

### 2. 测试指标监控

- 测试执行时间
- 测试成功率
- 代码覆盖率趋势
- 缺陷发现率

---

本测试指南提供了CHS-SDK项目的完整测试策略和实践方法，帮助开发团队构建高质量、可靠的软件系统。