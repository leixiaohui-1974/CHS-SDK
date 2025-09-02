#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from test_all_modes import AllModesRunner

def diagnose_mode_1_hardcoded(example):
    """诊断硬编码模式"""
    try:
        from examples.run_hardcoded import ExamplesHardcodedRunner
        runner = ExamplesHardcodedRunner()
        # 硬编码模式只能运行预定义的示例
        available_examples = [ex['name'] for ex in runner.examples]
        if example['name'] in available_examples:
            result = runner.run_example(example['name'])
            return True, "成功"
        else:
            return False, f"示例 '{example['name']}' 不在硬编码列表中，可用示例: {available_examples}"
    except Exception as e:
        return False, f"异常: {str(e)}"

def diagnose_mode_2_scenario(example):
    """诊断传统配置文件模式"""
    try:
        # 检查是否有传统配置文件
        config_files = ['config.yml', 'components.yml', 'topology.yml', 'agents.yml']
        missing_files = []
        for config_file in config_files:
            if not (example['full_path'] / config_file).exists():
                missing_files.append(config_file)
        
        if missing_files:
            return False, f"缺少传统配置文件: {missing_files}"
        
        from examples.run_scenario import ExamplesScenarioRunner
        runner = ExamplesScenarioRunner()
        result = runner.run_example(example['path'])
        return True, "成功"
    except Exception as e:
        return False, f"异常: {str(e)}"

def diagnose_mode_3_smart(example):
    """诊断智能运行器模式"""
    try:
        from examples.run_smart import SmartRunner
        runner = SmartRunner()
        result = runner.run_example(example['path'])
        return True, "成功"
    except Exception as e:
        return False, f"异常: {str(e)}"

def diagnose_mode_4_unified(example):
    """诊断统一配置模式"""
    try:
        unified_config = example['full_path'] / "unified_config.yml"
        if not unified_config.exists():
            return False, "缺少 unified_config.yml 文件"
        
        cmd = [sys.executable, str(project_root / "run_unified_scenario.py"), str(unified_config)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return True, "成功"
        else:
            return False, f"退出码: {result.returncode}, 错误: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, "超时"
    except Exception as e:
        return False, f"异常: {str(e)}"

def diagnose_mode_5_universal(example):
    """诊断通用配置模式"""
    try:
        universal_config = example['full_path'] / "universal_config.yml"
        if not universal_config.exists():
            return False, "缺少 universal_config.yml 文件"
        
        cmd = [sys.executable, str(project_root / "run_universal_config.py"), str(universal_config)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return True, "成功"
        else:
            return False, f"退出码: {result.returncode}, 错误: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, "超时"
    except Exception as e:
        return False, f"异常: {str(e)}"

def diagnose_mode_6_auto_test(example):
    """诊断自动测试模式"""
    try:
        from examples.run_hardcoded import ExamplesHardcodedRunner
        runner = ExamplesHardcodedRunner()
        # 自动测试模式实际上是运行硬编码示例
        available_examples = [ex['name'] for ex in runner.examples]
        if example['name'] in available_examples:
            success = runner.run_example(example['name'])
            return success, "成功" if success else "运行失败"
        else:
            return False, f"示例 '{example['name']}' 不在硬编码列表中"
    except Exception as e:
        return False, f"异常: {str(e)}"

def diagnose_mode_7_root_scenario(example):
    """诊断根目录场景模式"""
    try:
        cmd = [sys.executable, str(project_root / "run_scenario.py"), str(example['full_path'])]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return True, "成功"
        else:
            return False, f"退出码: {result.returncode}, 错误: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, "超时"
    except Exception as e:
        return False, f"异常: {str(e)}"

def main():
    """主诊断函数"""
    print("CHS-SDK 测试失败诊断")
    print("="*60)
    
    runner = AllModesRunner()
    
    modes = [
        ("硬编码模式", diagnose_mode_1_hardcoded),
        ("传统配置文件模式", diagnose_mode_2_scenario),
        ("智能运行器模式", diagnose_mode_3_smart),
        ("统一配置模式", diagnose_mode_4_unified),
        ("通用配置模式", diagnose_mode_5_universal),
        ("自动测试模式", diagnose_mode_6_auto_test),
        ("根目录场景模式", diagnose_mode_7_root_scenario)
    ]
    
    failure_summary = {}
    
    for example in runner.all_examples:
        print(f"\n--- 诊断示例: {example['path']} ---")
        
        for mode_name, diagnose_func in modes:
            success, message = diagnose_func(example)
            status = "✓" if success else "✗"
            print(f"  {mode_name}: {status} {message}")
            
            if not success:
                if mode_name not in failure_summary:
                    failure_summary[mode_name] = []
                failure_summary[mode_name].append({
                    'example': example['path'],
                    'reason': message
                })
    
    # 输出失败总结
    print("\n" + "="*60)
    print("失败原因总结")
    print("="*60)
    
    for mode_name, failures in failure_summary.items():
        print(f"\n{mode_name} ({len(failures)} 个失败):")
        for failure in failures:
            print(f"  - {failure['example']}: {failure['reason']}")

if __name__ == "__main__":
    main()