#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 1 - 物理模型仿真 (统一场景运行方式)

本脚本通过调用根目录的 run_unified_scenario 模块来运行物理模型仿真，
优先使用 universal_config_1.yml 或子目录中的 universal_config.yml 作为统一配置文件。

运行方式:
    python run_unified_scenario.py [scenario_number]
    
参数:
    scenario_number: 可选，指定运行的场景编号 (1-5)
                    1 - 基础物理模型仿真
                    2 - 物理IO智能体演示  
                    3 - 闸门控制智能体演示
                    4 - 数字孪生智能体演示
                    5 - 中央调度智能体演示
                    如果不指定，将显示交互式选择菜单
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from run_unified_scenario import main as run_unified_scenario_main
except ImportError:
    print("错误: 无法导入 run_unified_scenario 模块")
    print("请确保您在项目根目录下运行此脚本")
    sys.exit(1)

def select_scenario():
    """
    交互式选择仿真场景
    """
    scenarios = {
        "1": {
            "name": "基础物理模型仿真",
            "description": "纯物理组件（渠道和闸门）的动态行为演示",
            "config": "universal_config_1_1.yml",
            "subdir": "01_basic_simulation"
        },
        "2": {
            "name": "物理IO智能体演示",
            "description": "传感器读取和执行器控制的智能体演示",
            "config": "universal_config_1_2.yml",
            "subdir": "02_advanced_control"
        },
        "3": {
            "name": "闸门控制智能体演示",
            "description": "PID控制器的闸门自动控制演示",
            "config": "universal_config_1_3.yml",
            "subdir": "03_fault_tolerance"
        },
        "4": {
            "name": "数字孪生智能体演示",
            "description": "数据平滑和异常检测的数字孪生演示",
            "config": "universal_config_1_4.yml",
            "subdir": "04_digital_twin_advanced"
        },
        "5": {
            "name": "中央调度智能体演示",
            "description": "MPC优化和调度指令的中央调度演示",
            "config": "universal_config_1_5.yml",
            "subdir": "05_central_mpc_dispatcher"
        }
    }
    
    print("\n=== Mission Example 1 - 物理模型仿真场景选择 (统一配置) ===")
    print("\n可用的仿真场景:")
    
    for key, scenario in scenarios.items():
        print(f"  {key}. {scenario['name']}")
        print(f"     {scenario['description']}")
        print(f"     配置文件: {scenario['config']}")
    
    print("\n请选择要运行的场景 (1-5), 或按 'q' 退出: ", end="")
    
    while True:
        choice = input().strip().lower()
        
        if choice == 'q':
            print("退出程序")
            return None, None
            
        if choice in scenarios:
            return scenarios[choice]["config"], scenarios[choice]["subdir"]
            
        print(f"无效选择: {choice}. 请输入 1-5 或 'q': ", end="")

def find_config_file(config_name, subdir_name):
    """
    查找配置文件，按优先级顺序查找
    """
    example_dir = Path(__file__).parent
    
    # 优先级顺序
    search_paths = [
        example_dir / config_name,  # 主目录下的特定配置
        example_dir / "universal_config.yml",  # 主目录下的通用配置
        example_dir / subdir_name / "universal_config.yml",  # 子目录下的通用配置
    ]
    
    for config_path in search_paths:
        if config_path.exists():
            return config_path
    
    return None

def main():
    """
    主函数
    """
    # 解析命令行参数
    scenario_map = {
        "1": ("universal_config_1_1.yml", "01_basic_simulation"),
        "2": ("universal_config_1_2.yml", "02_advanced_control"), 
        "3": ("universal_config_1_3.yml", "03_fault_tolerance"),
        "4": ("universal_config_1_4.yml", "04_digital_twin_advanced"),
        "5": ("universal_config_1_5.yml", "05_central_mpc_dispatcher")
    }
    
    if len(sys.argv) > 1:
        scenario_num = sys.argv[1]
        if scenario_num in scenario_map:
            config_name, selected_subdir = scenario_map[scenario_num]
        else:
            print(f"错误: 无效的场景编号 '{scenario_num}'")
            print("有效的场景编号: 1-5")
            return 1
    else:
        # 交互式选择
        result = select_scenario()
        if result[0] is None:
            return 0
        config_name, selected_subdir = result
    
    # 查找配置文件
    config_path = find_config_file(config_name, selected_subdir)
    
    if config_path is None:
        print(f"❌ 错误: 找不到配置文件")
        print(f"   查找的配置文件: {config_name}")
        print(f"   场景目录: {selected_subdir}")
        print("\n请确保存在以下任一配置文件:")
        example_dir = Path(__file__).parent
        print(f"   - {example_dir / config_name}")
        print(f"   - {example_dir / 'universal_config.yml'}")
        print(f"   - {example_dir / selected_subdir / 'universal_config.yml'}")
        return 1
    
    print(f"\n🚀 启动场景: {selected_subdir}")
    print(f"📁 场景路径: {Path(__file__).parent / selected_subdir}")
    print(f"⚙️  配置文件: {config_path}")
    print(f"🔧 运行方式: 统一配置文件 (universal_config.yml)")
    
    # 切换到example_1目录并运行
    original_cwd = os.getcwd()
    try:
        os.chdir(Path(__file__).parent)
        
        # 调用 run_unified_scenario，传入配置文件路径
        sys.argv = ['run_unified_scenario.py', str(config_path)]
        return run_unified_scenario_main()
        
    except Exception as e:
        print(f"❌ 运行场景时发生错误: {e}")
        return 1
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)