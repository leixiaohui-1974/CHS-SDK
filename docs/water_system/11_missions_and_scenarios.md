# 11. 任务与场景 (Missions & Scenarios)

本篇文档是之前所有文档的实践应用篇。它将详细介绍如何通过**配置文件**来定义和运行一个完整的、包含物理模型和智能体的仿真任务。

## 1. 核心理念：声明式的场景定义

`core_lib` 的一个核心优势在于，它将**仿真场景的定义**与**框架的源代码**完全分离。用户无需编写Python代码，只需通过一组声明式的 **YAML 文件**，就可以描述一个完整的、复杂的仿真世界。

一个典型的场景由以下四个核心YAML文件构成：

1.  **`components.yml`**: 定义“有什么？” - 系统中的所有物理组件。
2.  **`topology.yml`**: 定义“在哪里？” - 这些物理组件如何连接。
3.  **`agents.yml`**: 定义“谁来思考和行动？” - 系统中的所有智能体及其配置。
4.  **`config.yml`**: 定义“世界如何运转？” - 仿真的基本参数（如时长、步长）。

## 2. `SimulationLoader`：从文件到世界的“创世引擎”

*   **位置**: `core_lib/io/yaml_loader.py`
*   **职责**: `SimulationLoader` 类是这一切的起点。它的核心功能是解析上述的YAML文件，并将其中描述的文本定义，**实例化**为Python世界中真实的对象。

其 `load()` 方法的执行流程（即“调用原理”）如下：

1.  **初始化基础设施**: 创建 `MessageBus` 和 `SimulationHarness` 的实例。
2.  **实例化物理组件**: 读取 `components.yml`，并根据其中每个条目的 `class` 字段，动态地从 `core_lib.physical_objects` 中找到对应的Python类（如`Reservoir`, `Gate`），并用 `initial_state` 和 `parameters` 来创建它的实例。所有创建的实例都被添加到 `SimulationHarness` 中。
3.  **构建拓扑**: 读取 `topology.yml`，并调用 `harness.add_connection()` 方法，在实例化的组件之间建立连接关系。
4.  **实例化智能体**: 读取 `agents.yml`，同样地，根据 `class` 字段动态创建每个智能体的实例。在创建过程中，它会将 `MessageBus` 的实例和在第2步中创建的相关物理组件的实例，作为参数传递给智能体的构造函数，从而完成“依赖注入”和“接线”(Wiring)。
5.  **构建Harness**: 所有对象都实例化并连接好之后，调用 `harness.build()`。
6.  **返回**: `load()` 方法最终返回一个完全配置好的、随时可以运行的 `SimulationHarness` 实例。

## 3. YAML 文件格式详解

### `components.yml`
定义一个组件列表。每个组件包含：
*   `id`: 唯一的字符串ID。
*   `class`: `core_lib.physical_objects` 中对应的类名。
*   `initial_state`: 包含初始状态变量的字典。
*   `parameters`: 包含模型物理参数的字典。

```yaml
# components.yml 示例
components:
  - id: main_reservoir
    class: Reservoir
    initial_state: { water_level: 98.0 }
    parameters: { area: 1000.0 }
  - id: flood_gate
    class: Gate
    initial_state: { opening: 0.1 }
    parameters: { width: 5.0 }
```

### `topology.yml`
定义一个连接列表。每个连接包含：
*   `upstream`: 上游组件的`id`。
*   `downstream`: 下游组件的`id`。

```yaml
# topology.yml 示例
connections:
  - upstream: main_reservoir
    downstream: flood_gate
```

### `agents.yml`
定义一个智能体列表。每个智能体包含：
*   `id`: 唯一的字符串ID。
*   `class`: `core_lib` 中对应的智能体类名。
*   `config`: 传递给该智能体构造函数的配置字典，用于定义其行为（如订阅/发布的主题、控制参数等）。

```yaml
# agents.yml 示例
agents:
  - id: reservoir_twin
    class: DigitalTwinAgent
    config:
      simulated_object_id: main_reservoir
      state_topic: "state/reservoir/main"
  - id: central_dispatcher
    class: CentralDispatcherAgent
    config:
      subscribed_topic: "state/reservoir/main"
      command_topic: "command/gate/flood"
      # ... more params
```

## 4. `ScenarioAgent`：在仿真中注入动态事件

*   **位置**: `core_lib/mission/scenario_agent.py`
*   **职责**: `ScenarioAgent` 本身也是一个可以被定义在 `agents.yml` 中的智能体。但它的功能很特殊：它允许用户在一个正在运行的仿真中，于**指定的时间点**，向**指定的主题**，发布**指定的消息**。
*   **用途**: 这是实现“任务(Mission)”或“场景”的关键。它常被用于：
    *   **注入扰动**: 在`t=3600s`时，向`topic_rainfall_intensity`发布一个大的降雨值，以模拟暴雨。
    *   **模拟故障**: 在`t=7200s`时，向`topic_pump_A_status`发布`{"status": "failed"}`，以测试系统的应急响应。
    *   **执行操作序列**: 模拟一套预定义的人工操作流程。

通过这套机制，`core_lib` 实现了一个高度灵活、可配置、可复现的仿真与测试框架。
