# 教程 6：集中式紧急防洪调度

本教程展示如何通过中央调度智能体在出现洪水风险时覆盖本地闸门控制，迅速将水库恢复到安全范围。场景在统一的消息总线下运行，所有组件都可以通过脚本、传统配置、统一配置以及通用配置四种方式复现实验，并通过自动评分验证达到满分（1.000）。

## 1. 问题描述
- 上游水库持续受到 200 m³/s 的入流，初始水位为 98.0 m。
- 下游泄洪闸在常规状态保持 12% 的开度，为灌溉提供稳定出流。
- 当水位超过 99.1 m 时存在漫顶风险，需要中央调度立即强制全开闸门。
- 控制目标是在 220 s 内完成应急动作，并将最终水位稳定在 99.0 ± 0.1 m，同时限制峰值水位不超过 99.2 m。

## 2. 建模与情景配置
- **物理组件**：
  - `main_reservoir`：储量-水位关系由双点曲线描述，持续接受恒定入流。
  - `flood_gate`：宽度 6 m、流量系数 0.78 的溢洪闸，最大开度 1.0，最大开度变化率 0.3 m/s。
- **通信拓扑**：水库连接至闸门，闸门执行动作时会自动订阅 `action/gate/flood` 主题。
- **消息总线主题**：
  - `state/reservoir/main`：数字孪生发布水位观测。
  - `action/gate/flood`：本地控制智能体和中央调度向闸门发送开度指令。
  - `command/gate/flood`：中央调度发布高优先级命令，LocalControlAgent 直接跟随。

## 3. 控制策略与智能体
- **Reservoir Twin**：实时将水位推送到消息总线，供所有决策者订阅。
- **LocalControlAgent + DirectGateController**：
  - 正常情况下保持 0.12 的闸门开度，维持灌溉供水。
  - 当收到中央调度命令时立即跟随新的设定值，确保指令可覆盖本地控制。
- **CentralDispatcherAgent（规则模式）**：
  - 监控水位并根据 98.9/99.1 m 的双阈值逻辑切换设定值。
  - 水位高于 99.1 m 时发布 1.0 的开度命令，水位回落至 98.9 m 以下时恢复 0.12 的常规开度。

## 4. 仿真结果与性能评价
运行 600 s 后的关键指标：

| 指标 | 数值 |
| --- | --- |
| 峰值水位 | 99.11 m |
| 最终水位 | 99.03 m |
| 紧急指令触发时间 | 207 s |
| 控制性能评分 | 1.000 |

评分规则与 `config.yml`/`unified_config.yml` 中的 `analysis` 或 `validation` 配置一致：
1. 最终水位需落在 99.0 ± 0.1 m；
2. 紧急命令必须在 220 s 之前触发；
3. 峰值水位不可超过 99.2 m。

所有运行模式均通过 `run_config.py` 自动生成的 `centralized_emergency_override_report.md` 报告验证满分。

## 5. 讨论与改进建议
- 通过 DirectGateController，中央调度可以直接操纵闸门，避免了传统 PID 设定点更新带来的延迟，非常适合于需要立即执行的应急响应。
- 若要进一步降低峰值水位，可以：
  - 将阈值调至更保守的 98.8/99.0 m 组合；
  - 提高闸门最大开度变化率，使全开动作更迅速；
  - 在常规阶段采用自适应反馈控制，让水位更接近 99.0 m 附近运行。
- 场景配置完全依赖公共组件与消息总线，其他示例（例如层级控制、分布式调度）可直接复用相同的控制器装配方式。

## 6. 运行方式
| 模式 | 命令 |
| --- | --- |
| 直接脚本 | `python examples/agent_based/06_centralized_emergency_override/run_emergency_override_simulation.py` |
| 传统多文件配置 | `python examples/agent_based/06_centralized_emergency_override/run_config.py` |
| 统一配置 | `python examples/run_unified_scenario.py --example agent_based_06_centralized_emergency_override` |
| 通用配置 | `python examples/run_universal_config.py --example agent_based_06_centralized_emergency_override` |

运行任一模式都会输出关键指标，并在传统配置模式下生成带评分的 Markdown 验证报告。
