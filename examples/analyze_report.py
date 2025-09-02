#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析报告统计工具
快速分析comprehensive_result_analyzer生成的JSON报告
"""

import json
from collections import defaultdict

def analyze_report():
    """分析报告统计"""
    with open('analysis_report.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = data['results']
    
    # 总体统计
    total_examples = len(results)
    total_tests = sum(len(example_results) for example_results in results.values())
    total_success = sum(
        sum(1 for result in example_results.values() if result['success'])
        for example_results in results.values()
    )
    
    print(f"\n=== CHS-SDK 全面结果分析统计 ===")
    print(f"时间戳: {data['timestamp']}")
    print(f"总示例数: {total_examples}")
    print(f"总测试数: {total_tests}")
    print(f"总成功数: {total_success}")
    print(f"总成功率: {total_success/total_tests*100:.1f}%")
    
    # 按模式统计
    print(f"\n=== 按模式统计 ===")
    mode_stats = defaultdict(lambda: {'success': 0, 'total': 0})
    
    for example_results in results.values():
        for mode, result in example_results.items():
            mode_stats[mode]['total'] += 1
            if result['success']:
                mode_stats[mode]['success'] += 1
    
    for mode, stats in mode_stats.items():
        success_rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"  {mode}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
    
    # 按示例统计成功率
    print(f"\n=== 示例成功率排行 (前10名) ===")
    example_success_rates = []
    
    for example_path, example_results in results.items():
        success_count = sum(1 for result in example_results.values() if result['success'])
        total_count = len(example_results)
        success_rate = success_count / total_count * 100 if total_count > 0 else 0
        example_success_rates.append((example_path, success_rate, success_count, total_count))
    
    example_success_rates.sort(key=lambda x: x[1], reverse=True)
    
    for i, (example_path, success_rate, success_count, total_count) in enumerate(example_success_rates[:10]):
        print(f"  {i+1:2d}. {example_path}: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    # 失败率最高的示例
    print(f"\n=== 失败率最高的示例 (后10名) ===")
    for i, (example_path, success_rate, success_count, total_count) in enumerate(example_success_rates[-10:]):
        print(f"  {len(example_success_rates)-10+i+1:2d}. {example_path}: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    # 错误类型统计
    print(f"\n=== 错误类型统计 ===")
    error_types = defaultdict(int)
    
    for example_results in results.values():
        for result in example_results.values():
            if not result['success']:
                error = result['error']
                if '缺少' in error and 'config' in error.lower():
                    error_types['缺少配置文件'] += 1
                elif '未在硬编码运行器中定义' in error:
                    error_types['硬编码运行器缺少定义'] += 1
                elif 'import' in error.lower() or 'module' in error.lower():
                    error_types['模块导入错误'] += 1
                elif 'unicode' in error.lower() or 'decode' in error.lower():
                    error_types['编码错误'] += 1
                else:
                    error_types['其他错误'] += 1
    
    for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {error_type}: {count} 次")
    
    print(f"\n=== 分析完成 ===")

if __name__ == "__main__":
    analyze_report()