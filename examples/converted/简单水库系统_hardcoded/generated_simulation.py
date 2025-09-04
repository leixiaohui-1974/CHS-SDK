#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成的仿真代码
基于自然语言描述生成
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core_lib.core_engine.testing.simulation_builder import SimulationBuilder
from core_lib.io.object_factory import ObjectFactory

def create_simulation():
    """创建仿真系统"""
    config = {
        'start_time': 0,
        'end_time': 3600,
        'dt': 1.0
    }
    builder = SimulationBuilder(config)
    
    # 创建简单的水库-闸门系统
    builder.add_reservoir("水库1", water_level=50.0, surface_area=10000)
    builder.add_gate("闸门1", opening=0.5, max_flow_rate=50.0)
    
    # 连接组件
    builder.connect_components([("水库1", "闸门1")])
    
    # 构建仿真系统
    builder.build()
    return builder

def main():
    """主函数"""
    builder = create_simulation()
    builder.run_simple_simulation()
    print("仿真完成")

if __name__ == '__main__':
    main()
