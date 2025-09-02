#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from test_all_modes import AllModesRunner

def main():
    """运行简化的全模式测试，只显示总结"""
    print("开始CHS-SDK全模式穷举测试（简化版）...")
    
    runner = AllModesRunner()
    
    # 静默运行所有测试
    import io
    import contextlib
    
    # 捕获输出
    f = io.StringIO()
    with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
        results = runner.run_all_modes()
    
    # 计算总结统计
    total_examples = len(runner.all_examples)
    total_tests = sum(result['total'] for result in results.values())
    total_success = sum(result['success'] for result in results.values())
    success_rate = (total_success / total_tests) * 100 if total_tests > 0 else 0
    
    print("\n" + "="*80)
    print("CHS-SDK 穷举测试结果总结")
    print("="*80)
    print(f"总示例数: {total_examples}")
    print(f"总测试数: {total_tests} (每个示例测试7种模式)")
    print(f"总成功数: {total_success}")
    print(f"总成功率: {success_rate:.1f}%")
    
    print("\n各示例详细结果:")
    for example_path, result in results.items():
        print(f"  {example_path}: {result['rate']:.1f}% ({result['success']}/{result['total']})")
    
    # 按类别统计
    category_stats = {}
    for example in runner.all_examples:
        category = example['category']
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'success': 0}
        
        example_result = results[example['path']]
        category_stats[category]['total'] += example_result['total']
        category_stats[category]['success'] += example_result['success']
    
    print("\n按类别统计:")
    for category, stats in category_stats.items():
        rate = (stats['success'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"  {category}: {rate:.1f}% ({stats['success']}/{stats['total']})")

if __name__ == "__main__":
    main()