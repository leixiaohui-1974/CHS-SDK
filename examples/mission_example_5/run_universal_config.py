#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 5 - 水电站仿真与调度策略通用配置运行脚本

这个脚本展示了如何使用run_universal_config方式运行水电站仿真与调度策略。
使用通用配置文件，包含完整的配置选项和高级功能。

运行方式:
    python run_universal_config.py [scenario_number]
    
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

# 导入根目录的run_universal_config模块
try:
    from run_universal_config import main as run_universal_config_main
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
            'features': [
                '水轮机效率建模',
                '泄洪闸门控制',
                '水位动态仿真',
                '尾水位影响分析',
                '实时性能监控'
            ]
        },
        '5.2': {
            'name': '多机组协调和电网交互',
            'directory': '02_multi_unit_coordination',
            'description': '多个水轮机组的协调运行和电网交互仿真',
            'features': [
                '多机组协调控制',
                '电网频率调节',
                '负荷分配优化',
                '故障响应机制',
                '智能体协作'
            ]
        },
        '5.3': {
            'name': '水轮机经济调度表计算',
            'directory': '03_economic_dispatch',
            'description': '基于经济性的水轮机调度优化计算',
            'features': [
                '经济调度优化',
                '成本效益分析',
                '调度表生成',
                '效率曲线计算',
                '市场价格考虑'
            ]
        },
        '5.4': {
            'name': '闸门调度表计算',
            'directory': '04_gate_scheduling',
            'description': '泄洪闸门的优化调度策略计算',
            'features': [
                '闸门调度优化',
                '安全约束验证',
                '调度表计算',
                '水位控制策略',
                '风险评估'
            ]
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
        print(f"       特性: {', '.join(info['features'][:3])}...")
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
    主函数 - 使用run_universal_config方式运行example_5
    """
    print("="*60)
    print("Mission Example 5 - 水电站仿真与调度策略通用配置仿真")
    print("="*60)
    print()
    print("这个示例展示了如何使用run_universal_config方式运行水电站仿真与调度策略。")
    print("使用通用配置文件格式：")
    print("- universal_config_5.yml: 通用配置文件")
    print("- 包含完整的配置选项和高级功能")
    print("- 支持调试、性能监控、可视化等")
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
    
    # 查找通用配置文件
    config_candidates = [
        current_dir / "universal_config_5.yml",  # 主目录通用配置
        current_dir / scenario_info['directory'] / "universal_config.yml"  # 子目录配置
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
    
    # 显示场景特性
    print(f"场景特性 ({selected_scenario}):")
    for feature in scenario_info['features']:
        print(f"- {feature}")
    print()
    
    # 显示通用配置文件的功能模块
    print("通用配置文件包含的功能模块:")
    print("- 仿真参数配置")
    print("- 调试和性能监控")
    print("- 可视化设置")
    print("- 数据输出管理")
    print("- 智能分析（感知、认知、预测）")
    print("- 日志和错误处理")
    print("- 缓存和网络配置")
    print("- 安全和扩展设置")
    
    if selected_scenario == '5.2':
        print("- 多机组协调参数")
        print("- 电网交互配置")
        print("- 通信协议设置")
    elif selected_scenario in ['5.3', '5.4']:
        print("- 优化算法配置")
        print("- 约束条件设置")
        print("- 目标函数定义")
    print()
    
    # 显示高级功能
    print("高级功能特性:")
    print("- 实时性能监控和分析")
    print("- 智能故障检测和恢复")
    print("- 预测性维护建议")
    print("- 自适应参数调优")
    print("- 多维度数据可视化")
    print("- 详细的分析报告生成")
    print("- 安全审计和合规检查")
    print("- 扩展插件支持")
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
        print(f"\n开始运行通用配置场景: {scenario_info['name']}")
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
        
        if selected_scenario in ['5.3', '5.4']:
            print(f"- 调度表文件: {current_dir / 'tables'}")
            print(f"- 优化结果: {current_dir / 'optimization'}")
            print(f"- 算法分析: {current_dir / 'algorithm_analysis'}")
        
        if selected_scenario == '5.2':
            print(f"- 协调日志: {current_dir / 'coordination'}")
            print(f"- 电网交互数据: {current_dir / 'grid_data'}")
            print(f"- 通信分析: {current_dir / 'communication'}")
        
        if selected_scenario == '5.1':
            print(f"- 水力学分析: {current_dir / 'hydraulics'}")
            print(f"- 控制系统日志: {current_dir / 'control_logs'}")
        
        print(f"- 安全审计报告: {current_dir / 'security'}")
        print(f"- 系统诊断报告: {current_dir / 'diagnostics'}")
        
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