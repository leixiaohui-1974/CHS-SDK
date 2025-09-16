#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 1 - 使用通用配置文件运行仿真
演示如何使用新的通用配置系统替代传统配置方式

这个脚本展示了：
1. 如何加载通用配置文件
2. 如何使用增强的YamlSimulationLoader
3. 如何运行带有调试、性能监控、可视化等功能的仿真
4. 如何与原有的组件配置文件集成
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core_lib.config.enhanced_yaml_loader import load_universal_config
from core_lib.io.yaml_loader import YamlSimulationLoader
import logging

def main():
    """
    主函数：使用通用配置文件运行Mission Example 1仿真
    """
    print("=" * 60)
    print("Mission Example 1 - 通用配置文件仿真")
    print("演示纯物理组件（渠道和闸门）动态行为")
    print("=" * 60)
    
    try:
        # 1. 设置路径
        current_dir = Path(__file__).parent
        universal_config_path = current_dir / "universal_config.yml"
        scenario_path = current_dir / "01_basic_simulation"
        
        print(f"\n📁 配置文件路径:")
        print(f"   通用配置: {universal_config_path}")
        print(f"   场景路径: {scenario_path}")
        
        # 2. 加载通用配置文件
        print(f"\n🔧 加载通用配置文件...")
        if not universal_config_path.exists():
            raise FileNotFoundError(f"通用配置文件不存在: {universal_config_path}")
            
        builder = load_universal_config(
            config_file=str(universal_config_path),
            scenario_path=str(scenario_path)
        )
        print("✅ 通用配置文件加载成功")
        
        # 3. 显示配置信息
        config = builder.enhanced_config
        sim_config = config.get('simulation', {})
        print(f"\n📋 仿真配置信息:")
        print(f"   名称: {sim_config.get('name', 'N/A')}")
        print(f"   描述: {sim_config.get('description', 'N/A')}")
        print(f"   版本: {sim_config.get('version', 'N/A')}")
        print(f"   持续时间: {sim_config.get('time', {}).get('end_time', 'N/A')} 秒")
        print(f"   时间步长: {sim_config.get('time', {}).get('time_step', 'N/A')} 秒")
        
        # 4. 显示启用的功能模块
        enabled_features = []
        if config.get('debug', {}).get('enabled', False):
            enabled_features.append("调试")
        if config.get('performance', {}).get('enabled', False):
            enabled_features.append("性能监控")
        if config.get('visualization', {}).get('enabled', False):
            enabled_features.append("可视化")
        if config.get('analysis', {}).get('enabled', False):
            enabled_features.append("分析")
        if config.get('logging', {}).get('enabled', False):
            enabled_features.append("日志")
            
        print(f"\n🚀 启用的功能模块: {', '.join(enabled_features)}")
        
        # 5. 构建仿真
        print(f"\n🏗️ 构建仿真系统...")
        simulation = builder.build_simulation()
        print("✅ 仿真系统构建成功")
        
        # 6. 运行增强仿真
        print(f"\n▶️ 开始运行增强仿真...")
        print("   (包含调试、性能监控、可视化等功能)")
        
        results = builder.run_enhanced_simulation()
        
        print("\n✅ 仿真运行完成!")
        
        # 7. 显示结果摘要
        if results:
            print(f"\n📊 仿真结果摘要:")
            if isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, (int, float)):
                        print(f"   {key}: {value:.4f}")
                    else:
                        print(f"   {key}: {type(value).__name__}")
        
        # 8. 显示输出文件信息
        output_config = config.get('output', {})
        if output_config.get('enabled', False):
            output_dir = output_config.get('output_directory', 'results/')
            print(f"\n📁 输出文件位置:")
            print(f"   结果目录: {output_dir}")
            
            if output_config.get('save_history', False):
                history_file = output_config.get('history_file', 'simulation_history.json')
                print(f"   历史文件: {history_file}")
        
        # 9. 显示可视化信息
        viz_config = config.get('visualization', {})
        if viz_config.get('enabled', False) and viz_config.get('plots', {}).get('enabled', False):
            plot_dir = viz_config.get('plots', {}).get('output_directory', 'plots/')
            print(f"   图表目录: {plot_dir}")
        
        # 10. 显示日志信息
        log_config = config.get('logging', {})
        if log_config.get('enabled', False):
            log_dir = log_config.get('log_directory', 'logs/')
            print(f"   日志目录: {log_dir}")
        
        print(f"\n🎉 Mission Example 1 仿真成功完成!")
        print(f"\n💡 提示:")
        print(f"   - 查看 {output_dir} 目录获取详细结果")
        print(f"   - 查看 {plot_dir} 目录获取可视化图表")
        print(f"   - 查看 {log_dir} 目录获取日志文件")
        print(f"   - 修改 universal_config.yml 来调整仿真参数")
        
    except FileNotFoundError as e:
        print(f"❌ 文件未找到错误: {e}")
        print(f"\n💡 解决方案:")
        print(f"   1. 确保 universal_config.yml 文件存在")
        print(f"   2. 确保 01_basic_simulation 目录存在")
        print(f"   3. 检查文件路径是否正确")
        return 1
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print(f"\n💡 解决方案:")
        print(f"   1. 确保已安装所有依赖包")
        print(f"   2. 确保项目路径设置正确")
        print(f"   3. 运行: pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        print(f"\n💡 调试建议:")
        print(f"   1. 检查配置文件语法是否正确")
        print(f"   2. 查看日志文件获取详细错误信息")
        print(f"   3. 确保所有组件配置文件存在")
        
        # 显示详细错误信息（仅在调试模式下）
        import traceback
        print(f"\n🔍 详细错误信息:")
        traceback.print_exc()
        return 1
    
    return 0

def compare_with_traditional():
    """
    比较传统配置方式和通用配置方式的差异
    """
    print("\n" + "=" * 60)
    print("配置方式对比")
    print("=" * 60)
    
    print("\n📋 传统配置方式:")
    print("   - 使用简单的 config.yml")
    print("   - 功能有限，主要是基础仿真参数")
    print("   - 调试和监控功能分散")
    print("   - 可视化需要手动编码")
    print("   - 缺乏标准化结构")
    
    print("\n🚀 通用配置方式:")
    print("   - 使用结构化的 universal_config.yml")
    print("   - 功能丰富，包含13个主要配置节")
    print("   - 集成调试、性能监控、可视化等功能")
    print("   - 自动生成图表和报告")
    print("   - 标准化配置结构")
    print("   - 向后兼容现有配置")
    
    print("\n✨ 主要优势:")
    print("   1. 🔧 标准化: 统一的配置结构")
    print("   2. 🚀 功能丰富: 集成多种高级功能")
    print("   3. 📊 自动化: 自动生成图表和报告")
    print("   4. 🔍 可观测性: 完整的调试和监控")
    print("   5. 🔄 兼容性: 与现有系统无缝集成")

if __name__ == "__main__":
    # 运行主程序
    exit_code = main()
    
    # 显示对比信息
    if exit_code == 0:
        compare_with_traditional()
    
    sys.exit(exit_code)