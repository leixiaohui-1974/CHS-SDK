#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 3 - 增强感知智能体场景运行脚本

这个脚本展示了如何使用run_scenario方式运行增强感知智能体仿真。
使用传统的多配置文件方式（agents.yml, components.yml, config.yml等）。

运行方式:
    python run_scenario.py
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入根目录的run_scenario模块
try:
    from run_scenario import main as run_scenario_main
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在项目根目录下运行此脚本")
    sys.exit(1)

def main():
    """
    主函数 - 使用run_scenario方式运行example_3
    """
    print("="*60)
    print("Mission Example 3 - 增强感知智能体场景仿真")
    print("="*60)
    print()
    print("这个示例展示了如何使用run_scenario方式运行增强感知智能体仿真。")
    print("使用传统的多配置文件方式：")
    print("- agents.yml: 智能体配置")
    print("- components.yml: 物理组件配置")
    print("- config.yml: 仿真参数配置")
    print()
    print("仿真特性:")
    print("- 水库物理组件仿真")
    print("- 增强感知智能体")
    print("- 传感器故障注入")
    print("- 基于YAML配置文件")
    print()
    
    # 设置场景路径为当前example_3的01_enhanced_perception子目录
    current_dir = Path(__file__).parent
    scenario_path = current_dir / "01_enhanced_perception"
    
    if not scenario_path.exists():
        print(f"错误: 场景目录不存在: {scenario_path}")
        print("请确保01_enhanced_perception目录存在并包含必要的配置文件")
        sys.exit(1)
    
    # 检查必要的配置文件
    required_files = ['config.yml', 'agents.yml', 'components.yml']
    missing_files = []
    
    for file_name in required_files:
        file_path = scenario_path / file_name
        if not file_path.exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"错误: 缺少必要的配置文件: {', '.join(missing_files)}")
        print(f"请确保{scenario_path}目录包含所有必要的配置文件")
        sys.exit(1)
    
    print(f"场景路径: {scenario_path.absolute()}")
    print(f"配置文件: {', '.join(required_files)}")
    print()
    
    # 询问用户是否继续
    try:
        response = input("按Enter键开始仿真，或输入'q'退出: ").strip().lower()
        if response == 'q':
            print("仿真已取消")
            return
    except KeyboardInterrupt:
        print("\n仿真已取消")
        return
    
    # 修改sys.argv以传递场景路径给run_scenario
    original_argv = sys.argv.copy()
    sys.argv = ['run_scenario.py', str(scenario_path)]
    
    try:
        # 调用根目录的run_scenario主函数
        print(f"\n开始运行场景: {scenario_path.name}")
        print("-" * 40)
        
        run_scenario_main()
        
        print("-" * 40)
        print("仿真完成！")
        print("\n结果文件位置:")
        print(f"- 输出目录: {scenario_path / 'output'}")
        print(f"- 日志文件: {scenario_path / 'logs'}")
        print(f"- 图表文件: {scenario_path / 'plots'}")
        
    except Exception as e:
        print(f"\n仿真运行失败: {e}")
        import traceback
        print("详细错误信息:")
        print(traceback.format_exc())
        sys.exit(1)
    
    finally:
        # 恢复原始的sys.argv
        sys.argv = original_argv

if __name__ == "__main__":
    main()