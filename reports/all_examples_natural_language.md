# CHS-SDK 所有示例配置文件的自然语言描述

生成时间: 2025-09-04 16:10:53

本报告包含了 128 个成功转换的配置文件的自然语言描述。

## 目录

1. [universal_config](#universal-config)
2. [简单水库系统_traditional](#简单水库系统-traditional)
3. [03_watershed_coordination](#03-watershed-coordination)
4. [unified_config](#unified-config)
5. [06_sensor_disturbance](#06-sensor-disturbance)
6. [universal_config](#universal-config)
7. [01_basic_simulation](#01-basic-simulation)
8. [03_economic_dispatch](#03-economic-dispatch)
9. [unified_config](#unified-config)
10. [mission_example_1](#mission-example-1)
11. [universal_config](#universal-config)
12. [universal_config](#universal-config)
13. [universal_config](#universal-config)
14. [universal_config](#universal-config)
15. [03_pipe_roughness](#03-pipe-roughness)
16. [unified_config](#unified-config)
17. [universal_config](#universal-config)
18. [universal_config](#universal-config)
19. [02_gate_discharge_coefficient](#02-gate-discharge-coefficient)
20. [01_simulation](#01-simulation)
21. [universal_config](#universal-config)
22. [universal_config](#universal-config)
23. [universal_config](#universal-config)
24. [universal_config](#universal-config)
25. [01_getting_started](#01-getting-started)
26. [09_agent_based_distributed_control](#09-agent-based-distributed-control)
27. [unified_config](#unified-config)
28. [unified_config](#unified-config)
29. [多组件水利系统_traditional](#多组件水利系统-traditional)
30. [unified_config](#unified-config)
31. [universal_config](#universal-config)
32. [unified_config](#unified-config)
33. [universal_config](#universal-config)
34. [unified_config](#unified-config)
35. [unified_config](#unified-config)
36. [01_reservoir_storage_curve](#01-reservoir-storage-curve)
37. [unified_config](#unified-config)
38. [universal_config](#universal-config)
39. [unified_config](#unified-config)
40. [universal_config](#universal-config)
41. [structured_control_example](#structured-control-example)
42. [10_canal_system](#10-canal-system)
43. [canal_model_comparison](#canal-model-comparison)
44. [03_pid_control_inlet](#03-pid-control-inlet)
45. [universal_config](#universal-config)
46. [universal_config](#universal-config)
47. [universal_config](#universal-config)
48. [universal_config](#universal-config)
49. [universal_config](#universal-config)
50. [unified_config](#unified-config)
51. [complex_fault_scenario_example](#complex-fault-scenario-example)
52. [universal_config](#universal-config)
53. [universal_config](#universal-config)
54. [universal_config](#universal-config)
55. [unified_config](#unified-config)
56. [02_advanced_control](#02-advanced-control)
57. [03_fault_tolerance](#03-fault-tolerance)
58. [canal_mpc_pid_control](#canal-mpc-pid-control)
59. [universal_config](#universal-config)
60. [simplified_reservoir_control](#simplified-reservoir-control)
61. [universal_config](#universal-config)
62. [unified_config](#unified-config)
63. [01_local_control](#01-local-control)
64. [unified_config](#unified-config)
65. [universal_config](#universal-config)
66. [universal_config](#universal-config)
67. [04_pid_control_outlet](#04-pid-control-outlet)
68. [universal_config](#universal-config)
69. [unified_config](#unified-config)
70. [02_multi_component_systems](#02-multi-component-systems)
71. [universal_config](#universal-config)
72. [unified_config](#unified-config)
73. [02_multi_unit_coordination](#02-multi-unit-coordination)
74. [02_hierarchical_control](#02-hierarchical-control)
75. [unified_config](#unified-config)
76. [unified_config](#unified-config)
77. [unified_config](#unified-config)
78. [unified_config](#unified-config)
79. [unified_config](#unified-config)
80. [universal_config](#universal-config)
81. [universal_config](#universal-config)
82. [universal_config](#universal-config)
83. [01_simple_simulation](#01-simple-simulation)
84. [universal_config](#universal-config)
85. [unified_config](#unified-config)
86. [04_gate_scheduling](#04-gate-scheduling)
87. [universal_config](#universal-config)
88. [universal_config](#universal-config)
89. [universal_config](#universal-config)
90. [unified_config](#unified-config)
91. [universal_config](#universal-config)
92. [universal_config](#universal-config)
93. [unified_config](#unified-config)
94. [universal_config](#universal-config)
95. [universal_config](#universal-config)
96. [universal_config](#universal-config)
97. [universal_config](#universal-config)
98. [universal_config](#universal-config)
99. [universal_config](#universal-config)
100. [unified_config](#unified-config)
101. [universal_config](#universal-config)
102. [hierarchical_distributed_control_example](#hierarchical-distributed-control-example)
103. [unified_config](#unified-config)
104. [universal_config](#universal-config)
105. [unified_config](#unified-config)
106. [universal_config](#universal-config)
107. [unified_config](#unified-config)
108. [unified_config](#unified-config)
109. [04_digital_twin_advanced](#04-digital-twin-advanced)
110. [canal_pid_control](#canal-pid-control)
111. [universal_config](#universal-config)
112. [universal_config](#universal-config)
113. [05_central_mpc_dispatcher](#05-central-mpc-dispatcher)
114. [universal_config](#universal-config)
115. [yinchuojiliao](#yinchuojiliao)
116. [unified_config](#unified-config)
117. [universal_config](#universal-config)
118. [01_turbine_gate_simulation](#01-turbine-gate-simulation)
119. [07_centralized_setpoint_optimization](#07-centralized-setpoint-optimization)
120. [unified_config](#unified-config)
121. [unified_config](#unified-config)
122. [unified_config](#unified-config)
123. [unified_config](#unified-config)
124. [universal_config](#universal-config)
125. [12_pid_control_comparison](#12-pid-control-comparison)
126. [universal_config](#universal-config)
127. [universal_config](#universal-config)
128. [unified_config](#unified-config)

---

## 1. universal_config

**配置路径:** `examples\watertank\01_simulation\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.56

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 2. 简单水库系统_traditional

**配置路径:** `examples\converted\简单水库系统_traditional`

**配置类型:** traditional_multi

**一致性得分:** 0.89

## 总结
配置文件总结：
配置类型：传统多配置文件
配置路径：examples\converted\简单水库系统_traditional
配置描述：传统多配置文件 (4个文件)
推荐运行器：run_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：2个
  - 闸门：1个
  - 传感器：1个

具体组件：
  - 仿真名称：水库
  - 水库1：水库
  - 闸门1：闸门
  - 传感器1：传感器

系统拓扑：包含1个连接关系
具体连接关系：
  1. 水库1 → 闸门1 (flow连接)


## 情景描述
情景描述：


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 3. 03_watershed_coordination

**配置路径:** `examples\mission_example_2\03_watershed_coordination`

**配置类型:** traditional_multi

**一致性得分:** 0.25

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_example_2\03_watershed_coordination
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：3600.0秒
时间步长：5.0秒
求解器：watershed_coordination


调试配置：启用了调试功能，日志级别为INFO

性能监控：启用了性能监控功能

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


可视化配置：启用了可视化功能，包括图表绘制

## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析


高级分析：包含以下分析功能：
  - 控制性能分析
  - 系统辨识



---

## 4. unified_config

**配置路径:** `examples\agent_based\03_event_driven_agents\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.69

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 5. 06_sensor_disturbance

**配置路径:** `examples\watertank_refactored\06_sensor_disturbance`

**配置类型:** traditional_multi

**一致性得分:** 0.38

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\watertank_refactored\06_sensor_disturbance
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
求解器：euler


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 6. universal_config

**配置路径:** `examples\mission_example_5\02_multi_unit_coordination\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 7. 01_basic_simulation

**配置路径:** `examples\mission_example_1\01_basic_simulation`

**配置类型:** traditional_multi

**一致性得分:** 0.12

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_example_1\01_basic_simulation
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：1000.0秒
时间步长：10.0秒
求解器：euler


调试配置：启用了调试功能，日志级别为INFO

性能监控：启用了性能监控功能

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


可视化配置：启用了可视化功能，包括图表绘制

## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析


高级分析：包含以下分析功能：
  - 控制性能分析



---

## 8. 03_economic_dispatch

**配置路径:** `examples\mission_example_5\03_economic_dispatch`

**配置类型:** traditional_multi

**一致性得分:** 0.50

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_example_5\03_economic_dispatch
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：1秒
时间步长：1.0秒
求解器：optimization


调试配置：启用了调试功能，日志级别为INFO

性能监控：启用了性能监控功能

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


可视化配置：启用了可视化功能，包括图表绘制

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析


高级分析：包含以下分析功能：



---

## 9. unified_config

**配置路径:** `examples\notebooks\07_centralized_setpoint_optimization\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.74

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 10. mission_example_1

**配置路径:** `examples\mission_example_1`

**配置类型:** traditional_multi

**一致性得分:** 0.88

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_example_1
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：100.0秒
时间步长：1.0秒
求解器：runge_kutta


调试配置：启用了调试功能，日志级别为INFO

性能监控：启用了性能监控功能

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


可视化配置：启用了可视化功能，包括图表绘制

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析


高级分析：包含以下分析功能：
  - 控制性能分析



---

## 11. universal_config

**配置路径:** `test_output\enhanced_rule_2\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.96

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 12. universal_config

**配置路径:** `examples\mission_example_2\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.38

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 13. universal_config

**配置路径:** `examples\mission_example_5\01_turbine_gate_simulation\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 14. universal_config

**配置路径:** `examples\agent_based\09_agent_based_distributed_control\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.31

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 15. 03_pipe_roughness

**配置路径:** `examples\identification\03_pipe_roughness`

**配置类型:** traditional_multi

**一致性得分:** 0.50

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\identification\03_pipe_roughness
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：20000秒
时间步长：100秒


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 16. unified_config

**配置路径:** `demo_output\round_trip_config\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.92

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 17. universal_config

**配置路径:** `examples\notebooks\10_canal_system\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.59

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 18. universal_config

**配置路径:** `examples\mission_example_1\03_fault_tolerance\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 19. 02_gate_discharge_coefficient

**配置路径:** `examples\identification\02_gate_discharge_coefficient`

**配置类型:** traditional_multi

**一致性得分:** 0.50

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\identification\02_gate_discharge_coefficient
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：20000秒
时间步长：100秒


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 20. 01_simulation

**配置路径:** `examples\watertank\01_simulation`

**配置类型:** traditional_multi

**一致性得分:** 0.88

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\watertank\01_simulation
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：1个

具体组件：
  - tank1：水库

智能体系统：包含1个智能体
具体智能体：
  1. inflow_driver：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：100秒
时间步长：1.0秒


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 21. universal_config

**配置路径:** `examples\mission_example_5\04_gate_scheduling\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 22. universal_config

**配置路径:** `examples\converted\灌区配水系统_universal\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.50

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 23. universal_config

**配置路径:** `demo_output\universal_config_config\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.70

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 24. universal_config

**配置路径:** `examples\mission_example_2\01_local_control\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 25. 01_getting_started

**配置路径:** `examples\non_agent_based\01_getting_started`

**配置类型:** traditional_multi

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\non_agent_based\01_getting_started
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 闸门：1个
  - 水库：1个

具体组件：
  - gate_1：闸门
  - reservoir_1：水库

## 情景描述
情景描述：
仿真时长：300秒
时间步长：1.0秒


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析


高级分析：包含以下分析功能：



---

## 26. 09_agent_based_distributed_control

**配置路径:** `examples\agent_based\09_agent_based_distributed_control`

**配置类型:** traditional_multi

**一致性得分:** 1.00

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\agent_based\09_agent_based_distributed_control
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：1个
  - 闸门：1个

具体组件：
  - target_reservoir：水库
  - control_gate：闸门

智能体系统：包含1个智能体
具体智能体：
  1. reservoir_twin：数字孪生智能体
     - 监控对象：target_reservoir
     - 状态主题：state/reservoir/target


## 情景描述
情景描述：
仿真时长：300秒
时间步长：1.0秒


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 27. unified_config

**配置路径:** `examples\canal_model\hierarchical_distributed_control_example\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.62

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 28. unified_config

**配置路径:** `examples\watertank\01_simulation\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 1.00

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 29. 多组件水利系统_traditional

**配置路径:** `examples\converted\多组件水利系统_traditional`

**配置类型:** traditional_multi

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：传统多配置文件
配置路径：examples\converted\多组件水利系统_traditional
配置描述：传统多配置文件 (4个文件)
推荐运行器：run_scenario.py


## 建模描述
建模描述：


## 情景描述
情景描述：


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 30. unified_config

**配置路径:** `examples\non_agent_based\07_pipe_and_valve\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 1.00

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 31. universal_config

**配置路径:** `examples\canal_model\canal_mpc_pid_control\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.28

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 32. unified_config

**配置路径:** `examples\converted\灌区配水系统_unified\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.67

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 33. universal_config

**配置路径:** `examples\converted\简单水库系统_universal\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.64

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 34. unified_config

**配置路径:** `test_output\round_trip_test\unified_config\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 1.00

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 35. unified_config

**配置路径:** `examples\converted\多组件水利系统_unified\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.92

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 36. 01_reservoir_storage_curve

**配置路径:** `examples\identification\01_reservoir_storage_curve`

**配置类型:** traditional_multi

**一致性得分:** 0.50

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\identification\01_reservoir_storage_curve
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：720000秒
时间步长：3600秒


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 37. unified_config

**配置路径:** `examples\demo\simplified_reservoir_control\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.62

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 38. universal_config

**配置路径:** `examples\mission_example_3\01_enhanced_perception\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 39. unified_config

**配置路径:** `examples\watertank_refactored\06_sensor_disturbance\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 40. universal_config

**配置路径:** `test_output\universal_config\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.67

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 41. structured_control_example

**配置路径:** `examples\canal_model\structured_control_example`

**配置类型:** traditional_multi

**一致性得分:** 0.72

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\canal_model\structured_control_example
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - core_lib.physical_objects.reservoir.Reservoir：1个
  - core_lib.physical_objects.gate.Gate：2个
  - core_lib.physical_objects.unified_canal.UnifiedCanal：2个

具体组件：
  - upstream_reservoir：core_lib.physical_objects.reservoir.Reservoir
  - gate_1：core_lib.physical_objects.gate.Gate
  - canal_1：core_lib.physical_objects.unified_canal.UnifiedCanal
  - canal_2：core_lib.physical_objects.unified_canal.UnifiedCanal
  - gate_2：core_lib.physical_objects.gate.Gate

智能体系统：包含2个智能体
具体智能体：
  1. gate1_dd_controller：core_lib.local_agents.control.structured_control_agent.StructuredControlAgent
  2. gate2_lu_controller：core_lib.local_agents.control.structured_control_agent.StructuredControlAgent


## 情景描述
情景描述：
仿真时长：3600秒
时间步长：10秒


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 42. 10_canal_system

**配置路径:** `examples\notebooks\10_canal_system`

**配置类型:** traditional_multi

**一致性得分:** 0.56

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\notebooks\10_canal_system
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - Lake：1个
  - 渠道：1个
  - 水库：1个
  - RiverChannel：1个

具体组件：
  - lake_1：Lake
  - canal_1：渠道
  - reservoir_1：水库
  - river_1：RiverChannel

智能体系统：包含4个智能体
具体智能体：
  1. lake_inflow：InflowAgent
  2. system_monitor：监控智能体
  3. canal_controller：FlowControlAgent
  4. weather_effects：WeatherAgent


## 情景描述
情景描述：
仿真时长：300秒
时间步长：1.0秒
求解器：runge_kutta


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


可视化配置：启用了可视化功能

## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 43. canal_model_comparison

**配置路径:** `examples\canal_model\canal_model_comparison`

**配置类型:** traditional_multi

**一致性得分:** 0.88

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\canal_model\canal_model_comparison
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：2个
  - 闸门：1个

具体组件：
  - upstream_reservoir：水库
  - gate_1：闸门
  - downstream_reservoir：水库

## 情景描述
情景描述：
仿真时长：3600秒
时间步长：10秒


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 44. 03_pid_control_inlet

**配置路径:** `examples\watertank_refactored\03_pid_control_inlet`

**配置类型:** traditional_multi

**一致性得分:** 0.38

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\watertank_refactored\03_pid_control_inlet
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
求解器：euler


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 45. universal_config

**配置路径:** `examples\watertank_refactored\01_simple_simulation\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 46. universal_config

**配置路径:** `examples\canal_model\structured_control_example\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.19

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 47. universal_config

**配置路径:** `examples\watertank_refactored\02_parameter_identification\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 48. universal_config

**配置路径:** `examples\non_agent_based\08_non_agent_simulation\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.50

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 49. universal_config

**配置路径:** `examples\notebooks\07_centralized_setpoint_optimization\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 50. unified_config

**配置路径:** `examples\watertank_refactored\05_joint_control\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.73

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 51. complex_fault_scenario_example

**配置路径:** `examples\canal_model\complex_fault_scenario_example`

**配置类型:** traditional_multi

**一致性得分:** 0.61

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\canal_model\complex_fault_scenario_example
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - core_lib.physical_objects.reservoir.Reservoir：1个
  - core_lib.physical_objects.disturbance_node.DisturbanceNode：3个
  - core_lib.physical_objects.gate.Gate：2个
  - core_lib.physical_objects.unified_canal.UnifiedCanal：2个

具体组件：
  - upstream_reservoir：core_lib.physical_objects.reservoir.Reservoir
  - turnout_1：core_lib.physical_objects.disturbance_node.DisturbanceNode
  - gate_1：core_lib.physical_objects.gate.Gate
  - canal_1：core_lib.physical_objects.unified_canal.UnifiedCanal
  - turnout_2：core_lib.physical_objects.disturbance_node.DisturbanceNode
  - gate_2：core_lib.physical_objects.gate.Gate
  - canal_2：core_lib.physical_objects.unified_canal.UnifiedCanal
  - terminal_user：core_lib.physical_objects.disturbance_node.DisturbanceNode

智能体系统：包含4个智能体
具体智能体：
  1. physical_io_agent：core_lib.local_agents.io.physical_io_agent.PhysicalIOAgent
  2. scenario_agent：core_lib.mission.scenario_agent.ScenarioAgent
  3. gate1_dd_controller：core_lib.local_agents.control.structured_control_agent.StructuredControlAgent
  4. gate2_lu_controller：core_lib.local_agents.control.structured_control_agent.StructuredControlAgent


## 情景描述
情景描述：
仿真时长：10800秒
时间步长：10秒


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 52. universal_config

**配置路径:** `examples\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.50

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 53. universal_config

**配置路径:** `examples\canal_model\hierarchical_distributed_control_example\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.19

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 54. universal_config

**配置路径:** `examples\identification\02_gate_discharge_coefficient\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 55. unified_config

**配置路径:** `examples\non_agent_based\08_non_agent_simulation\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 56. 02_advanced_control

**配置路径:** `examples\mission_example_1\02_advanced_control`

**配置类型:** traditional_multi

**一致性得分:** 0.12

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_example_1\02_advanced_control
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：1800.0秒
时间步长：5.0秒
求解器：runge_kutta


调试配置：启用了调试功能，日志级别为DEBUG

性能监控：启用了性能监控功能

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


可视化配置：启用了可视化功能，包括图表绘制

## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析


高级分析：包含以下分析功能：
  - 控制性能分析
  - 系统辨识



---

## 57. 03_fault_tolerance

**配置路径:** `examples\mission_example_1\03_fault_tolerance`

**配置类型:** traditional_multi

**一致性得分:** 0.12

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_example_1\03_fault_tolerance
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：2400.0秒
时间步长：2.0秒
求解器：runge_kutta


调试配置：启用了调试功能，日志级别为DEBUG

性能监控：启用了性能监控功能

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


可视化配置：启用了可视化功能，包括图表绘制

## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析


高级分析：包含以下分析功能：
  - 控制性能分析
  - 系统辨识



---

## 58. canal_mpc_pid_control

**配置路径:** `examples\canal_model\canal_mpc_pid_control`

**配置类型:** traditional_multi

**一致性得分:** 0.70

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\canal_model\canal_mpc_pid_control
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：1个
  - core_lib.physical_objects.disturbance_node.DisturbanceNode：3个
  - 闸门：2个
  - UnifiedCanal：1个

具体组件：
  - upstream_reservoir：水库
  - diversion_before_gate1：core_lib.physical_objects.disturbance_node.DisturbanceNode
  - gate_1：闸门
  - canal_1：UnifiedCanal
  - diversion_before_gate2：core_lib.physical_objects.disturbance_node.DisturbanceNode
  - gate_2：闸门
  - tail_user：core_lib.physical_objects.disturbance_node.DisturbanceNode

智能体系统：包含7个智能体
具体智能体：
  1. central_mpc_agent：core_lib.local_agents.control.local_control_agent.LocalControlAgent
  2. gate_1_flow_pid_agent：core_lib.local_agents.control.local_control_agent.LocalControlAgent
  3. gate_2_flow_pid_agent：core_lib.local_agents.control.local_control_agent.LocalControlAgent
  4. canal_1_perception_agent：数字孪生智能体
     - 监控对象：canal_1
     - 状态主题：canal_1_state
  5. gate_1_perception_agent：数字孪生智能体
     - 监控对象：gate_1
     - 状态主题：gate_1_state
  6. gate_2_perception_agent：数字孪生智能体
     - 监控对象：gate_2
     - 状态主题：gate_2_state
  7. disturbance_scenario_agent：core_lib.mission.scenario_agent.ScenarioAgent


## 情景描述
情景描述：
仿真时长：7200秒
时间步长：10秒


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 59. universal_config

**配置路径:** `examples\agent_based\06_centralized_emergency_override\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.31

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 60. simplified_reservoir_control

**配置路径:** `examples\demo\simplified_reservoir_control`

**配置类型:** traditional_multi

**一致性得分:** 0.56

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\demo\simplified_reservoir_control
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：1个
  - 闸门：1个

具体组件：
  - reservoir_1：水库
  - gate_1：闸门

智能体系统：包含2个智能体
具体智能体：
  1. pid_controller：PIDControlAgent
  2. inflow_disturbance：DisturbanceAgent


## 情景描述
情景描述：
仿真时长：200秒
时间步长：1.0秒
求解器：euler


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


可视化配置：启用了可视化功能

## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 61. universal_config

**配置路径:** `test_output\round_trip_test\universal_config\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 1.00

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 62. unified_config

**配置路径:** `examples\converted\简单水库系统_unified\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.81

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 63. 01_local_control

**配置路径:** `examples\mission_example_2\01_local_control`

**配置类型:** traditional_multi

**一致性得分:** 0.12

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_example_2\01_local_control
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：1200.0秒
时间步长：2.0秒
求解器：local_control


调试配置：启用了调试功能，日志级别为INFO

性能监控：启用了性能监控功能

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


可视化配置：启用了可视化功能，包括图表绘制

## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析


高级分析：包含以下分析功能：
  - 控制性能分析
  - 系统辨识



---

## 64. unified_config

**配置路径:** `examples\canal_model\canal_mpc_pid_control\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.72

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 65. universal_config

**配置路径:** `examples\mission_example_1\01_basic_simulation\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 66. universal_config

**配置路径:** `examples\converted\水库调度系统_universal\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.67

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 67. 04_pid_control_outlet

**配置路径:** `examples\watertank_refactored\04_pid_control_outlet`

**配置类型:** traditional_multi

**一致性得分:** 0.12

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
求解器：euler


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 68. universal_config

**配置路径:** `test_output\enhanced_rule_1\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.92

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 69. unified_config

**配置路径:** `demo_output\unified_single_config\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.87

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 70. 02_multi_component_systems

**配置路径:** `examples\non_agent_based\02_multi_component_systems`

**配置类型:** traditional_multi

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\non_agent_based\02_multi_component_systems
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - RiverChannel：1个
  - 闸门：2个
  - 水库：1个

具体组件：
  - channel_1：RiverChannel
  - gate_1：闸门
  - gate_2：闸门
  - reservoir_1：水库

## 情景描述
情景描述：
仿真时长：500秒
时间步长：1.0秒


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析


高级分析：包含以下分析功能：



---

## 71. universal_config

**配置路径:** `examples\identification\01_reservoir_storage_curve\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 72. unified_config

**配置路径:** `examples\notebooks\11_control_and_agents\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.68

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 73. 02_multi_unit_coordination

**配置路径:** `examples\mission_example_5\02_multi_unit_coordination`

**配置类型:** traditional_multi

**一致性得分:** 0.50

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_example_5\02_multi_unit_coordination
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：30秒
时间步长：10.0秒
求解器：runge_kutta


调试配置：启用了调试功能，日志级别为INFO

性能监控：启用了性能监控功能

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


可视化配置：启用了可视化功能，包括图表绘制

## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析


高级分析：包含以下分析功能：



---

## 74. 02_hierarchical_control

**配置路径:** `examples\mission_example_2\02_hierarchical_control`

**配置类型:** traditional_multi

**一致性得分:** 0.12

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_example_2\02_hierarchical_control
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：1800.0秒
时间步长：3.0秒
求解器：hierarchical


调试配置：启用了调试功能，日志级别为INFO

性能监控：启用了性能监控功能

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


可视化配置：启用了可视化功能，包括图表绘制

## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析


高级分析：包含以下分析功能：
  - 控制性能分析
  - 系统辨识



---

## 75. unified_config

**配置路径:** `examples\non_agent_based\01_getting_started\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 76. unified_config

**配置路径:** `examples\watertank_refactored\03_pid_control_inlet\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.71

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 77. unified_config

**配置路径:** `examples\converted\水库调度系统_unified\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.84

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 78. unified_config

**配置路径:** `examples\canal_model\complex_fault_scenario_example\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.62

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 79. unified_config

**配置路径:** `examples\converted\城市排水系统_unified\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.92

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 80. universal_config

**配置路径:** `examples\converted\多组件水利系统_universal\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 81. universal_config

**配置路径:** `examples\demo\simplified_reservoir_control\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.38

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 82. universal_config

**配置路径:** `examples\canal_model\canal_model_comparison\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.50

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 83. 01_simple_simulation

**配置路径:** `examples\watertank_refactored\01_simple_simulation`

**配置类型:** traditional_multi

**一致性得分:** 0.38

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\watertank_refactored\01_simple_simulation
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
求解器：euler


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 84. universal_config

**配置路径:** `examples\non_agent_based\02_multi_component_systems\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.50

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 85. unified_config

**配置路径:** `examples\non_agent_based\02_multi_component_systems\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 86. 04_gate_scheduling

**配置路径:** `examples\mission_example_5\04_gate_scheduling`

**配置类型:** traditional_multi

**一致性得分:** 0.50

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_example_5\04_gate_scheduling
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：1秒
时间步长：1.0秒
求解器：optimization


调试配置：启用了调试功能，日志级别为INFO

性能监控：启用了性能监控功能

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


可视化配置：启用了可视化功能，包括图表绘制

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析


高级分析：包含以下分析功能：



---

## 87. universal_config

**配置路径:** `examples\canal_model\complex_fault_scenario_example\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.19

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 88. universal_config

**配置路径:** `examples\agent_based\12_pid_control_comparison\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.31

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 89. universal_config

**配置路径:** `examples\canal_model\canal_pid_control\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.50

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 90. unified_config

**配置路径:** `examples\canal_model\canal_pid_control\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 91. universal_config

**配置路径:** `examples\mission_example_1\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 92. universal_config

**配置路径:** `examples\mission_example_5\03_economic_dispatch\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 93. unified_config

**配置路径:** `examples\canal_model\structured_control_example\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.62

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 94. universal_config

**配置路径:** `examples\watertank_refactored\03_pid_control_inlet\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 95. universal_config

**配置路径:** `examples\watertank_refactored\05_joint_control\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 96. universal_config

**配置路径:** `test_output\enhanced_rule_3\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.94

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 97. universal_config

**配置路径:** `examples\mission_example_1\04_digital_twin_advanced\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 98. universal_config

**配置路径:** `examples\watertank_refactored\06_sensor_disturbance\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 99. universal_config

**配置路径:** `examples\mission_example_1\05_central_mpc_dispatcher\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 100. unified_config

**配置路径:** `examples\converted\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.85

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 101. universal_config

**配置路径:** `examples\converted\城市排水系统_universal\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 102. hierarchical_distributed_control_example

**配置路径:** `examples\canal_model\hierarchical_distributed_control_example`

**配置类型:** traditional_multi

**一致性得分:** 0.61

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\canal_model\hierarchical_distributed_control_example
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - core_lib.physical_objects.reservoir.Reservoir：1个
  - core_lib.physical_objects.disturbance_node.DisturbanceNode：3个
  - core_lib.physical_objects.gate.Gate：2个
  - core_lib.physical_objects.unified_canal.UnifiedCanal：2个

具体组件：
  - upstream_reservoir：core_lib.physical_objects.reservoir.Reservoir
  - turnout_1：core_lib.physical_objects.disturbance_node.DisturbanceNode
  - gate_1：core_lib.physical_objects.gate.Gate
  - canal_1：core_lib.physical_objects.unified_canal.UnifiedCanal
  - turnout_2：core_lib.physical_objects.disturbance_node.DisturbanceNode
  - gate_2：core_lib.physical_objects.gate.Gate
  - canal_2：core_lib.physical_objects.unified_canal.UnifiedCanal
  - terminal_user：core_lib.physical_objects.disturbance_node.DisturbanceNode

智能体系统：包含5个智能体
具体智能体：
  1. physical_io_agent：core_lib.local_agents.io.physical_io_agent.PhysicalIOAgent
  2. scenario_agent：core_lib.mission.scenario_agent.ScenarioAgent
  3. central_mpc_agent：core_lib.central_agents.central_mpc_agent.CentralMPCAgent
  4. gate1_pid_controller：core_lib.local_agents.control.structured_control_agent.StructuredControlAgent
  5. gate2_pid_controller：core_lib.local_agents.control.structured_control_agent.StructuredControlAgent


## 情景描述
情景描述：
仿真时长：10800秒
时间步长：10秒


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 103. unified_config

**配置路径:** `examples\agent_based\12_pid_control_comparison\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 104. universal_config

**配置路径:** `examples\non_agent_based\01_getting_started\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.50

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 105. unified_config

**配置路径:** `examples\notebooks\10_canal_system\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.88

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 106. universal_config

**配置路径:** `examples\identification\03_pipe_roughness\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 107. unified_config

**配置路径:** `examples\watertank_refactored\01_simple_simulation\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.58

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 108. unified_config

**配置路径:** `test_output\unified_config\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.83

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 109. 04_digital_twin_advanced

**配置路径:** `examples\mission_example_1\04_digital_twin_advanced`

**配置类型:** traditional_multi

**一致性得分:** 0.12

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_example_1\04_digital_twin_advanced
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：30.0秒
时间步长：1.0秒
求解器：euler


调试配置：启用了调试功能，日志级别为INFO

性能监控：启用了性能监控功能

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


可视化配置：启用了可视化功能，包括图表绘制

## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析


高级分析：包含以下分析功能：
  - 系统辨识



---

## 110. canal_pid_control

**配置路径:** `examples\canal_model\canal_pid_control`

**配置类型:** traditional_multi

**一致性得分:** 0.97

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\canal_model\canal_pid_control
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：1个
  - 闸门：2个
  - UnifiedCanal：2个

具体组件：
  - upstream_reservoir：水库
  - gate_1：闸门
  - canal_1：UnifiedCanal
  - canal_2：UnifiedCanal
  - gate_2：闸门

## 情景描述
情景描述：
仿真时长：7200秒
时间步长：10秒


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 111. universal_config

**配置路径:** `examples\mission_example_2\02_hierarchical_control\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 112. universal_config

**配置路径:** `examples\mission_example_2\03_watershed_coordination\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 113. 05_central_mpc_dispatcher

**配置路径:** `examples\mission_example_1\05_central_mpc_dispatcher`

**配置类型:** traditional_multi

**一致性得分:** 0.12

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_example_1\05_central_mpc_dispatcher
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：36000.0秒
时间步长：3600.0秒
求解器：mpc


调试配置：启用了调试功能，日志级别为INFO

性能监控：启用了性能监控功能

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


可视化配置：启用了可视化功能，包括图表绘制

## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析


高级分析：包含以下分析功能：
  - 控制性能分析
  - 系统辨识



---

## 114. universal_config

**配置路径:** `examples\watertank_refactored\07_actuator_disturbance\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 115. yinchuojiliao

**配置路径:** `examples\mission_scenarios\yinchuojiliao`

**配置类型:** traditional_multi

**一致性得分:** 0.51

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 116. unified_config

**配置路径:** `examples\canal_model\canal_model_comparison\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 117. universal_config

**配置路径:** `examples\mission_scenarios\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.50

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 118. 01_turbine_gate_simulation

**配置路径:** `examples\mission_example_5\01_turbine_gate_simulation`

**配置类型:** traditional_multi

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_example_5\01_turbine_gate_simulation
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
仿真时长：100秒
时间步长：10.0秒
求解器：runge_kutta


调试配置：启用了调试功能，日志级别为INFO

性能监控：启用了性能监控功能

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


可视化配置：启用了可视化功能，包括图表绘制

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析


高级分析：包含以下分析功能：



---

## 119. 07_centralized_setpoint_optimization

**配置路径:** `examples\notebooks\07_centralized_setpoint_optimization`

**配置类型:** traditional_multi

**一致性得分:** 0.88

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\notebooks\07_centralized_setpoint_optimization
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：未定义系统组件

## 情景描述
情景描述：
求解器：runge_kutta


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应


## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 120. unified_config

**配置路径:** `examples\watertank_refactored\07_actuator_disturbance\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.71

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 121. unified_config

**配置路径:** `examples\agent_based\06_centralized_emergency_override\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 122. unified_config

**配置路径:** `examples\agent_based\09_agent_based_distributed_control\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 123. unified_config

**配置路径:** `examples\watertank_refactored\02_parameter_identification\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.58

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 124. universal_config

**配置路径:** `examples\mission_example_1\02_advanced_control\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 125. 12_pid_control_comparison

**配置路径:** `examples\agent_based\12_pid_control_comparison`

**配置类型:** traditional_multi

**一致性得分:** 0.82

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\agent_based\12_pid_control_comparison
配置描述：包含通用配置文件的目录
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：1个
  - 闸门：2个
  - IntegralDelayCanal：3个

具体组件：
  - upstream_reservoir：水库
  - gate_1：闸门
  - canal_1：IntegralDelayCanal
  - canal_2：IntegralDelayCanal
  - gate_2：闸门
  - canal_3：IntegralDelayCanal

智能体系统：包含6个智能体
具体智能体：
  1. gate1_local_controller：core_lib.local_agents.control.local_control_agent.LocalControlAgent
  2. gate2_local_controller：core_lib.local_agents.control.local_control_agent.LocalControlAgent
  3. gate1_distant_controller：core_lib.local_agents.control.local_control_agent.LocalControlAgent
  4. gate2_distant_controller：core_lib.local_agents.control.local_control_agent.LocalControlAgent
  5. gate1_mixed_controller：core_lib.local_agents.control.local_control_agent.LocalControlAgent
  6. gate2_mixed_controller：core_lib.local_agents.control.local_control_agent.LocalControlAgent


## 情景描述
情景描述：
仿真时长：7200秒
时间步长：10秒


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 126. universal_config

**配置路径:** `examples\watertank_refactored\04_pid_control_outlet\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.75

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 127. universal_config

**配置路径:** `examples\mission_scenarios\yinchuojiliao\universal_config.yml`

**配置类型:** universal_config

**一致性得分:** 0.61

## 总结
配置文件总结：
配置类型：通用配置文件
配置路径：examples\mission_scenarios\yinchuojiliao
配置描述：通用配置文件
推荐运行器：run_universal_config.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - 水库：3个
  - UnifiedCanal：3个
  - 管道：2个
  - 闸门：2个
  - 阀门：2个

具体组件：
  - wendegen_reservoir：水库
  - connection_pool：水库
  - terminal_pool：水库
  - tunnel_1：UnifiedCanal
  - tunnel_2：UnifiedCanal
  - tunnel_3：UnifiedCanal
  - pipe_1：管道
  - pipe_2：管道
  - inlet_gate：闸门
  - tunnel1_gate：闸门
  - pipe1_valve：阀门
  - outlet_valve：阀门

系统拓扑：包含11个连接关系
具体连接关系：
  1. wendegen_reservoir → inlet_gate (outlet连接)
  2. inlet_gate → tunnel_1 (inlet连接)
  3. tunnel_1 → tunnel1_gate (outlet连接)
  4. tunnel1_gate → connection_pool (inlet连接)
  5. connection_pool → tunnel_2 (outlet连接)
  6. tunnel_2 → pipe_1 (transition连接)
  7. pipe_1 → pipe1_valve (inline连接)
  8. pipe1_valve → tunnel_3 (transition连接)
  9. tunnel_3 → pipe_2 (transition连接)
  10. pipe_2 → outlet_valve (inline连接)
  11. outlet_valve → terminal_pool (inlet连接)


智能体系统：包含4个智能体
具体智能体：
  1. digital_twins：未知类型
  2. central_dispatcher：CentralDispatcherAgent
  3. emergency_agent：EmergencyAgent
  4. csv_inflow_agent：CsvInflowAgent


## 情景描述
情景描述：
仿真时长：168.0秒
时间步长：1.0秒
求解器：saint_venant


## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：
  - 闸门开度、流量、水位差
  - 水库水位、库容、入流、出流


## 分析描述
分析描述：
系统采用智能体控制，进行闭环控制分析
控制策略分析：
  - 性能分析
  - EmergencyAgent性能分析
  - CsvInflowAgent性能分析
  - CentralDispatcherAgent性能分析

控制性能评估：
  - 跟踪精度分析
  - 稳定性评估
  - 鲁棒性测试
  - 控制效率分析




---

## 128. unified_config

**配置路径:** `examples\watertank_refactored\04_pid_control_outlet\unified_config.yml`

**配置类型:** unified_single

**一致性得分:** 0.71

## 总结
配置文件总结：
配置类型：统一配置文件
配置路径：examples\watertank_refactored\04_pid_control_outlet
配置描述：统一配置文件
推荐运行器：run_unified_scenario.py


## 建模描述
建模描述：
系统包含以下组件类型：
  - WaterTank：1个
  - 阀门：1个

具体组件：
  - watertank：WaterTank
  - outlet_valve：阀门

## 情景描述
情景描述：
仿真时长：300.0秒
时间步长：1.0秒


控制策略：采用PID（已启用）

## 查询描述
查询描述：
系统将输出以下数据：
  - 各组件的状态变量时间序列
  - 系统性能指标
  - 控制信号和响应

具体输出变量包括：


输出配置：输出格式：json，保存路径：outlet_pid_results.json，输出变量：6个

## 分析描述
分析描述：
系统采用开环控制，主要进行系统响应分析
分析内容包括：
  - 系统动态响应特性
  - 稳态性能评估
  - 参数敏感性分析




---

## 统计信息

### 配置类型分布

- universal_config: 55 个
- traditional_multi: 37 个
- unified_single: 36 个

### 一致性得分统计

- 平均得分: 0.64
- 最高得分: 1.00
- 最低得分: 0.12

### 组件统计

- 总配置数: 128
- 平均组件数: 2.6
- 最多组件数: 12
- 最少组件数: 0
