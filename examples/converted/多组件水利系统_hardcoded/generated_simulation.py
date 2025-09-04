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
    
    # 构建并返回仿真系统
    return builder.build()

def main():
    """主函数"""
    simulation = create_simulation()
    simulation.run()
    simulation.save_results('results')

if __name__ == '__main__':
    main()
