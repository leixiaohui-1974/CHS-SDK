# 示例 1.3：泵站多机组协同控制（全面修订版）

## 1. 问题描述
在中大型供水或灌溉系统中，泵站通常由多台容量相同的水泵并联组成。运营者需要根据用水需求的阶跃变化灵活启停泵机组，以保障出流满足目标，同时避免频繁动作造成的能耗和机械磨损。本示例通过一个 3 机组泵站的离散动作控制任务，展示消息总线驱动的多智能体协同调度流程，并对跟踪性能、能效与鲁棒性进行量化验证。

## 2. 建模与情景分析
- **物理模型**：
  - 上游水库维持 11.5 m 的水位，并持续提供 32 m³/s 的入流；
  - 下游水库位于 24 m 的高程，模拟扬水工况；
  - 泵站包含 3 台额定流量 12.5 m³/s、额定扬程 22 m 的离散泵机组，开机即输出额定流量。
- **需求情景**：仿真 720 s，需求流量在 0、200、380、520 s 四个节点阶跃至 12.5 → 25.0 → 37.5 → 12.5 m³/s，代表常见的早高峰-平峰切换。
- **控制策略**：
  1. `DemandAgent` 根据预设时间表向主题 `demand.pump.flow` 发布需求；
  2. `PumpControlAgent` 监听需求并按离散泵数上取整启停机组，输出控制信号到 `action.pump.*`；
  3. 可选 `MonitoringAgent` 定期抓取三大组件的运行状态，用于运行后分析。
- **性能指标**：采用分段平均流量误差评价，并设置 0.25 m³/s 的稳态容差。所有运行模式都以“分段平均误差 ≤ 0.25 m³/s 且总评分=1.0”为合格标准。

## 3. 仿真流程与结果
| 运行模式 | 命令 | 说明 |
| --- | --- | --- |
| 传统脚本 | `python run_pump_station_simulation.py` | 手工装配物理组件与智能体，逐步展示消息交互细节。 |
| Builder 重构版 | `python run_pump_station_simulation_refactored.py` | 使用 `SimulationBuilder` 快速搭建系统并附加监控智能体。 |
| 通用智能体版 | `python run_pump_station_with_common_agents.py` | 结合复用型 `DemandAgent`/`MonitoringAgent` 展示最简胶水代码。 |
| 配置驱动版 | `python run_config.py` | 从 `config.yml` 读取参数，执行仿真、评分与报告生成。 |
| 统一配置 | `python ../../run_unified_scenario.py --example agent_based_08_pump_station_control` | 单文件 `unified_config.yml`，与示例总入口联动。 |
| 通用配置 | `python ../../run_universal_config.py --example agent_based_08_pump_station_control` | `universal_config.yml` 适配通用运行器与可视化、验证管线。 |

### 主要结果
所有模式均在 720 s 的仿真中稳定达到目标流量，分段平均误差均低于 0.05 m³/s，综合评分 1.000。`run_config.py` 会自动生成 `pump_station_report.md`（默认禁用图表，可在 `config.yml` 中开启）。下表给出典型段落的跟踪表现：

| 时间段 (s) | 目标流量 (m³/s) | 平均流量 (m³/s) | 绝对误差 (m³/s) |
| --- | --- | --- | --- |
| 0–200 | 12.50 | 12.50 | 0.00 |
| 200–380 | 25.00 | 25.00 | 0.00 |
| 380–520 | 37.50 | 37.50 | 0.00 |
| 520–720 | 12.50 | 12.50 | 0.00 |

## 4. 讨论与建议
- **控制策略**：阶跃需求采用离散机组上取整即可精确满足目标；若存在能效或磨损优化需求，可进一步引入基于成本的调度策略或连续调速泵。
- **需求不确定性**：示例使用确定性时间表，可扩展为外部预测或实时数据驱动；若存在预测误差，可通过增量调度或容差带策略提升鲁棒性。
- **能耗评估**：`MonitoringAgent` 记录的 `total_power_draw_kw` 可用于事后计算能耗；在实际工程中还需考虑泵效率曲线与电价模型。
- **配置通用性**：核心库已扩展以支持 `PumpStation` 及通用 `DemandAgent`/`MonitoringAgent` 的自动装配，确保其他示例加载泵站时也能直接复用。

## 5. 验证与扩展
1. 修改 `config.yml` 的 `analysis.tolerance` 或 `segments` 可快速重设评分标准；
2. 通过 `visualization.enabled: true` 可生成 `08_pump_station_results.png` 对比需求与实际出流；
3. `components.yml` / `agents.yml` / `universal_config.yml` 提供与 YAML Loader、统一运行器兼容的描述，可直接被 `run_unified_scenario.py`、`run_universal_config.py` 调用。

完成上述脚本后，确保运行日志显示“`Simulation complete with a perfect tracking score.`”或“评分：1.000”，即可确认泵站协同控制示例通过验证。
