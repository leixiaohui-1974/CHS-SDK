#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import yaml
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ConfigChecker:
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
    
    def check_hardcoded_support(self, example):
        """检查硬编码模式支持"""
        try:
            from examples.run_hardcoded import ExamplesHardcodedRunner
            runner = ExamplesHardcodedRunner()
            # runner.examples是字典，键是示例ID，值是示例信息
            available_example_names = [info['name'] for info in runner.examples.values()]
            available_example_paths = [info['path'] for info in runner.examples.values()]
            
            # 检查示例名称或路径是否匹配
            if (example['name'] in available_example_names or 
                example['path'] in available_example_paths):
                return True, "支持"
            else:
                return False, f"示例 '{example['name']}' 不在硬编码列表中"
        except Exception as e:
            return False, f"导入错误: {str(e)[:50]}"
    
    def check_scenario_files(self, example):
        """检查传统配置文件模式所需文件"""
        config_yml = example['full_path'] / "config.yml"
        components_yml = example['full_path'] / "components.yml"
        
        missing = []
        if not config_yml.exists():
            missing.append("config.yml")
        if not components_yml.exists():
            missing.append("components.yml")
        
        if missing:
            return False, f"缺少文件: {missing}"
        
        # 检查YAML语法
        try:
            with open(config_yml, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
        except Exception as e:
            return False, f"config.yml语法错误: {str(e)[:50]}"
        
        try:
            with open(components_yml, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
        except Exception as e:
            return False, f"components.yml语法错误: {str(e)[:50]}"
        
        return True, "配置文件完整"
    
    def check_unified_config(self, example):
        """检查统一配置模式"""
        unified_config = example['full_path'] / "unified_config.yml"
        if not unified_config.exists():
            return False, "缺少 unified_config.yml"
        
        try:
            with open(unified_config, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            return True, "配置文件存在且语法正确"
        except Exception as e:
            return False, f"YAML语法错误: {str(e)[:50]}"
    
    def check_universal_config(self, example):
        """检查通用配置模式"""
        universal_config = example['full_path'] / "universal_config.yml"
        if not universal_config.exists():
            return False, "缺少 universal_config.yml"
        
        try:
            with open(universal_config, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            return True, "配置文件存在且语法正确"
        except Exception as e:
            return False, f"YAML语法错误: {str(e)[:50]}"
    
    def check_smart_runner(self, example):
        """检查智能运行器模式"""
        # 智能运行器应该能自动检测配置文件
        config_files = [
            'config.yml', 'components.yml',
            'unified_config.yml', 'universal_config.yml'
        ]
        
        found_configs = []
        for config_file in config_files:
            if (example['full_path'] / config_file).exists():
                found_configs.append(config_file)
        
        if not found_configs:
            return False, "没有找到任何配置文件"
        
        return True, f"找到配置文件: {found_configs}"
    
    def run_check(self):
        """运行配置检查"""
        modes = [
            ("硬编码模式", self.check_hardcoded_support),
            ("传统配置文件模式", self.check_scenario_files),
            ("智能运行器模式", self.check_smart_runner),
            ("统一配置模式", self.check_unified_config),
            ("通用配置模式", self.check_universal_config),
            ("自动测试模式", self.check_hardcoded_support),  # 同硬编码
            ("根目录场景模式", self.check_scenario_files)     # 同传统配置
        ]
        
        print("CHS-SDK 配置检查结果")
        print("="*50)
        
        total_tests = 0
        total_success = 0
        mode_stats = {}
        
        for example in self.all_examples:
            print(f"\n{example['path']}:")
            
            for mode_name, check_func in modes:
                success, message = check_func(example)
                status = "OK" if success else "FAIL"
                print(f"  {mode_name}: {status} - {message}")
                
                if mode_name not in mode_stats:
                    mode_stats[mode_name] = {'success': 0, 'total': 0, 'failures': []}
                
                mode_stats[mode_name]['total'] += 1
                if success:
                    mode_stats[mode_name]['success'] += 1
                    total_success += 1
                else:
                    mode_stats[mode_name]['failures'].append({
                        'example': example['path'],
                        'reason': message
                    })
                
                total_tests += 1
        
        print(f"\n总体统计:")
        print(f"总测试数: {total_tests}")
        print(f"成功数: {total_success}")
        print(f"成功率: {total_success/total_tests*100:.1f}%")
        
        print(f"\n各模式统计:")
        for mode_name, stats in mode_stats.items():
            success_rate = stats['success'] / stats['total'] * 100
            print(f"{mode_name}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        
        print(f"\n需要修复的问题:")
        for mode_name, stats in mode_stats.items():
            if stats['failures']:
                print(f"\n{mode_name}:")
                # 统计失败原因
                reason_counts = {}
                for failure in stats['failures']:
                    reason = failure['reason']
                    if reason not in reason_counts:
                        reason_counts[reason] = []
                    reason_counts[reason].append(failure['example'])
                
                for reason, examples in reason_counts.items():
                    print(f"  - {reason} ({len(examples)} 个示例)")
                    for ex in examples[:3]:  # 只显示前3个示例
                        print(f"    * {ex}")
                    if len(examples) > 3:
                        print(f"    * ... 还有 {len(examples)-3} 个")

def main():
    checker = ConfigChecker()
    checker.run_check()

if __name__ == "__main__":
    main()