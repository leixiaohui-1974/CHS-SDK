#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import traceback
import io
import contextlib
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class SilentDiagnoser:
    def __init__(self):
        self.examples_dir = Path(__file__).parent
        self.project_root = Path(__file__).parent.parent
        self.all_examples = self._discover_all_examples()
    
    def _discover_all_examples(self):
        """发现所有示例目录和子目录"""
        examples = []
        
        categories = [
            "agent_based",
            "canal_model", 
            "non_agent_based",
            "identification",
            "demo",
            "watertank"
        ]
        
        for category in categories:
            category_path = self.examples_dir / category
            if category_path.exists() and category_path.is_dir():
                if self._has_config_files(category_path):
                    examples.append({
                        'path': category,
                        'name': category,
                        'category': category,
                        'full_path': category_path
                    })
                
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
    
    def _silent_run(self, func, *args, **kwargs):
        """静默运行函数，捕获所有输出"""
        try:
            f = io.StringIO()
            with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
                result = func(*args, **kwargs)
            return True, "成功"
        except Exception as e:
            return False, str(e)[:100]
    
    def diagnose_hardcoded(self, example):
        """诊断硬编码模式"""
        def run_hardcoded():
            from examples.run_hardcoded import ExamplesHardcodedRunner
            runner = ExamplesHardcodedRunner()
            available_examples = [ex['name'] for ex in runner.examples]
            if example['name'] in available_examples:
                return runner.run_example(example['name'])
            else:
                raise Exception(f"示例 '{example['name']}' 不在硬编码列表中")
        
        return self._silent_run(run_hardcoded)
    
    def diagnose_scenario(self, example):
        """诊断传统配置文件模式"""
        # 检查配置文件
        config_files = ['config.yml', 'components.yml']
        missing_files = []
        for config_file in config_files:
            if not (example['full_path'] / config_file).exists():
                missing_files.append(config_file)
        
        if missing_files:
            return False, f"缺少配置文件: {missing_files}"
        
        def run_scenario():
            from examples.run_scenario import ExamplesScenarioRunner
            runner = ExamplesScenarioRunner()
            return runner.run_example(example['path'])
        
        return self._silent_run(run_scenario)
    
    def diagnose_smart(self, example):
        """诊断智能运行器模式"""
        def run_smart():
            from examples.run_smart import SmartRunner
            runner = SmartRunner()
            return runner.run_example(example['path'])
        
        return self._silent_run(run_smart)
    
    def diagnose_unified(self, example):
        """诊断统一配置模式"""
        unified_config = example['full_path'] / "unified_config.yml"
        if not unified_config.exists():
            return False, "缺少 unified_config.yml"
        
        try:
            cmd = [sys.executable, str(self.project_root / "run_unified_scenario.py"), str(unified_config)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0, f"退出码: {result.returncode}" if result.returncode != 0 else "成功"
        except Exception as e:
            return False, str(e)[:100]
    
    def diagnose_universal(self, example):
        """诊断通用配置模式"""
        universal_config = example['full_path'] / "universal_config.yml"
        if not universal_config.exists():
            return False, "缺少 universal_config.yml"
        
        try:
            cmd = [sys.executable, str(self.project_root / "run_universal_config.py"), str(universal_config)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0, f"退出码: {result.returncode}" if result.returncode != 0 else "成功"
        except Exception as e:
            return False, str(e)[:100]
    
    def diagnose_auto_test(self, example):
        """诊断自动测试模式"""
        return self.diagnose_hardcoded(example)  # 自动测试实际上是硬编码模式
    
    def diagnose_root_scenario(self, example):
        """诊断根目录场景模式"""
        try:
            cmd = [sys.executable, str(self.project_root / "run_scenario.py"), str(example['full_path'])]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0, f"退出码: {result.returncode}" if result.returncode != 0 else "成功"
        except Exception as e:
            return False, str(e)[:100]
    
    def run_diagnosis(self):
        """运行完整诊断"""
        modes = [
            ("硬编码模式", self.diagnose_hardcoded),
            ("传统配置文件模式", self.diagnose_scenario),
            ("智能运行器模式", self.diagnose_smart),
            ("统一配置模式", self.diagnose_unified),
            ("通用配置模式", self.diagnose_universal),
            ("自动测试模式", self.diagnose_auto_test),
            ("根目录场景模式", self.diagnose_root_scenario)
        ]
        
        failure_summary = {}
        success_count = 0
        total_count = 0
        
        print("CHS-SDK 静默诊断结果")
        print("="*50)
        
        for example in self.all_examples:
            print(f"\n{example['path']}:")
            
            for mode_name, diagnose_func in modes:
                success, message = diagnose_func(example)
                status = "✓" if success else "✗"
                print(f"  {mode_name}: {status}")
                
                if success:
                    success_count += 1
                else:
                    if mode_name not in failure_summary:
                        failure_summary[mode_name] = []
                    failure_summary[mode_name].append({
                        'example': example['path'],
                        'reason': message
                    })
                
                total_count += 1
        
        print(f"\n总体统计:")
        print(f"总测试数: {total_count}")
        print(f"成功数: {success_count}")
        print(f"成功率: {success_count/total_count*100:.1f}%")
        
        print("\n失败原因分析:")
        for mode_name, failures in failure_summary.items():
            print(f"\n{mode_name} ({len(failures)} 个失败):")
            # 统计失败原因
            reason_counts = {}
            for failure in failures:
                reason = failure['reason']
                if reason not in reason_counts:
                    reason_counts[reason] = 0
                reason_counts[reason] += 1
            
            for reason, count in reason_counts.items():
                print(f"  - {reason} ({count} 个示例)")

def main():
    diagnoser = SilentDiagnoser()
    diagnoser.run_diagnosis()

if __name__ == "__main__":
    main()