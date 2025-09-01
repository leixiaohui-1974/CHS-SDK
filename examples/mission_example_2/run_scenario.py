#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 2 - 闭环与分层控制系统 (场景运行方式)

本脚本通过调用根目录的 run_scenario 模块来运行闭环与分层控制系统仿真，
使用传统的多配置文件方式（agents.yml、components.yml、config.yml等）。

运行方式:
    python run_scenario.py [scenario_number]
    
参数:
    scenario_number: 可选，指定运行的场景编号 (1-3)
                    1 - 本地闭环控制
                    2 - 分层控制
                    3 - 流域联合调度
                    如果不指定，将显示交互式选择菜单
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from run_scenario import main as run_scenario_main
except ImportError:
    print("错误: 无法导入 run_scenario 模块")
    print("请确保您在项目根目录下运行此脚本")
    sys.exit(1)

def select_scenario():
    """
    交互式选择仿真场景
    """
    scenarios = {
        "1": {
            "name": "本地闭环控制",
            "description": "完整的独立现地闭环控制系统，PID控制器自动调节闸门",
            "subdir": "01_local_control"
        },
        "2": {
            "name": "分层控制",
            "description": "两级分层控制系统，MPC上层优化 + PID下层执行",
            "subdir": "02_hierarchical_control"
        },
        "3": {
            "name": "流域联合调度",
            "description": "多设施流域联合调度，中央调度器协调多个本地控制器",
            "subdir": "03_watershed_coordination"
        }
    }
    
    print("\n=== Mission Example 2 - 闭环与分层控制系统场景选择 ===")
    print("\n可用的仿真场景:")
    
    for key, scenario in scenarios.items():
        print(f"  {key}. {scenario['name']}")
        print(f"     {scenario['description']}")
    
    print("\n请选择要运行的场景 (1-3), 或按 'q' 退出: ", end="")
    
    while True:
        choice = input().strip().lower()
        
        if choice == 'q':
            print("退出程序")
            return None
            
        if choice in scenarios:
            return scenarios[choice]["subdir"]
            
        print(f"无效选择: {choice}. 请输入 1-3 或 'q': ", end="")

def main():
    """
    主函数
    """
    # 解析命令行参数
    scenario_map = {
        "1": "01_local_control",
        "2": "02_hierarchical_control", 
        "3": "03_watershed_coordination"
    }
    
    if len(sys.argv) > 1:
        scenario_num = sys.argv[1]
        if scenario_num in scenario_map:
            selected_subdir = scenario_map[scenario_num]
        else:
            print(f"错误: 无效的场景编号 '{scenario_num}'")
            print("有效的场景编号: 1-3")
            return 1
    else:
        # 交互式选择
        selected_subdir = select_scenario()
        if selected_subdir is None:
            return 0
    
    # 构建场景路径
    example_dir = Path(__file__).parent
    scenario_path = example_dir / selected_subdir
    
    if not scenario_path.exists():
        print(f"错误: 场景目录不存在: {scenario_path}")
        return 1
    
    print(f"\n🚀 启动场景: {selected_subdir}")
    print(f"📁 场景路径: {scenario_path}")
    print(f"🔧 运行方式: 传统多配置文件 (agents.yml, components.yml, config.yml)")
    
    # 切换到场景目录并运行
    original_cwd = os.getcwd()
    try:
        os.chdir(scenario_path)
        
        # 检查必要的配置文件
        required_files = ['config.yml']
        missing_files = [f for f in required_files if not Path(f).exists()]
        
        if missing_files:
            print(f"⚠️  警告: 缺少配置文件: {missing_files}")
            print("将尝试使用默认配置运行...")
        
        # 调用 run_scenario
        return run_scenario_main()
        
    except Exception as e:
        print(f"❌ 运行场景时发生错误: {e}")
        return 1
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)