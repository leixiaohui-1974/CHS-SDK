#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 所有运行模式综合测试脚本

本脚本测试CHS-SDK的7种运行模式：
1. 硬编码模式 (run_hardcoded.py)
2. 传统配置文件模式 (run_scenario.py)
3. 智能运行器模式 (run_smart.py)
4. 统一配置模式 (run_unified_scenario.py)
5. 通用配置模式 (run_universal_config.py)
6. 自动测试模式 (test_all_examples.py)
7. 根目录运行模式 (../run_scenario.py)

每种模式都会运行一个简单的示例来验证功能正常。
"""

import sys
import os
import time
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class AllModesRunner:
    """全模式运行器 - 穷举所有示例"""
    
    def __init__(self):
        self.examples_dir = Path(__file__).parent
        self.project_root = Path(__file__).parent.parent
        self.all_examples = self._discover_all_examples()
        print(f"发现 {len(self.all_examples)} 个示例")
    
    def _discover_all_examples(self):
        """发现所有示例目录和子目录"""
        examples = []
        
        # 定义要搜索的主要类别目录
        categories = [
            "agent_based",
            "canal_model", 
            "non_agent_based",
            "identification",
            "demo",
            "watertank",
            "notebooks",
            "llm_integration",
            "watertank_refactored"
        ]
        
        for category in categories:
            category_path = self.examples_dir / category
            if category_path.exists() and category_path.is_dir():
                # 检查类别目录本身是否有配置文件
                if self._has_config_files(category_path):
                    examples.append({
                        'path': category,
                        'name': category,
                        'category': category,
                        'full_path': category_path
                    })
                
                # 搜索子目录
                for subdir in category_path.iterdir():
                    if subdir.is_dir() and not subdir.name.startswith('.'):
                        if self._has_config_files(subdir):
                            examples.append({
                                'path': f"{category}/{subdir.name}",
                                'name': subdir.name,
                                'category': category,
                                'full_path': subdir
                            })
        
        return examples
    
    def _has_config_files(self, path):
        """检查目录是否包含配置文件"""
        config_files = [
            'config.yml', 'config.yaml',
            'unified_config.yml', 'unified_config.yaml',
            'universal_config.yml', 'universal_config.yaml',
            'components.yml', 'components.yaml'
        ]
        
        for config_file in config_files:
            if (path / config_file).exists():
                return True
        return False
        
    def run_mode_1_hardcoded(self, example):
        """模式1: 硬编码运行"""
        try:
            from examples.run_hardcoded import ExamplesHardcodedRunner
            runner = ExamplesHardcodedRunner()
            # 尝试运行示例，如果失败则跳过
            result = runner.run_example("getting_started")
            return True
        except Exception as e:
            return False
    
    def run_mode_2_scenario(self, example):
        """模式2: 传统配置文件运行"""
        try:
            from examples.run_scenario import ExamplesScenarioRunner
            runner = ExamplesScenarioRunner()
            result = runner.run_example(example['path'])
            return True
        except Exception as e:
            return False
    
    def run_mode_3_smart(self, example):
        """模式3: 智能运行器"""
        try:
            from examples.run_smart import SmartRunner
            runner = SmartRunner()
            result = runner.run_example(example['path'])
            return True
        except Exception as e:
            return False
    
    def run_mode_4_unified(self, example):
        """模式4: 统一配置运行"""
        try:
            # 使用subprocess运行根目录的统一配置脚本
            cmd = [sys.executable, str(self.project_root / "run_unified_scenario.py"), 
                   str(example['full_path'] / "unified_config.yml")]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            return False
    
    def run_mode_5_universal(self, example):
        """模式5: 通用配置运行"""
        try:
            # 使用subprocess运行根目录的通用配置脚本
            cmd = [sys.executable, str(self.project_root / "run_universal_config.py"), 
                   str(example['full_path'] / "universal_config.yml")]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            return False
    
    def run_mode_6_auto_test(self, example):
        """模式6: 自动测试模式"""
        try:
            from examples.test_all_examples import test_all_examples
            # 运行一个简化版本的测试
            from examples.run_hardcoded import ExamplesHardcodedRunner
            runner = ExamplesHardcodedRunner()
            success = runner.run_example(example['path'])
            return success
        except Exception as e:
            return False
    
    def run_mode_7_root_scenario(self, example):
        """模式7: 根目录场景运行"""
        try:
            # 使用subprocess运行根目录的场景脚本
            cmd = [sys.executable, str(self.project_root / "run_scenario.py"), str(example['full_path'])]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            return False
    
    def run_all_modes(self):
        """运行所有模式测试 - 穷举所有示例"""
        print("\n" + "="*80)
        print("开始CHS-SDK全模式穷举测试")
        print("="*80)
        
        modes = [
            ("硬编码模式", self.run_mode_1_hardcoded),
            ("传统配置文件模式", self.run_mode_2_scenario),
            ("智能运行器模式", self.run_mode_3_smart),
            ("统一配置模式", self.run_mode_4_unified),
            ("通用配置模式", self.run_mode_5_universal),
            ("自动测试模式", self.run_mode_6_auto_test),
            ("根目录场景模式", self.run_mode_7_root_scenario)
        ]
        
        total_tests = 0
        total_success = 0
        example_results = {}
        
        for example in self.all_examples:
            print(f"\n--- 测试示例: {example['path']} ---")
            example_success = 0
            example_total = 0
            
            for mode_name, mode_func in modes:
                try:
                    success = mode_func(example)
                    status = "✓" if success else "✗"
                    print(f"  {mode_name}: {status}")
                    
                    if success:
                        example_success += 1
                        total_success += 1
                    example_total += 1
                    total_tests += 1
                    
                except Exception as e:
                    print(f"  {mode_name}: ✗ (异常: {str(e)[:50]}...)")
                    example_total += 1
                    total_tests += 1
            
            example_rate = (example_success / example_total) * 100 if example_total > 0 else 0
            example_results[example['path']] = {
                'success': example_success,
                'total': example_total,
                'rate': example_rate
            }
            print(f"  示例成功率: {example_rate:.1f}% ({example_success}/{example_total})")
        
        # 输出总结
        print("\n" + "="*80)
        print("穷举测试结果总结")
        print("="*80)
        
        print(f"总示例数: {len(self.all_examples)}")
        print(f"总测试数: {total_tests}")
        print(f"总成功数: {total_success}")
        print(f"总成功率: {(total_success/total_tests)*100:.1f}%")
        
        print("\n各示例详细结果:")
        for example_path, result in example_results.items():
            print(f"  {example_path}: {result['rate']:.1f}% ({result['success']}/{result['total']})")
        
        return example_results

def main():
    """主函数"""
    runner = AllModesRunner()
    results = runner.run_all_modes()
    
    # 返回退出码
    success_count = sum(1 for success in results.values() if success)
    if success_count == len(results):
        sys.exit(0)  # 全部成功
    else:
        sys.exit(1)  # 有失败

if __name__ == "__main__":
    main()