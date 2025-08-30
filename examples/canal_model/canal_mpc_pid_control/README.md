# 渠道系统MPC+PID分层控制示例（基于情景）

本示例在先前版本的基础上进行了重构，通过引入一个**情景智能体 (`ScenarioAgent`)**，用一种更强大和集中的方式来管理和注入系统扰动。

## 系统描述

本示例模拟了一个简化的渠道系统，其核心目的是通过上游的 `gate_1` 和下游的 `gate_2` 来精确控制 `canal_1` 中的水位。

### 物理组件

- **`upstream_reservoir`**: 上游水源。
- **`gate_1` 和 `gate_2`**: 两个控制闸门。
- **`canal_1`**: 一个使用积分-时滞模型 (`integral_delay`) 建模的渠段。
- **扰动节点**:
  - `diversion_before_gate1`: 模拟 `gate_1` 前方的分水。
  - `diversion_before_gate2`: 模拟 `gate_2` 前方的分水。
  - `tail_user`: 模拟渠系末端的终端用户用水。

### 系统拓扑

`reservoir` -> `diversion_1` -> `gate_1` -> `canal_1` -> `diversion_2` -> `gate_2` -> `tail_user`

## 控制架构

本示例采用一种先进的分层控制策略：

1.  **中央MPC控制器 (`central_mpc_agent`)**:
    - **目标**: 预测并优化 `canal_1` 的未来水位。
    - **动作**: 计算出最优的**水位设定点**，并将其发送给 `gate_1` 的PID控制器。
2.  **现地PID控制器 (`gate_1_pid_agent` 和 `gate_2_pid_agent`)**:
    - **`gate_1_pid_agent`**: 它的水位设定点由中央MPC动态调整。
    - **`gate_2_pid_agent`**: 它负责维持 `gate_2` 上游的水位稳定，其设定点是固定的。

## 基于情景的扰动管理

与之前使用多个`CsvInflowAgent`分散管理扰动不同，本示例现在采用一个中央`ScenarioAgent`来统一调度所有扰动事件。

### 情景智能体 (`ScenarioAgent`)

- **角色**: 该智能体是整个模拟的“导演”。它从`agents.yml`文件中的`scenario_script`部分读取一个预设的事件脚本。
- **工作原理**: `ScenarioAgent`在每个时间步检查脚本。当模拟时间到达脚本中某个事件的预定时间时，它就会将该事件中定义的消息发布到指定的主题上。
- **优点**: 这种方法非常灵活，允许用户在一个地方清晰地定义复杂的时间序列事件，轻松组合出无穷的扰动情景，极大地增强了测试的系统性和可重复性。

### 当前扰动情景

在`agents.yml`中定义的`scenario_script`包含以下事件：
- **t=1000s**: 渠首来流增加到55。
- **t=1500s**: 第一个分水口开始分水5个流量。
- **t=2000s**: 渠首来流减少到45。
- **t=2500s**: 第二个分水口开始分水7个流量。
- **t=3000s**: 渠首来流恢复到50。
- ...以此类推。

## 如何运行

本示例是数据驱动的，所有配置都在YAML文件中定义。要运行此模拟，请在项目的根目录下执行以下命令：

```bash
python run_scenario.py examples/canal_model/canal_mpc_pid_control
```

## 预期结果

脚本将执行模拟，并将所有组件和智能体的详细历史记录保存到 `output.yml` 文件中。您可以分析此文件来评估分层控制系统在`ScenarioAgent`注入的一系列复杂扰动下的性能表现。
