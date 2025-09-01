#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 3 - 增强感知智能体统一场景运行脚本

这个脚本展示了如何使用run_unified_scenario方式运行增强感知智能体仿真。
使用统一的配置文件格式，将所有配置整合到一个文件中。

运行方式:
    python run_unified_scenario.py
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入根目录的run_unified_scenario模块
try:
    from run_unified_scenario import main as run_unified_scenario_main
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在项目根目录下运行此脚本")
    sys.exit(1)

def main():
    """
    主函数 - 使用run_unified_scenario方式运行example_3
    """
    print("="*60)
    print("Mission Example 3 - 增强感知智能体统一场景仿真")
    print("="*60)
    print()
    print("这个示例展示了如何使用run_unified_scenario方式运行增强感知智能体仿真。")
    print("使用统一的配置文件格式：")
    print("- unified_config.yml: 统一配置文件")
    print("- 包含智能体、组件、仿真参数等所有配置")
    print()
    print("仿真特性:")
    print("- 水库物理组件仿真")
    print("- 增强感知智能体")
    print("- 传感器故障注入")
    print("- 统一配置文件格式")
    print("- 简化的配置管理")
    print()
    
    # 设置配置文件路径
    current_dir = Path(__file__).parent
    
    # 首先尝试使用universal_config.yml（如果存在）
    universal_config_path = current_dir / "universal_config_3.yml"
    unified_config_path = current_dir / "01_enhanced_perception" / "universal_config.yml"
    
    config_path = None
    if universal_config_path.exists():
        config_path = universal_config_path
        print(f"使用通用配置文件: {config_path.name}")
    elif unified_config_path.exists():
        config_path = unified_config_path
        print(f"使用子目录统一配置文件: {config_path.relative_to(current_dir)}")
    else:
        print("错误: 未找到统一配置文件")
        print("请确保存在以下文件之一:")
        print(f"- {universal_config_path.relative_to(current_dir)}")
        print(f"- {unified_config_path.relative_to(current_dir)}")
        sys.exit(1)
    
    print(f"配置文件路径: {config_path.absolute()}")
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
    
    # 修改sys.argv以传递配置文件路径给run_unified_scenario
    original_argv = sys.argv.copy()
    sys.argv = ['run_unified_scenario.py', str(config_path)]
    
    try:
        # 调用根目录的run_unified_scenario主函数
        print(f"\n开始运行统一场景: {config_path.name}")
        print("-" * 40)
        
        run_unified_scenario_main()
        
        print("-" * 40)
        print("仿真完成！")
        print("\n结果文件位置:")
        print(f"- 输出目录: {current_dir / 'output'}")
        print(f"- 日志文件: {current_dir / 'logs'}")
        print(f"- 图表文件: {current_dir / 'plots'}")
        
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