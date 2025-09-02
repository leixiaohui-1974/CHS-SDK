#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path
import subprocess
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class QuickTestRunner:
    def __init__(self):
        self.examples_dir = Path(__file__).parent
        self.all_examples = self._discover_examples()
        self.results = {}
        
    def _discover_examples(self):
        """发现所有示例"""
        examples = []
        
        categories = ["agent_based", "canal_model", "non_agent_based", "identification", "watertank"]
        
        for category in categories:
            category_path = self.examples_dir / category
            if category_path.exists():
                for subdir in category_path.iterdir():
                    if subdir.is_dir() and not subdir.name.startswith('.'):
                        if self._has_config_files(subdir):
                            examples.append(f"{category}/{subdir.name}")
        
        return examples
    
    def _has_config_files(self, path):
        """检查是否有配置文件"""
        config_files = ['config.yml', 'unified_config.yml', 'universal_config.yml']
        return any((path / f).exists() for f in config_files)
    
    def test_smart_runner(self, example):
        """测试智能运行器"""
        try:
            cmd = [sys.executable, "run_smart.py", example]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, cwd=self.examples_dir)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
    
    def test_config_check(self, example):
        """测试配置检查"""
        try:
            # 检查配置文件是否存在
            example_path = self.examples_dir / example
            config_files = ['config.yml', 'unified_config.yml', 'universal_config.yml', 'components.yml']
            
            found_configs = []
            for config_file in config_files:
                if (example_path / config_file).exists():
                    found_configs.append(config_file)
            
            return len(found_configs) >= 2  # 至少有2个配置文件
        except Exception:
            return False
    
    def test_hardcoded_support(self, example):
        """测试硬编码支持"""
        try:
            from examples.run_hardcoded import ExamplesHardcodedRunner
            runner = ExamplesHardcodedRunner()
            supported_paths = [info['path'] for info in runner.examples.values()]
            return example in supported_paths
        except Exception:
            return False
    
    def run_quick_test(self):
        """运行快速测试"""
        print(f"发现 {len(self.all_examples)} 个示例")
        print("\n" + "="*80)
        print("开始CHS-SDK快速配置测试")
        print("="*80)
        
        total_tests = 0
        passed_tests = 0
        
        for example in self.all_examples:
            print(f"\n--- 测试示例: {example} ---")
            
            # 测试1: 配置文件检查
            config_ok = self.test_config_check(example)
            total_tests += 1
            if config_ok:
                passed_tests += 1
                print("  配置文件: ✓")
            else:
                print("  配置文件: ✗")
            
            # 测试2: 硬编码支持
            hardcoded_ok = self.test_hardcoded_support(example)
            total_tests += 1
            if hardcoded_ok:
                passed_tests += 1
                print("  硬编码支持: ✓")
            else:
                print("  硬编码支持: ✗")
            
            # 测试3: 智能运行器（快速测试）
            smart_ok = self.test_smart_runner(example)
            total_tests += 1
            if smart_ok:
                passed_tests += 1
                print("  智能运行器: ✓")
            else:
                print("  智能运行器: ✗")
            
            self.results[example] = {
                'config': config_ok,
                'hardcoded': hardcoded_ok,
                'smart': smart_ok
            }
        
        print("\n" + "="*80)
        print("测试结果汇总")
        print("="*80)
        print(f"总测试数: {total_tests}")
        print(f"通过数: {passed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        # 按类别统计
        config_passed = sum(1 for r in self.results.values() if r['config'])
        hardcoded_passed = sum(1 for r in self.results.values() if r['hardcoded'])
        smart_passed = sum(1 for r in self.results.values() if r['smart'])
        
        print(f"\n各测试项统计:")
        print(f"配置文件检查: {config_passed}/{len(self.all_examples)} ({config_passed/len(self.all_examples)*100:.1f}%)")
        print(f"硬编码支持: {hardcoded_passed}/{len(self.all_examples)} ({hardcoded_passed/len(self.all_examples)*100:.1f}%)")
        print(f"智能运行器: {smart_passed}/{len(self.all_examples)} ({smart_passed/len(self.all_examples)*100:.1f}%)")
        
        # 显示失败的示例
        failed_examples = []
        for example, result in self.results.items():
            if not all(result.values()):
                failed_items = [k for k, v in result.items() if not v]
                failed_examples.append(f"{example}: {', '.join(failed_items)}")
        
        if failed_examples:
            print(f"\n需要关注的示例:")
            for failed in failed_examples:
                print(f"  - {failed}")
        else:
            print(f"\n🎉 所有示例都通过了基本测试！")
        
        return self.results

def main():
    runner = QuickTestRunner()
    results = runner.run_quick_test()
    return results

if __name__ == "__main__":
    main()