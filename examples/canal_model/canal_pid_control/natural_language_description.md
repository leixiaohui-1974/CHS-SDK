# 水利系统配置自然语言描述

## 系统概述
- 系统名称：canal_pid_control - 统一配置
- 系统描述：用于比较渠道系统中两种典型 PID 策略的简化模型
- 系统版本：1.0
- 系统类别：canal_model

## 主要组件
1. **上游水库（upstream_reservoir）**
   - 初始水位：10.0 m
   - 等效水面面积：10 000 m²
   - 稳定来水：18 m³/s

2. **闸门 1（gate_1）**
   - 初始开度：0.50
  - 线性化最大过水能力：36 m³/s
   - 作用：调节水库向渠道 1 的供水量

3. **渠道 1（canal_1）**
   - 初始水位：5.0 m
   - 等效蓄水面积：5 500 m²
   - 控制目标：维持 5.0 m 水位

4. **闸门 2（gate_2）**
   - 初始开度：0.50
   - 线性化最大过水能力：36 m³/s
   - 作用：保障尾水池及下游用户供水

5. **渠道 2（canal_2）**
   - 初始水位：4.5 m
   - 等效蓄水面积：4 800 m²
   - 控制目标：维持 4.5 m 水位，下游恒定需求 18 m³/s

## 拓扑关系
1. upstream_reservoir → gate_1
2. gate_1 → canal_1
3. canal_1 → gate_2
4. gate_2 → canal_2 → 下游需求

## 仿真配置
- 总时长：7 200 s（2 小时）
- 时间步长：10 s
- 运行脚本：`python examples/canal_model/canal_pid_control/run_pid_comparison.py`
- 输出：
  - `results_local_upstream.csv`
  - `results_distant_downstream.csv`
  - 控制性能汇总表（终端打印）

## 摘要
该配置以线性化的闸门能力与水量平衡方程描述渠道系统。脚本可快速验证不同 PID 策略对干渠与尾水池水位的调控能力，为后续引入更复杂的控制算法提供基准数据。
