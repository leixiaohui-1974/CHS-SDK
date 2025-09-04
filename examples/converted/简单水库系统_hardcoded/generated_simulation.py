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
    builder.set_simulation_time(3600)
    builder.set_time_step(1.0)
    
    # 创建组件: 仿真名称
    仿真名称 = factory.create_object('Reservoir', {'capacity': 1000000, 'initial_level': 50, 'min_level': 10, 'max_level': 100, 'area': 10000})
    builder.add_component('仿真名称', 仿真名称)

    # 创建组件: 水库1
    水库1 = factory.create_object('Reservoir', {'capacity': 5.0, 'initial_level': 50, 'min_level': 10, 'max_level': 100, 'area': 10000})
    builder.add_component('水库1', 水库1)

    # 创建组件: 闸门1
    闸门1 = factory.create_object('Gate', {'max_flow': 50.0, 'initial_opening': 0.5, 'min_opening': 0, 'max_opening': 1})
    builder.add_component('闸门1', 闸门1)

    # 创建组件: 传感器1
    传感器1 = factory.create_object('Sensor', {})
    builder.add_component('传感器1', 传感器1)

    # 连接: 水库1 -> 闸门1
    builder.connect('水库1', '闸门1')

    # 构建并返回仿真系统
    return builder.build()

def main():
    """主函数"""
    simulation = create_simulation()
    simulation.run()
    simulation.save_results('results')

if __name__ == '__main__':
    main()
