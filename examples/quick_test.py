#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_single_example_all_modes(example_path):
    """测试单个示例的所有模式"""
    results = []
    
    # 模式1: 硬编码
    try:
        from examples.run_hardcoded import ExamplesHardcodedRunner
        runner = ExamplesHardcodedRunner()
        runner.run_example("getting_started")
        results.append(True)
    except Exception as e:
        results.append(False)
    
    # 模式2: 传统配置文件
    try:
        from examples.run_scenario import ExamplesScenarioRunner
        runner = ExamplesScenarioRunner()
        runner.run_example(example_path)
        results.append(True)
    except Exception as e:
        results.append(False)
    
    # 模式3: 智能运行器
    try:
        from examples.run_smart import SmartRunner
        runner = SmartRunner()
        runner.run_example(example_path)
        results.append(True)
    except Exception as e:
        results.append(False)
    
    return results

def main():
    """快速测试主要示例"""
    print("CHS-SDK 快速穷举测试")
    print("="*50)
    
    # 测试几个主要示例
    test_examples = [
        "agent_based/06_centralized_emergency_override",
        "non_agent_based/01_getting_started",
        "canal_model/canal_pid_control",
        "identification/01_reservoir_storage_curve"
    ]
    
    total_tests = 0
    total_success = 0
    
    for example in test_examples:
        print(f"\n测试示例: {example}")
        results = test_single_example_all_modes(example)
        
        success_count = sum(results)
        total_tests += len(results)
        total_success += success_count
        
        print(f"  成功: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    
    print(f"\n总体结果:")
    print(f"总测试数: {total_tests}")
    print(f"总成功数: {total_success}")
    print(f"总成功率: {total_success/total_tests*100:.1f}%")

if __name__ == "__main__":
    # 抑制所有输出
    import io
    import contextlib
    
    f = io.StringIO()
    with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
        main()
    
    # 只输出最后的结果
    output = f.getvalue()
    lines = output.split('\n')
    
    # 找到总体结果部分
    for i, line in enumerate(lines):
        if "总体结果" in line:
            print('\n'.join(lines[i:]))
            break
    else:
        print("测试完成，但未找到总体结果")