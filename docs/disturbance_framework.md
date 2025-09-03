# 扰动框架使用指南

## 概述

扰动框架是CHS-SDK中用于模拟各种系统扰动的核心组件，支持物理扰动、网络扰动等多种类型的扰动模拟。该框架提供了统一的接口和高性能的实现，可以轻松集成到仿真系统中。

## 核心组件

### 1. 基础扰动类 (BaseDisturbance)

所有扰动的基类，定义了扰动的基本接口：

```python
from core_lib.disturbances.disturbance_framework import BaseDisturbance

class CustomDisturbance(BaseDisturbance):
    def apply(self, component, current_time: float):
        """应用扰动到组件"""
        pass
    
    def remove(self, component):
        """移除扰动效果"""
        pass
```

### 2. 扰动管理器 (DisturbanceManager)

管理所有扰动的生命周期：

```python
from core_lib.disturbances.disturbance_framework import DisturbanceManager

# 创建扰动管理器
manager = DisturbanceManager()

# 添加扰动
manager.add_disturbance(
    disturbance_id="inflow_disturbance_1",
    disturbance_type="inflow",
    config={
        "magnitude": 50.0,
        "component_id": "reservoir_1"
    }
)

# 激活扰动
manager.activate_disturbance(
    disturbance_id="inflow_disturbance_1",
    start_time=10.0,
    duration=30.0
)
```

### 3. 性能优化管理器

对于大规模仿真，可以使用性能优化的管理器：

```python
from core_lib.disturbances.performance_optimized_disturbance_manager import PerformanceOptimizedDisturbanceManager

# 创建优化管理器
optimized_manager = PerformanceOptimizedDisturbanceManager(
    cache_size=500,
    cleanup_interval=50
)
```

## 支持的扰动类型

### 1. 物理扰动

#### 入流扰动 (InflowDisturbance)
模拟水库、河道等的入流变化：

```python
config = {
    "magnitude": 100.0,  # 扰动幅度 (m³/s)
    "component_id": "reservoir_1",
    "disturbance_type": "step"  # 阶跃扰动
}
```

#### 传感器噪声扰动 (SensorNoiseDisturbance)
模拟传感器测量噪声：

```python
config = {
    "noise_std": 0.1,  # 噪声标准差
    "component_id": "sensor_1",
    "sensor_type": "water_level"
}
```

#### 执行器故障扰动 (ActuatorFailureDisturbance)
模拟执行器故障：

```python
config = {
    "failure_type": "stuck",  # 故障类型：stuck, drift, noise
    "component_id": "gate_1",
    "failure_value": 0.5  # 故障值
}
```

### 2. 网络扰动

#### 网络延迟扰动 (NetworkDelayDisturbance)
模拟网络通信延迟：

```python
from core_lib.disturbances.network_disturbance import NetworkDelayDisturbance

config = {
    "base_delay": 0.1,  # 基础延迟 (秒)
    "jitter": 0.05,     # 延迟抖动
    "distribution": "normal"  # 延迟分布类型
}
```

#### 丢包扰动 (PacketLossDisturbance)
模拟网络丢包：

```python
config = {
    "loss_rate": 0.05,  # 丢包率 (5%)
    "burst_length": 3   # 突发丢包长度
}
```

## 集成到仿真系统

### 1. 在EnhancedSimulationHarness中使用

```python
from core_lib.core_engine.testing.enhanced_simulation_harness import EnhancedSimulationHarness

# 创建仿真框架
harness = EnhancedSimulationHarness(
    components=[reservoir, gate],
    agents=[control_agent],
    config={
        'use_optimized_managers': True  # 启用性能优化
    }
)

# 添加物理扰动
harness.add_disturbance(
    disturbance_id="reservoir_inflow",
    disturbance_type="inflow",
    config={
        "magnitude": 75.0,
        "component_id": "reservoir_1"
    }
)

# 添加网络扰动
harness.activate_network_disturbance(
    disturbance_id="comm_delay",
    start_time=20.0,
    duration=60.0
)

# 运行仿真
harness.run_simulation(simulation_time=100.0, dt=0.1)
```

### 2. 自定义扰动类型

```python
from core_lib.disturbances.disturbance_framework import BaseDisturbance
import numpy as np

class TemperatureDisturbance(BaseDisturbance):
    """温度扰动示例"""
    
    def __init__(self, disturbance_id: str, config: dict):
        super().__init__(disturbance_id, config)
        self.temperature_change = config.get('temperature_change', 5.0)
        self.component_id = config.get('component_id')
    
    def apply(self, component, current_time: float):
        """应用温度扰动"""
        if hasattr(component, 'temperature'):
            component.temperature += self.temperature_change
            self.logger.info(f"应用温度扰动: +{self.temperature_change}°C")
    
    def remove(self, component):
        """移除温度扰动"""
        if hasattr(component, 'temperature'):
            component.temperature -= self.temperature_change
            self.logger.info(f"移除温度扰动: -{self.temperature_change}°C")

# 注册自定义扰动类型
from core_lib.disturbances.disturbance_framework import register_disturbance_type
register_disturbance_type("temperature", TemperatureDisturbance)
```

## 性能优化特性

### 1. 缓存机制
- 组件缓存：缓存频繁访问的组件引用
- 时间窗口缓存：缓存时间相关的计算结果

### 2. 批处理
- 批量更新扰动状态
- 减少单次操作开销

### 3. 内存管理
- 自动清理过期缓存
- 限制历史记录大小
- 定期内存优化

### 4. 性能监控

```python
# 获取性能报告
report = manager.get_performance_report()
print(f"缓存命中率: {report['cache_status']['cache_hit_rate']}")
print(f"内存优化次数: {report['performance_stats']['memory_optimizations']}")
```

## 最佳实践

### 1. 扰动配置
- 使用合理的扰动幅度，避免系统不稳定
- 根据实际系统特性设置扰动参数
- 考虑扰动之间的相互影响

### 2. 性能优化
- 大规模仿真时启用性能优化管理器
- 根据系统规模调整缓存大小
- 定期监控内存使用情况

### 3. 调试和测试
- 使用扰动历史记录分析系统行为
- 逐步增加扰动复杂度进行测试
- 验证扰动移除后系统能否恢复正常

## 故障排除

### 常见问题

1. **扰动未生效**
   - 检查扰动是否正确激活
   - 验证组件ID是否正确
   - 确认扰动时间窗口设置

2. **性能问题**
   - 启用性能优化管理器
   - 调整缓存大小和清理间隔
   - 监控内存使用情况

3. **网络扰动异常**
   - 检查网络扰动管理器配置
   - 验证消息总线连接
   - 确认延迟和丢包参数合理

### 调试工具

```python
# 启用详细日志
import logging
logging.getLogger('disturbance_framework').setLevel(logging.DEBUG)

# 获取扰动状态
status = harness.get_disturbance_status()
print(f"活跃扰动: {status['active_disturbances']}")
print(f"扰动历史: {status['history']}")
```

## API参考

详细的API文档请参考各模块的docstring和类型注解。主要接口包括：

- `BaseDisturbance`: 扰动基类
- `DisturbanceManager`: 标准扰动管理器
- `PerformanceOptimizedDisturbanceManager`: 性能优化管理器
- `NetworkDisturbanceManager`: 网络扰动管理器
- `EnhancedSimulationHarness`: 增强仿真框架

更多示例和详细用法请参考 `examples/` 目录下的示例代码。