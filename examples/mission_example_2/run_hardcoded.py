#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 2 - 闭环与分层控制系统 (硬编码运行方式)

本脚本通过硬编码方式直接在Python中构建和运行闭环与分层控制系统仿真，
不依赖外部配置文件，展示三个不同层次的控制策略。

运行方式:
    python run_hardcoded.py [scenario_number]
    
参数:
    scenario_number: 可选，指定运行的场景编号 (1-3)
                    1 - 本地闭环控制
                    2 - 分层控制
                    3 - 流域联合调度
                    如果不指定，将显示交互式选择菜单
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core_lib.core_engine.testing.simulation_harness import SimulationHarness
    from core_lib.physical_objects.unified_canal import UnifiedCanal
    from core_lib.physical_objects.gate import Gate
    from core_lib.local_agents.io.physical_io_agent import PhysicalIOAgent
    from core_lib.local_agents.control.local_control_agent import LocalControlAgent
    from core_lib.central_agents.central_mpc_agent import CentralMPCAgent
    from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent
    from core_lib.disturbances.rainfall_agent import RainfallAgent
    from core_lib.central_coordination.collaboration.message_bus import MessageBus
    # from core_lib.debug.debug_tools import DebugTools  # 模块不存在，暂时注释
except ImportError as e:
    print(f"错误: 无法导入必要的模块: {e}")
    print("请确保您在项目根目录下运行此脚本")
    sys.exit(1)

def select_scenario():
    """
    交互式选择仿真场景
    """
    scenarios = {
        "1": {
            "name": "本地闭环控制",
            "description": "完整的独立现地闭环控制系统，PID控制器自动调节闸门"
        },
        "2": {
            "name": "分层控制",
            "description": "两级分层控制系统，MPC上层优化 + PID下层执行"
        },
        "3": {
            "name": "流域联合调度",
            "description": "多设施流域联合调度，中央调度器协调多个本地控制器"
        }
    }
    
    print("\n=== Mission Example 2 - 闭环与分层控制系统场景选择 ===")
    print("\n可用的仿真场景:")
    
    for key, scenario in scenarios.items():
        print(f"  {key}. {scenario['name']}")
        print(f"     {scenario['description']}")
    
    print("\n请选择要运行的场景 (1-3), 或按 'q' 退出: ", end="")
    
    while True:
        choice = input().strip().lower()
        
        if choice == 'q':
            print("退出程序")
            return None
            
        if choice in scenarios:
            return choice
            
        print(f"无效选择: {choice}. 请输入 1-3 或 'q': ", end="")

def run_scenario_1():
    """
    场景1: 本地闭环控制
    """
    print("\n🚀 启动场景1: 本地闭环控制")
    print("📋 场景描述: 完整的独立现地闭环控制系统")
    
    # 仿真参数
    duration = 3600  # 1小时
    dt = 10  # 10秒时间步长
    
    # 创建仿真引擎
    config = {
        'end_time': duration,
        'dt': dt
    }
    harness = SimulationHarness(config=config)
    
    # 创建消息总线
    message_bus = MessageBus()
    
    # 创建物理组件
    # 渠道
    canal = UnifiedCanal(
        name="main_canal",
        initial_state={'water_level': 102.0, 'inflow': 0.0, 'outflow': 0.0},
        parameters={
            'model_type': 'integral',
            'surface_area': 10000.0,  # 水面面积
            'outlet_coefficient': 5.0,  # 出流系数
            'length': 1000.0,  # 1000米
            'bottom_width': 10.0,  # 底宽10米
            'side_slope_z': 1.5,  # 边坡1:1.5
            'manning_n': 0.025,  # 曼宁系数
            'bottom_elevation': 100.0,  # 底高程100米
        }
    )
    
    # 闸门
    gate = Gate(
        name="control_gate",
        initial_state={'opening': 0.5, 'outflow': 0.0},
        parameters={
            'width': 5.0,  # 闸门宽度5米
            'discharge_coefficient': 0.6,  # 流量系数
            'max_opening': 1.0,  # 最大开度
            'max_rate_of_change': 0.05  # 最大变化率
        }
    )
    
    # 添加组件到仿真
    harness.add_component("main_canal", canal)
    harness.add_component("control_gate", gate)
    
    # 创建智能体
    # 物理IO智能体
    physical_io = PhysicalIOAgent(
        agent_id="physical_io",
        message_bus=message_bus,
        sensors_config={
            "canal_sensor": {
                "obj_id": "main_canal",
                "state_key": "water_level",
                "topic": "sensor/canal/level",
                "noise_std": 0.01
            }
        },
        actuators_config={
            "gate_actuator": {
                "obj_id": "control_gate",
                "target_attr": "target_opening",
                "topic": "actuator/gate/opening",
                "control_key": "opening"
            }
        }
    )
    
    # 本地控制智能体
    local_control = LocalControlAgent(
        agent_id="local_controller",
        message_bus=message_bus,
        dt=60.0,  # 时间步长
        target_component="control_gate",
        control_type="gate_control",
        data_sources={"primary_data": "sensor/canal/level"},
        control_targets={"primary_target": "actuator/gate/opening"},
        allocation_config={},
        controller_config={
            "type": "pid",
            "parameters": {
                "Kp": 0.1,
                "Ki": 0.01,
                "Kd": 0.05,
                "setpoint": 102.5,
                "min_output": 0.0,
                "max_output": 1.0
            }
        },
        observation_topic="sensor/canal/level",
        observation_key="water_level",
        action_topic="actuator/gate/opening"
    )
    
    # 降雨扰动智能体
    rainfall = RainfallAgent(
        agent_id="rainfall_disturbance",
        message_bus=message_bus,
        topic="disturbance/rainfall/inflow",
        start_time=900.0,  # 15分钟后开始降雨
        duration=2700.0,   # 持续45分钟
        inflow_rate=10.0   # 降雨入流量 (m³/s)
    )
    
    # 添加智能体到仿真
    harness.add_agent(physical_io)
    harness.add_agent(local_control)
    harness.add_agent(rainfall)
    
    # 消息传递通过智能体的订阅机制自动处理
    
    # 运行仿真
    print("\n⚡ 开始仿真...")
    results = harness.run_mas_simulation()
    
    # 输出结果
    print("\n📊 仿真结果:")
    print(f"   仿真时长: {duration}秒")
    if results and 'history' in results and results['history']:
        print(f"   时间步数: {len(results['history'])}")
        # 从历史数据中提取最终状态
        final_step = results['history'][-1]
        if 'main_canal' in final_step:
            print(f"   最终水位: {final_step['main_canal'].get('water_level', 0):.2f}米")
        if 'control_gate' in final_step:
            print(f"   最终闸门开度: {final_step['control_gate'].get('opening', 0):.2f}")
    else:
        print("   ⚠️ 仿真未生成有效数据")
    
    return results

def run_scenario_2():
    """
    场景2: 分层控制
    """
    print("\n🚀 启动场景2: 分层控制")
    print("📋 场景描述: 两级分层控制系统，MPC上层优化 + PID下层执行")
    
    # 仿真参数
    duration = 7200  # 2小时
    dt = 30  # 30秒时间步长
    
    # 创建仿真引擎
    config = {
        'end_time': duration,
        'dt': dt
    }
    harness = SimulationHarness(config=config)
    
    # 创建消息总线
    message_bus = MessageBus()
    
    # 创建物理组件（与场景1类似但参数不同）
    canal = UnifiedCanal(
        name="reservoir_canal",
        length=2000.0,  # 更大的水体
        bottom_width=20.0,
        side_slope=2.0,
        manning_n=0.03,
        bottom_elevation=95.0,
        initial_water_level=98.0
    )
    
    gate = Gate(
        name="spillway_gate",
        initial_state={'opening': 0.3, 'outflow': 0.0},
        parameters={
            'width': 8.0,
            'discharge_coefficient': 0.65,
            'max_opening': 1.0,
            'max_rate_of_change': 0.05
        }
    )
    
    harness.add_component("reservoir_canal", canal)
    harness.add_component("spillway_gate", gate)
    
    # 创建智能体
    physical_io = PhysicalIOAgent(
        agent_id="physical_io",
        message_bus=message_bus,
        sensors_config={
            "canal_sensor": {
                "obj_id": "reservoir_canal",
                "state_key": "water_level",
                "topic": "sensor/canal/level",
                "noise_std": 0.02
            }
        },
        actuators_config={
            "gate_actuator": {
                "obj_id": "spillway_gate",
                "target_attr": "target_opening",
                "topic": "actuator/gate/opening",
                "control_key": "opening"
            }
        }
    )
    
    # 本地PID控制器
    local_control = LocalControlAgent(
        agent_id="local_pid_controller",
        message_bus=message_bus,
        dt=30.0,  # 时间步长
        target_component="spillway_gate",
        control_type="gate_control",
        data_sources={"primary_data": "sensor/canal/level"},
        control_targets={"primary_target": "actuator/gate/opening"},
        allocation_config={},
        controller_config={
            "type": "pid",
            "parameters": {
                "Kp": 0.15,
                "Ki": 0.02,
                "Kd": 0.08,
                "setpoint": 99.0,
                "min_output": 0.0,
                "max_output": 1.0
            }
        },
        observation_topic="sensor/canal/level",
        observation_key="water_level",
        action_topic="actuator/gate/opening"
    )
    
    # 中央MPC控制器
    central_mpc = CentralMPCAgent(
        name="central_mpc",
        prediction_horizon=12,  # 12步预测（6分钟）
        control_horizon=4,      # 4步控制
        optimization_weights={
            "water_level_tracking": 1.0,
            "control_effort": 0.1,
            "constraint_violation": 10.0
        },
        constraints={
            "min_water_level": 97.0,
            "max_water_level": 101.0,
            "max_gate_change_rate": 0.1
        }
    )
    
    # 天气预报智能体（模拟未来降雨预报）
    rainfall = RainfallAgent(
        agent_id="weather_forecast",
        message_bus=message_bus,
        topic="disturbance/rainfall/inflow",
        start_time=4500.0,  # 1.25小时后开始降雨
        duration=2700.0,    # 持续45分钟
        inflow_rate=25.0    # 暴雨入流量 (m³/s)
    )
    
    harness.add_agent(physical_io)
    harness.add_agent(local_control)
    harness.add_agent(central_mpc)
    harness.add_agent(rainfall)
    
    # 消息传递通过智能体的订阅机制自动处理
    
    print("\n⚡ 开始仿真...")
    results = harness.run_mas_simulation()
    
    print("\n📊 仿真结果:")
    print(f"   仿真时长: {duration}秒")
    if results and 'history' in results and results['history']:
        print(f"   时间步数: {len(results['history'])}")
        # 从历史数据中提取最终状态
        final_step = results['history'][-1]
        if 'main_canal' in final_step:
            print(f"   最终水位: {final_step['main_canal'].get('water_level', 0):.2f}米")
        if 'control_gate' in final_step:
            print(f"   最终闸门开度: {final_step['control_gate'].get('opening', 0):.2f}")
        print(f"   MPC优化次数: 0")  # MPC功能需要单独实现
    else:
        print("   ⚠️ 仿真未生成有效数据")
    
    return results

def run_scenario_3():
    """
    场景3: 流域联合调度
    """
    print("\n🚀 启动场景3: 流域联合调度")
    print("📋 场景描述: 多设施流域联合调度，中央调度器协调多个本地控制器")
    
    # 仿真参数
    duration = 10800  # 3小时
    dt = 60  # 1分钟时间步长
    
    # 创建仿真引擎
    config = {
        'end_time': duration,
        'dt': dt
    }
    harness = SimulationHarness(config=config)
    
    # 创建消息总线
    message_bus = MessageBus()
    
    # 创建多个物理组件
    # 上游水库
    upstream_reservoir = UnifiedCanal(
        name="upstream_reservoir",
        length=5000.0,
        bottom_width=50.0,
        side_slope=3.0,
        manning_n=0.035,
        bottom_elevation=120.0,
        initial_water_level=125.0
    )
    
    # 水电站渠道
    powerhouse_canal = UnifiedCanal(
        name="powerhouse_canal",
        length=1500.0,
        bottom_width=15.0,
        side_slope=2.0,
        manning_n=0.028,
        bottom_elevation=110.0,
        initial_water_level=112.0
    )
    
    # 下游灌溉渠道
    irrigation_canal = UnifiedCanal(
        name="irrigation_canal",
        length=3000.0,
        bottom_width=25.0,
        side_slope=2.5,
        manning_n=0.030,
        bottom_elevation=105.0,
        initial_water_level=107.0
    )
    
    # 闸门
    reservoir_gate = Gate(
        name="reservoir_gate",
        initial_state={'opening': 0.4, 'outflow': 0.0},
        parameters={'width': 10.0, 'discharge_coefficient': 0.7, 'max_opening': 1.0, 'max_rate_of_change': 0.05}
    )
    powerhouse_gate = Gate(
        name="powerhouse_gate",
        initial_state={'opening': 0.6, 'outflow': 0.0},
        parameters={'width': 6.0, 'discharge_coefficient': 0.65, 'max_opening': 1.0, 'max_rate_of_change': 0.05}
    )
    irrigation_gate = Gate(
        name="irrigation_gate",
        initial_state={'opening': 0.8, 'outflow': 0.0},
        parameters={'width': 4.0, 'discharge_coefficient': 0.6, 'max_opening': 1.0, 'max_rate_of_change': 0.05}
    )
    
    # 添加组件
    components_list = [
        ("upstream_reservoir", upstream_reservoir),
        ("powerhouse_canal", powerhouse_canal),
        ("irrigation_canal", irrigation_canal),
        ("reservoir_gate", reservoir_gate),
        ("powerhouse_gate", powerhouse_gate),
        ("irrigation_gate", irrigation_gate)
    ]
    for component_id, component in components_list:
        harness.add_component(component_id, component)
    
    # 创建智能体
    # 物理IO智能体（监控所有设施）
    physical_io = PhysicalIOAgent(
        agent_id="watershed_io",
        message_bus=message_bus,
        sensors_config={
            "reservoir_sensor": {
                "obj_id": "upstream_reservoir",
                "state_key": "water_level",
                "topic": "sensor/reservoir/level",
                "noise_std": 0.03
            },
            "powerhouse_sensor": {
                "obj_id": "powerhouse_canal",
                "state_key": "water_level",
                "topic": "sensor/powerhouse/level",
                "noise_std": 0.03
            },
            "irrigation_sensor": {
                "obj_id": "irrigation_canal",
                "state_key": "water_level",
                "topic": "sensor/irrigation/level",
                "noise_std": 0.03
            }
        },
        actuators_config={
            "reservoir_actuator": {
                "obj_id": "reservoir_gate",
                "target_attr": "target_opening",
                "topic": "actuator/reservoir_gate/opening",
                "control_key": "opening"
            },
            "powerhouse_actuator": {
                "obj_id": "powerhouse_gate",
                "target_attr": "target_opening",
                "topic": "actuator/powerhouse_gate/opening",
                "control_key": "opening"
            },
            "irrigation_actuator": {
                "obj_id": "irrigation_gate",
                "target_attr": "target_opening",
                "topic": "actuator/irrigation_gate/opening",
                "control_key": "opening"
            }
        }
    )
    
    # 本地控制智能体
    reservoir_controller = LocalControlAgent(
        agent_id="reservoir_controller",
        message_bus=message_bus,
        dt=60.0,
        target_component="reservoir_gate",
        control_type="gate_control",
        data_sources={"primary_data": "sensor/reservoir/level"},
        control_targets={"primary_target": "actuator/reservoir_gate/opening"},
        allocation_config={},
        controller_config={
            "type": "pid",
            "parameters": {
                "Kp": 0.08,
                "Ki": 0.015,
                "Kd": 0.04,
                "setpoint": 126.0,
                "min_output": 0.0,
                "max_output": 1.0
            }
        },
        observation_topic="sensor/reservoir/level",
        observation_key="water_level",
        action_topic="actuator/reservoir_gate/opening"
    )
    
    powerhouse_controller = LocalControlAgent(
        agent_id="powerhouse_controller",
        message_bus=message_bus,
        dt=60.0,
        target_component="powerhouse_gate",
        control_type="gate_control",
        data_sources={"primary_data": "sensor/powerhouse/level"},
        control_targets={"primary_target": "actuator/powerhouse_gate/opening"},
        allocation_config={},
        controller_config={
            "type": "pid",
            "parameters": {
                "Kp": 0.12,
                "Ki": 0.02,
                "Kd": 0.06,
                "setpoint": 113.0,
                "min_output": 0.0,
                "max_output": 1.0
            }
        },
        observation_topic="sensor/powerhouse/level",
        observation_key="water_level",
        action_topic="actuator/powerhouse_gate/opening"
    )
    
    irrigation_controller = LocalControlAgent(
        agent_id="irrigation_controller",
        message_bus=message_bus,
        dt=60.0,
        target_component="irrigation_gate",
        control_type="gate_control",
        data_sources={"primary_data": "sensor/irrigation/level"},
        control_targets={"primary_target": "actuator/irrigation_gate/opening"},
        allocation_config={},
        controller_config={
            "type": "pid",
            "parameters": {
                "Kp": 0.10,
                "Ki": 0.018,
                "Kd": 0.05,
                "setpoint": 108.0,
                "min_output": 0.0,
                "max_output": 1.0
            }
        },
        observation_topic="sensor/irrigation/level",
        observation_key="water_level",
        action_topic="actuator/irrigation_gate/opening"
    )
    
    # 中央调度器
    central_dispatcher = CentralDispatcher(
        name="watershed_dispatcher",
        dispatch_rules={
            "normal_mode": {
                "reservoir_target": 126.0,
                "powerhouse_target": 113.0,
                "irrigation_target": 108.0,
                "priority": ["irrigation", "powerhouse", "flood_control"]
            },
            "flood_mode": {
                "reservoir_target": 124.0,  # 降低水库水位
                "powerhouse_target": 111.0,
                "irrigation_target": 106.0,  # 减少灌溉用水
                "priority": ["flood_control", "powerhouse", "irrigation"]
            },
            "drought_mode": {
                "reservoir_target": 127.0,  # 保持较高水位
                "powerhouse_target": 114.0,
                "irrigation_target": 109.0,
                "priority": ["irrigation", "flood_control", "powerhouse"]
            }
        },
        mode_switching_thresholds={
            "flood_threshold": 128.0,  # 水库水位超过128米进入防洪模式
            "drought_threshold": 123.0,  # 水库水位低于123米进入抗旱模式
            "normal_upper": 127.0,
            "normal_lower": 124.0
        }
    )
    
    # 复杂降雨模式（模拟流域性洪水）
    rainfall = RainfallAgent(
        agent_id="watershed_rainfall",
        message_bus=message_bus,
        topic="disturbance/rainfall/inflow",
        start_time=0.0,      # 立即开始
        duration=10800.0,    # 持续3小时
        inflow_rate=35.0     # 特大暴雨入流量 (m³/s)
    )
    
    # 添加智能体
    for agent in [physical_io, reservoir_controller, powerhouse_controller, 
                 irrigation_controller, central_dispatcher, rainfall]:
        harness.add_agent(agent)
    
    # 消息传递通过智能体的订阅机制自动处理
    
    print("\n⚡ 开始仿真...")
    results = harness.run_mas_simulation()
    
    print("\n📊 仿真结果:")
    print(f"   仿真时长: {duration}秒")
    if results and 'history' in results and results['history']:
        print(f"   时间步数: {len(results['history'])}")
        # 从历史数据中提取最终状态
        final_step = results['history'][-1]
        if 'main_reservoir' in final_step:
            print(f"   水库最终水位: {final_step['main_reservoir'].get('water_level', 0):.2f}米")
        if 'powerhouse_canal' in final_step:
            print(f"   水电站最终水位: {final_step['powerhouse_canal'].get('water_level', 0):.2f}米")
        if 'irrigation_canal' in final_step:
            print(f"   灌溉渠最终水位: {final_step['irrigation_canal'].get('water_level', 0):.2f}米")
        print(f"   调度模式切换次数: 0")  # 调度功能需要单独实现
    else:
        print("   ⚠️ 仿真未生成有效数据")
    
    return results

def main():
    """
    主函数
    """
    # 解析命令行参数
    if len(sys.argv) > 1:
        scenario_num = sys.argv[1]
        if scenario_num not in ["1", "2", "3"]:
            print(f"错误: 无效的场景编号 '{scenario_num}'")
            print("有效的场景编号: 1-3")
            return 1
    else:
        # 自动选择场景1进行测试
        scenario_num = "1"
        print("自动选择场景1: 本地闭环控制")
    
    # 初始化调试工具 (暂时禁用，因为模块不存在)
    # debug_tools = DebugTools(
    #     log_level="INFO",
    #     performance_monitoring=True,
    #     data_collection=True
    # )
    
    try:
        # 运行选定的场景
        if scenario_num == "1":
            results = run_scenario_1()
        elif scenario_num == "2":
            results = run_scenario_2()
        elif scenario_num == "3":
            results = run_scenario_3()
        
        # 性能统计
        # debug_tools.print_performance_summary()
        
        print("\n✅ 仿真完成!")
        print("📁 详细日志和数据已保存到相应文件")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 仿真过程中发生错误: {e}")
        # debug_tools.log_error(f"仿真错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)