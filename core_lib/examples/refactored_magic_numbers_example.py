#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构魔数后的使用示例

这个示例展示了如何使用新的配置系统来避免硬编码魔数，
提高代码的可维护性和可读性。

作者: CHS-SDK Team
版本: 1.0.0
创建时间: 2024
"""

import sys
import os
from pathlib import Path

# 添加core_lib到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core_lib.config.parameter_manager import get_parameter_manager, initialize_parameter_manager
from core_lib.config.constants import PhysicalConstants, HydraulicConstants, StatusConstants
from core_lib.physical_objects.pump import Pump
from core_lib.physical_objects.valve import Valve
from core_lib.physical_objects.unified_canal import UnifiedCanal
from core_lib.local_agents.ontology_simulation_agent import OntologySimulationAgent
from core_lib.central_coordination.collaboration.message_bus import MessageBus


def demonstrate_parameter_manager():
    """演示参数管理器的使用"""
    print("=== 参数管理器演示 ===")
    
    # 初始化参数管理器（使用默认配置）
    param_manager = initialize_parameter_manager()
    
    # 获取物理常量
    gravity = param_manager.get_physical_constant('GRAVITY_ACCELERATION')
    water_density = param_manager.get_physical_constant('WATER_DENSITY')
    print(f"重力加速度: {gravity} m/s²")
    print(f"水密度: {water_density} kg/m³")
    
    # 获取水力工程常量
    weir_exponent = param_manager.get_hydraulic_constant('WEIR_FLOW_EXPONENT')
    print(f"堰流公式指数: {weir_exponent}")
    
    # 获取默认参数
    default_diameter = param_manager.get_parameter('physical_objects', 'default_diameter')
    default_efficiency = param_manager.get_parameter('pump_parameters', 'default_efficiency')
    print(f"默认直径: {default_diameter} m")
    print(f"默认效率: {default_efficiency}")
    
    # 设置自定义参数
    param_manager.set_parameter('business_scenarios', 'pump_station.upstream_level', 30.0)
    param_manager.set_parameter('business_scenarios', 'pump_station.downstream_level', 10.0)
    
    # 获取自定义参数
    upstream_level = param_manager.get_parameter('business_scenarios', 'pump_station.upstream_level')
    downstream_level = param_manager.get_parameter('business_scenarios', 'pump_station.downstream_level')
    print(f"自定义上游水位: {upstream_level} m")
    print(f"自定义下游水位: {downstream_level} m")
    
    print()


def demonstrate_pump_with_config():
    """演示使用配置系统的泵"""
    print("=== 泵配置演示 ===")
    
    # 创建泵的初始状态和参数
    initial_state = {
        'outflow': 0.0,
        'power_draw_kw': 0.0,
        'efficiency': 0.0,
        'status': StatusConstants.STATUS_OFF
    }
    
    parameters = {
        'max_flow_rate': 50.0,  # m³/s
        'max_head': 20.0,       # m
        'power_consumption_kw': 100.0,  # kW
        'efficiency': 0.85
    }
    
    # 创建泵实例
    pump = Pump("test_pump", initial_state, parameters)
    
    # 模拟动作
    action = {
        'upstream_level': 25.0,
        'downstream_level': 8.0
    }
    
    # 执行步进
    state = pump.step(action, 1.0)
    
    print(f"泵状态: {state}")
    print(f"出流量: {state['outflow']:.2f} m³/s")
    print(f"功率消耗: {state['power_draw_kw']:.2f} kW")
    print(f"效率: {state['efficiency']:.2f}")
    
    print()


def demonstrate_valve_with_config():
    """演示使用配置系统的阀门"""
    print("=== 阀门配置演示 ===")
    
    # 创建阀门的初始状态和参数
    initial_state = {
        'opening': 0.0,
        'outflow': 0.0
    }
    
    parameters = {
        'discharge_coefficient': 0.7,
        'diameter': 0.8  # m
    }
    
    # 创建阀门实例
    valve = Valve("test_valve", initial_state, parameters)
    
    # 模拟动作
    action = {
        'upstream_head': 10.0,
        'downstream_head': 5.0,
        'control_signal': 50.0  # 50% 开度
    }
    
    # 执行步进
    state = valve.step(action, 1.0)
    
    print(f"阀门状态: {state}")
    print(f"开度: {state['opening']:.1f}%")
    print(f"出流量: {state['outflow']:.2f} m³/s")
    print(f"流量系数: {state['discharge_coefficient']:.2f}")
    
    print()


def demonstrate_canal_with_config():
    """演示使用配置系统的渠道"""
    print("=== 渠道配置演示 ===")
    
    # 创建渠道的初始状态和参数
    initial_state = {
        'water_level': 2.0,
        'inflow': 15.0,
        'outflow': 12.0
    }
    
    parameters = {
        'model_type': 'integral',
        'surface_area': 5000.0,  # m²
        'outlet_coefficient': 8.0
    }
    
    # 创建渠道实例
    canal = UnifiedCanal("test_canal", initial_state, parameters)
    
    # 模拟动作
    action = {
        'inflow': 20.0
    }
    
    # 执行步进
    state = canal.step(action, 1.0)
    
    print(f"渠道状态: {state}")
    print(f"水位: {state['water_level']:.2f} m")
    print(f"入流量: {state['inflow']:.2f} m³/s")
    print(f"出流量: {state['outflow']:.2f} m³/s")
    
    print()


def demonstrate_simulation_agent_with_config():
    """演示使用配置系统的仿真智能体"""
    print("=== 仿真智能体配置演示 ===")
    
    # 创建消息总线
    message_bus = MessageBus()
    
    # 创建配置
    config = {
        'initial_state': {
            'upstream_level': 5.2,
            'downstream_level': 4.3,
            'inflow': 12.5,
            'gate_opening': 0.3
        },
        'physical_system': {
            'channel_surface_area': 8500
        },
        'gate_parameters': {
            'max_speed': 0.08,
            'flow_coefficient': 25
        },
        'simulation': {
            'step': 30.0,
            'time_step': 1.0,
            'print_interval': 5
        },
        'sensors': {
            'noise_level': 0.005,
            'inflow_noise_range': 0.08
        }
    }
    
    # 创建仿真智能体
    agent = OntologySimulationAgent("sim_agent", message_bus, config)
    
    print(f"仿真智能体已创建")
    print(f"重力加速度: {agent.GRAVITY_ACCELERATION} m/s²")
    print(f"堰流公式指数: {agent.WEIR_FLOW_EXPONENT}")
    print(f"默认时间步长: {agent.DEFAULT_TIME_STEP} s")
    print(f"默认打印间隔: {agent.DEFAULT_PRINT_INTERVAL}")
    print(f"最小开度限制: {agent.MIN_OPENING_LIMIT}")
    print(f"最大开度限制: {agent.MAX_OPENING_LIMIT}")
    print(f"默认噪声水平: {agent.DEFAULT_NOISE_LEVEL}")
    
    print()


def demonstrate_config_validation():
    """演示配置验证"""
    print("=== 配置验证演示 ===")
    
    param_manager = get_parameter_manager()
    
    # 验证配置
    is_valid = param_manager.validate_configuration()
    print(f"配置验证结果: {'通过' if is_valid else '失败'}")
    
    # 列出所有分类
    categories = param_manager.list_categories()
    print(f"参数分类: {categories}")
    
    # 列出泵参数
    pump_params = param_manager.list_parameters('pump_parameters')
    print(f"泵参数: {pump_params}")
    
    print()


def main():
    """主函数"""
    print("CHS-SDK 魔数重构演示")
    print("=" * 50)
    
    try:
        # 演示参数管理器
        demonstrate_parameter_manager()
        
        # 演示泵配置
        demonstrate_pump_with_config()
        
        # 演示阀门配置
        demonstrate_valve_with_config()
        
        # 演示渠道配置
        demonstrate_canal_with_config()
        
        # 演示仿真智能体配置
        demonstrate_simulation_agent_with_config()
        
        # 演示配置验证
        demonstrate_config_validation()
        
        print("所有演示完成！")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
