# 示例 2: 闭环与分层控制系统

本目录中的示例（2.1 至 2.3）着重于演示如何将独立的智能体（Agent）组合成一个完整的、可运行的闭环控制系统，并逐步构建更高级的分层与联合调度策略。

## 示例说明

### `example_2_1_local_closed_loop.py`
*   **目标**: 演示一个完整的、独立的现地（本地）闭环控制系统。
*   **内容**: 此示例使用 `SimulationHarness` 仿真引擎来集成一个完整的场景。它包含：
    1.  一个 `PhysicalIOAgent`，负责感知渠池水位并执行闸门动作。
    2.  一个 `LocalControlAgent`，内置PID控制器，根据感知到的水位自动调节闸门。
    3.  一个 `RainfallAgent`，模拟持续的外部扰动（上游来水）。
    整个系统在没有中央干预的情况下，自主地将渠池水位稳定在预设的目标值附近。
*   **核心概念**: 仿真引擎（`SimulationHarness`），完整的本地反馈控制回路，扰动响应。

### `example_2_2_hierarchical_control.py`
*   **目标**: 演示一个两级分层控制系统，引入预测与优化能力。
*   **内容**: 此示例在本地PID控制的基础上，增加了一个更高层次的中央调度智能体 `CentralMPCAgent`（模型预测控制）。
    1.  **上层 (MPC)**: 该智能体能接收未来的天气预报（例如，未来几小时有大暴雨），通过其内部优化模型，计算出最优的应对策略。它不下达具体的闸门开度，而是向前瞻性地调整下层PID控制器的**目标水位**（例如，在暴雨来临前，提前降低水库的目标水位以腾出库容）。
    2.  **下层 (PID)**: 本地PID控制器忠实地执行来自上层MPC的新设定点。
*   **核心概念**: 分层控制，模型预测控制（MPC），前瞻性控制，优化调度。

### `example_2_3_joint_dispatch.py`
*   **目标**: 演示一个更复杂的流域联合调度场景。
*   **内容**: 此示例模拟了一个包含多种水利设施的流域：一个上游水库、一个水电站（包含发电机组和泄洪闸）以及一个下游灌溉取水口。系统面临的挑战是，在应对上游洪水的同时，还要满足下游的用水需求。
    *   一个基于规则的 `CentralDispatcher` 智能体作为中央大脑，根据当前流域的整体状态（例如，水库水位是否超过汛限水位）切换全局策略（如“正常模式” vs “防洪模式”）。
    *   多个 `LocalControlAgent` 分别控制水电站和灌溉闸门，它们接收来自中央调度器的指令，并将其转化为对具体设备的控制动作。例如，在防洪模式下，水电站被命令加大下泄流量，而灌溉口则被命令关闭。
*   **核心概念**: 流域联合调度，多目标协调，基于规则的专家系统，多智能体协作。

## 如何运行

本目录中的所有示例支持四种不同的运行方式，你可以按顺序依次执行这些脚本，来理解不同层次的控制策略：

### 方式一：硬编码方式

```bash
# 交互式选择场景
python run_hardcoded.py

# 直接指定场景编号
python run_hardcoded.py 1  # 本地闭环控制
python run_hardcoded.py 2  # 分层控制
python run_hardcoded.py 3  # 流域联合调度
```

**特点**:
- 参数直接在代码中定义
- 代码逻辑清晰，适合学习和理解
- 快速测试和演示
- 完整集成调试工具

**适用场景**: 学习代码逻辑、快速原型验证

### 方式二：场景运行方式

```bash
# 交互式选择场景
python run_scenario.py

# 直接指定场景编号
python run_scenario.py 1  # 本地闭环控制
python run_scenario.py 2  # 分层控制
python run_scenario.py 3  # 流域联合调度
```

**特点**:
- 使用传统的多配置文件方式（agents.yml、components.yml、config.yml等）
- 支持交互式场景选择
- 每个场景独立配置
- 灵活的参数调整

**适用场景**: 传统配置管理、多场景对比测试

### 方式三：统一场景运行方式

```bash
# 交互式选择场景
python run_unified_scenario.py

# 直接指定场景编号
python run_unified_scenario.py 1  # 本地闭环控制
python run_unified_scenario.py 2  # 分层控制
python run_unified_scenario.py 3  # 流域联合调度
```

**特点**:
- 使用统一配置文件（universal_config_2_x.yml）
- 简化的配置管理
- 支持交互式场景选择
- 自动配置文件查找和回退

**适用场景**: 简化配置管理、标准化仿真流程

### 方式四：通用配置运行方式（推荐）

```bash
# 交互式选择场景
python run_universal_config.py

# 直接指定场景编号
python run_universal_config.py 1  # 本地闭环控制
python run_universal_config.py 2  # 分层控制
python run_universal_config.py 3  # 流域联合调度
```

**特点**:
- 使用最完整的通用配置文件（universal_config.yml）
- 支持所有高级功能（调试、性能监控、可视化等）
- 智能错误处理和恢复
- 自动验证和结果分析
- 配置文件验证和优化建议

**适用场景**: 生产环境、完整功能测试、性能分析

### 传统配置文件驱动方式（兼容性）

使用 `run_unified_scenario` 统一仿真运行器，代码简洁、易于维护：

```bash
# 示例 2.1: 本地闭环控制
python run_config_2_1.py

# 示例 2.2: 分层控制
python run_config_2_2.py

# 示例 2.3: 流域联合调度
python run_config_2_3.py
```

**特点**:
- 保持向后兼容性
- 每个场景独立的运行脚本
- 传统的配置文件结构

### 配置文件说明
- `config_2_1.yml`: 本地闭环控制系统配置
- `config_2_2.yml`: 分层分布式控制系统配置
- `config_2_3.yml`: 流域联合调度系统配置

每个配置文件都包含了完整的仿真参数、组件配置、智能体设置和验证标准，可以根据需要进行修改和扩展。

## 输出结果

### 控制台输出
- 🚀 仿真启动信息和配置摘要
- 📊 实时仿真进度条和状态显示
- 🎯 智能体协作和控制策略
- ✅ 自动验证结果和性能指标
- 📈 仿真总结和统计数据

### 数据文件
- **历史数据**: `simulation_history.yml` - 完整的仿真历史记录
- **日志文件**: 详细的运行日志和调试信息
- **验证报告**: 自动生成的结果验证报告

## 验证标准

每个示例都有特定的验证标准：

1. **本地闭环控制**: PID控制器的稳定性和响应性能
2. **分层控制**: MPC优化效果和分层协调能力
3. **流域联合调度**: 多目标协调和规则执行效果

## 文件结构

```
mission/example_2/
├── README.zh-CN.md              # 本文档
├── run_hardcoded.py             # 硬编码运行方式（新增）
├── run_scenario.py              # 场景运行方式（新增）
├── run_unified_scenario.py      # 统一场景运行方式（新增）
├── run_universal_config.py      # 通用配置运行方式（新增）
├── universal_config.yml         # 通用配置文件（新增）
├── config_2_1.yml              # 本地闭环控制配置
├── config_2_2.yml              # 分层控制配置
├── config_2_3.yml              # 流域联合调度配置
├── run_config_2_1.py           # 本地闭环控制运行脚本（兼容性）
├── run_config_2_2.py           # 分层控制运行脚本（兼容性）
├── run_config_2_3.py           # 流域联合调度运行脚本（兼容性）
├── example_2_1_local_closed_loop.py    # 原始硬编码脚本（兼容性）
├── example_2_2_hierarchical_control.py # 原始硬编码脚本（兼容性）
├── example_2_3_joint_dispatch.py       # 原始硬编码脚本（兼容性）
├── example_2_1/             # 本地闭环控制子场景目录（新增）
│   └── universal_config.yml # 子场景通用配置文件
├── example_2_2/             # 分层控制子场景目录（新增）
│   └── universal_config.yml # 子场景通用配置文件
└── example_2_3/             # 流域联合调度子场景目录（新增）
    └── universal_config.yml # 子场景通用配置文件
```

## 技术特性

- **统一架构**: 使用 `run_unified_scenario` 统一仿真运行器
- **配置驱动**: 所有参数通过 YAML 配置文件管理
- **自动验证**: 内置结果验证和分析功能
- **进度显示**: 实时仿真进度和状态监控
- **多智能体**: 支持复杂的智能体协作和分层控制
- **易于扩展**: 模块化设计，便于添加新的控制策略
