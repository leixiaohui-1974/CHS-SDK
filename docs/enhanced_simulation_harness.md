# 增强仿真框架使用指南

## 概述

EnhancedSimulationHarness 是CHS-SDK中的核心仿真引擎，提供了完整的仿真环境管理功能。它集成了扰动框架、消息总线、智能体管理等多个组件，支持复杂的多智能体仿真场景。

## 核心特性

### 1. 统一仿真管理
- 物理模型和智能体的统一管理
- 自动化的仿真循环控制
- 灵活的时间步进机制

### 2. 扰动集成
- 内置扰动框架支持
- 物理扰动和网络扰动统一管理
- 性能优化的扰动处理

### 3. 消息总线集成
- 高性能消息传递
- 智能体间通信支持
- 事件驱动的仿真控制

### 4. 数据记录和分析
- 自动化数据收集
- 实时状态监控
- 历史数据回放

## 基本使用

### 1. 创建仿真框架

```python
from core_lib.core_engine.testing.enhanced_simulation_harness import EnhancedSimulationHarness
from core_lib.hydro_nodes.reservoir import Reservoir
from core_lib.hydro_nodes.gate import Gate
from core_lib.local_agents.digital_twin_agent import DigitalTwinAgent

# 创建物理组件
reservoir = Reservoir(
    name="main_reservoir",
    initial_state={"water_level": 10.0},
    parameters={"surface_area": 1000.0}
)

gate = Gate(
    name="outlet_gate",
    initial_state={"opening": 0.5},
    parameters={"max_flow": 100.0}
)

# 创建智能体
control_agent = DigitalTwinAgent(
    agent_id="reservoir_controller",
    controlled_component=reservoir
)

# 创建仿真框架
harness = EnhancedSimulationHarness(
    components=[reservoir, gate],
    agents=[control_agent],
    config={
        'dt': 0.1,
        'use_optimized_managers': True,
        'enable_logging': True,
        'log_level': 'INFO'
    }
)
```

### 2. 运行仿真

```python
# 基本仿真运行
harness.run_simulation(
    simulation_time=100.0,
    dt=0.1
)

# 多智能体仿真
harness.run_mas_simulation(
    simulation_time=200.0,
    dt=0.1,
    max_iterations=1000
)

# 手动步进仿真
for t in range(0, 1000):
    current_time = t * 0.1
    harness.step()
    
    # 自定义逻辑
    if current_time > 50.0:
        harness.add_disturbance(
            "emergency_inflow",
            "inflow",
            {"magnitude": 150.0, "component_id": "main_reservoir"}
        )
```

### 3. 添加扰动

```python
# 添加物理扰动
harness.add_disturbance(
    disturbance_id="inflow_variation",
    disturbance_type="inflow",
    config={
        "magnitude": 75.0,
        "component_id": "main_reservoir",
        "pattern": "sinusoidal",
        "frequency": 0.1
    }
)

# 激活扰动
harness.activate_disturbance(
    disturbance_id="inflow_variation",
    start_time=20.0,
    duration=60.0
)

# 添加网络扰动
harness.activate_network_disturbance(
    disturbance_id="comm_delay",
    start_time=30.0,
    duration=40.0
)

# 添加传感器噪声
harness.add_disturbance(
    disturbance_id="level_sensor_noise",
    disturbance_type="sensor_noise",
    config={
        "noise_std": 0.1,
        "component_id": "main_reservoir",
        "sensor_type": "water_level"
    }
)
```

## 高级功能

### 1. 自定义仿真循环

```python
class CustomSimulationHarness(EnhancedSimulationHarness):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_data = []
    
    def step(self):
        # 执行标准步骤
        super().step()
        
        # 自定义逻辑
        self.collect_custom_data()
        self.check_emergency_conditions()
    
    def collect_custom_data(self):
        # 收集自定义数据
        data = {
            'timestamp': self.current_time,
            'total_flow': sum(c.get_outflow() for c in self.components if hasattr(c, 'get_outflow')),
            'energy_consumption': self.calculate_energy_consumption()
        }
        self.custom_data.append(data)
    
    def check_emergency_conditions(self):
        # 检查紧急情况
        for component in self.components:
            if hasattr(component, 'water_level') and component.water_level > 15.0:
                self.trigger_emergency_response(component)
```

### 2. 事件驱动仿真

```python
# 注册事件处理器
@harness.event_handler('water_level_high')
def handle_high_water_level(event_data):
    component_id = event_data['component_id']
    level = event_data['water_level']
    print(f"高水位警告: {component_id} 水位达到 {level}m")
    
    # 自动响应
    harness.add_disturbance(
        f"emergency_release_{component_id}",
        "actuator_override",
        {"component_id": component_id, "action": "open_gates"}
    )

# 触发事件
harness.trigger_event('water_level_high', {
    'component_id': 'main_reservoir',
    'water_level': 16.5
})

# 条件事件
harness.add_condition_monitor(
    condition=lambda: reservoir.water_level > 15.0,
    event_type='water_level_critical',
    event_data={'component': reservoir.name}
)
```

### 3. 数据收集和分析

```python
# 配置数据收集
harness.configure_data_collection(
    components=['main_reservoir', 'outlet_gate'],
    metrics=['water_level', 'flow_rate', 'gate_opening'],
    sampling_interval=1.0
)

# 运行仿真并收集数据
results = harness.run_simulation_with_data_collection(
    simulation_time=100.0,
    dt=0.1
)

# 分析结果
import matplotlib.pyplot as plt

time_series = results['time']
water_levels = results['main_reservoir']['water_level']

plt.figure(figsize=(10, 6))
plt.plot(time_series, water_levels)
plt.xlabel('时间 (s)')
plt.ylabel('水位 (m)')
plt.title('水库水位变化')
plt.grid(True)
plt.show()

# 导出数据
harness.export_data(
    filename='simulation_results.csv',
    format='csv',
    include_metadata=True
)
```

### 4. 并行仿真

```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

def run_scenario(scenario_config):
    """运行单个仿真场景"""
    harness = EnhancedSimulationHarness(**scenario_config)
    results = harness.run_simulation(simulation_time=100.0)
    return results

# 定义多个场景
scenarios = [
    {
        'components': [reservoir1, gate1],
        'agents': [agent1],
        'disturbances': [{'type': 'inflow', 'magnitude': 50}]
    },
    {
        'components': [reservoir2, gate2],
        'agents': [agent2],
        'disturbances': [{'type': 'inflow', 'magnitude': 100}]
    },
    # 更多场景...
]

# 并行运行
with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
    results = list(executor.map(run_scenario, scenarios))

# 分析所有结果
for i, result in enumerate(results):
    print(f"场景 {i+1} 结果: {result['summary']}")
```

## 性能优化

### 1. 启用优化管理器

```python
# 启用性能优化
harness = EnhancedSimulationHarness(
    components=components,
    agents=agents,
    config={
        'use_optimized_managers': True,
        'disturbance_cache_size': 1000,
        'network_batch_size': 50,
        'enable_parallel_processing': True
    }
)
```

### 2. 内存管理

```python
# 配置内存管理
harness.configure_memory_management(
    max_history_size=10000,
    cleanup_interval=100,
    enable_compression=True
)

# 定期清理
harness.schedule_cleanup(
    interval=300,  # 5分钟
    cleanup_types=['history', 'cache', 'logs']
)
```

### 3. 性能监控

```python
# 启用性能监控
harness.enable_performance_monitoring(
    metrics=['step_time', 'memory_usage', 'cpu_usage'],
    reporting_interval=10.0
)

# 获取性能报告
perf_report = harness.get_performance_report()
print(f"平均步骤时间: {perf_report['avg_step_time']:.3f}ms")
print(f"内存使用: {perf_report['memory_usage']:.1f}MB")
print(f"缓存命中率: {perf_report['cache_hit_rate']:.1f}%")
```

## 集成示例

### 1. 水库控制系统仿真

```python
from core_lib.hydro_nodes.reservoir import Reservoir
from core_lib.hydro_nodes.gate import Gate
from core_lib.local_agents.digital_twin_agent import DigitalTwinAgent
from core_lib.local_agents.pid_control_agent import PIDControlAgent

# 创建水库系统
reservoir = Reservoir(
    name="main_reservoir",
    initial_state={"water_level": 10.0},
    parameters={"surface_area": 2000.0, "max_capacity": 30000.0}
)

inlet_gate = Gate(
    name="inlet_gate",
    initial_state={"opening": 0.3},
    parameters={"max_flow": 200.0}
)

outlet_gate = Gate(
    name="outlet_gate",
    initial_state={"opening": 0.5},
    parameters={"max_flow": 150.0}
)

# 创建控制智能体
level_controller = PIDControlAgent(
    agent_id="level_controller",
    controlled_component=reservoir,
    control_variable="water_level",
    setpoint=12.0,
    kp=1.0, ki=0.1, kd=0.05
)

flow_controller = PIDControlAgent(
    agent_id="flow_controller",
    controlled_component=outlet_gate,
    control_variable="flow_rate",
    setpoint=80.0,
    kp=0.5, ki=0.05, kd=0.02
)

# 创建仿真框架
harness = EnhancedSimulationHarness(
    components=[reservoir, inlet_gate, outlet_gate],
    agents=[level_controller, flow_controller],
    config={
        'dt': 0.1,
        'use_optimized_managers': True,
        'enable_logging': True
    }
)

# 添加扰动场景
harness.add_disturbance(
    "seasonal_inflow",
    "inflow",
    {
        "magnitude": 100.0,
        "component_id": "main_reservoir",
        "pattern": "seasonal",
        "period": 365 * 24 * 3600  # 一年周期
    }
)

harness.add_disturbance(
    "equipment_failure",
    "actuator_failure",
    {
        "component_id": "inlet_gate",
        "failure_type": "stuck",
        "failure_value": 0.1
    }
)

# 运行仿真
harness.activate_disturbance("seasonal_inflow", 0.0, 3600.0)
harness.activate_disturbance("equipment_failure", 1800.0, 600.0)

results = harness.run_mas_simulation(
    simulation_time=3600.0,  # 1小时仿真
    dt=0.1
)

# 分析结果
print(f"仿真完成，处理了 {len(results['history'])} 个时间步")
print(f"最终水位: {reservoir.water_level:.2f}m")
print(f"平均流量: {results['avg_flow_rate']:.2f}m³/s")
```

### 2. 多智能体协调控制

```python
from core_lib.central_agents.coordination_agent import CoordinationAgent
from core_lib.local_agents.negotiation_agent import NegotiationAgent

# 创建协调智能体
coordinator = CoordinationAgent(
    agent_id="system_coordinator",
    managed_components=[reservoir, inlet_gate, outlet_gate],
    optimization_objective="minimize_cost"
)

# 创建协商智能体
negotiator1 = NegotiationAgent(
    agent_id="upstream_negotiator",
    controlled_component=inlet_gate,
    negotiation_strategy="cooperative"
)

negotiator2 = NegotiationAgent(
    agent_id="downstream_negotiator",
    controlled_component=outlet_gate,
    negotiation_strategy="competitive"
)

# 创建多智能体仿真
mas_harness = EnhancedSimulationHarness(
    components=[reservoir, inlet_gate, outlet_gate],
    agents=[coordinator, negotiator1, negotiator2],
    config={
        'enable_agent_communication': True,
        'communication_protocol': 'contract_net',
        'negotiation_timeout': 5.0
    }
)

# 设置协调规则
mas_harness.add_coordination_rule(
    rule_type="resource_allocation",
    condition=lambda: reservoir.water_level < 8.0,
    action="emergency_coordination"
)

# 运行多智能体仿真
mas_results = mas_harness.run_mas_simulation(
    simulation_time=7200.0,  # 2小时
    dt=0.1,
    enable_negotiation=True
)
```

## 配置参考

### 完整配置示例

```python
config = {
    # 基础仿真配置
    'dt': 0.1,
    'max_simulation_time': 86400.0,
    'time_unit': 'seconds',
    
    # 性能优化
    'use_optimized_managers': True,
    'disturbance_cache_size': 1000,
    'network_batch_size': 50,
    'enable_parallel_processing': True,
    
    # 数据管理
    'enable_logging': True,
    'log_level': 'INFO',
    'max_history_size': 100000,
    'data_compression': True,
    
    # 扰动配置
    'enable_disturbances': True,
    'disturbance_update_interval': 0.1,
    'network_disturbance_enabled': True,
    
    # 智能体配置
    'enable_agent_communication': True,
    'communication_protocol': 'message_passing',
    'agent_update_order': 'priority',
    
    # 监控配置
    'enable_performance_monitoring': True,
    'monitoring_interval': 10.0,
    'alert_thresholds': {
        'memory_usage': 80,  # 80% 内存使用率
        'step_time': 100     # 100ms 步骤时间
    }
}

harness = EnhancedSimulationHarness(
    components=components,
    agents=agents,
    config=config
)
```

## 最佳实践

### 1. 仿真设计
- 合理设置时间步长，平衡精度和性能
- 使用层次化的智能体架构
- 实现适当的错误处理和恢复机制

### 2. 性能优化
- 启用优化管理器处理大规模仿真
- 使用批量处理减少通信开销
- 定期清理历史数据防止内存泄漏

### 3. 数据管理
- 配置合适的数据采样频率
- 使用压缩减少存储空间
- 实现增量数据保存

### 4. 调试和测试
- 使用单步调试验证仿真逻辑
- 实现单元测试覆盖关键功能
- 监控性能指标识别瓶颈

## 故障排除

### 常见问题

1. **仿真运行缓慢**
   - 启用性能优化管理器
   - 调整时间步长
   - 减少数据记录频率

2. **内存使用过高**
   - 启用数据压缩
   - 限制历史记录大小
   - 定期清理缓存

3. **智能体通信异常**
   - 检查消息总线配置
   - 验证智能体注册状态
   - 监控消息队列状态

4. **扰动效果不明显**
   - 验证扰动参数设置
   - 检查扰动激活时间
   - 确认组件ID正确

更多详细信息和示例请参考源代码文档和examples目录。