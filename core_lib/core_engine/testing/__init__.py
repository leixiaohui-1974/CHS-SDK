# This package contains the in-the-loop testing framework. It provides
# a sandbox environment to test agents and systems under various scenarios,
# supporting Model-in-the-Loop (MIL), Software-in-the-Loop (SIL), etc.

"""
核心仿真测试框架

主要模块:
- simulation_harness: 现代化仿真框架，基于新架构
- common_agents: 通用Agent实现，提供可重用的Agent类型

使用说明:
1. 使用simulation_harness.SimulationHarness作为主要仿真框架
2. 使用common_agents中的Agent类型处理常见任务
3. 直接使用core_lib.physical_objects创建物理组件

简化原则:
- 移除过度抽象的组件创建系统
- 专注核心仿真功能
- 减少不必要的复杂性
"""

from .simulation_harness import SimulationHarness
from .common_agents import (
    ScheduledEventAgent,
    DemandAgent, 
    DisturbanceAgent,
    MonitoringAgent,
    ThresholdAlarmAgent
)

# 为向后兼容提供别名
EnhancedSimulationHarness = SimulationHarness
ModernSimulationHarness = SimulationHarness

__all__ = [
    # 主要仿真框架
    'SimulationHarness',
    'EnhancedSimulationHarness',  # 兼容别名
    'ModernSimulationHarness',    # 兼容别名
    
    # 通用Agent类型
    'ScheduledEventAgent',
    'DemandAgent',
    'DisturbanceAgent', 
    'MonitoringAgent',
    'ThresholdAlarmAgent',
]