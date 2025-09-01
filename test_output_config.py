#!/usr/bin/env python3
"""
测试output配置功能的简单脚本
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from core_lib.io.yaml_loader import SimulationBuilder

def test_output_config():
    """
    测试output配置功能
    """
    print("=== 测试output配置功能 ===")
    
    # 使用watertank_refactored/04_pid_control_outlet示例
    scenario_path = project_root / "examples" / "watertank_refactored" / "04_pid_control_outlet"
    
    if not scenario_path.exists():
        print(f"错误：找不到示例目录 {scenario_path}")
        return
    
    print(f"加载示例：{scenario_path}")
    
    try:
        # 创建SimulationBuilder
        builder = SimulationBuilder(str(scenario_path))
        
        # 加载仿真
        print("正在加载仿真...")
        harness = builder.load()
        
        print(f"仿真加载成功，组件数量：{len(harness.components)}")
        print(f"代理数量：{len(harness.agents)}")
        
        # 打印所有代理的信息
        print("\n代理列表：")
        for i, agent in enumerate(harness.agents):
            print(f"  {i+1}. {agent.agent_id} ({type(agent).__name__})")
        
        # 检查是否有output配置
        if hasattr(harness, '_output_configs'):
            print(f"\n找到output配置：{len(harness._output_configs)}个")
            for config in harness._output_configs:
                print(f"  - 主题：{config['topic']}，文件：{config['file']}，代理ID：{config['agent_id']}")
        else:
            print("\n未找到output配置")
        
        # 运行仿真
        print("\n开始运行仿真...")
        harness.run_mas_simulation()
        
        # 手动调用export_output_data
        if hasattr(harness, '_output_configs'):
            print("\n正在导出CSV文件...")
            harness.export_output_data()
        
        print("\n仿真完成！")
        
        # 检查output目录
        output_dir = scenario_path / "output"
        if output_dir.exists():
            output_files = list(output_dir.glob("*.csv"))
            print(f"\n生成的CSV文件数量：{len(output_files)}")
            for file in output_files:
                print(f"  - {file.name}")
                # 显示文件内容的前几行
                try:
                    with open(file, 'r') as f:
                        lines = f.readlines()[:5]
                        print(f"    前{len(lines)}行内容：")
                        for line in lines:
                            print(f"      {line.strip()}")
                except Exception as read_error:
                    print(f"    读取文件失败：{read_error}")
        else:
            print("\noutput目录不存在")
            
    except Exception as e:
        print(f"错误：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_output_config()