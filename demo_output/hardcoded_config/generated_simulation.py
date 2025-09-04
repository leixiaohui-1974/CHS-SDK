#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成的仿真代码
基于自然语言描述生成
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core_lib.core_engine.simulation_builder import SimulationBuilder
from core_lib.io.object_factory import ObjectFactory

def create_simulation():
    """创建仿真系统"""
    builder = SimulationBuilder()
    factory = ObjectFactory()
    
    # 设置仿真参数
    builder.set_simulation_time(7200)
    builder.set_time_step(0.5)
    
    # 创建组件: 仿真名称
    仿真名称 = factory.create_object('Reservoir', {'capacity': 1000000, 'initial_level': 50, 'min_level': 10, 'max_level': 100, 'area': 10000})
    builder.add_component('仿真名称', 仿真名称)

    # 创建组件: 主水库
    主水库 = factory.create_object('Reservoir', {'capacity': 10.0, 'initial_level': 50, 'min_level': 10, 'max_level': 100, 'area': 10000})
    builder.add_component('主水库', 主水库)

    # 创建组件: 调节闸门
    调节闸门 = factory.create_object('Gate', {'max_flow': 100.0, 'initial_opening': 0.5, 'min_opening': 0, 'max_opening': 1})
    builder.add_component('调节闸门', 调节闸门)

    # 创建组件: 下游水库
    下游水库 = factory.create_object('Reservoir', {'capacity': 8.0, 'initial_level': 50, 'min_level': 10, 'max_level': 100, 'area': 10000})
    builder.add_component('下游水库', 下游水库)

    # 创建组件: 水位传感器1
    水位传感器1 = factory.create_object('Reservoir', {'capacity': 1000000, 'initial_level': 50, 'min_level': 10, 'max_level': 100, 'area': 10000})
    builder.add_component('水位传感器1', 水位传感器1)

    # 创建组件: 水位传感器2
    水位传感器2 = factory.create_object('Reservoir', {'capacity': 1000000, 'initial_level': 50, 'min_level': 10, 'max_level': 100, 'area': 10000})
    builder.add_component('水位传感器2', 水位传感器2)

    # 创建组件: 流量传感器
    流量传感器 = factory.create_object('Gate', {'max_flow': 1000, 'initial_opening': 0.5, 'min_opening': 0, 'max_opening': 1})
    builder.add_component('流量传感器', 流量传感器)

    # 创建组件: 智能水泵
    智能水泵 = factory.create_object('Pump', {'max_flow': 30.0, 'efficiency': 0.85, 'power': 1000, 'initial_speed': 0})
    builder.add_component('智能水泵', 智能水泵)

    # 创建组件: 控制目标
    控制目标 = factory.create_object('Reservoir', {'capacity': 1000000, 'initial_level': 12.0, 'min_level': 10, 'max_level': 100, 'area': 10000})
    builder.add_component('控制目标', 控制目标)

    # 创建组件: 约束条件
    约束条件 = factory.create_object('Gate', {'max_flow': 30.0, 'initial_opening': 0.5, 'min_opening': 0, 'max_opening': 1})
    builder.add_component('约束条件', 约束条件)

    # 连接: 主水库 -> 调节闸门
    builder.connect('主水库', '调节闸门')

    # 连接: 调节闸门 -> 下游水库
    builder.connect('调节闸门', '下游水库')

    # 连接: 智能水泵 -> 主水库
    builder.connect('智能水泵', '主水库')

    # 构建并返回仿真系统
    return builder.build()

def main():
    """主函数"""
    simulation = create_simulation()
    simulation.run()
    simulation.save_results('results')

if __name__ == '__main__':
    main()
