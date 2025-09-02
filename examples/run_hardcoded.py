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
            }
        }
        
        self.debug_mode = False
        self.performance_monitor = False
    
    def create_getting_started_simulation(self):
        """创建入门示例仿真"""
        print("构建入门示例：基础水库-闸门系统...")
        
        # 创建核心组件
        message_bus = MessageBus()
        builder = SimulationBuilder()
        
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
            if example_key == "getting_started":
                harness = self.create_getting_started_simulation()
            elif example_key == "multi_component":
                harness = self.create_multi_component_simulation()
            elif example_key in ["event_driven_agents", "hierarchical_control"]:
                harness = self.create_agent_based_simulation(example_key)
            else:
                # 其他示例的通用处理
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