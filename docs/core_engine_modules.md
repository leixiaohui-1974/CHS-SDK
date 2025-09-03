# 核心引擎模块使用指南

## 概述

核心引擎模块是CHS-SDK的基础架构组件，提供了仿真系统的核心功能。这些模块包括增强消息总线、扰动框架、增强仿真框架等，为构建复杂的水利系统仿真提供了强大的基础设施。

## 模块架构

```
core_lib/
├── core/
│   ├── enhanced_message_bus.py      # 增强消息总线
│   └── ...
├── core_engine/
│   ├── testing/
│   │   └── enhanced_simulation_harness.py  # 增强仿真框架
│   └── ...
├── disturbances/
│   ├── base_disturbance.py          # 基础扰动类
│   ├── disturbance_manager.py       # 扰动管理器
│   ├── network_disturbance.py       # 网络扰动
│   ├── performance_optimized_disturbance_manager.py  # 性能优化管理器
│   └── performance_optimized_network_manager.py      # 网络扰动优化管理器
└── ...
```

## 核心模块详解

### 1. 增强消息总线 (EnhancedMessageBus)

增强消息总线提供了高性能的异步消息传递机制，支持智能体间通信、事件驱动处理和消息持久化。

#### 主要特性
- **异步处理**: 支持非阻塞消息传递
- **消息持久化**: 可选的消息存储和恢复
- **优先级队列**: 支持消息优先级处理
- **消息过滤**: 基于内容和类型的消息过滤
- **性能优化**: 连接池和批量处理

#### 使用示例
```python
from core_lib.core.enhanced_message_bus import EnhancedMessageBus

# 创建消息总线
bus = EnhancedMessageBus(
    enable_persistence=True,
    max_queue_size=10000,
    enable_priority=True
)

# 发送消息
bus.send_message(
    topic="water_level_update",
    message={
        "component_id": "reservoir_1",
        "water_level": 12.5,
        "timestamp": time.time()
    },
    priority=1
)

# 订阅消息
def handle_water_level(message):
    print(f"水位更新: {message['water_level']}m")

bus.subscribe("water_level_update", handle_water_level)
```

### 2. 扰动框架 (Disturbance Framework)

扰动框架提供了统一的扰动管理机制，支持物理扰动、网络扰动和传感器噪声等多种扰动类型。

#### 核心组件
- **BaseDisturbance**: 扰动基类
- **DisturbanceManager**: 标准扰动管理器
- **PerformanceOptimizedDisturbanceManager**: 性能优化管理器
- **NetworkDisturbanceManager**: 网络扰动专用管理器

#### 扰动类型
```python
# 物理扰动
from core_lib.disturbances.disturbance_manager import DisturbanceManager

manager = DisturbanceManager()

# 添加流量扰动
manager.add_disturbance(
    "inflow_spike",
    "inflow",
    {
        "magnitude": 150.0,
        "component_id": "reservoir_1",
        "pattern": "step",
        "duration": 300.0
    }
)

# 添加传感器噪声
manager.add_disturbance(
    "sensor_noise",
    "sensor_noise",
    {
        "noise_std": 0.1,
        "component_id": "level_sensor_1",
        "noise_type": "gaussian"
    }
)

# 网络扰动
from core_lib.disturbances.network_disturbance import NetworkDelayDisturbance

delay_disturbance = NetworkDelayDisturbance(
    disturbance_id="comm_delay",
    config={
        "base_delay": 0.05,
        "jitter": 0.02,
        "affected_agents": ["agent_1", "agent_2"]
    }
)
```

### 3. 增强仿真框架 (EnhancedSimulationHarness)

增强仿真框架是核心仿真引擎，集成了所有核心模块，提供完整的仿真环境。

#### 核心功能
- **统一组件管理**: 物理模型和智能体的统一管理
- **扰动集成**: 内置扰动框架支持
- **消息总线集成**: 高性能消息传递
- **性能优化**: 多种性能优化策略
- **数据收集**: 自动化数据记录和分析

#### 集成示例
```python
from core_lib.core_engine.testing.enhanced_simulation_harness import EnhancedSimulationHarness
from core_lib.hydro_nodes.reservoir import Reservoir
from core_lib.local_agents.digital_twin_agent import DigitalTwinAgent

# 创建组件
reservoir = Reservoir(
    name="main_reservoir",
    initial_state={"water_level": 10.0},
    parameters={"surface_area": 1000.0}
)

# 创建智能体
agent = DigitalTwinAgent(
    agent_id="controller",
    controlled_component=reservoir
)

# 创建仿真框架
harness = EnhancedSimulationHarness(
    components=[reservoir],
    agents=[agent],
    config={
        'use_optimized_managers': True,
        'enable_logging': True,
        'dt': 0.1
    }
)

# 运行仿真
harness.run_simulation(simulation_time=100.0)
```

## 性能优化模块

### 1. 性能优化扰动管理器

```python
from core_lib.disturbances.performance_optimized_disturbance_manager import PerformanceOptimizedDisturbanceManager

# 创建优化管理器
optimized_manager = PerformanceOptimizedDisturbanceManager(
    cache_size=1000,
    batch_size=50,
    enable_async=True
)

# 批量添加扰动
disturbances = [
    ("dist_1", "inflow", {"magnitude": 100}),
    ("dist_2", "outflow", {"magnitude": 80}),
    ("dist_3", "sensor_noise", {"noise_std": 0.1})
]

optimized_manager.add_disturbances_batch(disturbances)

# 性能监控
perf_stats = optimized_manager.get_performance_stats()
print(f"缓存命中率: {perf_stats['cache_hit_rate']:.2f}%")
print(f"平均处理时间: {perf_stats['avg_processing_time']:.3f}ms")
```

### 2. 网络扰动优化管理器

```python
from core_lib.disturbances.performance_optimized_network_manager import PerformanceOptimizedNetworkDisturbanceManager

# 创建网络扰动管理器
network_manager = PerformanceOptimizedNetworkDisturbanceManager(
    batch_size=100,
    enable_compression=True
)

# 批量处理网络扰动
network_events = [
    {"type": "delay", "agent_id": "agent_1", "delay": 0.05},
    {"type": "packet_loss", "agent_id": "agent_2", "loss_rate": 0.01},
    {"type": "bandwidth_limit", "agent_id": "agent_3", "bandwidth": 1000}
]

network_manager.process_network_events_batch(network_events)
```

## 模块集成模式

### 1. 标准集成模式

```python
class StandardSimulationSetup:
    def __init__(self):
        # 创建消息总线
        self.message_bus = EnhancedMessageBus(
            enable_persistence=False,
            max_queue_size=1000
        )
        
        # 创建扰动管理器
        self.disturbance_manager = DisturbanceManager()
        
        # 创建仿真框架
        self.harness = EnhancedSimulationHarness(
            components=[],
            agents=[],
            message_bus=self.message_bus,
            disturbance_manager=self.disturbance_manager
        )
    
    def setup_simulation(self, components, agents):
        # 添加组件和智能体
        for component in components:
            self.harness.add_component(component)
        
        for agent in agents:
            self.harness.add_agent(agent)
            # 注册到消息总线
            self.message_bus.register_agent(agent)
    
    def run(self, simulation_time):
        return self.harness.run_simulation(simulation_time)
```

### 2. 高性能集成模式

```python
class HighPerformanceSimulationSetup:
    def __init__(self):
        # 使用优化组件
        self.message_bus = EnhancedMessageBus(
            enable_persistence=True,
            max_queue_size=10000,
            enable_batching=True,
            batch_size=100
        )
        
        self.disturbance_manager = PerformanceOptimizedDisturbanceManager(
            cache_size=5000,
            batch_size=200,
            enable_async=True
        )
        
        self.network_manager = PerformanceOptimizedNetworkDisturbanceManager(
            batch_size=500,
            enable_compression=True
        )
        
        self.harness = EnhancedSimulationHarness(
            components=[],
            agents=[],
            config={
                'use_optimized_managers': True,
                'enable_parallel_processing': True,
                'memory_optimization': True
            }
        )
    
    def setup_large_scale_simulation(self, components, agents):
        # 批量添加组件
        self.harness.add_components_batch(components)
        self.harness.add_agents_batch(agents)
        
        # 配置性能监控
        self.harness.enable_performance_monitoring(
            metrics=['step_time', 'memory_usage', 'throughput'],
            reporting_interval=10.0
        )
```

### 3. 分布式集成模式

```python
class DistributedSimulationSetup:
    def __init__(self, node_id, cluster_config):
        self.node_id = node_id
        
        # 分布式消息总线
        self.message_bus = EnhancedMessageBus(
            enable_persistence=True,
            distributed_mode=True,
            cluster_config=cluster_config
        )
        
        # 分布式扰动管理
        self.disturbance_manager = PerformanceOptimizedDisturbanceManager(
            distributed_mode=True,
            node_id=node_id
        )
        
        self.harness = EnhancedSimulationHarness(
            components=[],
            agents=[],
            config={
                'distributed_mode': True,
                'node_id': node_id,
                'synchronization_interval': 1.0
            }
        )
    
    def setup_distributed_simulation(self, local_components, local_agents):
        # 只添加本地组件
        self.harness.add_components_batch(local_components)
        self.harness.add_agents_batch(local_agents)
        
        # 配置分布式同步
        self.harness.configure_distributed_sync(
            sync_protocol='consensus',
            sync_interval=1.0
        )
```

## 配置管理

### 配置文件示例

```yaml
# simulation_config.yaml
simulation:
  dt: 0.1
  max_time: 3600.0
  time_unit: "seconds"

message_bus:
  enable_persistence: true
  max_queue_size: 10000
  enable_priority: true
  batch_size: 100
  compression: true

disturbance_manager:
  type: "performance_optimized"
  cache_size: 1000
  batch_size: 50
  enable_async: true
  cleanup_interval: 300

network_disturbances:
  enable: true
  batch_size: 200
  compression: true
  max_delay: 1.0

performance:
  enable_monitoring: true
  monitoring_interval: 10.0
  memory_limit: 2048  # MB
  cpu_limit: 80       # %

logging:
  level: "INFO"
  enable_file_logging: true
  log_rotation: true
  max_log_size: 100   # MB
```

### 配置加载

```python
import yaml
from core_lib.core_engine.testing.enhanced_simulation_harness import EnhancedSimulationHarness

def load_simulation_config(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 创建配置化的仿真环境
    harness = EnhancedSimulationHarness(
        components=[],
        agents=[],
        config=config
    )
    
    return harness, config

# 使用配置文件
harness, config = load_simulation_config('simulation_config.yaml')
```

## 监控和调试

### 1. 性能监控

```python
# 启用详细监控
harness.enable_detailed_monitoring(
    components=['reservoir_1', 'gate_1'],
    agents=['controller_1', 'optimizer_1'],
    metrics=[
        'processing_time',
        'memory_usage',
        'message_throughput',
        'disturbance_impact'
    ]
)

# 获取监控报告
monitoring_report = harness.get_monitoring_report()
print(f"系统性能报告:")
print(f"- 平均步骤时间: {monitoring_report['avg_step_time']:.3f}ms")
print(f"- 内存使用: {monitoring_report['memory_usage']:.1f}MB")
print(f"- 消息吞吐量: {monitoring_report['message_throughput']:.0f} msg/s")
print(f"- 扰动处理延迟: {monitoring_report['disturbance_latency']:.3f}ms")
```

### 2. 调试工具

```python
# 启用调试模式
harness.enable_debug_mode(
    log_level='DEBUG',
    trace_messages=True,
    trace_disturbances=True,
    save_state_snapshots=True
)

# 单步调试
harness.enable_step_by_step_mode()
for step in range(100):
    harness.step()
    
    # 检查状态
    state = harness.get_current_state()
    if state['reservoir_1']['water_level'] > 15.0:
        print(f"警告: 水位过高 {state['reservoir_1']['water_level']:.2f}m")
        harness.pause_simulation()
        break

# 状态回放
harness.save_state_snapshot('critical_state')
# ... 继续仿真 ...
harness.restore_state_snapshot('critical_state')
```

### 3. 错误处理

```python
try:
    harness.run_simulation(simulation_time=3600.0)
except SimulationError as e:
    print(f"仿真错误: {e}")
    
    # 获取错误详情
    error_details = harness.get_last_error_details()
    print(f"错误组件: {error_details['component']}")
    print(f"错误时间: {error_details['timestamp']}")
    print(f"错误堆栈: {error_details['traceback']}")
    
    # 尝试恢复
    if error_details['recoverable']:
        harness.recover_from_error()
        harness.resume_simulation()
except PerformanceError as e:
    print(f"性能问题: {e}")
    
    # 自动优化
    harness.auto_optimize_performance()
    harness.restart_simulation()
```

## 扩展开发

### 1. 自定义扰动类型

```python
from core_lib.disturbances.base_disturbance import BaseDisturbance

class CustomWeatherDisturbance(BaseDisturbance):
    def __init__(self, disturbance_id, config):
        super().__init__(disturbance_id, "weather", config)
        self.temperature = config.get('temperature', 20.0)
        self.humidity = config.get('humidity', 0.5)
        self.wind_speed = config.get('wind_speed', 0.0)
    
    def apply(self, component, dt):
        # 实现天气扰动逻辑
        if hasattr(component, 'evaporation_rate'):
            # 温度影响蒸发
            temp_factor = 1.0 + (self.temperature - 20.0) * 0.02
            component.evaporation_rate *= temp_factor
            
            # 湿度影响蒸发
            humidity_factor = 1.0 - self.humidity * 0.3
            component.evaporation_rate *= humidity_factor
        
        return {
            'temperature_effect': temp_factor,
            'humidity_effect': humidity_factor
        }

# 注册自定义扰动
from core_lib.disturbances.disturbance_factory import register_disturbance_type
register_disturbance_type('weather', CustomWeatherDisturbance)
```

### 2. 自定义消息处理器

```python
from core_lib.core.enhanced_message_bus import MessageHandler

class CustomMessageHandler(MessageHandler):
    def __init__(self):
        super().__init__()
        self.processed_count = 0
    
    def handle_message(self, topic, message, metadata):
        # 自定义消息处理逻辑
        if topic == 'emergency_alert':
            self.handle_emergency(message)
        elif topic == 'optimization_request':
            self.handle_optimization(message)
        
        self.processed_count += 1
        return True
    
    def handle_emergency(self, message):
        # 紧急情况处理
        component_id = message['component_id']
        alert_type = message['alert_type']
        
        # 发送响应消息
        response = {
            'response_to': message['message_id'],
            'action': 'emergency_response_initiated',
            'timestamp': time.time()
        }
        
        self.send_message('emergency_response', response)

# 注册处理器
bus.register_handler('emergency_alert', CustomMessageHandler())
```

## 最佳实践

### 1. 模块化设计
- 保持模块间的松耦合
- 使用依赖注入提高可测试性
- 实现清晰的接口定义

### 2. 性能优化
- 根据仿真规模选择合适的管理器
- 合理配置缓存和批处理参数
- 监控内存使用避免泄漏

### 3. 错误处理
- 实现完善的异常处理机制
- 提供详细的错误信息和恢复建议
- 使用日志记录关键操作

### 4. 测试策略
- 编写单元测试覆盖核心功能
- 实现集成测试验证模块协作
- 进行性能测试确保扩展性

更多详细信息请参考各模块的专门文档和API参考。