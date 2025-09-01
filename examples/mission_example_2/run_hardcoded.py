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
    from core_lib.core_engine.simulation_harness import SimulationHarness
    from core_lib.hydro_nodes.unified_canal import UnifiedCanal
    from core_lib.hydro_nodes.gate import Gate
    from core_lib.local_agents.physical_io_agent import PhysicalIOAgent
    from core_lib.local_agents.local_control_agent import LocalControlAgent
    from core_lib.central_agents.central_mpc_agent import CentralMPCAgent
    from core_lib.central_agents.central_dispatcher import CentralDispatcher
    from core_lib.disturbances.rainfall_agent import RainfallAgent
    from core_lib.debug.debug_tools import DebugTools
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
    harness = SimulationHarness(
        duration=duration,
        dt=dt,
        description="本地闭环控制系统仿真"
    )
    
    # 创建物理组件
    # 渠道
    canal = UnifiedCanal(
        name="main_canal",
        length=1000.0,  # 1000米
        bottom_width=10.0,  # 底宽10米
        side_slope=1.5,  # 边坡1:1.5
        manning_n=0.025,  # 曼宁系数
        bottom_elevation=100.0,  # 底高程100米
        initial_water_level=102.0  # 初始水位102米
    )
    
    # 闸门
    gate = Gate(
        name="control_gate",
        gate_width=5.0,  # 闸门宽度5米
        discharge_coefficient=0.6,  # 流量系数
        initial_opening=0.5  # 初始开度50%
    )
    
    # 添加组件到仿真
    harness.add_component(canal)
    harness.add_component(gate)
    
    # 创建智能体
    # 物理IO智能体
    physical_io = PhysicalIOAgent(
        name="physical_io",
        sensor_components=["main_canal"],
        actuator_components=["control_gate"],
        sensor_noise=0.01,  # 1cm传感器噪声
        actuator_delay=5.0  # 5秒执行器延迟
    )
    
    # 本地控制智能体
    local_control = LocalControlAgent(
        name="local_controller",
        target_water_level=102.5,  # 目标水位102.5米
        pid_params={
            "kp": 0.1,  # 比例增益
            "ki": 0.01,  # 积分增益
            "kd": 0.05,  # 微分增益
            "output_min": 0.0,  # 最小输出
            "output_max": 1.0   # 最大输出
        }
    )
    
    # 降雨扰动智能体
    rainfall = RainfallAgent(
        name="rainfall_disturbance",
        target_component="main_canal",
        rainfall_pattern=[
            {"time": 0, "intensity": 0.0},
            {"time": 900, "intensity": 5.0},  # 15分钟后开始降雨
            {"time": 1800, "intensity": 10.0},  # 30分钟后增强
            {"time": 2700, "intensity": 2.0},  # 45分钟后减弱
            {"time": 3600, "intensity": 0.0}   # 1小时后停止
        ]
    )
    
    # 添加智能体到仿真
    harness.add_agent(physical_io)
    harness.add_agent(local_control)
    harness.add_agent(rainfall)
    
    # 配置消息主题
    harness.configure_messaging({
        "water_level_sensor": ["physical_io", "local_controller"],
        "gate_control": ["local_controller", "physical_io"],
        "rainfall_data": ["rainfall_disturbance", "physical_io"]
    })
    
    # 运行仿真
    print("\n⚡ 开始仿真...")
    results = harness.run()
    
    # 输出结果
    print("\n📊 仿真结果:")
    print(f"   仿真时长: {duration}秒")
    print(f"   时间步数: {len(results.get('time', []))}")
    print(f"   最终水位: {results.get('water_levels', [0])[-1]:.2f}米")
    print(f"   最终闸门开度: {results.get('gate_openings', [0])[-1]:.2f}")
    
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
    harness = SimulationHarness(
        duration=duration,
        dt=dt,
        description="分层控制系统仿真"
    )
    
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
        gate_width=8.0,
        discharge_coefficient=0.65,
        initial_opening=0.3
    )
    
    harness.add_component(canal)
    harness.add_component(gate)
    
    # 创建智能体
    physical_io = PhysicalIOAgent(
        name="physical_io",
        sensor_components=["reservoir_canal"],
        actuator_components=["spillway_gate"],
        sensor_noise=0.02,
        actuator_delay=10.0
    )
    
    # 本地PID控制器
    local_control = LocalControlAgent(
        name="local_pid_controller",
        target_water_level=99.0,  # 初始目标水位
        pid_params={
            "kp": 0.15,
            "ki": 0.02,
            "kd": 0.08,
            "output_min": 0.0,
            "output_max": 1.0
        }
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
        name="weather_forecast",
        target_component="reservoir_canal",
        rainfall_pattern=[
            {"time": 0, "intensity": 0.0},
            {"time": 3600, "intensity": 0.0},
            {"time": 4500, "intensity": 15.0},  # 预报1.25小时后有大雨
            {"time": 5400, "intensity": 25.0},  # 1.5小时后暴雨
            {"time": 6300, "intensity": 8.0},   # 1.75小时后减弱
            {"time": 7200, "intensity": 0.0}
        ],
        forecast_enabled=True,  # 启用预报功能
        forecast_horizon=3600   # 1小时预报时长
    )
    
    harness.add_agent(physical_io)
    harness.add_agent(local_control)
    harness.add_agent(central_mpc)
    harness.add_agent(rainfall)
    
    # 配置消息主题
    harness.configure_messaging({
        "water_level_sensor": ["physical_io", "local_pid_controller", "central_mpc"],
        "gate_control": ["local_pid_controller", "physical_io"],
        "setpoint_update": ["central_mpc", "local_pid_controller"],
        "weather_forecast": ["weather_forecast", "central_mpc"],
        "rainfall_data": ["weather_forecast", "physical_io"]
    })
    
    print("\n⚡ 开始仿真...")
    results = harness.run()
    
    print("\n📊 仿真结果:")
    print(f"   仿真时长: {duration}秒")
    print(f"   时间步数: {len(results.get('time', []))}")
    print(f"   最终水位: {results.get('water_levels', [0])[-1]:.2f}米")
    print(f"   最终闸门开度: {results.get('gate_openings', [0])[-1]:.2f}")
    print(f"   MPC优化次数: {results.get('mpc_optimizations', 0)}")
    
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
    harness = SimulationHarness(
        duration=duration,
        dt=dt,
        description="流域联合调度系统仿真"
    )
    
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
    reservoir_gate = Gate(name="reservoir_gate", gate_width=10.0, discharge_coefficient=0.7, initial_opening=0.4)
    powerhouse_gate = Gate(name="powerhouse_gate", gate_width=6.0, discharge_coefficient=0.65, initial_opening=0.6)
    irrigation_gate = Gate(name="irrigation_gate", gate_width=4.0, discharge_coefficient=0.6, initial_opening=0.8)
    
    # 添加组件
    for component in [upstream_reservoir, powerhouse_canal, irrigation_canal, 
                     reservoir_gate, powerhouse_gate, irrigation_gate]:
        harness.add_component(component)
    
    # 创建智能体
    # 物理IO智能体（监控所有设施）
    physical_io = PhysicalIOAgent(
        name="watershed_io",
        sensor_components=["upstream_reservoir", "powerhouse_canal", "irrigation_canal"],
        actuator_components=["reservoir_gate", "powerhouse_gate", "irrigation_gate"],
        sensor_noise=0.03,
        actuator_delay=15.0
    )
    
    # 本地控制智能体
    reservoir_controller = LocalControlAgent(
        name="reservoir_controller",
        target_water_level=126.0,
        pid_params={"kp": 0.08, "ki": 0.015, "kd": 0.04, "output_min": 0.0, "output_max": 1.0}
    )
    
    powerhouse_controller = LocalControlAgent(
        name="powerhouse_controller",
        target_water_level=113.0,
        pid_params={"kp": 0.12, "ki": 0.02, "kd": 0.06, "output_min": 0.0, "output_max": 1.0}
    )
    
    irrigation_controller = LocalControlAgent(
        name="irrigation_controller",
        target_water_level=108.0,
        pid_params={"kp": 0.10, "ki": 0.018, "kd": 0.05, "output_min": 0.0, "output_max": 1.0}
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
        name="watershed_rainfall",
        target_component="upstream_reservoir",
        rainfall_pattern=[
            {"time": 0, "intensity": 2.0},
            {"time": 1800, "intensity": 5.0},   # 30分钟后增强
            {"time": 3600, "intensity": 20.0},  # 1小时后暴雨
            {"time": 5400, "intensity": 35.0},  # 1.5小时后特大暴雨
            {"time": 7200, "intensity": 15.0},  # 2小时后减弱
            {"time": 9000, "intensity": 5.0},   # 2.5小时后小雨
            {"time": 10800, "intensity": 0.0}   # 3小时后停止
        ]
    )
    
    # 添加智能体
    for agent in [physical_io, reservoir_controller, powerhouse_controller, 
                 irrigation_controller, central_dispatcher, rainfall]:
        harness.add_agent(agent)
    
    # 配置复杂的消息主题
    harness.configure_messaging({
        "water_level_sensors": ["watershed_io", "reservoir_controller", "powerhouse_controller", 
                               "irrigation_controller", "watershed_dispatcher"],
        "gate_controls": ["reservoir_controller", "powerhouse_controller", "irrigation_controller", "watershed_io"],
        "dispatch_commands": ["watershed_dispatcher", "reservoir_controller", "powerhouse_controller", "irrigation_controller"],
        "system_status": ["watershed_io", "watershed_dispatcher"],
        "rainfall_data": ["watershed_rainfall", "watershed_io", "watershed_dispatcher"]
    })
    
    print("\n⚡ 开始仿真...")
    results = harness.run()
    
    print("\n📊 仿真结果:")
    print(f"   仿真时长: {duration}秒")
    print(f"   时间步数: {len(results.get('time', []))}")
    print(f"   水库最终水位: {results.get('reservoir_levels', [0])[-1]:.2f}米")
    print(f"   水电站最终水位: {results.get('powerhouse_levels', [0])[-1]:.2f}米")
    print(f"   灌溉渠最终水位: {results.get('irrigation_levels', [0])[-1]:.2f}米")
    print(f"   调度模式切换次数: {results.get('mode_switches', 0)}")
    
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
        # 交互式选择
        scenario_num = select_scenario()
        if scenario_num is None:
            return 0
    
    # 初始化调试工具
    debug_tools = DebugTools(
        log_level="INFO",
        performance_monitoring=True,
        data_collection=True
    )
    
    try:
        # 运行选定的场景
        if scenario_num == "1":
            results = run_scenario_1()
        elif scenario_num == "2":
            results = run_scenario_2()
        elif scenario_num == "3":
            results = run_scenario_3()
        
        # 性能统计
        debug_tools.print_performance_summary()
        
        print("\n✅ 仿真完成!")
        print("📁 详细日志和数据已保存到相应文件")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 仿真过程中发生错误: {e}")
        debug_tools.log_error(f"仿真错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)