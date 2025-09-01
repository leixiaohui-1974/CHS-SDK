#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动测试所有示例的脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples.run_hardcoded import ExamplesHardcodedRunner

def test_all_examples():
    """测试所有示例"""
    runner = ExamplesHardcodedRunner()
    
    # 测试的示例列表（使用正确的键名）
    test_examples = [
        ("getting_started", "入门示例"),
        ("multi_component", "多组件系统"),
        ("event_driven_agents", "事件驱动智能体"),
        ("hierarchical_control", "分层控制"),
        ("complex_networks", "复杂网络"),
        ("pump_station", "泵站控制"),
        ("hydropower_plant", "水电站"),
        ("canal_pid_control", "渠道PID控制"),
        ("canal_mpc_control", "渠道MPC控制"),
        ("reservoir_identification", "水库参数辨识"),
        ("simplified_demo", "简化演示"),
        ("mission_example_1", "任务示例1"),
        ("mission_example_2", "任务示例2"),
        ("mission_example_3", "任务示例3"),
        ("mission_example_5", "任务示例5"),
        ("mission_scenarios", "Mission场景示例")
    ]
    
    results = {}
    
    print("=== 开始自动测试所有示例 ===")
    print(f"总共需要测试 {len(test_examples)} 个示例\n")
    
    for i, (example_key, example_name) in enumerate(test_examples, 1):
        print(f"[{i}/{len(test_examples)}] 测试示例: {example_name} ({example_key})")
        
        try:
            success = runner.run_example(example_key)
            results[example_key] = {
                'name': example_name,
                'success': success,
                'error': None
            }
            status = "✓ 成功" if success else "✗ 失败"
            print(f"结果: {status}\n")
            
        except Exception as e:
            results[example_key] = {
                'name': example_name,
                'success': False,
                'error': str(e)
            }
            print(f"结果: ✗ 异常 - {str(e)}\n")
    
    # 输出总结
    print("=== 测试总结 ===")
    successful = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    print(f"总测试数: {total}")
    print(f"成功: {successful}")
    print(f"失败: {total - successful}")
    print(f"成功率: {successful/total*100:.1f}%\n")
    
    # 详细结果
    print("详细结果:")
    for example_key, result in results.items():
        status = "✓" if result['success'] else "✗"
        print(f"  {status} {result['name']} ({example_key})")
        if result['error']:
            print(f"    错误: {result['error']}")
    
    return results

if __name__ == "__main__":
    test_all_examples()