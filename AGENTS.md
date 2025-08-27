# 智能水务平台 Agent 开发指南

本文档为在此代码库上工作的AI代理提供了说明和约定。主要目标是维护初始设计中建立的模块化、可扩展和健壮的架构。

## 1. 核心架构原则

- **模块化至上 (Modularity is Paramount)**: 每一个新功能，无论是仿真模型、控制算法还是数据处理工具，都应被设计为一个自包含的模块。
- **遵守接口 (Adhere to Interfaces)**: 所有主要组件**必须**继承自 `swp/core/interfaces.py` 中定义的相应抽象基类。这是不可协商的，因为它确保了系统的“可插拔”特性。
  - `Simulatable`: 用于所有动态模型（物理或逻辑）。
  - `Controller`: 用于所有控制算法。
  - `Agent`: 用于所有自治代理。
- **解耦组件 (Decouple Components)**: 组件之间不应有硬编码的依赖关系。交互应通过 `SimulationHarness` (用于仿真时耦合) 或 `MessageBus` (用于代理间通信) 进行协调。避免在非设计紧密耦合的组件之间直接进行方法调用。
- **配置驱动 (Configuration-Driven)**: 不要硬编码参数或系统结构。`AgentFactory` (`swp/core_engine/agent_factory/factory.py`) 被设计为从配置字典中构建系统。在添加新组件时，请扩展该工厂以支持它们。

## 2. 如何添加新组件

### 添加新的物理模型 (例如，管道 Pipe)

1.  **创建类文件**: `swp/simulation_identification/physical_objects/pipe.py`。
2.  **实现 `Simulatable` 接口**:
    ```python
    from swp.core.interfaces import Simulatable, State, Parameters

    class Pipe(Simulatable):
        # ... 实现所有抽象方法: step, get_state, set_state, get_parameters
    ```
3.  **扩展 `AgentFactory`**: 修改 `swp/core_engine/agent_factory/factory.py` 以识别并从配置块中构建 `Pipe` 模型。
4.  **编写单元测试**: 在新的 `tests/` 目录中创建一个测试文件 (例如, `tests/simulation/test_pipe.py`)，以在隔离环境中验证模型的行为。
5.  **更新文档**: 将 `Pipe` 模型添加到 `README.md` 和任何相关的教程文档中。

### 添加新的控制算法 (例如，模型预测控制 MPC)

1.  **创建类文件**: `swp/local_agents/control/mpc_controller.py`。
2.  **实现 `Controller` 接口**:
    ```python
    from swp.core.interfaces import Controller, State

    class MPCController(Controller):
        # ... 实现 compute_control_action
    ```
3.  **扩展 `AgentFactory`**: 更新工厂以支持从配置块中创建 `MPCController`。
4.  **更新 `SimulationHarness` (如果需要)**: 可能需要更新平台以提供MPC控制器所需的更复杂的状态预测。
5.  **创建示例**: 添加一个新的示例脚本或扩展现有脚本，以展示如何使用 `MPCController`。

## 3. 测试与验证

- **运行示例**: 在提交任何更改之前，始终运行 `example_simulation.py` 脚本，以确保您没有破坏核心集成。
  ```bash
  python3 example_simulation.py
  ```
- **添加测试**: 对于任何新功能，添加相应的单元测试。目标是构建一个可以自动运行的全面测试套件。

通过遵循这些指南，我们可以确保平台以一种结构化和可维护的方式发展，实现其作为智能水务系统真正的“母体机器”的愿景。
