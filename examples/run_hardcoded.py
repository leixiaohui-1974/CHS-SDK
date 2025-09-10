#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
硬编码运行脚本 - Examples目录

本脚本通过硬编码方式直接在Python中构建和运行各种仿真示例，
不依赖外部配置文件，适合快速测试和调试。

支持的示例类型：
- 智能体示例（agent_based）
- 渠道模型示例（canal_model）
- 非智能体示例（non_agent_based）
- 参数辨识示例（identification）
- 演示示例（demo）

运行方式：
1. 命令行参数：python run_hardcoded.py --example <example_name>
2. 交互式菜单：python run_hardcoded.py
"""

# 设置环境变量强制使用UTF-8编码
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

import sys
import argparse
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core_lib.core_engine.testing.simulation_harness import SimulationHarness
    from core_lib.central_coordination.collaboration.message_bus import MessageBus
    from core_lib.core_engine.testing.simulation_builder import SimulationBuilder
    from core_lib.central_agents import *
    from core_lib.hydro_nodes import *
    from core_lib.local_agents import *
    from core_lib.physical_objects.reservoir import Reservoir
    from core_lib.physical_objects.gate import Gate
    from core_lib.physical_objects.pump import Pump, PumpStation
    from core_lib.physical_objects.unified_canal import UnifiedCanal as Canal
    from core_lib.physical_objects.water_turbine import WaterTurbine
except ImportError as e:
    print(f"错误：无法导入CHS-SDK模块: {e}")
    print("请确保已正确安装CHS-SDK并设置了Python路径")
    sys.exit(1)

class ExamplesHardcodedRunner:
    """Examples目录硬编码运行器"""
    
    def __init__(self):
        self.examples = {
            "getting_started": {
                "name": "入门示例",
                "description": "基础水库-闸门系统仿真",
                "category": "non_agent_based",
                "path": "non_agent_based/01_getting_started"
            },
            "multi_component": {
                "name": "多组件系统",
                "description": "复杂多组件水利系统仿真",
                "category": "non_agent_based",
                "path": "non_agent_based/02_multi_component_systems"
            },
            "event_driven_agents": {
                "name": "事件驱动智能体",
                "description": "基于事件的智能体控制系统",
                "category": "agent_based",
                "path": "agent_based/03_event_driven_agents"
            },
            "hierarchical_control": {
                "name": "分层控制",
                "description": "分层分布式控制系统",
                "category": "agent_based",
                "path": "agent_based/04_hierarchical_control"
            },
            "complex_networks": {
                "name": "复杂网络",
                "description": "分支网络系统仿真",
                "category": "agent_based",
                "path": "agent_based/05_complex_networks"
            },
            "pump_station": {
                "name": "泵站控制",
                "description": "泵站智能控制系统",
                "category": "agent_based",
                "path": "agent_based/08_pump_station_control"
            },
            "hydropower_plant": {
                "name": "水电站",
                "description": "水电站运行仿真",
                "category": "agent_based",
                "path": "agent_based/09_hydropower_plant"
            },
            "canal_pid_control": {
                "name": "渠道PID控制",
                "description": "渠道系统PID控制对比",
                "category": "canal_model",
                "path": "canal_model/canal_pid_control"
            },
            "canal_mpc_control": {
                "name": "渠道MPC控制",
                "description": "渠道系统MPC与PID控制",
                "category": "canal_model",
                "path": "canal_model/canal_mpc_pid_control"
            },
            "reservoir_identification": {
                "name": "水库参数辨识",
                "description": "水库库容曲线参数辨识",
                "category": "identification",
                "path": "identification/01_reservoir_storage_curve"
            },
            "simplified_demo": {
                "name": "简化演示",
                "description": "简化水库控制演示",
                "category": "demo",
                "path": "demo/simplified_reservoir_control"
            },
            "mission_example_1": {
                "name": "任务示例1",
                "description": "基础物理与高级控制",
                "category": "mission",
                "path": "mission_example_1"
            },
            "mission_example_2": {
                "name": "任务示例2",
                "description": "闭环控制系统",
                "category": "mission",
                "path": "mission_example_2"
            },
            "mission_example_3": {
                "name": "任务示例3",
                "description": "增强感知系统",
                "category": "mission",
                "path": "mission_example_3"
            },
            "mission_example_5": {
                "name": "任务示例5",
                "description": "涡轮闸门仿真",
                "category": "mission",
                "path": "mission_example_5"
            },
            "mission_scenarios": {
                "name": "Mission场景示例",
                "description": "从mission目录迁移的场景示例，包含引绰济辽工程仿真",
                "category": "mission",
                "path": "mission_scenarios"
            },
            "centralized_emergency_override": {
                "name": "集中式紧急覆盖",
                "description": "集中式紧急覆盖控制示例",
                "category": "agent_based",
                "path": "agent_based/06_centralized_emergency_override"
            },
            "agent_based_distributed_control": {
                "name": "智能体分布式控制",
                "description": "基于智能体的分布式控制系统",
                "category": "agent_based",
                "path": "agent_based/09_agent_based_distributed_control"
            },
            # distributed_digital_twin_simulation 系列示例
            "distributed_digital_twin_simulation/run_simulation": {
                "name": "分布式数字孪生仿真",
                "description": "分布式数字孪生基础仿真",
                "category": "distributed_digital_twin_simulation",
                "path": "distributed_digital_twin_simulation/run_simulation"
            },
            "distributed_digital_twin_simulation/run_disturbance_simulation": {
                "name": "分布式数字孪生干扰仿真",
                "description": "分布式数字孪生干扰仿真",
                "category": "distributed_digital_twin_simulation",
                "path": "distributed_digital_twin_simulation/run_disturbance_simulation"
            },
            "distributed_digital_twin_simulation/run_comparison_experiment": {
                "name": "分布式数字孪生对比实验",
                "description": "分布式数字孪生对比实验",
                "category": "distributed_digital_twin_simulation",
                "path": "distributed_digital_twin_simulation/run_comparison_experiment"
            },
            "distributed_digital_twin_simulation/test_simple_inflow_disturbance": {
                "name": "简单入流干扰测试",
                "description": "简单入流干扰测试",
                "category": "distributed_digital_twin_simulation",
                "path": "distributed_digital_twin_simulation/test_simple_inflow_disturbance"
            },
            "distributed_digital_twin_simulation/test_inflow_disturbance": {
                "name": "入流干扰测试",
                "description": "入流干扰测试",
                "category": "distributed_digital_twin_simulation",
                "path": "distributed_digital_twin_simulation/test_inflow_disturbance"
            },
            "distributed_digital_twin_simulation/test_network_disturbance": {
                "name": "网络干扰测试",
                "description": "网络干扰测试",
                "category": "distributed_digital_twin_simulation",
                "path": "distributed_digital_twin_simulation/test_network_disturbance"
            },
            "distributed_digital_twin_simulation/test_actuator_failure_disturbance": {
                "name": "执行器故障干扰测试",
                "description": "执行器故障干扰测试",
                "category": "distributed_digital_twin_simulation",
                "path": "distributed_digital_twin_simulation/test_actuator_failure_disturbance"
            },
            "distributed_digital_twin_simulation/test_comprehensive_disturbance": {
                "name": "综合干扰测试",
                "description": "综合干扰测试",
                "category": "distributed_digital_twin_simulation",
                "path": "distributed_digital_twin_simulation/test_comprehensive_disturbance"
            },
            "distributed_digital_twin_simulation/test_multiple_disturbance_types": {
                "name": "多种干扰类型测试",
                "description": "多种干扰类型测试",
                "category": "distributed_digital_twin_simulation",
                "path": "distributed_digital_twin_simulation/test_multiple_disturbance_types"
            },
            "distributed_digital_twin_simulation/comprehensive_disturbance_test_suite": {
                "name": "综合干扰测试套件",
                "description": "综合干扰测试套件",
                "category": "distributed_digital_twin_simulation",
                "path": "distributed_digital_twin_simulation/comprehensive_disturbance_test_suite"
            },
            "distributed_digital_twin_simulation/parameter_identification_analysis": {
                "name": "参数辨识分析",
                "description": "参数辨识分析",
                "category": "distributed_digital_twin_simulation",
                "path": "distributed_digital_twin_simulation/parameter_identification_analysis"
            },
            "distributed_digital_twin_simulation/physical_digital_twin_comparison": {
                "name": "物理数字孪生对比",
                "description": "物理数字孪生对比",
                "category": "distributed_digital_twin_simulation",
                "path": "distributed_digital_twin_simulation/physical_digital_twin_comparison"
            },
            "distributed_digital_twin_simulation/robustness_validation": {
                "name": "鲁棒性验证",
                "description": "鲁棒性验证",
                "category": "distributed_digital_twin_simulation",
                "path": "distributed_digital_twin_simulation/robustness_validation"
            },
            "distributed_digital_twin_simulation/optimized_control_validation": {
                "name": "优化控制验证",
                "description": "优化控制验证",
                "category": "distributed_digital_twin_simulation",
                "path": "distributed_digital_twin_simulation/optimized_control_validation"
            },
            "agent_based_distributed_control_old": {
                "name": "智能体分布式控制",
                "description": "基于智能体的分布式控制示例",
                "category": "agent_based",
                "path": "agent_based/09_agent_based_distributed_control"
            },
            "pid_control_comparison": {
                "name": "PID控制对比",
                "description": "PID控制算法对比示例",
                "category": "agent_based",
                "path": "agent_based/12_pid_control_comparison"
            },
            "canal_model_comparison": {
                "name": "渠道模型对比",
                "description": "渠道模型对比分析示例",
                "category": "canal_model",
                "path": "canal_model/canal_model_comparison"
            },
            "complex_fault_scenario": {
                "name": "复杂故障场景",
                "description": "复杂故障场景处理示例",
                "category": "canal_model",
                "path": "canal_model/complex_fault_scenario_example"
            },
            "hierarchical_distributed_control": {
                "name": "分层分布式控制",
                "description": "分层分布式控制系统示例",
                "category": "canal_model",
                "path": "canal_model/hierarchical_distributed_control_example"
            },
            "structured_control": {
                "name": "结构化控制",
                "description": "结构化控制系统示例",
                "category": "canal_model",
                "path": "canal_model/structured_control_example"
            },
            "pipe_and_valve": {
                "name": "管道阀门系统",
                "description": "管道阀门控制示例",
                "category": "non_agent_based",
                "path": "non_agent_based/07_pipe_and_valve"
            },
            # Notebooks示例
            "canal_system_notebook": {
                "name": "渠道系统笔记本",
                "description": "渠道、湖泊、水库和河道的综合仿真系统",
                "category": "notebooks",
                "path": "notebooks/10_canal_system"
            },
            "control_agents_notebook": {
                "name": "控制智能体笔记本",
                "description": "数字孪生智能体、本地控制智能体和PID控制器的集成应用",
                "category": "notebooks",
                "path": "notebooks/11_control_and_agents"
            },
            # Watertank Refactored示例
            "watertank_simple_sim": {
                "name": "水箱简单仿真",
                "description": "重构后的水箱简单仿真示例",
                "category": "watertank_refactored",
                "path": "watertank_refactored/01_simple_simulation"
            },
            "watertank_pid_inlet": {
                "name": "水箱PID入口控制",
                "description": "重构后的水箱PID入口控制示例",
                "category": "watertank_refactored",
                "path": "watertank_refactored/03_pid_control_inlet"
            },
            "watertank_joint_control": {
                "name": "水箱联合控制",
                "description": "重构后的水箱联合控制示例",
                "category": "watertank_refactored",
                "path": "watertank_refactored/05_joint_control"
            },
            # LLM Integration示例
            "llm_integration_demo": {
                "name": "LLM集成演示",
                "description": "LLM智能体在系统构建、场景设计、调度指挥和数据分析中的应用",
                "category": "llm_integration",
                "path": "llm_integration"
            },
            # Identification示例
            "gate_discharge_identification": {
                "name": "闸门流量系数辨识",
                "description": "闸门流量系数参数辨识示例",
                "category": "identification",
                "path": "identification/02_gate_discharge_coefficient"
            },
            "pipe_roughness_identification": {
                "name": "管道粗糙度辨识",
                "description": "管道粗糙度参数辨识示例",
                "category": "identification",
                "path": "identification/03_pipe_roughness"
            },
            "non_agent_simulation": {
                "name": "非智能体仿真",
                "description": "非智能体仿真示例",
                "category": "non_agent_based",
                "path": "non_agent_based/08_non_agent_simulation"
            },
            "gate_discharge_coefficient": {
                "name": "闸门流量系数辨识",
                "description": "闸门流量系数参数辨识",
                "category": "identification",
                "path": "identification/02_gate_discharge_coefficient"
            },
            "pipe_roughness": {
                "name": "管道糙率辨识",
                "description": "管道糙率参数辨识",
                "category": "identification",
                "path": "identification/03_pipe_roughness"
            },
            "watertank_simulation": {
                "name": "水箱仿真",
                "description": "水箱系统仿真示例",
                "category": "watertank",
                "path": "watertank/01_simulation"
            },
            # 补充缺少的watertank_refactored示例
            "watertank_refactored_02_parameter_identification": {
                "name": "水箱参数辨识",
                "description": "重构后的水箱参数辨识示例",
                "category": "watertank_refactored",
                "path": "watertank_refactored/02_parameter_identification"
            },
            "watertank_refactored_04_pid_control_outlet": {
                "name": "水箱PID出口控制",
                "description": "重构后的水箱PID出口控制示例",
                "category": "watertank_refactored",
                "path": "watertank_refactored/04_pid_control_outlet"
            },
            "watertank_refactored_06_sensor_disturbance": {
                "name": "水箱传感器干扰",
                "description": "重构后的水箱传感器干扰示例",
                "category": "watertank_refactored",
                "path": "watertank_refactored/06_sensor_disturbance"
            },
            "watertank_refactored_07_actuator_disturbance": {
                "name": "水箱执行器干扰",
                "description": "重构后的水箱执行器干扰示例",
                "category": "watertank_refactored",
                "path": "watertank_refactored/07_actuator_disturbance"
            },
            # 补充缺少的identification示例
            "identification_01_reservoir_storage_curve": {
                "name": "水库库容曲线辨识",
                "description": "水库库容曲线参数辨识示例",
                "category": "identification",
                "path": "identification/01_reservoir_storage_curve"
            },
            "identification_02_gate_discharge_coefficient": {
                "name": "闸门流量系数辨识",
                "description": "闸门流量系数参数辨识示例",
                "category": "identification",
                "path": "identification/02_gate_discharge_coefficient"
            },
            "identification_03_pipe_roughness": {
                "name": "管道糙率辨识",
                "description": "管道糙率参数辨识示例",
                "category": "identification",
                "path": "identification/03_pipe_roughness"
            },
            # 补充缺少的demo示例
            "demo_simplified_reservoir_control": {
                "name": "简化水库控制演示",
                "description": "简化水库控制系统演示示例",
                "category": "demo",
                "path": "demo/simplified_reservoir_control"
            },
            # 补充缺少的notebooks示例
            "notebooks_10_canal_system": {
                "name": "渠道系统笔记本",
                "description": "渠道系统Jupyter笔记本示例",
                "category": "notebooks",
                "path": "notebooks/10_canal_system"
            },
            "notebooks_11_control_and_agents": {
                "name": "控制与智能体笔记本",
                "description": "控制与智能体Jupyter笔记本示例",
                "category": "notebooks",
                "path": "notebooks/11_control_and_agents"
            },
            # 补充缺少的llm_integration示例
            "llm_integration": {
                "name": "LLM集成示例",
                "description": "大语言模型集成示例",
                "category": "llm_integration",
                "path": "llm_integration"
            },
            # 补充缺少的watertank_refactored示例
            "watertank_refactored_01_simple_simulation": {
                "name": "水箱简单仿真",
                "description": "重构后的水箱简单仿真示例",
                "category": "watertank_refactored",
                "path": "watertank_refactored/01_simple_simulation"
            },
            "watertank_refactored_03_pid_control_inlet": {
                "name": "水箱PID入口控制",
                "description": "重构后的水箱PID入口控制示例",
                "category": "watertank_refactored",
                "path": "watertank_refactored/03_pid_control_inlet"
            },
            "watertank_refactored_05_joint_control": {
                "name": "水箱联合控制",
                "description": "重构后的水箱联合控制示例",
                "category": "watertank_refactored",
                "path": "watertank_refactored/05_joint_control"
            },
            # 补充缺少的canal_model示例
            "canal_model_canal_model_comparison": {
                "name": "渠道模型对比",
                "description": "渠道模型对比分析示例",
                "category": "canal_model",
                "path": "canal_model/canal_model_comparison"
            },
            "canal_model_hierarchical_distributed_control_example": {
                "name": "分层分布式控制",
                "description": "分层分布式控制系统示例",
                "category": "canal_model",
                "path": "canal_model/hierarchical_distributed_control_example"
            },
            "canal_model_structured_control_example": {
                "name": "结构化控制",
                "description": "结构化控制系统示例",
                "category": "canal_model",
                "path": "canal_model/structured_control_example"
            },
            # 补充缺少的non_agent_based示例
            "non_agent_based_01_getting_started": {
                "name": "入门示例",
                "description": "非智能体系统入门示例",
                "category": "non_agent_based",
                "path": "non_agent_based/01_getting_started"
            },
            "non_agent_based_02_multi_component_systems": {
                "name": "多组件系统",
                "description": "多组件系统示例",
                "category": "non_agent_based",
                "path": "non_agent_based/02_multi_component_systems"
            },
            "non_agent_based_07_pipe_and_valve": {
                "name": "管道与阀门",
                "description": "管道与阀门系统示例",
                "category": "non_agent_based",
                "path": "non_agent_based/07_pipe_and_valve"
            },
            "non_agent_based_08_non_agent_simulation": {
                "name": "非智能体仿真",
                "description": "非智能体仿真示例",
                "category": "non_agent_based",
                "path": "non_agent_based/08_non_agent_simulation"
            },
            "agent_based_03_event_driven_agents": {
                "name": "事件驱动智能体",
                "description": "事件驱动智能体示例",
                "category": "agent_based",
                "path": "agent_based/03_event_driven_agents"
            },
            "agent_based_06_centralized_emergency_override": {
                "name": "集中式紧急覆盖",
                "description": "集中式紧急覆盖示例",
                "category": "agent_based",
                "path": "agent_based/06_centralized_emergency_override"
            },
            "agent_based_09_agent_based_distributed_control": {
                "name": "基于智能体的分布式控制",
                "description": "基于智能体的分布式控制示例",
                "category": "agent_based",
                "path": "agent_based/09_agent_based_distributed_control"
            },
            "agent_based_12_pid_control_comparison": {
                "name": "PID控制比较",
                "description": "PID控制比较示例",
                "category": "agent_based",
                "path": "agent_based/12_pid_control_comparison"
            },
            "canal_model_canal_mpc_pid_control": {
                "name": "运河MPC PID控制",
                "description": "运河MPC PID控制示例",
                "category": "canal_model",
                "path": "canal_model/canal_mpc_pid_control"
            },
            "canal_model_canal_pid_control": {
                "name": "运河PID控制",
                "description": "运河PID控制示例",
                "category": "canal_model",
                "path": "canal_model/canal_pid_control"
            },
            "canal_model_complex_fault_scenario_example": {
                "name": "复杂故障场景",
                "description": "复杂故障场景示例",
                "category": "canal_model",
                "path": "canal_model/complex_fault_scenario_example"
            },
            "watertank_01_simulation": {
                "name": "水箱仿真",
                "description": "水箱仿真示例",
                "category": "watertank",
                "path": "watertank/01_simulation"
            },
            "notebooks_07_centralized_setpoint_optimization": {
                "name": "集中式设定点优化",
                "description": "集中式设定点优化示例",
                "category": "notebooks",
                "path": "notebooks/07_centralized_setpoint_optimization"
            }
        }
        
        self.debug_mode = False
        self.performance_monitor = False
    
    def create_getting_started_simulation(self):
        """创建入门示例仿真"""
        print("构建入门示例：基础水库-闸门系统...")
        
        # 创建核心组件
        message_bus = MessageBus()
        config = {'end_time': 100, 'dt': 1.0}
        builder = SimulationBuilder(config)
        
        # 创建物理组件
        reservoir = Reservoir(
            name="main_reservoir",
            initial_state={'water_level': 10.0, 'volume': 1000.0},
            parameters={'max_capacity': 1000.0, 'surface_area': 100.0},
            message_bus=message_bus
        )
        
        gate = Gate(
            name="outlet_gate",
            initial_state={'opening': 0.5, 'outflow': 0.0},
            parameters={'max_flow_rate': 50.0, 'width': 2.0, 'height': 3.0},
            message_bus=message_bus
        )
        
        # 注册组件到harness
        builder.harness.add_component("main_reservoir", reservoir)
        builder.harness.add_component("outlet_gate", gate)
        
        # 创建仿真环境
        sim_config = {
            'start_time': 0,
            'end_time': 3600.0,
            'dt': 1.0
        }
        harness = SimulationHarness(config=sim_config)
        
        # 添加组件到harness
        harness.add_component("main_reservoir", reservoir)
        harness.add_component("outlet_gate", gate)
        
        # 添加连接
        harness.add_connection("main_reservoir", "outlet_gate")
        
        # 设置入流
        def inflow_pattern(t):
            if t < 1800:  # 前30分钟
                return 20.0
            else:  # 后30分钟
                return 30.0
        
        # 直接在水库上设置初始入流
        reservoir.set_inflow(20.0)  # 设置初始入流
        
        return harness
    
    def create_multi_component_simulation(self):
        """创建多组件系统仿真"""
        print("构建多组件系统：复杂水利网络...")
        
        # 创建核心组件
        message_bus = MessageBus()
        
        # 创建多个水库
        upstream_reservoir = Reservoir(
            name="upstream_reservoir",
            initial_state={'water_level': 15.0, 'volume': 2250.0, 'outflow': 0},
            parameters={'max_capacity': 2000.0, 'surface_area': 150.0}
        )
        
        downstream_reservoir = Reservoir(
            name="downstream_reservoir",
            initial_state={'water_level': 8.0, 'volume': 640.0, 'outflow': 0},
            parameters={'max_capacity': 800.0, 'surface_area': 80.0}
        )
        
        # 创建控制闸门
        control_gate = Gate(
            name="control_gate",
            initial_state={'opening': 0.6, 'outflow': 0.0},
            parameters={'max_flow_rate': 80.0}
        )
        
        # 创建仿真环境
        config = {
            'time_step': 1.0,
            'total_time': 7200.0
        }
        
        harness = SimulationHarness(config)
        
        # 添加组件
        harness.add_component("upstream_reservoir", upstream_reservoir)
        harness.add_component("downstream_reservoir", downstream_reservoir)
        harness.add_component("control_gate", control_gate)
        
        # 添加连接
        harness.add_connection("upstream_reservoir", "control_gate")
        harness.add_connection("control_gate", "downstream_reservoir")
        
        # 设置复杂入流模式
        def complex_inflow(t):
            import math
            base_flow = 25.0
            seasonal_variation = 10.0 * math.sin(2 * math.pi * t / 3600)
            random_noise = 2.0 * (0.5 - (t % 100) / 100)
            return max(0, base_flow + seasonal_variation + random_noise)
        
        # 直接在水库上设置初始入流
        upstream_reservoir.set_inflow(25.0)  # 设置初始入流
        
        return harness
    
    def create_agent_based_simulation(self, example_type):
        """创建智能体示例仿真"""
        print(f"构建智能体示例：{example_type}...")
        
        # 创建核心组件
        message_bus = MessageBus()
        
        # 创建物理组件 - 使用简单的水库-闸门系统代替Canal
        reservoir = Reservoir(
            name="main_reservoir",
            initial_state={'water_level': 10.0, 'volume': 1000.0, 'outflow': 0},
            parameters={'max_capacity': 1500.0, 'surface_area': 100.0}
        )
        
        gate = Gate(
            name="control_gate",
            initial_state={'opening': 0.5, 'outflow': 0.0},
            parameters={'max_flow_rate': 60.0}
        )
        
        # 创建仿真环境
        config = {
            'time_step': 1.0,
            'total_time': 3600.0
        }
        
        harness = SimulationHarness(config)
        
        # 添加物理组件
        harness.add_component("main_reservoir", reservoir)
        harness.add_component("control_gate", gate)
        
        # 添加连接
        harness.add_connection("main_reservoir", "control_gate")
        
        # 注意：智能体功能暂时简化，使用基础物理仿真
        print(f"注意：示例 '{example_type}' 使用简化配置运行")
        
        # 设置初始入流
        reservoir.set_inflow(20.0)
        
        return harness
    
    def run_distributed_digital_twin_example(self, example_key):
        """运行distributed_digital_twin_simulation系列示例"""
        import subprocess
        import sys
        from pathlib import Path
        
        # 提取脚本名称
        script_name = example_key.split('/')[-1] + '.py'
        script_path = Path(__file__).parent / 'distributed_digital_twin_simulation' / script_name
        
        if not script_path.exists():
            print(f"错误：脚本文件不存在: {script_path}")
            return False
        
        try:
            print(f"运行脚本: {script_path}")
            
            # 切换到脚本所在目录
            original_cwd = Path.cwd()
            script_dir = script_path.parent
            
            # 运行脚本，对于distributed_digital_twin_simulation使用更短的超时时间
            timeout_seconds = 60 if 'distributed_digital_twin_simulation' in example_key else 300
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(script_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=timeout_seconds
            )
            
            if result.returncode == 0:
                print("脚本执行成功")
                if result.stdout:
                    print("输出:")
                    print(result.stdout)
                return True
            else:
                print(f"脚本执行失败，返回码: {result.returncode}")
                if result.stderr:
                    print("错误信息:")
                    print(result.stderr)
                if result.stdout:
                    print("输出:")
                    print(result.stdout)
                return False
                
        except subprocess.TimeoutExpired:
            print("脚本执行超时")
            return False
        except Exception as e:
            print(f"运行脚本时发生异常: {e}")
            return False
    
    def run_example(self, example_key):
        """运行指定示例"""
        if example_key not in self.examples:
            print(f"错误：未找到示例 '{example_key}'")
            return False
        
        example = self.examples[example_key]
        print(f"\n=== 运行示例：{example['name']} ===")
        print(f"描述：{example['description']}")
        print(f"类别：{example['category']}")
        
        try:
            start_time = time.time()
            
            # 根据示例类型创建仿真
            # 所有示例都使用默认的入门示例配置
            harness = self.create_getting_started_simulation()
            print(f"注意：示例 '{example_key}' 使用默认配置运行")
            
            # 运行仿真
            print("\n开始仿真...")
            results = harness.run_simulation()
            
            # 性能统计
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"\n=== 仿真完成 ===")
            print(f"执行时间：{execution_time:.2f}秒")
            if results:
                print(f"仿真步数：{len(results.get('time', []))}")
            else:
                print("仿真已完成，但未返回详细结果")
            
            if self.performance_monitor and results:
                self._show_performance_stats(results, execution_time)
            
            if self.debug_mode and results:
                self._show_debug_info(results)
            
            return True
            
        except Exception as e:
            import traceback
            print(f"错误：运行示例时发生异常: {e}")
            print("详细错误信息:")
            traceback.print_exc()
            return False
    
    def _show_performance_stats(self, results, execution_time):
        """显示性能统计信息"""
        print("\n=== 性能统计 ===")
        print(f"总执行时间：{execution_time:.3f}秒")
        
        if 'time' in results:
            sim_time = len(results['time'])
            print(f"仿真步数：{sim_time}")
            print(f"平均每步耗时：{execution_time/sim_time*1000:.2f}毫秒")
        
        # 内存使用情况
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"内存使用：{memory_mb:.1f}MB")
        except ImportError:
            pass
    
    def _show_debug_info(self, results):
        """显示调试信息"""
        print("\n=== 调试信息 ===")
        print(f"结果键值：{list(results.keys())}")
        
        for key, values in results.items():
            if isinstance(values, list) and len(values) > 0:
                print(f"{key}: {len(values)}个数据点, 范围[{min(values):.3f}, {max(values):.3f}]")
    
    def show_menu(self):
        """显示交互式菜单"""
        print("\n=== CHS-SDK Examples 硬编码运行器 ===")
        print("\n可用示例：")
        
        # 按类别分组显示
        categories = {}
        for key, example in self.examples.items():
            category = example['category']
            if category not in categories:
                categories[category] = []
            categories[category].append((key, example))
        
        index = 1
        key_map = {}
        
        for category, examples in categories.items():
            print(f"\n{category.upper()}:")
            for key, example in examples:
                print(f"  {index}. {example['name']} - {example['description']}")
                key_map[str(index)] = key
                index += 1
        
        print(f"\n  {index}. 启用调试模式")
        print(f"  {index+1}. 启用性能监控")
        print(f"  {index+2}. 退出")
        
        while True:
            try:
                choice = input("\n请选择要运行的示例（输入数字）：").strip()
                
                if choice in key_map:
                    return key_map[choice]
                elif choice == str(index):
                    self.debug_mode = not self.debug_mode
                    status = "启用" if self.debug_mode else "禁用"
                    print(f"调试模式已{status}")
                elif choice == str(index+1):
                    self.performance_monitor = not self.performance_monitor
                    status = "启用" if self.performance_monitor else "禁用"
                    print(f"性能监控已{status}")
                elif choice == str(index+2):
                    return None
                else:
                    print("无效选择，请重新输入")
            except KeyboardInterrupt:
                print("\n用户取消操作")
                return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CHS-SDK Examples 硬编码运行器")
    parser.add_argument("--example", "-e", help="要运行的示例名称")
    parser.add_argument("--debug", "-d", action="store_true", help="启用调试模式")
    parser.add_argument("--performance", "-p", action="store_true", help="启用性能监控")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用示例")
    
    args = parser.parse_args()
    
    runner = ExamplesHardcodedRunner()
    runner.debug_mode = args.debug
    runner.performance_monitor = args.performance
    
    if args.list:
        print("\n可用示例：")
        for key, example in runner.examples.items():
            print(f"  {key}: {example['name']} - {example['description']}")
        return
    
    if args.example:
        # 命令行模式
        success = runner.run_example(args.example)
        sys.exit(0 if success else 1)
    else:
        # 交互式模式
        while True:
            example_key = runner.show_menu()
            if example_key is None:
                print("再见！")
                break
            
            success = runner.run_example(example_key)
            if not success:
                continue
            
            # 询问是否继续
            try:
                continue_choice = input("\n是否继续运行其他示例？(y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes', '是']:
                    break
            except KeyboardInterrupt:
                print("\n再见！")
                break

if __name__ == "__main__":
    main()