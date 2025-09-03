#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
只测试传统多配置文件方法的调试脚本
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path.cwd()))

from test_all_simulation_modes import SimulationModesTester

def main():
    print("🔍 只测试传统多配置文件方法")
    print("=" * 60)
    
    # 创建测试器实例
    tester = SimulationModesTester()
    
    # 只运行传统多配置文件方法测试
    print("\n[1/1] 🔄 Testing Traditional Multi-Configuration File Method...")
    try:
        success = tester.test_scenario_runner()
        if success:
            print("[1/1] ✓ Traditional Multi-Configuration File Method test passed")
        else:
            print("[1/1] ✗ Traditional Multi-Configuration File Method test failed")
    except Exception as e:
        print(f"[1/1] ✗ Test Traditional Multi-Configuration File Method exception occurred: {e}")
        success = False
    
    # 显示结果
    print("\n" + "=" * 60)
    print("🎯 测试结果:")
    if success:
        print("✅ 传统多配置文件方法测试通过")
    else:
        print("❌ 传统多配置文件方法测试失败")
        
        # 显示详细的测试结果
        if "run_scenario" in tester.test_results:
            result = tester.test_results["run_scenario"]
            print(f"\n详细信息:")
            print(f"成功: {result['success']}")
            print(f"执行时间: {result['execution_time']:.2f}秒")
            print(f"总示例数: {result['total_examples']}")
            print(f"失败示例: {result['failed_examples']}")
            if result['output']:
                print(f"\n输出 (前1000字符):")
                print(result['output'][:1000])
                if len(result['output']) > 1000:
                    print("...")

if __name__ == "__main__":
    main()