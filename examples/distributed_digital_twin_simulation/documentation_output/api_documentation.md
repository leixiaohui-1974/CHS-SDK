# API 文档

## 核心模块

### EnhancedSimulationHarness

增强版仿真框架，提供完整的仿真环境管理。

#### 类定义

```python
class EnhancedSimulationHarness:
    """增强版仿真框架"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化仿真框架
        
        Args:
            config: 仿真配置字典
                - start_time: 仿真开始时间
                - end_time: 仿真结束时间
                - dt: 时间步长
                - enable_network_disturbance: 是否启用网络扰动
        """
```

#### 主要方法

##### add_component(component_id: str, component: BaseComponent)

添加物理组件到仿真环境。

**参数:**
- `component_id`: 组件唯一标识符
- `component`: 组件实例

**示例:**
```python
reservoir = Reservoir(
    name="main_reservoir",
    initial_state={'water_level': 100.0, 'volume': 5000.0},
    parameters={'surface_area': 50.0, 'capacity': 10000.0}
)
harness.add_component("main_reservoir", reservoir)
```

##### add_agent(agent: BaseAgent)

添加智能体到仿真环境。

**参数:**
- `agent`: 智能体实例

**示例:**
```python
agent = PIDController("level_controller", config)
harness.add_agent(agent)
```

##### add_disturbance(disturbance: BaseDisturbance)

添加扰动到仿真环境。

**参数:**
- `disturbance`: 扰动实例

**示例:**
```python
disturbance = InflowDisturbance(disturbance_config)
harness.add_disturbance(disturbance)
```

##### build()

构建仿真环境，初始化所有组件和连接。

**返回:**
- 无返回值

**异常:**
- `RuntimeError`: 如果构建过程中出现错误

##### run_simulation()

运行仿真。

**返回:**
- 无返回值

**异常:**
- `RuntimeError`: 如果仿真过程中出现错误

##### get_simulation_history() -> List[Dict[str, Any]]

获取仿真历史数据。

**返回:**
- 仿真历史记录列表

##### shutdown()

关闭仿真环境，清理资源。

**返回:**
- 无返回值

### 扰动框架

#### DisturbanceConfig

扰动配置类。

```python
@dataclass
class DisturbanceConfig:
    disturbance_id: str          # 扰动唯一标识
    disturbance_type: DisturbanceType  # 扰动类型
    target_component_id: str     # 目标组件ID
    start_time: float           # 开始时间
    end_time: float             # 结束时间
    intensity: float            # 扰动强度 (0.0-1.0)
    parameters: Dict[str, Any]  # 扰动参数
```

#### DisturbanceType

扰动类型枚举。

```python
class DisturbanceType(Enum):
    INFLOW_CHANGE = "inflow_change"        # 入流变化
    SENSOR_NOISE = "sensor_noise"          # 传感器噪声
    ACTUATOR_FAILURE = "actuator_failure"  # 执行器故障
    NETWORK_DELAY = "network_delay"        # 网络延迟
    PACKET_LOSS = "packet_loss"            # 数据包丢失
```

#### InflowDisturbance

入流扰动类。

```python
class InflowDisturbance(BaseDisturbance):
    """入流扰动"""
    
    def __init__(self, config: DisturbanceConfig):
        """初始化入流扰动
        
        Args:
            config: 扰动配置
                parameters应包含:
                - target_inflow: 目标入流量
                - change_rate: 变化速率 (可选)
        """
    
    def apply_disturbance(self, component: BaseComponent, current_time: float) -> bool:
        """应用入流扰动
        
        Args:
            component: 目标组件
            current_time: 当前时间
            
        Returns:
            bool: 是否成功应用扰动
        """
```

#### SensorNoiseDisturbance

传感器噪声扰动类。

```python
class SensorNoiseDisturbance(BaseDisturbance):
    """传感器噪声扰动"""
    
    def __init__(self, config: DisturbanceConfig):
        """初始化传感器噪声扰动
        
        Args:
            config: 扰动配置
                parameters应包含:
                - noise_level: 噪声强度
                - affected_sensors: 受影响的传感器列表
                - noise_type: 噪声类型 ("gaussian", "uniform")
        """
```

#### ActuatorFailureDisturbance

执行器故障扰动类。

```python
class ActuatorFailureDisturbance(BaseDisturbance):
    """执行器故障扰动"""
    
    def __init__(self, config: DisturbanceConfig):
        """初始化执行器故障扰动
        
        Args:
            config: 扰动配置
                parameters应包含:
                - failure_type: 故障类型 ("complete", "partial", "intermittent")
                - efficiency_factor: 效率因子 (0.0-1.0)
                - target_actuator: 目标执行器名称
        """
```

### 物理组件

#### BaseComponent

物理组件基类。

```python
class BaseComponent:
    """物理组件基类"""
    
    def __init__(self, name: str, initial_state: Dict[str, Any], parameters: Dict[str, Any]):
        """初始化组件
        
        Args:
            name: 组件名称
            initial_state: 初始状态字典
            parameters: 参数字典
        """
    
    def step(self, dt: float, current_time: float) -> Dict[str, Any]:
        """仿真步骤
        
        Args:
            dt: 时间步长
            current_time: 当前时间
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        raise NotImplementedError
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.state.copy()
    
    def set_state(self, new_state: Dict[str, Any]):
        """设置状态"""
        self.state.update(new_state)
```

#### Reservoir

水库组件。

```python
class Reservoir(BaseComponent):
    """水库组件"""
    
    def __init__(self, name: str, initial_state: Dict[str, Any], parameters: Dict[str, Any]):
        """初始化水库
        
        Args:
            name: 水库名称
            initial_state: 初始状态
                - water_level: 水位 (m)
                - volume: 蓄水量 (m³)
                - inflow: 入流量 (m³/s)
                - outflow: 出流量 (m³/s)
            parameters: 参数
                - surface_area: 水面面积 (m²)
                - capacity: 库容 (m³)
                - min_level: 最低水位 (m)
                - max_level: 最高水位 (m)
        """
```

#### Gate

闸门组件。

```python
class Gate(BaseComponent):
    """闸门组件"""
    
    def __init__(self, name: str, initial_state: Dict[str, Any], parameters: Dict[str, Any]):
        """初始化闸门
        
        Args:
            name: 闸门名称
            initial_state: 初始状态
                - opening: 开度 (0.0-1.0)
                - flow_rate: 流量 (m³/s)
            parameters: 参数
                - max_flow_rate: 最大流量 (m³/s)
                - response_time: 响应时间 (s)
        """
```

### 智能体系统

#### BaseAgent

智能体基类。

```python
class BaseAgent:
    """智能体基类"""
    
    def __init__(self, name: str):
        """初始化智能体
        
        Args:
            name: 智能体名称
        """
        self.name = name
        self.message_bus = None
    
    def set_message_bus(self, message_bus):
        """设置消息总线"""
        self.message_bus = message_bus
    
    def step(self, current_time: float):
        """智能体步骤
        
        Args:
            current_time: 当前时间
        """
        raise NotImplementedError
    
    def get_name(self) -> str:
        """获取智能体名称"""
        return self.name
```

### 性能监控

#### SystemMonitor

系统性能监控器。

```python
class SystemMonitor:
    """系统性能监控器"""
    
    def __init__(self):
        """初始化监控器"""
    
    def start_monitoring(self, interval: float = 1.0):
        """开始监控
        
        Args:
            interval: 监控间隔 (秒)
        """
    
    def stop_monitoring(self):
        """停止监控"""
    
    def get_summary(self) -> Dict[str, Any]:
        """获取监控摘要
        
        Returns:
            Dict[str, Any]: 性能摘要
                - duration_seconds: 监控时长
                - cpu_usage: CPU使用情况
                - memory_usage: 内存使用情况
                - sample_count: 采样次数
        """
```

## 配置验证

### YAMLScenarioValidator

YAML配置文件验证器。

```python
class YAMLScenarioValidator:
    """YAML场景验证器"""
    
    def validate_all_files(self) -> Dict[str, Any]:
        """验证所有配置文件
        
        Returns:
            Dict[str, Any]: 验证结果
                - total_files: 总文件数
                - passed_files: 通过验证的文件数
                - failed_files: 验证失败的文件数
                - file_results: 详细的文件验证结果
        """
    
    def validate_single_file(self, file_path: str) -> Dict[str, Any]:
        """验证单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 验证结果
                - status: 验证状态 ("passed", "failed")
                - errors: 错误列表
                - warnings: 警告列表
        """
```

## 测试工具

### ComprehensiveDisturbanceTestSuite

全面扰动测试套件。

```python
class ComprehensiveDisturbanceTestSuite:
    """全面扰动测试套件"""
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试
        
        Returns:
            Dict[str, Any]: 测试结果
                - single_disturbance_tests: 单一扰动测试结果
                - combination_tests: 组合扰动测试结果
                - complex_scenario_tests: 复杂场景测试结果
                - performance_tests: 性能测试结果
        """
    
    def run_single_disturbance_tests(self) -> Dict[str, Any]:
        """运行单一扰动测试"""
    
    def run_combination_tests(self) -> Dict[str, Any]:
        """运行组合扰动测试"""
    
    def run_complex_scenario_tests(self) -> Dict[str, Any]:
        """运行复杂场景测试"""
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """运行性能测试"""
```

### IntegrationPerformanceValidator

集成性能验证器。

```python
class IntegrationPerformanceValidator:
    """集成性能验证器"""
    
    def run_all_validations(self) -> Dict[str, Any]:
        """运行所有验证
        
        Returns:
            Dict[str, Any]: 验证结果
                - basic_integration: 基础集成测试结果
                - stress_tests: 压力测试结果
                - concurrent_tests: 并发测试结果
                - memory_tests: 内存测试结果
                - stability_tests: 稳定性测试结果
        """
```

## 异常处理

### 自定义异常

```python
class SimulationError(Exception):
    """仿真错误基类"""
    pass

class ComponentError(SimulationError):
    """组件错误"""
    pass

class AgentError(SimulationError):
    """智能体错误"""
    pass
```

## 使用示例

详细的使用示例请参考 examples/ 目录下的示例代码。
