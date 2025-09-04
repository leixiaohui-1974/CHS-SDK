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
        'end_time': 7200,
        'dt': 0.5
    }
    builder = SimulationBuilder(config)
    factory = ObjectFactory()
    
    # 添加一个简单的水库-闸门系统作为示例
    builder.add_reservoir("reservoir_1", water_level=10.0)
    builder.add_gate("gate_1", opening=0.5)
    builder.connect_components([("reservoir_1", "gate_1")])
    
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
