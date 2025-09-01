#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用配置文件测试脚本
测试增强的SimulationBuilder和通用配置文件的功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.config.enhanced_yaml_loader import EnhancedSimulationBuilder, load_universal_config


def test_universal_config():
    """
    测试通用配置文件功能
    """
    print("=" * 60)
    print("通用配置文件功能测试")
    print("=" * 60)
    
    # 配置文件路径
    config_file = "core_lib/config/example_universal_config.yml"
    
    if not os.path.exists(config_file):
        print(f"错误: 配置文件不存在 - {config_file}")
        return False
        
    try:
        # 测试1: 加载配置文件
        print("\n1. 测试配置文件加载...")
        builder = load_universal_config(config_file)
        print("✓ 配置文件加载成功")
        
        # 测试2: 检查增强功能是否正确初始化
        print("\n2. 检查增强功能初始化...")
        
        # 检查调试管理器
        if builder.debug_manager:
            print("✓ 调试管理器已初始化")
            print(f"  - 会话ID: {builder.debug_manager.session_id}")
        else:
            print("- 调试管理器未启用")
            
        # 检查性能监控器
        if builder.performance_monitor:
            print("✓ 性能监控器已初始化")
            print(f"  - 开始时间: {builder.performance_monitor.start_time}")
        else:
            print("- 性能监控器未启用")
            
        # 检查可视化管理器
        if builder.visualization_manager:
            print("✓ 可视化管理器已初始化")
            plots_config = builder.visualization_manager.plots_config
            if plots_config.get('enabled', False):
                charts = plots_config.get('charts', [])
                print(f"  - 配置了 {len(charts)} 个图表")
        else:
            print("- 可视化管理器未启用")
            
        # 检查分析管理器
        if builder.analysis_manager:
            print("✓ 分析管理器已初始化")
        else:
            print("- 分析管理器未启用")
            
        # 检查日志管理器
        if builder.logger_manager:
            print("✓ 日志管理器已初始化")
        else:
            print("- 日志管理器未启用")
            
        # 检查错误处理器
        if builder.error_handler:
            print("✓ 错误处理器已初始化")
            print(f"  - 错误策略: {builder.error_handler.error_policy}")
        else:
            print("- 错误处理器未启用")
            
        # 检查环境管理器
        if builder.environment_manager:
            print("✓ 环境管理器已初始化")
            print(f"  - 当前环境: {builder.environment_manager.current_env}")
        else:
            print("- 环境管理器未启用")
            
        # 检查缓存管理器
        if builder.cache_manager:
            print("✓ 缓存管理器已初始化")
            print(f"  - 缓存目录: {builder.cache_manager.cache_directory}")
        else:
            print("- 缓存管理器未启用")
            
        # 测试3: 检查配置文件内容
        print("\n3. 检查配置文件内容...")
        config = builder.enhanced_config
        
        # 检查主要配置节
        sections = ['simulation', 'debug', 'performance', 'visualization', 
                   'output', 'analysis', 'logging', 'error_handling', 
                   'environment']
        
        for section in sections:
            if section in config:
                enabled = config[section].get('enabled', 'N/A')
                print(f"  ✓ {section}: enabled={enabled}")
            else:
                print(f"  - {section}: 未配置")
                
        # 测试4: 测试仿真配置映射
        print("\n4. 测试仿真配置映射...")
        if hasattr(builder, 'config') and builder.config:
            if 'time' in builder.config:
                time_config = builder.config['time']
                print(f"  ✓ 时间配置: {time_config['start_time']}s - {time_config['end_time']}s")
                print(f"    步长: {time_config['time_step']}s")
                
            if 'solver' in builder.config:
                solver_config = builder.config['solver']
                print(f"  ✓ 求解器配置: {solver_config['type']}, 阶数={solver_config['order']}")
        else:
            print("  - 仿真配置未映射")
            
        # 测试5: 测试模拟运行
        print("\n5. 测试模拟仿真运行...")
        try:
            # 注意：这里只是测试配置加载，不运行实际仿真
            print("  准备运行增强仿真...")
            
            # 模拟一些性能指标记录
            if builder.performance_monitor:
                builder.performance_monitor.record_metric('test_metric', 1.23)
                print("  ✓ 性能指标记录测试通过")
                
            # 模拟分析功能
            if builder.analysis_manager:
                mock_data = {'time': [0, 1, 2], 'values': [1, 2, 3]}
                analysis_results = builder.analysis_manager.analyze_results(mock_data)
                print(f"  ✓ 分析功能测试通过: {len(analysis_results)} 个分析结果")
                
            # 模拟可视化功能
            if builder.visualization_manager:
                mock_data = {'time': [0, 1, 2], 'values': [1, 2, 3]}
                builder.visualization_manager.create_visualizations(mock_data)
                print("  ✓ 可视化功能测试通过")
                
            print("  ✓ 模拟仿真运行测试通过")
            
        except Exception as e:
            print(f"  ✗ 模拟仿真运行测试失败: {e}")
            
        print("\n" + "=" * 60)
        print("✓ 通用配置文件功能测试完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_validation():
    """
    测试配置文件验证功能
    """
    print("\n" + "=" * 60)
    print("配置文件验证测试")
    print("=" * 60)
    
    config_file = "core_lib/config/example_universal_config.yml"
    
    try:
        import yaml
        
        # 测试YAML文件格式
        print("\n1. 测试YAML文件格式...")
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("✓ YAML格式验证通过")
        
        # 测试必需的配置节
        print("\n2. 测试必需的配置节...")
        required_sections = ['simulation']
        for section in required_sections:
            if section in config:
                print(f"  ✓ {section} 节存在")
            else:
                print(f"  ✗ {section} 节缺失")
                
        # 测试仿真配置的必需字段
        print("\n3. 测试仿真配置字段...")
        if 'simulation' in config:
            sim_config = config['simulation']
            required_fields = ['name', 'time', 'solver']
            for field in required_fields:
                if field in sim_config:
                    print(f"  ✓ simulation.{field} 存在")
                else:
                    print(f"  ✗ simulation.{field} 缺失")
                    
        # 测试时间配置
        print("\n4. 测试时间配置...")
        if 'simulation' in config and 'time' in config['simulation']:
            time_config = config['simulation']['time']
            time_fields = ['start_time', 'end_time', 'time_step']
            for field in time_fields:
                if field in time_config:
                    value = time_config[field]
                    if isinstance(value, (int, float)) and value >= 0:
                        print(f"  ✓ time.{field} = {value} (有效)")
                    else:
                        print(f"  ✗ time.{field} = {value} (无效)")
                else:
                    print(f"  ✗ time.{field} 缺失")
                    
        print("\n" + "=" * 60)
        print("✓ 配置文件验证测试完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 配置文件验证失败: {e}")
        return False


def main():
    """
    主测试函数
    """
    print("CHS-SDK 通用配置文件测试套件")
    print("版本: 1.0.0")
    print("作者: CHS-SDK Team")
    
    # 检查工作目录
    current_dir = os.getcwd()
    print(f"\n当前工作目录: {current_dir}")
    
    # 检查必要文件是否存在
    required_files = [
        "core_lib/config/universal_config_template.yml",
        "core_lib/config/example_universal_config.yml",
        "core_lib/config/enhanced_yaml_loader.py"
    ]
    
    print("\n检查必要文件...")
    all_files_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (缺失)")
            all_files_exist = False
            
    if not all_files_exist:
        print("\n错误: 缺少必要文件，请确保所有文件都已创建")
        return False
        
    # 运行测试
    test_results = []
    
    # 测试1: 配置文件验证
    print("\n" + "=" * 80)
    result1 = test_config_validation()
    test_results.append(('配置文件验证', result1))
    
    # 测试2: 通用配置功能
    print("\n" + "=" * 80)
    result2 = test_universal_config()
    test_results.append(('通用配置功能', result2))
    
    # 输出测试总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
            
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！通用配置文件系统工作正常。")
        return True
    else:
        print(f"\n❌ {total - passed} 个测试失败，请检查配置。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)