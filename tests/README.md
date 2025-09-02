# CHS-SDK 测试套件

## 概述

本目录包含 CHS-SDK 项目的完整测试套件，涵盖单元测试、集成测试、性能测试、安全测试和端到端测试。测试套件确保系统的可靠性、性能和安全性。

## 测试目录结构

```
tests/
├── README.md                           # 本文档
├── conftest.py.bak                     # pytest 配置备份
├── test_data/                          # 测试数据
│   └── test_inflow.csv                # 测试流入数据
├── e2e/                                # 端到端测试
│   └── test_e2e.py                    # 端到端功能测试
├── performance/                        # 性能测试
│   └── test_load.py                   # 负载测试
├── security/                           # 安全测试
│   └── test_security.py               # 安全功能测试
├── unit/                               # 单元测试 (按模块组织)
│   ├── test_agents/                   # 智能体单元测试
│   ├── test_api/                      # API 单元测试
│   └── test_core/                     # 核心模块单元测试
├── integration/                        # 集成测试
│   ├── test_api_integration.py        # API 集成测试
│   └── test_workflow_integration.py   # 工作流集成测试
└── 各种测试文件                        # 现有测试文件
```

## 测试分类说明

### 1. 智能体测试

#### 中央智能体测试
- `test_central_dispatcher_agent.py`: 中央调度智能体
- `test_central_mpc_agent.py`: 中央MPC控制智能体
- `test_central_perception_agent.py`: 中央感知智能体

#### 本地智能体测试
- `test_csv_inflow_agent.py`: CSV流入数据智能体
- `test_emergency_agent.py`: 应急响应智能体
- `test_reservoir_perception_agent.py`: 水库感知智能体
- `test_valve_control_agent.py`: 阀门控制智能体

### 2. API 测试

#### 基础 API 测试
- `test_api_endpoints.py`: 基础API端点测试
- `test_api_auth.py`: API认证测试
- `test_api_monitoring.py`: API监控测试

#### 综合 API 测试
- `test_api_endpoints_comprehensive.py`: 全面API端点测试
- `test_backend_comprehensive.py`: 后端综合测试

### 3. 集成测试

#### 智能体集成
- `test_agents_integration.py`: 智能体间协作测试
- `test_integration_workflow.py`: 集成工作流测试

#### 系统集成
- `test_batch_simulation.py`: 批处理仿真测试
- `test_simulation_workflow.py`: 仿真工作流测试

### 4. 性能测试

#### 基础性能测试
- `test_performance.py`: 基础性能测试
- `test_simple_performance.py`: 简单性能测试

#### 压力测试
- `test_performance_stress.py`: 性能压力测试
- `test_performance_benchmark.py`: 性能基准测试

#### WebSocket 测试
- `test_websocket_monitor.py`: WebSocket监控测试
- `test_websocket_stress.py`: WebSocket压力测试

### 5. 组件测试

#### 核心组件
- `test_reservoir.py`: 水库组件测试
- `test_simulation_builder.py`: 仿真构建器测试

#### 监控组件
- `test_simple_monitoring.py`: 简单监控测试
- `test_simple_scenario.py`: 简单场景测试

### 6. 部署测试

- `test_cloud_deployment.py`: 云部署测试

### 7. 安全测试

- `test_simple_security.py`: 简单安全测试
- `security/test_security.py`: 综合安全测试

## 运行测试

### 1. 运行所有测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=api --cov=core_lib --cov-report=html

# 运行测试并显示详细输出
pytest -v
```

### 2. 运行特定类型的测试

```bash
# 运行单元测试
pytest -m unit

# 运行集成测试
pytest -m integration

# 运行性能测试
pytest -m performance

# 运行安全测试
pytest -m security

# 运行端到端测试
pytest -m e2e
```

### 3. 运行特定模块的测试

```bash
# 运行智能体测试
pytest tests/test_*agent*.py

# 运行API测试
pytest tests/test_api*.py

# 运行性能相关测试
pytest tests/test_*performance*.py tests/performance/

# 运行WebSocket测试
pytest tests/test_websocket*.py
```

### 4. 运行特定测试文件

```bash
# 运行单个测试文件
pytest tests/test_backend_comprehensive.py

# 运行特定测试方法
pytest tests/test_backend_comprehensive.py::TestMultiAgentIntegration::test_agent_initialization

# 运行特定测试类
pytest tests/test_performance_benchmark.py::TestAgentPerformanceBenchmarks
```

### 5. 并行运行测试

```bash
# 使用多进程并行运行
pytest -n auto  # 自动检测CPU核心数
pytest -n 4     # 使用4个进程

# 分布式运行测试
pytest --dist=loadscope
```

## 测试配置

### pytest 标记 (Markers)

```python
# 在测试文件中使用标记
@pytest.mark.unit
def test_reservoir_initialization():
    pass

@pytest.mark.integration
def test_agent_communication():
    pass

@pytest.mark.performance
def test_simulation_speed():
    pass

@pytest.mark.slow
def test_long_running_simulation():
    pass

@pytest.mark.security
def test_authentication():
    pass
```

### 跳过测试

```bash
# 跳过慢速测试
pytest -m "not slow"

# 跳过特定标记的测试
pytest -m "not performance"

# 只运行快速测试
pytest -m "unit or integration"
```

## 测试数据管理

### 测试数据文件

- `test_data/test_inflow.csv`: 测试用的流入数据
- 其他测试数据文件按需添加到 `test_data/` 目录

### 使用测试数据

```python
import pandas as pd
from pathlib import Path

def load_test_data(filename: str) -> pd.DataFrame:
    """加载测试数据。"""
    test_data_dir = Path(__file__).parent / "test_data"
    return pd.read_csv(test_data_dir / filename)

# 在测试中使用
def test_inflow_processing():
    test_data = load_test_data("test_inflow.csv")
    result = process_inflow_data(test_data)
    assert len(result) > 0
```

## 测试环境配置

### 环境变量

```bash
# 设置测试环境
export TESTING=true
export DATABASE_URL="sqlite:///./test.db"
export LOG_LEVEL="DEBUG"

# 或使用 .env.test 文件
cp .env.example .env.test
# 编辑 .env.test 设置测试专用配置
```

### 数据库配置

```python
# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_db():
    """创建测试数据库。"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    # 清理
    os.remove("test.db")
```

## 性能测试详解

### 负载测试

```bash
# 使用 locust 进行负载测试
locust -f tests/performance/test_load.py --host=http://localhost:8000

# 命令行负载测试
locust -f tests/performance/test_load.py --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 60s --headless
```

### 性能基准测试

```bash
# 运行性能基准测试
pytest tests/test_performance_benchmark.py -v

# 生成性能报告
pytest tests/test_performance_benchmark.py --benchmark-only --benchmark-sort=mean
```

### WebSocket 压力测试

```bash
# 运行WebSocket压力测试
pytest tests/test_websocket_stress.py -v

# 指定并发连接数
pytest tests/test_websocket_stress.py -v --concurrent-connections=100
```

## 安全测试详解

### 认证测试

```bash
# 运行认证相关测试
pytest tests/test_api_auth.py -v

# 运行安全测试套件
pytest tests/security/ -v
```

### 输入验证测试

```bash
# 测试输入验证和注入攻击防护
pytest tests/test_simple_security.py -v
```

## 端到端测试详解

### 完整工作流测试

```bash
# 运行端到端测试
pytest tests/e2e/ -v

# 运行集成工作流测试
pytest tests/test_integration_workflow.py -v
```

## 测试报告

### 生成测试报告

```bash
# 生成HTML测试报告
pytest --html=reports/report.html --self-contained-html

# 生成JUnit XML报告
pytest --junitxml=reports/junit.xml

# 生成覆盖率报告
pytest --cov=api --cov=core_lib --cov-report=html:reports/coverage
```

### 查看报告

```bash
# 查看覆盖率报告
open reports/coverage/index.html  # macOS
start reports/coverage/index.html  # Windows
xdg-open reports/coverage/index.html  # Linux
```

## 持续集成

### GitHub Actions 配置

```yaml
# .github/workflows/test.yml
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
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: |
        pytest --cov=api --cov=core_lib --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 调试测试

### 调试失败的测试

```bash
# 在失败时进入调试器
pytest --pdb

# 在第一个失败时停止
pytest -x

# 显示详细的失败信息
pytest -vvv

# 显示本地变量
pytest -l
```

### 重新运行失败的测试

```bash
# 只运行上次失败的测试
pytest --lf

# 先运行失败的测试，再运行其他测试
pytest --ff
```

## 测试最佳实践

### 1. 测试命名

```python
# 好的测试命名
def test_reservoir_agent_sets_target_level_successfully():
    pass

def test_api_returns_401_when_token_is_invalid():
    pass

def test_simulation_completes_within_timeout():
    pass

# 避免的命名
def test_reservoir():
    pass

def test_api():
    pass
```

### 2. 测试结构 (AAA 模式)

```python
def test_water_level_calculation():
    # Arrange - 准备测试数据
    reservoir = WaterReservoir(capacity=1000, initial_level=500)
    inflow_rate = 10.0
    
    # Act - 执行被测试的操作
    reservoir.add_inflow(inflow_rate, duration=60)
    
    # Assert - 验证结果
    expected_level = 500 + (10.0 * 60)
    assert reservoir.current_level == expected_level
```

### 3. 使用 Fixtures

```python
@pytest.fixture
def sample_reservoir():
    """创建示例水库。"""
    return WaterReservoir(capacity=1000, initial_level=500)

@pytest.fixture
def api_client():
    """创建API测试客户端。"""
    with TestClient(app) as client:
        yield client

def test_reservoir_with_fixture(sample_reservoir):
    """使用fixture的测试。"""
    assert sample_reservoir.capacity == 1000
```

### 4. 参数化测试

```python
@pytest.mark.parametrize("level,expected_status", [
    (0.0, "empty"),
    (0.3, "low"),
    (0.7, "normal"),
    (1.0, "full"),
])
def test_water_level_status(level, expected_status):
    reservoir = WaterReservoir(capacity=1000)
    reservoir.set_level(level * 1000)
    assert reservoir.get_status() == expected_status
```

## 故障排查

### 常见问题

1. **测试数据库连接失败**
   ```bash
   # 检查测试数据库配置
   echo $TEST_DATABASE_URL
   
   # 重新创建测试数据库
   rm test.db
   python -c "from api.database.database import create_tables; create_tables()"
   ```

2. **导入错误**
   ```bash
   # 检查Python路径
   export PYTHONPATH=$PWD:$PYTHONPATH
   
   # 或在pytest.ini中配置
   [tool:pytest]
   pythonpath = .
   ```

3. **测试超时**
   ```bash
   # 增加超时时间
   pytest --timeout=300
   
   # 或在测试中设置
   @pytest.mark.timeout(60)
   def test_long_running_operation():
       pass
   ```

4. **内存不足**
   ```bash
   # 减少并行进程数
   pytest -n 2
   
   # 或分批运行测试
   pytest tests/test_api*.py
   pytest tests/test_agent*.py
   ```

### 获取帮助

```bash
# 查看pytest帮助
pytest --help

# 查看可用的标记
pytest --markers

# 查看可用的fixtures
pytest --fixtures
```

## 贡献指南

### 添加新测试

1. 确定测试类型（单元/集成/性能/安全）
2. 选择合适的文件或创建新文件
3. 遵循命名规范和代码风格
4. 添加适当的标记和文档
5. 确保测试可以独立运行

### 测试代码审查

- 测试覆盖了所有重要的代码路径
- 测试是独立的，不依赖其他测试
- 测试有清晰的断言和错误消息
- 测试运行速度合理
- 测试代码易于理解和维护

---

本测试套件为 CHS-SDK 项目提供全面的质量保障。如有问题或建议，请联系开发团队或提交 Issue。