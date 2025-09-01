# 任务描述：构建分层分布式水利仿真系统

请根据提供的平台框架，分步构建一个包含一个闸门、两个渠池（闸前、闸后）的串联仿真系统。本任务的核心是拆解各个智能体的功能，通过一系列由小及大的例子，最终实现一个完整的分层分布式控制与调度系统。

## 1. 最小单元独立示例

在这一部分，我们将分别展示每个核心智能体的功能，使其在最简单的环境中独立运行。

### 示例 1.1：本体仿真智能体（物理模型）

**目标**：演示纯物理组件（渠道和闸门）的动态行为。

**任务**：

1.  初始化 `upstream_canal` 和 `control_gate` 物理组件。
2.  模拟 `upstream_canal` 接收一个阶跃式入流（例如，入流从 10m³/s 变为 20m³/s）。
3.  在仿真循环中，手动推进 `upstream_canal` 和 `control_gate` 的 `step()` 方法。
4.  验证 `upstream_canal` 的水位和 `control_gate` 的出流如何响应入流的变化而变化。

**核心功能点**：展示水利模型（一维水力学或简化模型）的运行，不涉及任何控制智能体。

### 示例 1.2：传感器与执行器仿真智能体

**目标**：演示一个独立的 `PhysicalIOAgent` 如何模拟传感器的感知和执行器的物理动作。

**任务**：

1.  初始化一个 `upstream_canal` 物理组件和一个 `control_gate` 物理组件。
2.  创建 `PhysicalIOAgent`，将其与 `upstream_canal` 和 `control_gate` 绑定，并配置好其消息发布与订阅主题。
3.  创建一个简单的指令发送函数，手动向 `PhysicalIOAgent` 的指令主题发布一个目标开度。
4.  在仿真循环中，调用 `PhysicalIOAgent` 的 `run()` 方法。
5.  验证 `PhysicalIOAgent` 是否能从物理模型读取状态并带噪声发布，同时将收到的指令转化为 `control_gate` 的实际物理开度。

**核心功能点**：将传感器仿真和执行器仿真独立为一个智能体，体现物理世界与控制系统的IO接口。

### 示例 1.3：闸站控制智能体（现地PID）

**目标**：展示现地PID智能体如何实现一个本地的反馈控制闭环。

**任务**：

1.  初始化一个 `MessageBus` 和一个 `PIDController`。
2.  创建 `gate_control_agent`，将 `PIDController` 封装在其中。
3.  配置 `gate_control_agent` 订阅一个观测主题（例如，`state.upstream_canal.level`）并发布一个动作主题（例如，`action.control_gate.opening`）。
4.  创建一个模拟的传感器，手动向观测主题发布一个与设定点有偏差的水位值。
5.  验证 `gate_control_agent` 是否被触发，并向动作主题发布了正确的控制信号。

**核心功能点**：此示例聚焦于“决策”和“行动”的逻辑，将“感知”和“物理执行”抽象化。

### 示例 1.4：数字孪生智能体（高级功能）

**目标**：演示 `DigitalTwinAgent` 如何在接收到感知数据后，执行更高级的功能，如数据清洗、系统辨识和预测。

**任务**：

1.  初始化一个 `MessageBus` 和一个 `upstream_canal` 模型。
2.  创建 `DigitalTwinAgent`，订阅 `PhysicalIOAgent` 发布的数据主题（带噪声）。
3.  在仿真循环中，调用 `DigitalTwinAgent` 的 `run()` 方法。
4.  验证 `DigitalTwinAgent` 是否能对收到的数据进行平滑处理或参数辨识，并发布一个更精确的模型状态。

**核心功能点**：此示例突出了 `DigitalTwinAgent` 的“认知”功能，即从不完美的数据中提取有价值的信息。

### 示例 1.5：中心MPC调度智能体

**目标**：展示 `CentralDispatcher`（中心MPC）如何在孤立环境下接收预测信息，并输出高层调度指令。

**任务**：

1.  初始化一个 `MessageBus` 和一个 `MPCController`。
2.  创建 `central_dispatcher`，配置其MPC模型、规则和预测主题订阅。
3.  创建一个模拟的预测智能体，向预测主题发布一个未来入流的预测序列。
4.  手动发布一个初始的闸前水位状态。
5.  调用 `central_dispatcher` 的 `run()` 方法。
6.  验证 `central_dispatcher` 是否根据预测信息和当前水位，向一个命令主题（例如，`command.gate.setpoint`）发布了一个新的PID设定点。

**核心功能点**：此示例突出MPC的“前瞻性”和“优化”特性，即在物理环境变化之前，就能提前调整控制策略。

## 2. 组合与分层示例

在这一部分，我们将把上述最小单元组合起来，构建一个完整的、可运行的分层分布式系统。

### 示例 2.1：现地闭环控制

**目标**：构建一个由现地PID智能体独立工作的完整闭环控制系统。

**任务**：

1.  将示例 1.1、1.2 和 1.3 的组件和逻辑整合进一个完整的 `SimulationHarness` 仿真。
2.  `PhysicalIOAgent` 实时发布闸前水位。
3.  `gate_control_agent` 实时接收水位并调整闸门。
4.  `PhysicalIOAgent` 响应指令并改变闸门的物理状态。
5.  `upstream_canal` 的水位因入流和出流的动态平衡而变化。
6.  验证 `gate_control_agent` 是否能将闸前水位稳定维持在预设的PID设定点。

**核心功能点**：展示一个完全解耦的、事件驱动的现地控制闭环。

### 示例 2.2：分层分布式控制与复杂扰动应对

**目标**：构建一个完整的、具备分层控制能力的复杂系统，并测试其在多种扰动下的鲁棒性。

**任务**：

1.  将所有组件和所有智能体整合进 `SimulationHarness`。
2.  设置MPC的正常和应急设定点规则。
3.  设置 `rainfall_agent` 和 `water_use_agent` 注入扰动的时间和强度。
4.  运行仿真，并观察在不同扰动情景下，MPC如何调整PID的设定点，以及整个系统如何协同工作以维持稳定。

**核心功能点**：这是最终的、最完整的示例，它将验证所有智能体、预测和控制层面的协同工作能力。

## 运行方式 (Running Methods)

CHS-SDK Examples目录支持四种不同的运行方式，以满足不同的使用需求：

### 1. 硬编码运行方式 (Hardcoded Approach)
**特点**: 直接在Python代码中构建仿真，无需外部配置文件
**适用场景**: 快速原型开发、教学演示、简单测试
**运行命令**:
```bash
python run_hardcoded.py [example_type]
# 或交互式选择
python run_hardcoded.py
```

### 2. 场景运行方式 (Scenario-based Approach)
**特点**: 使用传统的多配置文件方式（config.yml, components.yml等）
**适用场景**: 复杂仿真配置、团队协作、版本控制
**运行命令**:
```bash
python run_scenario.py [example_type]
# 或交互式选择
python run_scenario.py
```

### 3. 统一场景运行方式 (Unified Scenario Approach)
**特点**: 优先使用统一配置文件，提供更好的配置管理
**适用场景**: 标准化配置、批量运行、配置模板化
**运行命令**:
```bash
python run_unified_scenario.py [example_type]
# 或交互式选择
python run_unified_scenario.py
```

### 4. 通用配置运行方式 (Universal Config Approach) - 推荐
**特点**: 使用universal_config.yml提供最完整的功能支持
**适用场景**: 生产环境、高级功能需求、性能优化
**运行命令**:
```bash
python run_universal_config.py [example_type]
# 或交互式选择
python run_universal_config.py
```

### 可用的示例类型 (Available Example Types)
- `agent_based`: 智能体示例
- `canal_model`: 渠道模型示例
- `non_agent_based`: 非智能体示例
- `identification`: 参数辨识示例
- `demo`: 演示示例
- `watertank`: 水箱示例
- `notebooks`: Jupyter笔记本示例
- `mission_example_1`: Mission示例1 - 基础物理仿真和高级控制
- `mission_example_2`: Mission示例2 - 闭环控制系统
- `mission_example_3`: Mission示例3 - 增强感知系统
- `mission_example_5`: Mission示例5 - 水轮机闸门仿真
- `mission_scenarios`: Mission场景示例 - 引绰济辽工程仿真
- `mission_data`: Mission示例共享数据文件

### 配置文件说明
- **universal_config.yml**: 通用配置文件，包含所有高级功能配置
- **各子目录配置**: 每个示例子目录可包含专用的配置文件
- **兼容性**: 支持传统的多文件配置方式作为备选方案

## Mission示例说明 (Mission Examples)

从mission目录迁移的示例提供了完整的水利仿真系统案例，展示了从基础物理仿真到复杂控制系统的完整实现。

### Mission Example 1: 基础物理仿真和高级控制
**目录**: `mission_example_1`
**包含子示例**:
- `01_basic_simulation`: 基础仿真入门
- `02_advanced_control`: 高级控制策略
- `03_fault_tolerance`: 容错机制
- `04_digital_twin_advanced`: 高级数字孪生
- `05_central_mpc_dispatcher`: 中央MPC调度

**特点**: 从简单到复杂的渐进式学习路径，涵盖物理建模、控制算法、容错设计等核心概念。

### Mission Example 2: 闭环控制系统
**目录**: `mission_example_2`
**包含子示例**:
- `01_local_control`: 本地控制
- `02_hierarchical_control`: 分层控制
- `03_watershed_coordination`: 流域协调

**特点**: 专注于控制系统设计，展示从单点控制到分布式协调的完整控制架构。

### Mission Example 3: 增强感知系统
**目录**: `mission_example_3`
**包含子示例**:
- `01_enhanced_perception`: 增强感知能力

**特点**: 展示智能感知和数据处理技术在水利系统中的应用。

### Mission Example 5: 水轮机闸门仿真
**目录**: `mission_example_5`
**包含子示例**:
- `01_turbine_gate_simulation`: 水轮机闸门基础仿真
- `02_multi_unit_coordination`: 多机组协调
- `03_economic_dispatch`: 经济调度
- `04_gate_scheduling`: 闸门调度

**特点**: 专门针对水电站运行的仿真示例，包含经济性分析和优化调度。

### Mission Scenarios: 引绰济辽工程仿真
**目录**: `mission_scenarios`
**包含子示例**:
- `yinchuojiliao`: 引绰济辽工程完整仿真场景

**特点**: 展示大型跨流域调水工程的完整仿真实现，包含多泵站协调控制、长距离输水系统建模、复杂水力学计算等核心技术。

### 迁移指南
详细的迁移指南请参考 `MIGRATION_GUIDE.md` 文件，其中包含:
- 配置文件迁移步骤
- 功能对比和映射
- 最佳实践建议
- 常见问题解答
