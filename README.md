# 智能水务平台 (SWP) - 数字孪生与多代理系统框架

本代码库包含一个前瞻性的“智慧水务系统数字孪生与协同控制平台”的基础框架。该项目被构想为一个“母体机器”——一个用于模拟、生成、测试和管理复杂水务系统的元平台，其核心采用了多代理系统（MAS）的方法。

## 核心架构

SWP 建立在一个分层的、模块化的架构之上，其设计灵感来源于 Simulink 的模块化建模思想。每个组件都被设计为可独立开发、测试和组合的模块。

- **核心库 (`swp`)**: 包含平台的所有核心逻辑，包括物理模型、智能体、控制器和调度算法。
- **示例 (`examples`)**: 提供了一系列配置驱动的示例，用于演示平台的功能。
- **运行器 (`examples/run_*.py`)**: 通用的脚本，用于执行配置好的仿真和任务。

## 示例：一个分层的、配置驱动的框架

本项目中的示例经过精心设计，以实现**关注点分离**，使得用户可以专注于业务逻辑，而不是代码实现。

### 1. 配置文件

每个复杂示例都由一组JSON文件定义：
- **`*_sim.json`**: **系统定义文件**。描述了仿真的核心，包括物理组件、拓扑连接、控制智能体和它们的静态参数。
- **`*_disturbances.json`**: **场景定义文件**。描述了系统在该次仿真中所经历的外部事件和扰动，例如洪水、用户取水、设备故障等。
- **`*_plots.json`**: **可视化配置文件**。定义了仿真结束后需要生成的图表的样式和内容。

### 2. 通用运行器

我们提供了一系列通用的Python脚本来解析这些配置文件并执行相应的任务：
- **`run_simulation.py`**: 主仿真运行器。它读取 `_sim.json` 和 `_disturbances.json` 文件，构建并运行一个完整的仿真，最终生成一个标准的 `history.csv` 数据文件。
- **`visualize_results.py`**: 通用可视化脚本。它读取 `history.csv` 和 `_plots.json` 文件，生成标准化的图表。
- **`run_table_computation.py`**: 用于执行数据生成任务，例如计算水轮机或闸门的优化调度表。

### 3. Jupyter Notebook 教程

为了获得最佳的交互式体验，我们推荐使用 `examples/main_tutorial_zh.ipynb`。这个Notebook将引导您完成：
1.  运行一个复杂的仿真。
2.  生成标准化的可视化结果。
3.  加载结果数据进行自定义的业务逻辑分析。

## 如何运行一个示例

以 **分层控制示例 (Hierarchical Control)** 为例：

**1. 运行仿真**
```bash
# 这将读取 mission_2_2_sim.json 和 mission_2_2_disturbances.json,
# 运行仿真并将结果（history.csv, plots.json）保存到 output/mission_2_2/
python3 examples/run_simulation.py examples/mission_2_2_sim.json
```

**2. 生成可视化图表**
```bash
# 这将读取 output/mission_2_2/ 中的 history.csv 和 plots.json,
# 并生成一个 results.png 图表文件。
python3 examples/visualize_results.py output/mission_2_2/
```
