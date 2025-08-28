# 案例说明：分支渠网闸门控制

## 1. 案例概述

本案例模拟了一个基础的分支渠网系统。该系统的核心是一个由单座闸门（Gate）控制、连接上下游两条渠道（Reach）的水力学模型。

这个案例的主要目的是：
- 演示如何通过JSON配置文件来定义一个水网的拓扑结构、物理参数和边界条件。
- 演示如何通过配置`disturbances`（扰动）来模拟仿真过程中的人工干预或突发事件。
- 作为后续更复杂案例重构的基础模板。

## 2. 拓扑结构

系统的拓扑结构非常简单，水流方向如下：

`Reach1 -> Gate1 -> Reach2`

- **Reach1**: 上游渠道，接收外部来水作为系统的上游边界。
- **Gate1**: 控制闸门，通过调整其开度来控制上下游之间的水流量。
- **Reach2**: 下游渠道，其末端水位被设为固定值，作为系统的下游边界。

## 3. 配置文件 (`config.json`) 说明

所有与本案例相关的配置都存储在`config.json`文件中。

- **`metadata`**: 包含案例的名称和描述等元数据。
- **`simulation_settings`**: 定义仿真的基本参数，如时间步长 (`dt`) 和总步数 (`num_steps`)。
- **`components`**: 定义了构成水网的所有物理组件。
  - 每个组件都有唯一的 `id` 和 `type`。
  - `type` 必须与`run_simulation.py`中`COMPONENT_CLASS_MAP`字典里的键名相匹配。
  - `params` 字段包含了初始化该物理组件所需的所有参数。
- **`connections`**: 定义了组件之间的连接关系，通过`from`和`to`字段指定上下游`id`。
- **`boundary_conditions`**: 定义了系统边界。在本例中，我们固定了`reach1`的起始水位和`reach2`的末端水位。
- **`disturbances`**: 定义了仿真过程中的计划性扰动。
  - `time_step`: 事件发生的仿真步。
  - `component_id`: 要操作的组件ID。
  - `action`: 要执行的方法名（例如`set_opening`）。
  - `value`: 传递给该方法的值。

## 4. 如何运行

可以直接通过Python运行本目录下的`run_simulation.py`脚本：

```bash
python examples/branched_network/run_simulation.py
```

脚本会自动加载同目录下的`config.json`文件，执行仿真，并在结束后于同目录下生成一个`output.json`文件，其中包含了详细的仿真结果数据。
