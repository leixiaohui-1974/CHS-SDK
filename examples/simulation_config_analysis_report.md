# 仿真配置参数使用情况分析报告

## 概述
本报告分析了 examples 目录下所有文件中 `duration` 和 `end_time` 参数的使用情况。

## 使用 `duration` 参数的文件

### 1. 配置文件 (YAML/JSON)
- **watertank_refactored/** 系列
  - `01_simple_simulation/config.yml` - duration: 200
  - `02_parameter_identification/config.yml` - duration: 200
  - `03_pid_control_inlet/config.yml` - duration: 300
  - `04_pid_control_outlet/config.yml` - duration: 300
  - `05_joint_control/config.yml` - duration: 400
  - `06_sensor_disturbance/config.yml` - duration: 300
  - `07_actuator_disturbance/config.yml` - duration: 300

- **watertank/** 系列
  - `01_simulation/config.yml` - duration: 100
  - `02_parameter_identification/config.json` - 扰动模式中的duration
  - `03_pid_control_inlet/config.json` - 扰动模式中的duration
  - `04_pid_control_outlet/config.json` - 扰动模式中的duration
  - `05_joint_control/config.json` - 扰动模式中的duration
  - `06_sensor_disturbance/config.json` - 扰动模式中的duration
  - `07_actuator_disturbance/config.json` - 扰动模式中的duration

- **non_agent_based/** 系列
  - `01_getting_started/config.yml` - duration: 300
  - `02_multi_component_systems/config.yml` - duration: 500
  - `07_pipe_and_valve/config.yml` - duration: 600
  - `08_non_agent_simulation/config.yml` - duration: 100

- **agent_based/** 系列
  - `03_event_driven_agents/config.yml` - duration: 60000

- **mission_scenarios/** 系列
  - `yinchuojiliao/config.yml` - duration: 168 (小时)
  - `universal_config.yml` - duration: 168.0

- **mission_example_5/** 系列
  - 多个配置文件使用 duration 作为仿真步数

### 2. Python 代码文件
- **agent_based/03_event_driven_agents/**
  - `plot_control_process.py` - simulation_config = {'duration': 100, 'dt': 1.0}
  - `debug_mas_simulation.py` - simulation_config = {'duration': 50, 'dt': 1.0}

- **watertank/** 系列
  - 多个 main.py 文件中使用 duration 进行扰动模式控制

- **non_agent_based/07_pipe_and_valve/**
  - `run_pipe_valve_simulation.py` - duration = 600
  - `run_config.py` - duration = sim_config['duration']

- **run_universal_config.py** - 支持 duration 作为备选参数
- **run_unified_scenario.py** - 支持 duration 作为备选参数

## 使用 `end_time` 参数的文件

### 1. Python 代码文件
- **agent_based/** 系列
  - `05_equipment_control/02_hydropower_control/hydropower_station_control_demo.py` - end_time: 600
  - `05_equipment_control/01_pump_control/pump_efficiency.py` - end_time: 600
  - `05_equipment_control/01_pump_control/basic_pump_control_refactored.py` - end_time: 600
  - `05_equipment_control/01_pump_control/advanced_pump_station.py` - end_time: 600
  - `08_pump_station_control/run_pump_station_simulation.py` - end_time: 600
  - `05_complex_networks/run_branched_network_simulation_refactored.py` - end_time: 10000
  - `06_handling_disturbances/run_disturbance_simulation.py` - end_time: 8000
  - `04_hierarchical_control/run_hierarchical_simulation.py` - end_time: 5000
  - `03_event_driven_agents/run_mas_simulation.py` - end_time: 60000
  - `13 pump_control_system/basic_examples/basic_pump_station.py` - end_time: 600
  - `13 pump_control_system/advanced_examples/pump_station_with_common_agents.py` - end_time: 600

- **mission_example_1/** 系列
  - 多个配置文件使用 end_time 作为仿真持续时间

- **mission_example_2/** 系列
  - 多个配置文件使用 end_time 作为仿真持续时间

- **mission_example_5/** 系列
  - 多个配置文件使用 end_time 作为仿真持续时间

- **distributed_digital_twin_simulation/** 系列
  - 多个测试文件使用 end_time 参数

### 2. 配置文件
- **mission_example_5/config_5.yml** - end_time: 300
- **mission_example_5/02_multi_unit_coordination/config.yml** - end_time: 300

## 混合使用情况

### 同时支持 duration 和 end_time 的文件
- **run_universal_config.py** - 优先使用 end_time，备选 duration
- **run_unified_scenario.py** - 优先使用 end_time，备选 duration
- **agent_based/03_event_driven_agents/run_config.py** - 从 duration 转换为 end_time

## 建议

### 1. 统一参数命名
- 建议统一使用 `end_time` 参数，因为这是 `SimulationHarness` 和 `SimulationBuilder` 的标准参数
- 逐步将 `duration` 参数迁移到 `end_time`

### 2. 配置文件更新
- 更新所有 YAML/JSON 配置文件，将 `duration` 改为 `end_time`
- 确保所有 Python 代码使用 `end_time` 参数

### 3. 代码兼容性
- 在 `run_universal_config.py` 和 `run_unified_scenario.py` 中保持对 `duration` 的向后兼容
- 在配置读取时优先使用 `end_time`，备选 `duration`

### 4. 文档更新
- 更新所有 README 文件，说明使用 `end_time` 而不是 `duration`
- 在示例代码中统一使用 `end_time` 参数

## 总结

目前 examples 目录中存在大量使用 `duration` 参数的配置文件，而 Python 代码文件主要使用 `end_time` 参数。建议进行统一化处理，以 `end_time` 作为标准参数，同时保持对 `duration` 的向后兼容性。
