# 教程 4：分层控制多智能体系统示例

本示例构建了一个具有监督层和执行层的分层控制系统，用于调节水库—闸门组合的水位。高层 `CentralDispatcherAgent` 根据库水位动态调整目标设定点，低层 `LocalControlAgent` 则通过 PID 控制器调节闸门开度完成具体执行。该示例在四种运行模式下均实现满分性能验证，并生成完整的分析报告与可视化结果。

## 问题描述
- **目标**：在来水扰动极小的工况下，将初始 19.0 m 的库水位安全地拉回 15.0 m 的目标水位，并保持在调度允许范围内。
- **挑战**：
  - 单闸门在最大开度受限情况下需要快速泄量，避免长时间超限。
  - 控制器必须根据调度命令自动切换设定点，以兼顾防洪安全与蓄水需求。
  - 验证过程需输出准确、合理且可复现的性能评分。

## 建模与情景分析原理
### 物理建模
- **水库**：水面面积 8.0×10⁴ m²，初始库容 1.52×10⁶ m³，采用分段库容曲线刻画水位-库容关系。
- **闸门**：最大开度 5 m、宽度 12 m，泄流系数 0.75，并设置 0.75 m/s 的最大开度变化率，保证执行器动态可实现。

### 控制层级
1. **执行层（LocalControlAgent + PIDController）**
   - 观测水库水位 `state.reservoir.level`，输出闸门动作到 `action.gate.opening`。
   - PID 参数：Kp = -0.8，Ki = -0.1，Kd = -0.2，输出范围 [0, 5] m，对应闸门几何开度。
2. **监督层（CentralDispatcherAgent）**
   - 监视同一水位主题，当水位高于 18 m 时发布 12 m 的紧急设定点，低于 12 m 时恢复到 15 m 常规设定点。
   - 通过 `command.gate1.setpoint` 将设定点下发给执行层。
3. **数字孪生代理**：为水库和闸门分别创建 `DigitalTwinAgent`，负责同步物理状态到消息总线。

### 情景分析
- 使用 `SimulationHarness` 以 1 s 时间步运行 500 s，保障泄量充足且数值稳定。
- 通过多种运行方式（脚本、Builder、YAML 配置、统一运行器）验证参数对不同入口的一致性。
- 自动化分析计算稳态误差、水位/闸门运行范围，并生成 Markdown 报告和图形。

## 结果分析
- 所有运行模式下最终水位稳定在 **14.97–14.98 m**，稳态误差 **≤ 0.03 m**，小于 0.1 m 的容差，评价得分 **1.0/1.0**。
- 闸门在前期快速打开至 5 m，实现高效泄流；当水位降至 15 m 附近后逐步关闭，避免过度泄放。
- 自动化报告 `hierarchical_control_report.md` 与图像 `04_hierarchical_results.png` 展示了水位回落过程、闸门调节轨迹及库容演化，验证结果准确且与物理预期一致。

## 讨论与建议
- 监督层采用滞回规则（12 m/18 m）能够防止频繁切换设定点，建议在真实工程中结合实时来水预报进一步优化阈值。
- PID 参数针对该库容与闸门几何量标定，若扩展到多闸或不同库容，应重新计算控制器增益并保持消息总线主题命名规范。
- 若需要考虑来水或多执行器，可在配置文件中扩展数据源、目标主题和调度规则，核心代码无需修改。

## 运行方式（四种验证入口）
1. **硬编码脚本**：`python examples/agent_based/04_hierarchical_control/run_hierarchical_simulation.py`
2. **SimulationBuilder 构建**：`python examples/agent_based/04_hierarchical_control/run_hierarchical_simulation_refactored.py`
3. **YAML 配置驱动**：`python examples/agent_based/04_hierarchical_control/run_config.py`
4. **统一运行器**：
   - `python examples/run_unified_scenario.py --example agent_based_04_hierarchical_control`
   - `python examples/run_universal_config.py --example agent_based_04_hierarchical_control`

运行配置脚本会自动生成验证报告和图像，同时在终端输出满分评分与关键统计指标。

## 生成的关键文件
- `config.yml` / `unified_config.yml` / `universal_config.yml`：分别用于传统、多入口和统一配置运行。
- `hierarchical_control_report.md`：仿真结果与性能验证报告。
- `04_hierarchical_results.png`：水位、开度与库容的情景可视化。
- `run_config.py`：统一的自动化构建、运行、分析脚本。

通过上述结构，示例在保持核心库通用性的同时，确保所有运行模式的一致性与验证结果的准确性，可直接作为后续复杂分层调度场景的模板。
