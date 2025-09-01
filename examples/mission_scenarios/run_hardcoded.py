#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景硬编码运行脚本

本脚本通过硬编码方式直接在Python中构建和运行仿真场景，
不依赖外部配置文件，适合学习和理解场景逻辑。

支持的场景:
1. 引绰济辽工程仿真

使用方法:
    python run_hardcoded.py [场景编号]
    
    场景编号:
    1 - 引绰济辽工程仿真
    
    如果不提供场景编号，将显示交互式菜单。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from debug_tools import DebugToolsManager
from performance_monitor import PerformanceMonitor

def run_yinchuojiliao_hardcoded():
    """
    硬编码方式运行引绰济辽工程仿真
    """
    print("\n=== 引绰济辽工程仿真 (硬编码方式) ===")
    print("正在构建仿真环境...")
    
    # 初始化调试工具
    debug_manager = DebugToolsManager()
    debug_manager.setup_logging("yinchuojiliao_hardcoded")
    
    # 初始化性能监控
    perf_monitor = PerformanceMonitor()
    perf_monitor.start_monitoring()
    
    try:
        # 导入必要的模块
        from simulation_engine import SimulationEngine
        from components import Reservoir, UnifiedCanal, Pipe, Gate, Valve
        from agents import DigitalTwinAgent, CentralDispatcherAgent, EmergencyAgent, CsvInflowAgent
        from controllers import PIDController
        import pandas as pd
        
        # 创建仿真引擎
        engine = SimulationEngine(dt=1.0)  # 1小时时间步长
        
        # === 创建物理组件 ===
        print("创建物理组件...")
        
        # 水库
        wendegen_reservoir = Reservoir(
            id="wendegen_reservoir",
            initial_state={"water_level": 350.0, "storage": 1.5e9},
            parameters={"surface_area": 5.0e7, "max_capacity": 2.0e9}
        )
        
        connection_pool = Reservoir(
            id="connection_pool",
            initial_state={"water_level": 300.0, "storage": 1.0e8},
            parameters={"surface_area": 1.0e6, "max_capacity": 2.0e8}
        )
        
        terminal_pool = Reservoir(
            id="terminal_pool",
            initial_state={"water_level": 250.0, "storage": 5.0e7},
            parameters={"surface_area": 5.0e5, "max_capacity": 1.0e8}
        )
        
        # 隧洞
        tunnel_1 = UnifiedCanal(
            id="tunnel_1",
            model_type="integral",
            initial_state={"water_level": 340.0, "flow_rate": 50.0},
            parameters={"length": 5000.0, "cross_section_area": 100.0, "roughness": 0.025}
        )
        
        tunnel_2 = UnifiedCanal(
            id="tunnel_2",
            model_type="integral",
            initial_state={"water_level": 320.0, "flow_rate": 50.0},
            parameters={"length": 8000.0, "cross_section_area": 120.0, "roughness": 0.025}
        )
        
        tunnel_3 = UnifiedCanal(
            id="tunnel_3",
            model_type="integral",
            initial_state={"water_level": 280.0, "flow_rate": 50.0},
            parameters={"length": 6000.0, "cross_section_area": 100.0, "roughness": 0.025}
        )
        
        # 管道
        pipe_1 = Pipe(
            id="pipe_1",
            initial_state={"pressure": 2.5e6, "flow_rate": 45.0},
            parameters={"length": 3000.0, "diameter": 3.0, "roughness": 0.02}
        )
        
        pipe_2 = Pipe(
            id="pipe_2",
            initial_state={"pressure": 2.0e6, "flow_rate": 45.0},
            parameters={"length": 4000.0, "diameter": 2.8, "roughness": 0.02}
        )
        
        # 闸门和阀门
        inlet_gate = Gate(
            id="inlet_gate",
            initial_state={"opening": 0.6, "flow_rate": 50.0},
            parameters={"max_flow_capacity": 100.0, "gate_type": "radial"}
        )
        
        tunnel1_gate = Gate(
            id="tunnel1_gate",
            initial_state={"opening": 0.7, "flow_rate": 50.0},
            parameters={"max_flow_capacity": 80.0, "gate_type": "sluice"}
        )
        
        pipe1_valve = Valve(
            id="pipe1_valve",
            initial_state={"opening": 0.8, "flow_rate": 45.0},
            parameters={"max_flow_capacity": 60.0, "valve_type": "butterfly"}
        )
        
        outlet_valve = Valve(
            id="outlet_valve",
            initial_state={"opening": 0.75, "flow_rate": 45.0},
            parameters={"max_flow_capacity": 60.0, "valve_type": "gate"}
        )
        
        # 添加组件到仿真引擎
        components = [
            wendegen_reservoir, connection_pool, terminal_pool,
            tunnel_1, tunnel_2, tunnel_3,
            pipe_1, pipe_2,
            inlet_gate, tunnel1_gate, pipe1_valve, outlet_valve
        ]
        
        for component in components:
            engine.add_component(component)
        
        # === 定义系统拓扑 ===
        print("定义系统拓扑...")
        connections = [
            ("wendegen_reservoir", "inlet_gate"),
            ("inlet_gate", "tunnel_1"),
            ("tunnel_1", "tunnel1_gate"),
            ("tunnel1_gate", "connection_pool"),
            ("connection_pool", "tunnel_2"),
            ("tunnel_2", "pipe_1"),
            ("pipe_1", "pipe1_valve"),
            ("pipe1_valve", "tunnel_3"),
            ("tunnel_3", "pipe_2"),
            ("pipe_2", "outlet_valve"),
            ("outlet_valve", "terminal_pool")
        ]
        
        for upstream, downstream in connections:
            engine.add_connection(upstream, downstream)
        
        # === 创建控制器 ===
        print("创建控制器...")
        
        # PID控制器 - 控制隧洞1水位
        taoriver_ctrl = PIDController(
            id="taoriver_ctrl",
            controlled_id="tunnel1_gate",
            observed_id="tunnel_1",
            observation_key="water_level",
            config={
                "Kp": -0.1,
                "Ki": -0.01,
                "Kd": -0.005,
                "setpoint": 340.0,
                "output_limits": (0.1, 1.0)
            }
        )
        
        # PID控制器 - 控制管道1压力
        pipe_pressure_ctrl = PIDController(
            id="pipe_pressure_ctrl",
            controlled_id="pipe1_valve",
            observed_id="pipe_1",
            observation_key="pressure",
            config={
                "Kp": -1e-7,
                "Ki": -1e-8,
                "Kd": -5e-8,
                "setpoint": 2.5e6,
                "output_limits": (0.2, 1.0)
            }
        )
        
        engine.add_controller(taoriver_ctrl)
        engine.add_controller(pipe_pressure_ctrl)
        
        # === 创建智能体 ===
        print("创建智能体...")
        
        # 数字孪生体
        digital_twins = []
        for component in components:
            twin = DigitalTwinAgent(
                id=f"{component.id}_twin",
                config={
                    "simulated_object_id": component.id,
                    "state_topic": f"state/{component.id}",
                    "update_frequency": 1.0
                }
            )
            digital_twins.append(twin)
            engine.add_agent(twin)
        
        # 中央调度智能体
        central_dispatcher = CentralDispatcherAgent(
            id="central_dispatcher",
            config={
                "monitored_component_id": "terminal_pool",
                "controlled_component_id": "inlet_gate",
                "target_water_level": 250.0,
                "control_gain": 0.05,
                "dispatch_interval": 6.0  # 每6小时调度一次
            }
        )
        engine.add_agent(central_dispatcher)
        
        # 应急处理智能体
        emergency_agent = EmergencyAgent(
            id="emergency_agent",
            config={
                "monitored_component_ids": ["pipe_1", "pipe_2"],
                "pressure_threshold": 1.5e6,
                "emergency_actions": {
                    "close_valves": ["pipe1_valve", "outlet_valve"],
                    "reduce_gates": ["inlet_gate"]
                }
            }
        )
        engine.add_agent(emergency_agent)
        
        # CSV入流数据智能体
        data_file = project_root / "mission" / "scenarios" / "yinchuojiliao" / "data" / "historical_inflow.csv"
        if data_file.exists():
            csv_inflow_agent = CsvInflowAgent(
                id="csv_inflow_agent",
                config={
                    "target_component_id": "wendegen_reservoir",
                    "csv_file_path": str(data_file),
                    "time_column": "time",
                    "inflow_column": "inflow",
                    "interpolation_method": "linear"
                }
            )
            engine.add_agent(csv_inflow_agent)
        
        # === 运行仿真 ===
        print("\n开始仿真运行...")
        print(f"仿真时长: 168小时 (7天)")
        print(f"时间步长: 1.0小时")
        
        # 运行仿真
        results = engine.run_simulation(duration=168.0)
        
        # === 保存结果 ===
        output_file = project_root / "mission" / "scenarios" / "yinchuojiliao" / "output_hardcoded.yml"
        engine.save_results(str(output_file))
        
        print(f"\n仿真完成！")
        print(f"结果已保存到: {output_file}")
        
        # 显示关键统计信息
        print("\n=== 仿真结果摘要 ===")
        final_states = engine.get_final_states()
        
        print(f"文得根水库最终水位: {final_states['wendegen_reservoir']['water_level']:.2f} m")
        print(f"末端水池最终水位: {final_states['terminal_pool']['water_level']:.2f} m")
        print(f"隧洞1最终流量: {final_states['tunnel_1']['flow_rate']:.2f} m³/s")
        print(f"管道1最终压力: {final_states['pipe_1']['pressure']:.2e} Pa")
        
        # 性能统计
        perf_stats = perf_monitor.get_statistics()
        print(f"\n=== 性能统计 ===")
        print(f"仿真用时: {perf_stats['total_time']:.2f} 秒")
        print(f"平均步长用时: {perf_stats['avg_step_time']:.4f} 秒")
        print(f"内存使用峰值: {perf_stats['peak_memory']:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 仿真运行失败: {e}")
        debug_manager.log_error(f"硬编码仿真失败: {e}")
        return False
    
    finally:
        perf_monitor.stop_monitoring()
        debug_manager.cleanup()

def show_menu():
    """
    显示交互式场景选择菜单
    """
    print("\n=== 场景硬编码运行器 ===")
    print("请选择要运行的场景:")
    print("1. 引绰济辽工程仿真")
    print("0. 退出")
    
    while True:
        try:
            choice = input("\n请输入场景编号 (0-1): ").strip()
            if choice == "0":
                print("退出程序。")
                return None
            elif choice == "1":
                return 1
            else:
                print("❌ 无效选择，请输入 0-1 之间的数字。")
        except KeyboardInterrupt:
            print("\n\n程序被用户中断。")
            return None
        except Exception as e:
            print(f"❌ 输入错误: {e}")

def main():
    """
    主函数
    """
    # 检查命令行参数
    if len(sys.argv) > 1:
        try:
            scenario_num = int(sys.argv[1])
        except ValueError:
            print("❌ 场景编号必须是整数")
            sys.exit(1)
    else:
        scenario_num = show_menu()
        if scenario_num is None:
            sys.exit(0)
    
    # 运行对应场景
    success = False
    if scenario_num == 1:
        success = run_yinchuojiliao_hardcoded()
    else:
        print(f"❌ 不支持的场景编号: {scenario_num}")
        sys.exit(1)
    
    if success:
        print("\n✅ 场景运行成功完成！")
        sys.exit(0)
    else:
        print("\n❌ 场景运行失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()