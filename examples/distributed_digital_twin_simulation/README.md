# 分布式数字孪生仿真系统

## 概述

本项目是一个先进的分布式数字孪生仿真系统，专门用于水利工程的智能化管理和控制。系统支持多种扰动场景测试，包括入流变化、传感器噪声、执行器故障等，为水利系统的稳定性和可靠性分析提供强大的仿真平台。

## 主要特性

### 🌊 核心仿真功能
- **分布式架构**: 支持多节点分布式仿真
- **实时仿真**: 高性能实时仿真引擎
- **智能体系统**: 支持多智能体协同控制
- **物理建模**: 精确的水利工程物理模型

### 🔧 扰动测试系统
- **入流扰动**: 模拟上游来水变化
- **传感器噪声**: 模拟传感器测量误差
- **执行器故障**: 模拟设备故障情况
- **网络扰动**: 模拟通信延迟和丢包
- **组合扰动**: 支持多种扰动同时作用

### 📊 监控与分析
- **实时监控**: 系统状态实时监控
- **性能分析**: 详细的性能指标分析
- **历史数据**: 完整的仿真历史记录
- **可视化**: 丰富的数据可视化功能

## 快速开始

### 环境要求

- Python 3.8+
- NumPy
- PyYAML
- psutil
- 其他依赖见 `requirements.txt`

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd distributed_digital_twin_simulation

# 安装依赖
pip install -r requirements.txt
```

### 基础使用

#### 1. 运行基础仿真

```bash
python enhanced_single_disturbance_test.py
```

#### 2. 运行全面扰动测试

```bash
python comprehensive_disturbance_test_suite.py
```

#### 3. 运行集成性能验证

```bash
python integration_performance_validator.py
```

#### 4. 验证配置文件

```bash
python yaml_scenario_validator.py
```

## 项目结构

```
distributed_digital_twin_simulation/
├── config.yml                              # 主配置文件
├── agents.yml                              # 智能体配置
├── components.yml                          # 组件配置
├── topology.yml                            # 拓扑配置
├── disturbance_scenarios/                  # 扰动场景配置
│   └── basic_disturbances/
│       ├── actuator_interference.yml
│       ├── data_packet_loss.yml
│       ├── diversion_demand_change.yml
│       ├── inflow_disturbance.yml
│       ├── network_delay.yml
│       └── sensor_noise.yml
├── enhanced_single_disturbance_test.py     # 单一扰动测试
├── comprehensive_disturbance_test_suite.py # 全面扰动测试套件
├── integration_performance_validator.py    # 集成性能验证
├── yaml_scenario_validator.py             # YAML配置验证
├── enhanced_simulation_harness.py         # 增强仿真框架
├── network_disturbance.py                 # 网络扰动模块
├── docs/                                   # 文档目录
├── examples/                               # 示例代码
└── output/                                 # 输出结果
```

## 配置说明

### 主配置文件 (config.yml)

主配置文件定义了仿真的基本参数：

```yaml
simulation:
  name: "分布式数字孪生仿真"
  description: "水利工程数字孪生仿真系统"
  version: "1.0.0"

time_config:
  start_time: 0
  end_time: 100
  dt: 1.0

solver_config:
  type: "euler"
  tolerance: 1e-6
  max_iterations: 1000

parallel_config:
  enable_parallel: true
  num_processes: 4
  load_balancing: "dynamic"
```

### 扰动场景配置

扰动场景通过YAML文件定义，支持多种扰动类型：

```yaml
# 入流扰动示例
disturbance:
  id: "inflow_change_001"
  type: "inflow_change"
  description: "上游来水量突然增加"
  target_component: "Upstream_Reservoir"
  start_time: 10.0
  end_time: 30.0
  parameters:
    target_inflow: 150.0
    change_rate: 5.0
```

## 扰动测试指南

### 支持的扰动类型

1. **入流扰动 (Inflow Disturbance)**
   - 模拟上游来水变化
   - 支持渐变和突变模式
   - 可配置目标流量和变化速率

2. **传感器噪声 (Sensor Noise)**
   - 模拟传感器测量误差
   - 支持高斯噪声和均匀噪声
   - 可配置噪声强度和影响范围

3. **执行器故障 (Actuator Failure)**
   - 模拟设备故障情况
   - 支持完全故障和部分故障
   - 可配置故障类型和恢复时间

4. **网络扰动 (Network Disturbance)**
   - 模拟通信延迟和丢包
   - 支持延迟变化和包丢失
   - 可配置网络质量参数

### 测试流程

1. **单一扰动测试**: 验证每种扰动类型的基本功能
2. **组合扰动测试**: 测试多种扰动同时作用的情况
3. **复杂场景测试**: 模拟真实的复杂故障场景
4. **性能基准测试**: 评估系统在扰动下的性能表现

## API 文档

### 核心类

#### EnhancedSimulationHarness

增强版仿真框架，提供完整的仿真环境管理功能。

```python
from enhanced_simulation_harness import EnhancedSimulationHarness

# 创建仿真环境
config = {
    'start_time': 0,
    'end_time': 100,
    'dt': 1.0,
    'enable_network_disturbance': True
}

harness = EnhancedSimulationHarness(config)

# 添加组件
harness.add_component("reservoir", reservoir_instance)

# 添加智能体
harness.add_agent(agent_instance)

# 添加扰动
harness.add_disturbance(disturbance_instance)

# 构建并运行仿真
harness.build()
harness.run_simulation()

# 获取结果
history = harness.get_simulation_history()

# 关闭仿真
harness.shutdown()
```

#### 扰动类

```python
from core_lib.disturbances.disturbance_framework import (
    InflowDisturbance, SensorNoiseDisturbance, ActuatorFailureDisturbance,
    DisturbanceConfig, DisturbanceType
)

# 创建入流扰动
config = DisturbanceConfig(
    disturbance_id="test_inflow",
    disturbance_type=DisturbanceType.INFLOW_CHANGE,
    target_component_id="reservoir",
    start_time=10.0,
    end_time=30.0,
    intensity=1.0,
    parameters={"target_inflow": 150.0}
)

disturbance = InflowDisturbance(config)
```

## 性能优化

### 系统性能

- **高频仿真**: 支持0.1秒时间步长的高频仿真
- **大规模组件**: 支持10+组件的大规模仿真
- **并发处理**: 支持多线程并发仿真
- **内存优化**: 有效的内存管理，避免内存泄漏

### 性能指标

根据集成性能验证结果：
- **仿真速度**: 45,000+ 步/秒
- **内存使用**: 稳定，无明显泄漏
- **并发性能**: 支持3个并发仿真实例
- **稳定性**: 长时间运行稳定

## 故障排除

### 常见问题

1. **导入错误**
   ```
   ModuleNotFoundError: No module named 'xxx'
   ```
   解决方案：检查Python路径设置，确保所有依赖已安装

2. **配置文件错误**
   ```
   yaml.scanner.ScannerError
   ```
   解决方案：使用 `yaml_scenario_validator.py` 验证配置文件

3. **编码问题**
   ```
   UnicodeDecodeError: 'gbk' codec can't decode
   ```
   解决方案：确保文件使用UTF-8编码

### 调试技巧

1. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **使用验证工具**
   ```bash
   python yaml_scenario_validator.py
   python integration_performance_validator.py
   ```

3. **检查系统资源**
   ```python
   import psutil
   print(f"CPU: {psutil.cpu_percent()}%")
   print(f"Memory: {psutil.virtual_memory().percent}%")
   ```

## 贡献指南

### 开发环境设置

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

### 代码规范

- 遵循 PEP 8 代码风格
- 添加适当的文档字符串
- 编写单元测试
- 更新相关文档

### 测试要求

- 所有新功能必须包含测试
- 确保所有测试通过
- 性能测试验证

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [Issues]
- 文档: [Documentation]

## 更新日志

### v1.0.0 (2025-09-03)

- ✅ 完整的扰动测试系统
- ✅ 集成性能验证
- ✅ 配置文件验证
- ✅ 全面的文档和示例
- ✅ 高性能仿真引擎
- ✅ 稳定的并发支持

---

**感谢使用分布式数字孪生仿真系统！**
