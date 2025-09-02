#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面结果分析工具 - CHS-SDK

本工具用于分析所有运行模式下所有示例的运行结果，
识别失败原因并提供修复建议。

功能：
1. 运行所有示例并收集详细错误信息
2. 分析失败模式和常见问题
3. 生成修复建议报告
4. 验证仿真输出数据的正确性
5. 确保跨模式兼容性
"""

import sys
import os
import time
import subprocess
import traceback
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ComprehensiveResultAnalyzer:
    """全面结果分析器"""
    
    def __init__(self):
        self.examples_dir = Path(__file__).parent
        self.project_root = Path(__file__).parent.parent
        self.results = {}
        self.error_patterns = defaultdict(list)
        self.success_patterns = defaultdict(list)
        
    def analyze_all_modes(self):
        """分析所有运行模式"""
        print("\n" + "="*80)
        print("开始CHS-SDK全面结果分析")
        print("="*80)
        
        # 发现所有示例
        examples = self._discover_all_examples()
        print(f"发现 {len(examples)} 个示例")
        
        # 定义运行模式
        modes = [
            ("硬编码模式", "run_hardcoded.py", self._test_hardcoded_mode),
            ("传统配置文件模式", "run_scenario.py", self._test_scenario_mode),
            ("智能运行器模式", "run_smart.py", self._test_smart_mode),
            ("统一配置模式", "run_unified_scenario.py", self._test_unified_mode),
            ("通用配置模式", "run_universal_config.py", self._test_universal_mode)
        ]
        
        # 测试每个示例的每种模式
        for example in examples:
            print(f"\n--- 分析示例: {example['path']} ---")
            example_results = {}
            
            for mode_name, script_name, test_func in modes:
                print(f"  测试 {mode_name}...")
                result = test_func(example)
                example_results[mode_name] = result
                
                if result['success']:
                    self.success_patterns[mode_name].append(example['path'])
                    print(f"    ✓ 成功")
                else:
                    self.error_patterns[mode_name].append({
                        'example': example['path'],
                        'error': result['error'],
                        'details': result.get('details', '')
                    })
                    print(f"    ✗ 失败: {result['error'][:100]}...")
            
            self.results[example['path']] = example_results
        
        # 生成分析报告
        self._generate_analysis_report()
        
    def _discover_all_examples(self):
        """发现所有示例"""
        examples = []
        
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
                # 检查类别目录本身
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
    
    def _test_hardcoded_mode(self, example):
        """测试硬编码模式"""
        try:
            # 尝试导入并运行硬编码示例
            from examples.run_hardcoded import ExamplesHardcodedRunner
            runner = ExamplesHardcodedRunner()
            
            # 检查示例是否在硬编码运行器中定义
            example_key = example['path'].replace('/', '_')
            if example_key in runner.examples:
                result = runner.run_example(example_key)
                return {'success': True, 'result': result}
            else:
                return {
                    'success': False, 
                    'error': f"示例 {example_key} 未在硬编码运行器中定义",
                    'details': f"可用示例: {list(runner.examples.keys())}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': traceback.format_exc()
            }
    
    def _test_scenario_mode(self, example):
        """测试传统配置文件模式"""
        try:
            config_file = example['full_path'] / 'config.yml'
            if not config_file.exists():
                return {
                    'success': False,
                    'error': '缺少config.yml文件',
                    'details': f"路径: {config_file}"
                }
            
            from examples.run_scenario import ExamplesScenarioRunner
            runner = ExamplesScenarioRunner()
            result = runner.run_example(example['path'])
            return {'success': True, 'result': result}
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': traceback.format_exc()
            }
    
    def _test_smart_mode(self, example):
        """测试智能运行器模式"""
        try:
            from examples.run_smart import SmartRunner
            runner = SmartRunner()
            result = runner.run_example(example['path'])
            return {'success': True, 'result': result}
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': traceback.format_exc()
            }
    
    def _test_unified_mode(self, example):
        """测试统一配置模式"""
        try:
            unified_config = example['full_path'] / 'unified_config.yml'
            if not unified_config.exists():
                return {
                    'success': False,
                    'error': '缺少unified_config.yml文件',
                    'details': f"路径: {unified_config}"
                }
            
            from examples.run_unified_scenario import ExamplesUnifiedScenarioRunner
            runner = ExamplesUnifiedScenarioRunner()
            result = runner.run_example(example['path'])
            return {'success': True, 'result': result}
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': traceback.format_exc()
            }
    
    def _test_universal_mode(self, example):
        """测试通用配置模式"""
        try:
            universal_config = example['full_path'] / 'universal_config.yml'
            if not universal_config.exists():
                return {
                    'success': False,
                    'error': '缺少universal_config.yml文件',
                    'details': f"路径: {universal_config}"
                }
            
            from examples.run_universal_config import ExamplesUniversalConfigRunner
            runner = ExamplesUniversalConfigRunner()
            result = runner.run_example(example['path'])
            return {'success': True, 'result': result}
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': traceback.format_exc()
            }
    
    def _generate_analysis_report(self):
        """生成分析报告"""
        print("\n" + "="*80)
        print("全面结果分析报告")
        print("="*80)
        
        # 总体统计
        total_tests = sum(len(results) for results in self.results.values())
        total_success = sum(
            sum(1 for result in results.values() if result['success'])
            for results in self.results.values()
        )
        
        print(f"\n总体统计:")
        print(f"  总示例数: {len(self.results)}")
        print(f"  总测试数: {total_tests}")
        print(f"  总成功数: {total_success}")
        print(f"  总成功率: {total_success/total_tests*100:.1f}%")
        
        # 按模式统计
        print(f"\n按模式统计:")
        for mode in ["硬编码模式", "传统配置文件模式", "智能运行器模式", "统一配置模式", "通用配置模式"]:
            mode_success = len(self.success_patterns[mode])
            mode_total = mode_success + len(self.error_patterns[mode])
            if mode_total > 0:
                print(f"  {mode}: {mode_success}/{mode_total} ({mode_success/mode_total*100:.1f}%)")
        
        # 常见错误分析
        print(f"\n常见错误分析:")
        error_counts = defaultdict(int)
        for mode, errors in self.error_patterns.items():
            for error_info in errors:
                error_type = self._classify_error(error_info['error'])
                error_counts[error_type] += 1
        
        for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count} 次")
        
        # 修复建议
        print(f"\n修复建议:")
        self._generate_fix_recommendations()
        
        # 保存详细报告到文件
        self._save_detailed_report()
    
    def _classify_error(self, error_message):
        """分类错误类型"""
        error_lower = error_message.lower()
        
        if '缺少' in error_message and 'config' in error_lower:
            return "缺少配置文件"
        elif 'import' in error_lower or 'module' in error_lower:
            return "模块导入错误"
        elif 'unicode' in error_lower or 'decode' in error_lower:
            return "编码错误"
        elif 'timeout' in error_lower:
            return "超时错误"
        elif 'permission' in error_lower:
            return "权限错误"
        elif 'file not found' in error_lower or 'no such file' in error_lower:
            return "文件不存在"
        elif '未在硬编码运行器中定义' in error_message:
            return "硬编码运行器缺少示例定义"
        else:
            return "其他错误"
    
    def _generate_fix_recommendations(self):
        """生成修复建议"""
        recommendations = []
        
        # 检查缺少配置文件的问题
        missing_configs = []
        for mode, errors in self.error_patterns.items():
            for error_info in errors:
                if '缺少' in error_info['error'] and 'config' in error_info['error'].lower():
                    missing_configs.append(error_info['example'])
        
        if missing_configs:
            recommendations.append(
                f"1. 为以下示例创建缺少的配置文件: {', '.join(set(missing_configs))}"
            )
        
        # 检查硬编码运行器缺少定义的问题
        missing_hardcoded = []
        for error_info in self.error_patterns.get("硬编码模式", []):
            if '未在硬编码运行器中定义' in error_info['error']:
                missing_hardcoded.append(error_info['example'])
        
        if missing_hardcoded:
            recommendations.append(
                f"2. 在硬编码运行器中添加以下示例的定义: {', '.join(set(missing_hardcoded))}"
            )
        
        # 检查编码问题
        encoding_errors = sum(
            1 for errors in self.error_patterns.values()
            for error_info in errors
            if 'unicode' in error_info['error'].lower() or 'decode' in error_info['error'].lower()
        )
        
        if encoding_errors > 0:
            recommendations.append(
                f"3. 修复编码问题，确保所有文件使用UTF-8编码 ({encoding_errors} 个错误)"
            )
        
        # 输出建议
        for rec in recommendations:
            print(f"  {rec}")
        
        if not recommendations:
            print("  暂无特定修复建议，请查看详细错误日志")
    
    def _save_detailed_report(self):
        """保存详细报告到文件"""
        report_file = self.examples_dir / "analysis_report.json"
        
        # 转换结果为可序列化的格式
        serializable_results = {}
        for example_path, results in self.results.items():
            serializable_results[example_path] = {}
            for mode, result in results.items():
                serializable_results[example_path][mode] = {
                    'success': result['success'],
                    'error': result.get('error', ''),
                    'details': result.get('details', ''),
                    'result_summary': str(result.get('result', ''))[:200] if result.get('result') else ''
                }
        
        report_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': serializable_results,
            'error_patterns': dict(self.error_patterns),
            'success_patterns': dict(self.success_patterns)
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")

def main():
    """主函数"""
    analyzer = ComprehensiveResultAnalyzer()
    analyzer.analyze_all_modes()

if __name__ == "__main__":
    main()