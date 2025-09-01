# 通用调试系统

一个功能强大的调试和日志管理系统，专为复杂仿真和开发项目设计。该系统提供统一的日志管理、智能数据收集、自动分析和实时监控功能。

## 🌟 主要特性

### 📝 统一日志管理
- **多级日志支持**: TRACE, DEBUG, INFO, WARNING, ERROR, FATAL
- **多种输出目标**: 控制台、文件、数据库
- **结构化日志**: JSON格式，支持自定义字段
- **异步写入**: 高性能，不阻塞主程序
- **自动轮转**: 文件大小和时间轮转，自动压缩

### 🔍 智能数据收集
- **自动收集**: 系统资源、性能指标、函数调用
- **自定义收集**: 仿真状态、业务数据、错误信息
- **实时监控**: 内存、CPU、磁盘使用情况
- **事件追踪**: 用户操作、系统事件

### 📊 智能日志分析
- **模式识别**: 自动发现日志模式和异常
- **性能分析**: 识别性能瓶颈和趋势
- **错误分析**: 错误分类和根因分析
- **趋势分析**: 长期趋势和预测
- **智能报告**: 自动生成分析报告

### 🖥️ 实时监控仪表板
- **Web界面**: 现代化的实时监控界面
- **命令行界面**: 轻量级的终端监控
- **实时数据**: 自动刷新的监控数据
- **交互式图表**: 性能趋势可视化
- **告警系统**: 异常情况实时通知

## 🚀 快速开始

### 基础使用

```python
from core_lib.debug import setup_logging, get_logger, collect_debug_data

# 1. 设置日志系统
log_config = {
    'session_id': 'my_project_session',
    'console': {'enabled': True, 'level': 'INFO'},
    'file': {
        'enabled': True,
        'path': 'logs/my_project.log',
        'level': 'DEBUG'
    }
}
setup_logging(log_config)

# 2. 获取日志器并记录日志
logger = get_logger()
logger.info("应用程序启动", "main", version="1.0.0")

# 3. 收集调试数据
collect_debug_data(
    'performance_metric',
    'response_time',
    0.123,
    {'endpoint': '/api/data', 'method': 'GET'}
)
```

### 启动Web仪表板

```python
from core_lib.debug import start_web_dashboard

# 启动Web仪表板
url = start_web_dashboard(port=8080, open_browser=True)
print(f"仪表板地址: {url}")
```

### 日志分析

```python
from core_lib.debug import get_analysis_engine

# 分析日志文件
engine = get_analysis_engine()
results = engine.analyze_file(
    'logs/my_project.log',
    ['pattern', 'performance', 'error']
)

# 生成分析报告
report = engine.generate_report(results)
with open('analysis_report.md', 'w') as f:
    f.write(report)
```

## 📁 系统架构

```
core_lib/debug/
├── debug_system_architecture.md  # 系统架构文档
├── log_manager.py                # 日志管理器
├── debug_collector.py            # 调试数据收集器
├── log_analyzer.py               # 日志分析工具
├── debug_dashboard.py            # 调试仪表板
├── debug_example.py              # 使用示例
└── README.md                     # 本文档
```

### 核心组件

#### 1. 日志管理器 (`log_manager.py`)
- `LogManager`: 统一日志管理
- `LogHandler`: 多种输出处理器
- `LogRecord`: 结构化日志记录

#### 2. 调试数据收集器 (`debug_collector.py`)
- `DebugCollectorManager`: 收集器管理
- `DataCollector`: 各种数据收集器
- `DebugData`: 调试数据模型

#### 3. 日志分析工具 (`log_analyzer.py`)
- `LogAnalysisEngine`: 分析引擎
- `LogAnalyzer`: 各种分析器
- `AnalysisResult`: 分析结果模型

#### 4. 调试仪表板 (`debug_dashboard.py`)
- `WebDashboard`: Web监控界面
- `ConsoleDashboard`: 命令行监控
- `DashboardManager`: 仪表板管理

## 🔧 配置说明

### 日志配置

```python
log_config = {
    'session_id': 'unique_session_id',  # 会话标识
    
    # 控制台输出配置
    'console': {
        'enabled': True,
        'level': 'INFO',  # TRACE, DEBUG, INFO, WARNING, ERROR, FATAL
        'format': '[{timestamp}] {level} - {logger}: {message}'
    },
    
    # 文件输出配置
    'file': {
        'enabled': True,
        'path': 'logs/app.log',
        'level': 'DEBUG',
        'max_size': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5,
        'compress': True
    },
    
    # 数据库输出配置
    'database': {
        'enabled': True,
        'path': 'logs/app.db',
        'table_name': 'debug_logs',
        'level': 'INFO'
    }
}
```

### 收集器配置

```python
from core_lib.debug import get_collector_manager

collector_manager = get_collector_manager('session_id')

# 启动自动收集
collector_manager.start_auto_collect(
    interval=5.0,  # 收集间隔（秒）
    collectors=['system_resource', 'performance']  # 启用的收集器
)

# 添加自定义数据处理器
def custom_handler(data):
    print(f"收到数据: {data.name} = {data.value}")

collector_manager.add_data_handler(custom_handler)
```

## 📊 使用示例

### 示例1: 基础日志记录

```python
from core_lib.debug import setup_logging, get_logger

# 设置日志
setup_logging({
    'session_id': 'basic_example',
    'console': {'enabled': True, 'level': 'INFO'},
    'file': {'enabled': True, 'path': 'basic.log'}
})

logger = get_logger()

# 记录不同级别的日志
logger.debug("调试信息", "module_name", debug_data="some_value")
logger.info("信息日志", "module_name", user_id=123)
logger.warning("警告信息", "module_name", warning_code="W001")
logger.error("错误信息", "module_name", error_code="E001")
```

### 示例2: 性能监控

```python
import time
from core_lib.debug import get_logger, collect_debug_data

logger = get_logger()

def monitored_function():
    start_time = time.time()
    
    # 执行一些工作
    time.sleep(1.0)
    
    execution_time = time.time() - start_time
    
    # 记录性能数据
    collect_debug_data(
        'performance_metric',
        'function_execution_time',
        execution_time,
        {
            'function_name': 'monitored_function',
            'parameters': {},
            'result': 'success'
        }
    )
    
    logger.info(
        f"函数执行完成，耗时 {execution_time:.3f}s",
        "performance",
        execution_time=execution_time
    )

monitored_function()
```

### 示例3: 错误追踪

```python
from core_lib.debug import get_logger, collect_debug_data

logger = get_logger()

def error_prone_function(data):
    try:
        # 可能出错的操作
        result = 10 / data
        return result
    except Exception as e:
        # 记录错误日志
        logger.error(
            f"函数执行失败: {e}",
            "error_handler",
            error_type=type(e).__name__,
            input_data=data,
            stack_trace=str(e)
        )
        
        # 收集错误数据
        collect_debug_data(
            'error',
            'function_error',
            str(e),
            {
                'function_name': 'error_prone_function',
                'error_type': type(e).__name__,
                'input_data': data
            }
        )
        
        raise

# 测试错误情况
try:
    error_prone_function(0)  # 除零错误
except:
    pass
```

### 示例4: 仿真监控

```python
from core_lib.debug import (
    setup_logging, get_logger, collect_debug_data,
    start_web_dashboard, get_collector_manager
)

# 设置完整的调试环境
setup_logging({
    'session_id': 'simulation_session',
    'console': {'enabled': True, 'level': 'INFO'},
    'file': {'enabled': True, 'path': 'simulation.log'},
    'database': {'enabled': True, 'path': 'simulation.db'}
})

# 启动数据收集
collector_manager = get_collector_manager('simulation_session')
collector_manager.start_auto_collect(interval=2.0)

# 启动Web仪表板
url = start_web_dashboard(port=8080)
print(f"监控仪表板: {url}")

logger = get_logger()

class Simulation:
    def __init__(self, name):
        self.name = name
        self.step = 0
        logger.info(f"仿真 '{name}' 初始化", "simulation", name=name)
    
    def run_step(self):
        self.step += 1
        start_time = time.time()
        
        # 模拟计算
        result = self.step * 2.5
        time.sleep(0.1)
        
        execution_time = time.time() - start_time
        
        # 记录步骤日志
        logger.info(
            f"步骤 {self.step} 完成",
            "simulation",
            step=self.step,
            result=result,
            execution_time=execution_time
        )
        
        # 收集仿真数据
        collect_debug_data(
            'simulation_state',
            'step_result',
            result,
            {
                'simulation_name': self.name,
                'step': self.step,
                'execution_time': execution_time
            }
        )
        
        return result

# 运行仿真
sim = Simulation("水库调度仿真")
for i in range(10):
    sim.run_step()
    time.sleep(1)

# 清理资源
collector_manager.close()
```

## 🔍 日志分析

### 自动分析

```python
from core_lib.debug import get_analysis_engine

engine = get_analysis_engine()

# 分析日志文件
results = engine.analyze_file(
    'simulation.log',
    analysis_types=['pattern', 'performance', 'error', 'anomaly']
)

# 查看分析结果
for result in results:
    print(f"[{result.severity}] {result.title}")
    print(f"  {result.description}")
    print(f"  置信度: {result.confidence:.1%}")
    print()

# 生成报告
report = engine.generate_report(results)
with open('analysis_report.md', 'w', encoding='utf-8') as f:
    f.write(report)
```

### 数据库分析

```python
# 分析数据库日志
db_results = engine.analyze_database(
    'simulation.db',
    'debug_logs',
    analysis_types=['trend', 'error']
)

print(f"发现 {len(db_results)} 个趋势和问题")
```

## 🖥️ 仪表板使用

### Web仪表板

```python
from core_lib.debug import get_dashboard_manager

dashboard = get_dashboard_manager()

# 启动Web仪表板
url = dashboard.start_web_dashboard(
    port=8080,
    host='localhost',
    open_browser=True
)

print(f"Web仪表板: {url}")

# 仪表板将显示:
# - 系统概览
# - 实时日志
# - 性能图表
# - 分析结果
# - 错误统计
```

### 命令行仪表板

```python
# 启动命令行仪表板
dashboard.start_console_dashboard(update_interval=3.0)

# 命令行将显示:
# - 系统状态摘要
# - 最近日志
# - 性能指标
# - 错误统计
```

## 🛠️ 高级功能

### 自定义收集器

```python
from core_lib.debug.debug_collector import DataCollector, DebugData

class CustomCollector(DataCollector):
    def __init__(self):
        super().__init__("custom_collector")
    
    def collect(self) -> List[DebugData]:
        # 实现自定义数据收集逻辑
        data = DebugData(
            data_type='custom_metric',
            name='my_metric',
            value=get_my_metric_value(),
            metadata={'source': 'custom_collector'}
        )
        return [data]

# 注册自定义收集器
collector_manager = get_collector_manager()
collector_manager.add_collector(CustomCollector())
```

### 自定义分析器

```python
from core_lib.debug.log_analyzer import LogAnalyzer, AnalysisResult

class CustomAnalyzer(LogAnalyzer):
    def __init__(self):
        super().__init__("custom_analyzer")
    
    def analyze_logs(self, logs: List[LogRecord]) -> List[AnalysisResult]:
        # 实现自定义分析逻辑
        results = []
        
        # 分析逻辑...
        
        return results

# 注册自定义分析器
engine = get_analysis_engine()
engine.add_analyzer(CustomAnalyzer())
```

### 自定义日志处理器

```python
from core_lib.debug.log_manager import LogHandler, LogRecord

class CustomLogHandler(LogHandler):
    def __init__(self):
        super().__init__("custom_handler")
    
    def emit(self, record: LogRecord):
        # 实现自定义日志处理逻辑
        # 例如: 发送到外部系统、触发告警等
        pass

# 注册自定义处理器
from core_lib.debug import get_logger
logger = get_logger()
logger.add_handler(CustomLogHandler())
```

## 📋 最佳实践

### 1. 日志记录
- 使用合适的日志级别
- 包含足够的上下文信息
- 避免在循环中记录过多日志
- 使用结构化数据字段

```python
# 好的做法
logger.info(
    "用户登录成功",
    "auth",
    user_id=user.id,
    ip_address=request.ip,
    user_agent=request.user_agent
)

# 避免的做法
logger.info(f"用户 {user.id} 从 {request.ip} 登录成功")
```

### 2. 性能监控
- 监控关键函数的执行时间
- 收集系统资源使用情况
- 设置合理的收集间隔

```python
def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            status = 'success'
        except Exception as e:
            result = None
            status = 'error'
            raise
        finally:
            execution_time = time.time() - start_time
            collect_debug_data(
                'performance_metric',
                f'{func.__name__}_execution_time',
                execution_time,
                {
                    'function': func.__name__,
                    'status': status,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }
            )
        return result
    return wrapper
```

### 3. 错误处理
- 记录完整的错误信息
- 包含错误上下文
- 分类错误类型

```python
try:
    risky_operation()
except SpecificError as e:
    logger.error(
        "特定错误发生",
        "error_handler",
        error_type="SpecificError",
        error_message=str(e),
        operation="risky_operation",
        retry_count=retry_count
    )
except Exception as e:
    logger.fatal(
        "未预期错误",
        "error_handler",
        error_type=type(e).__name__,
        error_message=str(e),
        stack_trace=traceback.format_exc()
    )
```

### 4. 资源管理
- 及时关闭收集器和仪表板
- 设置合理的日志轮转策略
- 监控磁盘空间使用

```python
# 使用上下文管理器
from contextlib import contextmanager

@contextmanager
def debug_session(session_id):
    # 设置调试环境
    setup_logging({'session_id': session_id, ...})
    collector_manager = get_collector_manager(session_id)
    collector_manager.start_auto_collect()
    
    try:
        yield
    finally:
        # 清理资源
        collector_manager.close()
        # 其他清理工作...

# 使用
with debug_session('my_session'):
    # 执行需要调试的代码
    pass
```

## 🔧 故障排除

### 常见问题

1. **日志文件过大**
   - 检查日志轮转配置
   - 调整日志级别
   - 减少不必要的日志输出

2. **性能影响**
   - 使用异步日志写入
   - 调整收集器间隔
   - 禁用不需要的收集器

3. **Web仪表板无法访问**
   - 检查端口是否被占用
   - 确认防火墙设置
   - 查看控制台错误信息

4. **分析结果不准确**
   - 检查日志格式是否正确
   - 确认分析器配置
   - 增加日志上下文信息

### 调试技巧

```python
# 启用调试模式
setup_logging({
    'session_id': 'debug_session',
    'console': {'enabled': True, 'level': 'DEBUG'},
    'file': {'enabled': True, 'level': 'TRACE'}
})

# 查看系统状态
from core_lib.debug import get_collector_manager
collector_manager = get_collector_manager()
print(f"活跃收集器: {collector_manager.get_active_collectors()}")

# 手动触发分析
from core_lib.debug import get_analysis_engine
engine = get_analysis_engine()
results = engine.analyze_file('debug.log', ['error'])
print(f"发现 {len(results)} 个问题")
```

## 📚 API 参考

详细的API文档请参考各模块的docstring：

- `log_manager.py`: 日志管理API
- `debug_collector.py`: 数据收集API
- `log_analyzer.py`: 日志分析API
- `debug_dashboard.py`: 仪表板API

## 🤝 贡献

欢迎提交问题报告和功能请求！

## 📄 许可证

本项目采用 MIT 许可证。