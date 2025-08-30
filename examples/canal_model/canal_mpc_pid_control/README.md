# 渠道系统MPC+PID分层控制示例

本示例演示了一个应用于渠道系统的分层控制架构，结合了中央模型预测控制（MPC）和现地PID控制器，以在存在多种扰动的情况下维持系统稳定。

## 系统描述

本示例模拟了一个简化的渠道系统，其核心目的是通过上游的 `gate_1` 和下游的 `gate_2` 来精确控制 `canal_1` 中的水位。

### 物理组件

- **`upstream_reservoir`**: 上游水源，其来水流量会受到扰动。
- **`gate_1` 和 `gate_2`**: 两个控制闸门。
- **`canal_1`**: 一个使用积分-时滞模型 (`integral_delay`) 建模的渠段。
- **扰动节点**:
  - `diversion_before_gate1`: 模拟 `gate_1` 前方的分水（如农业灌溉）。
  - `diversion_before_gate2`: 模拟 `gate_2` 前方的分水。
  - `tail_user`: 模拟渠系末端的终端用户用水。

### 系统拓扑

组件按以下顺序串联连接：
`reservoir` -> `diversion_1` -> `gate_1` -> `canal_1` -> `diversion_2` -> `gate_2` -> `tail_user`

## 控制架构

本示例采用一种先进的分层控制策略：

1.  **中央MPC控制器 (`central_mpc_agent`)**:
    - **目标**: 预测并优化 `canal_1` 的未来水位。
    - **动作**: 它不直接控制闸门，而是计算出最优的**水位设定点**，并将其发送给 `gate_1` 的PID控制器。
    - **依据**: MPC的决策基于 `canal_1` 的积分-时滞模型，并能将未来的扰动（如果提供预测）纳入考量。

2.  **现地PID控制器 (`gate_1_pid_agent` 和 `gate_2_pid_agent`)**:
    - **`gate_1_pid_agent`**:
        - 这是一个从动控制器，它的**水位设定点由中央MPC动态调整**。
        - 它负责执行MPC的指令，通过精确调节 `gate_1` 的开度来实现MPC下发的水位目标。
    - **`gate_2_pid_agent`**:
        - 这是一个标准的现地上游控制器，其水位设定点是固定的。
        - 它负责维持 `gate_2` 上游（即 `canal_1` 末端）的水位稳定。

这种“MPC优化设定点 + PID精确执行”的架构结合了MPC的远见性和PID控制器的快速响应与鲁棒性。

## 系统扰动

为了测试控制系统的性能，本示例引入了多种扰动，这些扰动由`CsvInflowAgent`从CSV文件中读取并注入系统：

- **渠首来水扰动**: `upstream_reservoir` 的入流量会根据 `headwater_inflow_disturbance.csv` 的定义而波动。
- **分水扰动**:
  - `diversion_1_disturbance.csv` 定义了 `gate_1` 前方的分水流量。
  - `diversion_2_disturbance.csv` 定义了 `gate_2` 前方的分水流量。
- **渠末用水扰动**: (待实现) `tail_user` 的用水量也可以通过类似方式进行扰动。

## 如何运行

本示例是数据驱动的，所有配置（组件、拓扑、智能体）都在YAML文件中定义。

要运行此模拟，请在项目的根目录下执行以下命令：

```bash
python run_scenario.py examples/canal_model/canal_mpc_pid_control
```

## 预期结果

脚本将执行模拟，并将所有组件和智能体的详细历史记录保存到 `output.yml` 文件中。

您可以分析 `output.yml` 文件来观察：
- `canal_1` 的水位是否在MPC的调控下保持稳定。
- `gate_1` 的开度如何根据MPC的设定点和PID的计算进行调整。
- 系统在各种扰动下的响应情况。
- MPC智能体与PID智能体之间的协同工作。
