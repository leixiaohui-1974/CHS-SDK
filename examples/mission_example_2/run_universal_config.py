#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 2 - 闭环与分层控制系统 (通用配置运行方式)

本脚本用于运行闭环与分层控制系统仿真，它通过调用根目录的 run_universal_config 模块，
并优先使用 universal_config_2.yml 或子目录中的 universal_config.yml 作为通用配置文件。
支持完整的配置选项和高级功能，如调试、性能监控、可视化等。

运行方式:
    python run_universal_config.py [scenario_number]
    
参数:
    scenario_number: 可选，指定运行的场景编号 (1-3)
                    1 - 本地闭环控制
                    2 - 分层控制
                    3 - 流域联合调度
                    如果不指定，将显示交互式选择菜单

高级功能:
    - 完整的调试和日志系统
    - 性能监控和分析
    - 实时可视化（如果启用）
    - 自动验证和结果分析
    - 智能错误处理和恢复
    - 配置文件验证和优化建议
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from run_universal_config import main as run_universal_config_main
except ImportError:
    print("错误: 无法导入 run_universal_config 模块")
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
            "config": "universal_config_2_1.yml",
            "subdir": "01_local_control",
            "features": ["PID控制", "传感器噪声模拟", "执行器延迟", "扰动响应"]
        },
        "2": {
            "name": "分层控制",
            "description": "两级分层控制系统，MPC上层优化 + PID下层执行",
            "config": "universal_config_2_2.yml",
            "subdir": "02_hierarchical_control",
            "features": ["MPC优化", "预测控制", "分层协调", "天气预报集成"]
        },
        "3": {
            "name": "流域联合调度",
            "description": "多设施流域联合调度，中央调度器协调多个本地控制器",
            "config": "universal_config_2_3.yml",
            "subdir": "03_watershed_coordination",
            "features": ["多目标优化", "规则引擎", "模式切换", "流域协调"]
        }
    }
    
    print("\n=== Mission Example 2 - 闭环与分层控制系统场景选择 (通用配置) ===")
    print("\n可用的仿真场景:")
    
    for key, scenario in scenarios.items():
        print(f"\n  {key}. {scenario['name']}")
        print(f"     {scenario['description']}")
        print(f"     配置文件: {scenario['config']}")
        print(f"     主要功能: {', '.join(scenario['features'])}")
    
    print("\n🔧 通用配置运行方式特性:")
    print("   ✅ 完整的调试和日志系统")
    print("   ✅ 性能监控和分析")
    print("   ✅ 实时可视化（如果启用）")
    print("   ✅ 自动验证和结果分析")
    print("   ✅ 智能错误处理和恢复")
    print("   ✅ 配置文件验证和优化建议")
    
    print("\n请选择要运行的场景 (1-3), 或按 'q' 退出: ", end="")
    
    while True:
        choice = input().strip().lower()
        
        if choice == 'q':
            print("退出程序")
            return None, None
            
        if choice in scenarios:
            return scenarios[choice]["config"], scenarios[choice]["subdir"]
            
        print(f"无效选择: {choice}. 请输入 1-3 或 'q': ", end="")

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

def validate_config_file(config_path):
    """
    验证配置文件的完整性
    """
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 检查必要的配置节
        required_sections = ['simulation', 'components', 'agents']
        missing_sections = [section for section in required_sections if section not in config]
        
        if missing_sections:
            print(f"⚠️  警告: 配置文件缺少必要节: {missing_sections}")
            return False
        
        # 检查高级功能配置
        advanced_features = {
            'debug': '调试功能',
            'performance': '性能监控',
            'visualization': '可视化',
            'validation': '自动验证'
        }
        
        available_features = []
        for feature, description in advanced_features.items():
            if feature in config and config[feature].get('enabled', False):
                available_features.append(description)
        
        if available_features:
            print(f"🔧 启用的高级功能: {', '.join(available_features)}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  警告: 配置文件验证失败: {e}")
        return False

def main():
    """
    主函数
    """
    # 解析命令行参数
    scenario_map = {
        "1": ("universal_config_2_1.yml", "01_local_control"),
        "2": ("universal_config_2_2.yml", "02_hierarchical_control"), 
        "3": ("universal_config_2_3.yml", "03_watershed_coordination")
    }
    
    if len(sys.argv) > 1:
        scenario_num = sys.argv[1]
        if scenario_num in scenario_map:
            config_name, selected_subdir = scenario_map[scenario_num]
        else:
            print(f"错误: 无效的场景编号 '{scenario_num}'")
            print("有效的场景编号: 1-3")
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
        print(f"\n❌ 错误: 找不到配置文件")
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
    print(f"🔧 运行方式: 通用配置 (完整功能支持)")
    
    # 验证配置文件
    print("\n🔍 验证配置文件...")
    if not validate_config_file(config_path):
        print("⚠️  配置文件验证失败，但将继续运行...")
    
    # 切换到example_2目录并运行
    original_cwd = os.getcwd()
    try:
        os.chdir(Path(__file__).parent)
        
        print("\n⚡ 启动通用配置仿真引擎...")
        print("📊 启用完整的调试、监控和分析功能")
        
        # 调用 run_universal_config，传入配置文件路径
        sys.argv = ['run_universal_config.py', str(config_path)]
        return run_universal_config_main()
        
    except Exception as e:
        print(f"\n❌ 运行场景时发生错误: {e}")
        print("\n🔧 故障排除建议:")
        print("   1. 检查配置文件格式是否正确")
        print("   2. 确认所有依赖模块已正确安装")
        print("   3. 验证组件和智能体配置参数")
        print("   4. 查看详细日志文件获取更多信息")
        return 1
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    print("\n🔧 Mission Example 2 - 通用配置运行方式")
    print("   支持完整的调试、监控、可视化和分析功能")
    
    exit_code = main()
    
    if exit_code == 0:
        print("\n✅ 仿真成功完成!")
        print("📁 详细日志、性能数据和分析结果已保存")
        print("📊 可查看生成的报告和可视化图表")
    else:
        print("\n❌ 仿真未能成功完成")
        print("📋 请查看错误信息和日志文件进行故障排除")
    
    sys.exit(exit_code)