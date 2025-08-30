# 结构化控制智能体示例

本示例演示了如何使用 `StructuredControlAgent`，这是一个能够根据预定义的“控制模式”自动管理其观测目标的智能体。

## 系统描述

本示例中的模拟系统与 `canal_pid_control` 示例的系统相同，包含：
- 一个 `upstream_reservoir`
- 两个 `gates` (`gate_1`, `gate_2`)
- 两个 `canal reaches` (`canal_1`, `canal_2`)

连接方式如下：
`水库 -> 闸门1 -> 渠道1 -> 闸门2 -> 渠道2`

## 核心功能：`StructuredControlAgent`

与之前的示例不同，我们不再手动为每个智能体配置其`observation_topic`。取而代之的是，我们使用 `StructuredControlAgent` 并为其提供一个 `control_mode`。

- **`control_mode: 'dd'` (Distant Downstream)**: 智能体将自动观测其所控制的闸门 **下游** 的渠段水位。
- **`control_mode: 'lu'` (Local Upstream)**: 智能体将自动观测其所控制的闸门 **上游** 的渠段水位。

这种方法将控制逻辑封装在智能体内部，使得系统配置（`agents.yml`）更简洁、更具语义化，并减少了出错的可能性。

## 如何运行示例

要运行此模拟，请从代码库的根目录执行以下命令：

```bash
python run_scenario.py examples/canal_model/structured_control_example/
```

该命令将使用根目录的通用场景运行器来加载并执行此示例的配置。

## 预期结果

模拟运行后，将在 `examples/canal_model/structured_control_example/` 目录下生成一个 `output.yml` 文件。该文件包含了模拟过程中所有组件在每个时间步长的状态历史。您可以检查此文件以验证模拟是否按预期运行。
