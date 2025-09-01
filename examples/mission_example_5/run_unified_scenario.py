#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 5 - 水电站仿真与调度策略统一场景运行脚本

这个脚本展示了如何使用run_unified_scenario方式运行水电站仿真与调度策略。
使用统一的配置文件格式，将所有配置整合到一个文件中。

运行方式:
    python run_unified_scenario.py [scenario_number]
    
可选的场景编号:
    5.1 - 水轮机和泄洪闸仿真
    5.2 - 多机组协调和电网交互
    5.3 - 水轮机经济调度表计算
    5.4 - 闸门调度表计算
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

def get_scenario_info():
    """
    获取可用场景信息
    """
    scenarios = {
        '5.1': {
            'name': '水轮机和泄洪闸仿真',
            'directory': '01_turbine_gate_simulation',
            'description': '基本的水轮机和泄洪闸仿真，包括水力学建模和控制策略',
            'config_file': 'universal_config.yml'
        },
        '5.2': {
            'name': '多机组协调和电网交互',
            'directory': '02_multi_unit_coordination',
            'description': '多个水轮机组的协调运行和电网交互仿真',
            'config_file': 'universal_config.yml'
        },
        '5.3': {
            'name': '水轮机经济调度表计算',
            'directory': '03_economic_dispatch',
            'description': '基于经济性的水轮机调度优化计算',
            'config_file': 'universal_config.yml'
        },
        '5.4': {
            'name': '闸门调度表计算',
            'directory': '04_gate_scheduling',
            'description': '泄洪闸门的优化调度策略计算',
            'config_file': 'universal_config.yml'
        }
    }
    return scenarios

def select_scenario(scenarios):
    """
    选择要运行的场景
    """
    print("可用的水电站仿真场景:")
    print()
    
    for scenario_id, info in scenarios.items():
        print(f"  {scenario_id}: {info['name']}")
        print(f"       {info['description']}")
        print()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        selected = sys.argv[1]
        if selected in scenarios:
            return selected
        else:
            print(f"错误: 无效的场景编号 '{selected}'")
            print(f"可用的场景编号: {', '.join(scenarios.keys())}")
            sys.exit(1)
    
    # 交互式选择
    while True:
        try:
            choice = input(f"请选择场景编号 ({'/'.join(scenarios.keys())}) 或按Enter选择5.1: ").strip()
            
            if not choice:
                choice = '5.1'
            
            if choice in scenarios:
                return choice
            else:
                print(f"无效选择，请输入: {', '.join(scenarios.keys())}")
                
        except KeyboardInterrupt:
            print("\n已取消")
            sys.exit(0)

def main():
    """
    主函数 - 使用run_unified_scenario方式运行example_5
    """
    print("="*60)
    print("Mission Example 5 - 水电站仿真与调度策略统一场景仿真")
    print("="*60)
    print()
    print("这个示例展示了如何使用run_unified_scenario方式运行水电站仿真与调度策略。")
    print("使用统一的配置文件格式：")
    print("- universal_config.yml: 统一配置文件")
    print("- 包含智能体、组件、仿真参数等所有配置")
    print("- 简化的配置管理")
    print()
    
    # 获取场景信息
    scenarios = get_scenario_info()
    
    # 选择场景
    selected_scenario = select_scenario(scenarios)
    scenario_info = scenarios[selected_scenario]
    
    print(f"已选择场景: {selected_scenario} - {scenario_info['name']}")
    print(f"场景描述: {scenario_info['description']}")
    print()
    
    # 设置配置文件路径
    current_dir = Path(__file__).parent
    
    # 查找统一配置文件
    config_candidates = [
        current_dir / "universal_config_5.yml",  # 主目录通用配置
        current_dir / scenario_info['directory'] / scenario_info['config_file']  # 子目录配置
    ]
    
    config_path = None
    for candidate in config_candidates:
        if candidate.exists():
            config_path = candidate
            break
    
    if config_path is None:
        print("错误: 未找到统一配置文件")
        print("请确保存在以下文件之一:")
        for candidate in config_candidates:
            print(f"- {candidate.relative_to(current_dir)}")
        sys.exit(1)
    
    print(f"使用配置文件: {config_path.relative_to(current_dir)}")
    print(f"配置文件路径: {config_path.absolute()}")
    print()
    
    # 显示场景特性
    if selected_scenario == '5.1':
        print("场景特性:")
        print("- 水轮机建模和控制")
        print("- 泄洪闸门操作")
        print("- 水位和流量仿真")
        print("- 尾水位变化影响")
        print("- 统一配置管理")
    elif selected_scenario == '5.2':
        print("场景特性:")
        print("- 多机组协调控制")
        print("- 电网交互仿真")
        print("- 负荷分配优化")
        print("- 频率调节")
        print("- 智能体协调")
    elif selected_scenario == '5.3':
        print("场景特性:")
        print("- 经济调度优化")
        print("- 成本效益分析")
        print("- 调度表生成")
        print("- 效率曲线计算")
        print("- 优化算法集成")
    elif selected_scenario == '5.4':
        print("场景特性:")
        print("- 闸门调度优化")
        print("- 安全约束考虑")
        print("- 调度表计算")
        print("- 水位控制策略")
        print("- 安全规则验证")
    print()
    
    # 显示统一配置文件的优势
    print("统一配置文件的优势:")
    print("- 单一配置文件，管理简单")
    print("- 配置一致性保证")
    print("- 部署和分发方便")
    print("- 版本控制友好")
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
        print(f"\n开始运行统一场景: {scenario_info['name']}")
        print("-" * 40)
        
        run_unified_scenario_main()
        
        print("-" * 40)
        print("仿真完成！")
        print("\n结果文件位置:")
        print(f"- 输出目录: {current_dir / 'output'}")
        print(f"- 日志文件: {current_dir / 'logs'}")
        print(f"- 图表文件: {current_dir / 'plots'}")
        
        if selected_scenario in ['5.3', '5.4']:
            print(f"- 调度表文件: {current_dir / 'tables'}")
            print(f"- 优化结果: {current_dir / 'optimization'}")
        
        if selected_scenario == '5.2':
            print(f"- 协调日志: {current_dir / 'coordination'}")
            print(f"- 电网交互数据: {current_dir / 'grid_data'}")
        
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