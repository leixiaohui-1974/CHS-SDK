#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一场景运行脚本

本脚本通过调用根目录的run_unified_scenario模块来运行仿真场景，
优先使用universal_config.yml作为统一配置文件。

支持的场景:
1. 引绰济辽工程仿真

使用方法:
    python run_unified_scenario.py [场景编号]
    
    场景编号:
    1 - 引绰济辽工程仿真
    
    如果不提供场景编号，将显示交互式菜单。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_yinchuojiliao_unified_scenario():
    """
    运行引绰济辽工程仿真统一场景
    """
    print("\n=== 引绰济辽工程仿真 (统一场景方式) ===")
    print("正在查找统一配置文件...")
    
    try:
        # 导入根目录的run_unified_scenario模块
        from run_unified_scenario import main as run_unified_scenario_main
        
        # 设置场景目录路径
        scenario_path = project_root / "mission" / "scenarios" / "yinchuojiliao"
        
        if not scenario_path.exists():
            print(f"❌ 场景目录不存在: {scenario_path}")
            return False
        
        # 查找统一配置文件（按优先级顺序）
        config_candidates = [
            scenario_path / "universal_config.yml",
            project_root / "mission" / "scenarios" / "universal_config_yinchuojiliao.yml",
            project_root / "mission" / "scenarios" / "universal_config.yml"
        ]
        
        config_file = None
        for candidate in config_candidates:
            if candidate.exists():
                config_file = candidate
                break
        
        if not config_file:
            print("❌ 未找到统一配置文件")
            print("尝试查找的文件:")
            for candidate in config_candidates:
                print(f"  - {candidate}")
            print("\n回退到传统配置文件方式...")
            
            # 回退到传统方式
            from run_scenario import main as run_scenario_main
            
            # 临时修改sys.argv
            original_argv = sys.argv.copy()
            sys.argv = ["run_scenario.py", str(scenario_path)]
            
            try:
                run_scenario_main()
                return True
            finally:
                sys.argv = original_argv
        
        print(f"使用配置文件: {config_file}")
        
        # 临时修改sys.argv来传递配置文件路径
        original_argv = sys.argv.copy()
        sys.argv = ["run_unified_scenario.py", str(config_file)]
        
        try:
            # 调用根目录的run_unified_scenario主函数
            print("\n开始运行统一场景...")
            run_unified_scenario_main()
            print("\n✅ 统一场景运行完成！")
            
            # 检查输出文件
            output_file = scenario_path / "output.yml"
            if output_file.exists():
                print(f"结果已保存到: {output_file}")
            else:
                print("⚠️  未找到输出文件，可能仿真未正常完成")
            
            return True
            
        finally:
            # 恢复原始的sys.argv
            sys.argv = original_argv
    
    except ImportError as e:
        print(f"❌ 无法导入run_unified_scenario模块: {e}")
        print("请确保在项目根目录下运行此脚本")
        return False
    except Exception as e:
        print(f"❌ 统一场景运行失败: {e}")
        return False

def show_menu():
    """
    显示交互式场景选择菜单
    """
    print("\n=== 统一场景运行器 ===")
    print("请选择要运行的场景:")
    print("1. 引绰济辽工程仿真")
    print("0. 退出")
    
    while True:
        try:
            choice = input("\n请输入场景编号 (0-1): ").strip()
            if choice == "0":
                print("退出程序。")
                return None
            elif choice == "1":
                return 1
            else:
                print("❌ 无效选择，请输入 0-1 之间的数字。")
        except KeyboardInterrupt:
            print("\n\n程序被用户中断。")
            return None
        except Exception as e:
            print(f"❌ 输入错误: {e}")

def main():
    """
    主函数
    """
    # 检查命令行参数
    if len(sys.argv) > 1:
        try:
            scenario_num = int(sys.argv[1])
        except ValueError:
            print("❌ 场景编号必须是整数")
            sys.exit(1)
    else:
        scenario_num = show_menu()
        if scenario_num is None:
            sys.exit(0)
    
    # 运行对应场景
    success = False
    if scenario_num == 1:
        success = run_yinchuojiliao_unified_scenario()
    else:
        print(f"❌ 不支持的场景编号: {scenario_num}")
        sys.exit(1)
    
    if success:
        print("\n✅ 统一场景运行成功完成！")
        sys.exit(0)
    else:
        print("\n❌ 统一场景运行失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()