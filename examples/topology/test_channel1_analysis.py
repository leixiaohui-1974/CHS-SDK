#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试渠道1入流分析功能的简单脚本
"""

import os
import sys
from pathlib import Path

# 添加核心库路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

def test_import():
    """测试导入是否正常"""
    try:
        from run_topology_demo import (
            load_configuration, 
            create_simulation_components,
            create_channel1_inflow_analysis
        )
        print("[OK] 导入测试成功")
        return True
    except Exception as e:
        print(f"[ERROR] 导入测试失败: {e}")
        return False

def test_config_files():
    """测试配置文件是否存在"""
    config_files = [
        'config.yml',
        'components.yml', 
        'topology.yml',
        'agents.yml'
    ]
    
    all_exist = True
    for config_file in config_files:
        file_path = current_dir / config_file
        if file_path.exists():
            print(f"[OK] {config_file} 存在")
        else:
            print(f"[ERROR] {config_file} 不存在")
            all_exist = False
    
    return all_exist

def test_csv_creation():
    """测试CSV创建函数"""
    try:
        from run_topology_demo import create_channel1_inflow_analysis
        
        # 创建模拟数据
        mock_results = [
            {
                'time': 0,
                'Channel_1': {'inflow': 25.0, 'outflow': 25.0, 'water_level': 61.9, 'volume': 800000},
                'Upstream_Reservoir': {'outflow': 25.0, 'water_level': 62.8, 'volume': 15000}
            },
            {
                'time': 60,
                'Channel_1': {'inflow': 25.1, 'outflow': 25.0, 'water_level': 61.9, 'volume': 800100},
                'Upstream_Reservoir': {'outflow': 25.1, 'water_level': 62.8, 'volume': 15100}
            }
        ]
        
        test_csv_file = current_dir / "test_channel1_analysis.csv"
        create_channel1_inflow_analysis(mock_results, None, None, test_csv_file)
        
        if test_csv_file.exists():
            print("[OK] CSV创建测试成功")
            # 读取并显示前几行
            with open(test_csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:5]
                print("CSV内容预览:")
                for i, line in enumerate(lines):
                    print(f"  行{i+1}: {line.strip()}")
            
            # 清理测试文件
            test_csv_file.unlink()
            return True
        else:
            print("[ERROR] CSV文件未创建")
            return False
            
    except Exception as e:
        print(f"[ERROR] CSV创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("渠道1入流分析功能测试")
    print("=" * 40)
    
    tests = [
        ("导入测试", test_import),
        ("配置文件测试", test_config_files), 
        ("CSV创建测试", test_csv_creation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 40)
    print("测试结果汇总:")
    all_passed = True
    for test_name, result in results:
        status = "通过" if result else "失败"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n[OK] 所有测试通过！可以运行完整的仿真演示")
        print("运行命令: python run_topology_demo.py")
    else:
        print("\n[ERROR] 部分测试失败，请检查配置")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
