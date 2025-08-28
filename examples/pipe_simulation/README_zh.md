# 案例说明：管道输水系统仿真

## 1. 案例概述

本案例模拟了一个通过压力管道连接的输水系统。该系统由一个上游水库（Reservoir）、一段有压管道（Pipe）和一个下游的控制闸门（Gate）组成。

这个案例的主要目的是：
- 演示如何使用`SimulationHarness`仿真器来运行一个基于状态的物理模型。
- 展示如何配置包含`Reservoir`、`Pipe`和`Gate`等不同类型物理组件的系统。
- 作为后续包含有压管道和压力控制的复杂案例的基础。

## 2. 拓扑结构

系统的拓扑结构如下，代表水从水库流出，经过管道，最终由闸门控制出流：

`Reservoir -> Pipe -> Gate`

- **Reservoir**: 上游水源，拥有较大的初始蓄水量。
- **Pipe**: 连接水库和闸门的有压管道，其水流由达西-韦斯巴赫方程（Darcy-Weisbach equation）计算。
- **Gate**: 位于管道末端的控制闸门，其开度决定了系统的最终出流量。

## 3. 配置文件 (`config.json`) 说明

所有与本案例相关的配置都存储在`config.json`文件中。

- **`metadata`**: 包含案例的名称和描述。
- **`simulation_settings`**: 定义仿真的基本参数，如仿真时长 (`duration`) 和时间步长 (`dt`)。
- **`components`**: 定义了构成水网的所有物理组件。
  - 每个组件都有唯一的 `id` 和 `type`。
  - `type` 必须与`run_simulation.py`中`COMPONENT_CLASS_MAP`字典里的键名相匹配。
  - `initial_state` 字段定义了组件在仿真开始时的初始状态变量（如水库的初始水位、闸门的初始开度）。
  - `params` 字段包含了初始化该物理组件所需的物理参数（如管道的长度、直径等）。
- **`connections`**: 定义了组件之间的连接关系，通过`from`和`to`字段指定上下游`id`。

## 4. 如何运行

可以直接通过Python运行本目录下的`run_simulation.py`脚本：

```bash
python examples/pipe_simulation/run_simulation.py
```

脚本会自动加载同目录下的`config.json`文件，执行仿真，并在结束后于同目录下生成一个`output.json`文件。`output.json`以时间步为单位，记录了每个组件在仿真过程中所有状态变量的历史数据。
