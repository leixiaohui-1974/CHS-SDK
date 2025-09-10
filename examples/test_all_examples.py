#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动测试所有示例的脚本
"""

import sys
import os
from pathlib import Path
import io

# 设置环境变量强制UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 设置标准输出编码为UTF-8
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from run_hardcoded import ExamplesHardcodedRunner

def test_all_examples():
    """测试所有示例"""
    runner = ExamplesHardcodedRunner()
    
    # 测试的示例列表（基于run_hardcoded.py中的实际键名）
    test_examples = [
        # 基础示例
        ("getting_started", "入门示例"),
        ("multi_component", "多组件系统"),
        
        # agent_based 系列示例
        ("event_driven_agents", "事件驱动智能体"),
        ("hierarchical_control", "分层控制"),
        ("complex_networks", "复杂网络"),
        ("pump_station", "泵站控制"),
        ("hydropower_plant", "水电站"),
        ("centralized_emergency_override", "集中式紧急覆盖"),
        ("agent_based_distributed_control", "基于智能体的分布式控制"),
        ("pid_control_comparison", "PID控制比较"),
        
        # canal_model 系列示例
        ("canal_pid_control", "运河PID控制"),
        ("canal_mpc_control", "运河MPC PID控制"),
        ("canal_model_comparison", "渠道模型对比"),
        ("complex_fault_scenario", "复杂故障场景"),
        ("hierarchical_distributed_control", "分层分布式控制"),
        ("structured_control", "结构化控制"),
        
        # identification 系列示例
        ("reservoir_identification", "水库库容曲线辨识"),
        ("gate_discharge_identification", "闸门流量系数辨识"),
        ("pipe_roughness_identification", "管道糙率辨识"),
        
        # mission_example 系列示例
        ("mission_example_1", "任务示例1"),
        ("mission_example_2", "任务示例2"),
        ("mission_example_3", "任务示例3"),
        ("mission_example_5", "任务示例5"),
        ("mission_scenarios", "Mission场景示例"),
        
        # watertank 系列示例
        ("watertank_simulation", "水箱仿真"),
        ("watertank_simple_sim", "水箱简单仿真"),
        ("watertank_pid_inlet", "水箱PID入口控制"),
        ("watertank_joint_control", "水箱联合控制"),
        
        # 其他示例
        ("simplified_demo", "简化演示"),
        ("pipe_and_valve", "管道与阀门"),
        ("non_agent_simulation", "非智能体仿真"),
        ("llm_integration", "LLM集成示例")
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
            status = "[PASS]" if success else "[FAIL]"
            print(f"Result: {status}\n")
            
        except Exception as e:
            results[example_key] = {
                'name': example_name,
                'success': False,
                'error': str(e)
            }
            print(f"Result: [ERROR] - {str(e)}\n")
    
    # 输出总结
    print("=== TEST SUMMARY ===")
    successful = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    print(f"Total tests: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success rate: {successful/total*100:.1f}%\n")
    
    # 详细结果
    print("Detailed results:")
    for example_key, result in results.items():
        status = "[PASS]" if result['success'] else "[FAIL]"
        print(f"  {status} {result['name']} ({example_key})")
        if result['error']:
            print(f"    Error: {result['error']}")
    
    return results

if __name__ == "__main__":
    test_all_examples()