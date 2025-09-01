# 示例重构策略

## 目标
基于通用工具库重构所有examples和mission目录下的示例，提供配置文件和硬编码两种程序入口方式。

## 发现的示例目录

### Examples目录（10个主要目录）
1. `agent_based/` - 基于智能体的示例
2. `canal_model/` - 渠道模型示例
3. `demo/` - 演示示例
4. `identification/` - 识别相关示例
5. `llm_integration/` - LLM集成示例
6. `non_agent_based/` - 非智能体示例
7. `notebooks/` - Jupyter笔记本示例
8. `watertank/` - 水箱仿真示例（已有配置文件驱动）
9. `watertank_refactored/` - 重构后的水箱示例

### Mission目录（5个示例目录）
1. `example_1/` - 物理模型示例
2. `example_2/` - 第二个示例
3. `example_3/` - 第三个示例
4. `example_5/` - 第五个示例
5. `scenarios/` - 场景示例

## 重构策略

### 1. 通用工具库集成
每个重构后的示例都将集成以下通用工具：
- **日志管理器** (`core_lib.debug.log_manager`)
- **调试数据收集器** (`core_lib.debug.debug_collector`)
- **性能监控器** (`core_lib.debug.performance_monitor`)
- **日志分析器** (`core_lib.debug.log_analyzer`)

### 2. 双入口方式设计

#### 方式一：配置文件驱动
- 创建 `config.yml` 配置文件
- 包含仿真参数、组件配置、调试设置
- 主程序 `run_with_config.py` 读取配置文件

#### 方式二：硬编码方式
- 主程序 `run_hardcoded.py` 直接在代码中定义参数
- 适合快速测试和教学演示
- 保持代码简洁易懂

### 3. 标准化文件结构
每个示例目录将包含：
```
example_name/
├── config.yml              # 配置文件
├── run_with_config.py      # 配置文件驱动入口
├── run_hardcoded.py        # 硬编码入口
├── README.md               # 说明文档
├── requirements.txt        # 依赖（如有特殊需求）
└── data/                   # 数据文件（如需要）
    └── ...
```

### 4. 通用调试功能集成

#### 日志配置
```python
from core_lib.debug.log_manager import get_log_manager, setup_logging

# 设置日志
setup_logging(level='INFO', log_file=f'logs/{example_name}.log')
logger = get_log_manager()
```

#### 性能监控
```python
from core_lib.debug.performance_monitor import PerformanceMonitor

perf_monitor = PerformanceMonitor()
with perf_monitor.measure('simulation_step'):
    # 仿真步骤代码
    pass
```

#### 调试数据收集
```python
from core_lib.debug.debug_collector import collect_debug_data

# 收集调试数据
collect_debug_data(
    data_type='simulation_state',
    data={'water_level': level, 'flow_rate': flow},
    timestamp=datetime.utcnow(),
    source=f'{example_name}_simulation'
)
```

### 5. 配置文件模板

#### 基础配置模板
```yaml
# 仿真配置
simulation:
  duration: 100.0
  time_step: 1.0
  output_interval: 10.0

# 调试配置
debug:
  log_level: INFO
  log_file: logs/simulation.log
  enable_performance_monitoring: true
  enable_data_collection: true
  data_collection_interval: 5.0

# 组件配置
components:
  # 具体组件配置根据示例而定

# 输出配置
output:
  save_results: true
  output_directory: results/
  plot_results: true
```

### 6. 实施步骤
1. 为每个示例创建标准化目录结构
2. 分析原有代码，提取核心仿真逻辑
3. 集成通用工具库
4. 创建配置文件和双入口程序
5. 测试功能完整性
6. 更新文档

### 7. 质量保证
- 确保重构后的示例功能与原版一致
- 验证调试工具正常工作
- 检查配置文件和硬编码两种方式都能正常运行
- 确保日志和性能数据正确收集

## 预期收益
1. **统一的调试体验** - 所有示例都有一致的日志和调试功能
2. **灵活的使用方式** - 支持配置文件和硬编码两种方式
3. **更好的可维护性** - 标准化的结构和通用工具
4. **增强的可观测性** - 内置性能监控和数据收集
5. **改进的用户体验** - 清晰的文档和一致的接口