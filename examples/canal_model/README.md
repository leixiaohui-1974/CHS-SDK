# 渠池模型与控制示例

本目录包含与渠池（Canal）的水力学建模和自动控制相关的示例。

## 示例列表

1.  **[渠池模型比较 (`canal_model_comparison`)](./canal_model_comparison/README.md)**
    -   **目的**: 演示并比较四种不同的渠池简化数学模型。
    -   **内容**: 通过观察不同模型对上游闸门阶跃变化的响应，来理解积分模型、积分-时滞模型、积分-时滞-零点模型和线性水库模型之间的差异。
    -   **核心类**: `UnifiedCanal`

2.  **[PID 控制策略比较 (`canal_pid_control`)](./canal_pid_control/README.md)**
    -   **目的**: 演示并比较三种不同的PID控制策略在一个三段串联渠池系统中的性能。
    -   **内容**: 对比本地上游控制、远程下游控制和混合控制在水位调节任务中的稳定性、响应速度和鲁棒性。
    -   **核心类**: `UnifiedCanal`, `LocalControlAgent`, `PIDController`

## 如何运行

请分别进入每个子目录，并参考其内部的 `README.md` 文件来运行各个示例。
