# 案例一：基础水箱仿真（场景驱动版）

## 1. 案例目标

本案例旨在演示一个基础的水箱物理仿真过程。与其它示例不同，本案例已被重构为**场景驱动模式**，这是本平台推荐的标准实现方式。

其核心思想是将系统的**定义**（在YAML配置文件中）与**执行**（由`run_scenario.py`统一处理）完全分离。

## 2. 架构与原理

本仿真由项目根目录的 `run_scenario.py` 脚本启动。该脚本会加载本目录下的`*.yml`配置文件，并利用`SimulationHarness`（仿真平台）来执行仿真：

1.  **加载组件**: `components.yml`中定义的`Reservoir`（水箱）被创建。
2.  **加载智能体**: `agents.yml`中定义的`CsvInflowAgent`被创建。这个智能体的作用是从`data/inflow.csv`文件中读取数据。
3.  **运行**: `SimulationHarness`开始运行。
    - 在每个时间步，`CsvInflowAgent`会读取当前时间的入流值，并将其发布到消息总线。
    - `Reservoir`对象（在`components.yml`中已配置好监听相应主题）接收到这个入流值。
    - `SimulationHarness`调用`Reservoir`的`.step()`方法，根据入流计算其内部状态（水量、水位）的变化。
    - 由于没有下游组件，水箱的出流量为0。

## 3. 文件结构

- `config.yml`: 定义仿真的全局参数，如总时长和时间步。
- `components.yml`: 定义物理组件，这里只有一个`Reservoir`。
- `topology.yml`: 定义组件连接，这里为空。
- `agents.yml`: 定义智能体，这里只有一个`CsvInflowAgent`，负责从CSV文件读取数据并驱动仿真。
- `data/inflow.csv`: 存放驱动仿真所用的入流数据。
- `README.md`: 本说明文档。
- `output.yml`: (运行后生成) 保存详细的仿真结果历史记录。

## 4. 如何运行

确保您位于项目的根目录。然后执行以下命令：

```bash
python run_scenario.py examples/watertank/01_simulation
```

仿真结束后，您可以在本目录下的 `output.yml` 文件中查看详细的逐时步仿真结果。
