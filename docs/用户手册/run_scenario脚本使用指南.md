# run_scenario.py 脚本使用指南

## 概述

`run_scenario.py` 是 CHS-SDK 的核心仿真运行脚本，提供了一个通用的命令行接口来运行基于多 YAML 配置文件格式的仿真场景。该脚本是连接用户配置和仿真引擎的桥梁，支持智能体系统、物理组件和拓扑结构的完整仿真。

## 核心功能

### 主要特性
- **多文件配置支持**: 支持 `config.yml`、`components.yml`、`topology.yml`、`agents.yml` 四个配置文件
- **智能体系统**: 完整的智能体加载和运行支持
- **灵活配置**: 可指定自定义智能体配置文件
- **结果保存**: 自动保存仿真历史数据为 YAML 格式
- **错误处理**: 完善的错误检查和日志记录

### 业务逻辑
1. **配置验证**: 检查场景目录和必要配置文件的存在性
2. **系统加载**: 通过 `SimulationBuilder` 加载完整的仿真系统
3. **仿真执行**: 运行多智能体系统（MAS）仿真
4. **结果处理**: 保存仿真历史数据并生成输出文件

## 使用方法

### 基本语法
```bash
python run_scenario.py <scenario_path> [--agents agents_file]
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `scenario_path` | str | 是 | - | 仿真场景目录路径 |
| `--agents` | str | 否 | "agents.yml" | 智能体配置文件名 |

### 使用示例

#### 1. 基本运行
```bash
# 使用默认 agents.yml 文件
python run_scenario.py examples/canal_model/canal_pid_control

# 指定自定义智能体配置文件
python run_scenario.py examples/canal_model/canal_pid_control --agents custom_agents.yml
```

#### 2. 运行渠道案例演示
```bash
# 运行我们创建的渠道演示案例
python run_scenario.py canal_demo_scenario --agents agents.yml
```

#### 3. 运行分布式数字孪生案例
```bash
python run_scenario.py examples/distributed_digital_twin_simulation --agents agents.yml
```

## 配置文件结构

### 必需的配置文件

#### 1. config.yml - 仿真配置
```yaml
simulation:
  name: "Simulation Name"
  time_config:
    start_time: 0.0
    end_time: 3600.0
    time_step: 10.0
  solver_config:
    type: "runge_kutta_4"
    tolerance: 1e-6
```

#### 2. components.yml - 物理组件
```yaml
components:
  - id: "Reservoir_1"
    class: "core_lib.physical_objects.reservoir.Reservoir"
    config:
      initial_state:
        water_level: 10.0
      parameters:
        surface_area: 10000
```

#### 3. topology.yml - 拓扑连接
```yaml
connections:
  - upstream: "Reservoir_1"
    downstream: "Gate_1"
    connection_type: "water_flow"
```

#### 4. agents.yml - 智能体配置
```yaml
agents:
  - id: "PID_Controller_1"
    class: "core_lib.local_agents.control.pid_controller.PIDController"
    config:
      controlled_id: "Gate_1"
      target_value: 10.0
```

## 核心模块依赖

### 主要依赖模块
- **core_lib.io.yaml_loader.SimulationBuilder**: 核心 YAML 加载器
- **core_lib.io.yaml_writer.save_history_to_yaml**: 历史数据保存器
- **core_lib.core_engine.testing.simulation_harness.SimulationHarness**: 仿真引擎

### 数据流
```
配置文件 → SimulationBuilder → SimulationHarness → 仿真结果 → YAML输出
```

## 输出文件

### 自动生成的输出文件
- `output_{agents_file_stem}.yml`: 仿真历史数据（YAML格式）
- 控制台日志: 详细的运行状态和进度信息

### 输出文件示例
```yaml
# output_agents.yml
- time: 0.0
  Reservoir_1_water_level: 10.0
  Gate_1_opening: 0.3
  Gate_1_outflow: 25.0
- time: 10.0
  Reservoir_1_water_level: 9.95
  Gate_1_opening: 0.32
  Gate_1_outflow: 26.5
```

## 错误处理

### 常见错误及解决方案

#### 1. 场景路径不存在
```
错误: Provided scenario path is not a valid directory: /path/to/scenario
```
**解决方案**: 检查路径是否正确，确保目录存在

#### 2. 配置文件缺失
```
ValueError: Core configuration files (config, components, topology) are missing.
```
**解决方案**: 确保场景目录包含必需的配置文件

#### 3. 智能体配置错误
```
Error loading agent: Agent configuration is invalid
```
**解决方案**: 检查 agents.yml 文件格式和智能体类名

#### 4. 模块导入失败
```
ImportError: No module named 'core_lib'
```
**解决方案**: 确保 CHS-SDK 已正确安装，Python 路径设置正确

## 日志系统

### 日志级别
- **INFO**: 正常运行信息
- **WARNING**: 非致命警告
- **ERROR**: 错误信息

### 日志格式
```
2025-09-15 13:01:23,456 - __main__ - INFO - Starting Simulation Scenario: canal_demo
2025-09-15 13:01:23,789 - __main__ - INFO - Loading scenario from: canal_demo using agents file: agents.yml
2025-09-15 13:01:24,123 - __main__ - INFO - Starting MAS simulation run...
```

## 性能考虑

### 影响性能的因素
1. **仿真时长**: `end_time - start_time`
2. **时间步长**: `time_step` 越小，计算越精确但耗时越长
3. **组件数量**: 物理组件和智能体数量
4. **求解器类型**: 不同求解器的计算复杂度

### 性能优化建议
- 合理设置时间步长（通常 1-10 秒）
- 避免过长的仿真时间
- 使用适当的求解器类型
- 监控内存使用情况

## 扩展和定制

### 自定义智能体
```python
# 在 agents.yml 中添加自定义智能体
agents:
  - id: "Custom_Agent"
    class: "your_module.CustomAgent"
    config:
      custom_parameter: "value"
```

### 自定义物理组件
```python
# 在 components.yml 中添加自定义组件
components:
  - id: "Custom_Component"
    class: "your_module.CustomComponent"
    config:
      custom_config: "value"
```

## 最佳实践

### 1. 配置文件组织
- 保持配置文件结构清晰
- 使用有意义的组件和智能体 ID
- 添加适当的注释说明

### 2. 错误处理
- 在运行前检查配置文件语法
- 使用较小的测试案例验证配置
- 查看详细日志信息排查问题

### 3. 性能优化
- 根据需求调整仿真参数
- 使用合适的求解器设置
- 定期清理输出文件

## 相关脚本

### 配套脚本
- `canal_demo.py`: 渠道案例演示脚本（基于 run_scenario.py）
- `examples/run_scenario.py`: Examples 目录的场景运行器
- `run_unified_scenario.py`: 统一配置格式运行器

### 工具脚本
- `scripts/preprocess_examples.py`: 示例预处理脚本
- `test_all_simulation_modes.py`: 仿真模式测试脚本

## 版本兼容性

### 支持的 Python 版本
- Python 3.8+
- 推荐使用 Python 3.9 或更高版本

### 依赖包要求
- core_lib (CHS-SDK 核心库)
- PyYAML >= 6.0
- 其他 core_lib 内部依赖

## 故障排除

### 调试步骤
1. 检查 Python 路径设置
2. 验证配置文件格式
3. 查看详细错误日志
4. 使用较小的测试案例
5. 检查依赖包安装

### 获取帮助
- 查看控制台错误信息
- 检查日志文件
- 参考示例配置文件
- 查阅 core_lib 文档

## 总结

`run_scenario.py` 是 CHS-SDK 的核心运行脚本，提供了完整的仿真场景运行能力。通过合理的配置和使用，可以实现复杂的水利系统仿真，包括物理建模、智能体控制和数据分析等全流程功能。该脚本的设计充分考虑了易用性、可扩展性和错误处理，是进行水利系统仿真的重要工具。
