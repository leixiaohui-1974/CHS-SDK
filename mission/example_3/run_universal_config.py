#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 3 - 增强感知智能体通用配置运行脚本

这个脚本展示了如何使用run_universal_config方式运行增强感知智能体仿真。
使用通用配置文件，包含完整的配置选项和高级功能。

运行方式:
    python run_universal_config.py
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入根目录的run_universal_config模块
try:
    from run_universal_config import main as run_universal_config_main
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在项目根目录下运行此脚本")
    sys.exit(1)

def main():
    """
    主函数 - 使用run_universal_config方式运行example_3
    """
    print("="*60)
    print("Mission Example 3 - 增强感知智能体通用配置仿真")
    print("="*60)
    print()
    print("这个示例展示了如何使用run_universal_config方式运行增强感知智能体仿真。")
    print("使用通用配置文件格式：")
    print("- universal_config_3.yml: 通用配置文件")
    print("- 包含完整的配置选项和高级功能")
    print("- 支持调试、性能监控、可视化等")
    print()
    print("仿真特性:")
    print("- 水库物理组件仿真")
    print("- 增强感知智能体")
    print("- 传感器故障注入")
    print("- 完整的配置管理")
    print("- 高级调试和监控功能")
    print("- 智能分析和预测")
    print("- 可视化和数据输出")
    print()
    
    # 设置配置文件路径
    current_dir = Path(__file__).parent
    
    # 查找通用配置文件
    config_candidates = [
        current_dir / "universal_config_3.yml",
        current_dir / "01_enhanced_perception" / "universal_config.yml"
    ]
    
    config_path = None
    for candidate in config_candidates:
        if candidate.exists():
            config_path = candidate
            break
    
    if config_path is None:
        print("错误: 未找到通用配置文件")
        print("请确保存在以下文件之一:")
        for candidate in config_candidates:
            print(f"- {candidate.relative_to(current_dir)}")
        sys.exit(1)
    
    print(f"使用配置文件: {config_path.relative_to(current_dir)}")
    print(f"配置文件路径: {config_path.absolute()}")
    print()
    
    # 显示配置文件特性
    print("通用配置文件包含的功能模块:")
    print("- 仿真参数配置")
    print("- 调试和性能监控")
    print("- 可视化设置")
    print("- 数据输出管理")
    print("- 智能分析（感知、认知、预测）")
    print("- 日志和错误处理")
    print("- 缓存和网络配置")
    print("- 安全和扩展设置")
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
    
    # 修改sys.argv以传递配置文件路径给run_universal_config
    original_argv = sys.argv.copy()
    sys.argv = ['run_universal_config.py', str(config_path)]
    
    try:
        # 调用根目录的run_universal_config主函数
        print(f"\n开始运行通用配置场景: {config_path.name}")
        print("-" * 40)
        
        run_universal_config_main()
        
        print("-" * 40)
        print("仿真完成！")
        print("\n结果文件位置:")
        print(f"- 输出目录: {current_dir / 'output'}")
        print(f"- 日志文件: {current_dir / 'logs'}")
        print(f"- 图表文件: {current_dir / 'plots'}")
        print(f"- 分析报告: {current_dir / 'analysis'}")
        print(f"- 性能报告: {current_dir / 'performance'}")
        
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