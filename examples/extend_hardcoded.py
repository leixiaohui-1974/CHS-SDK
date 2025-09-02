#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class HardcodedExtender:
    def __init__(self):
        self.examples_dir = Path(__file__).parent
        self.all_examples = self._discover_all_examples()
        self.hardcoded_file = self.examples_dir / "run_hardcoded.py"
    
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
    
    def get_current_hardcoded_examples(self):
        """获取当前硬编码运行器中的示例"""
        try:
            from examples.run_hardcoded import ExamplesHardcodedRunner
            runner = ExamplesHardcodedRunner()
            return set(info['path'] for info in runner.examples.values())
        except Exception as e:
            print(f"获取当前硬编码示例失败: {e}")
            return set()
    
    def generate_missing_examples_dict(self):
        """生成缺失示例的字典定义"""
        current_paths = self.get_current_hardcoded_examples()
        missing_examples = []
        
        for example in self.all_examples:
            if example['path'] not in current_paths:
                missing_examples.append(example)
        
        if not missing_examples:
            print("所有示例都已在硬编码运行器中！")
            return
        
        print(f"发现 {len(missing_examples)} 个缺失的示例：")
        
        # 生成字典条目
        dict_entries = []
        for example in missing_examples:
            # 生成键名（使用路径的最后部分，去掉数字前缀）
            key_name = example['name']
            if key_name.startswith(('01_', '02_', '03_', '04_', '05_', '06_', '07_', '08_', '09_')):
                key_name = key_name[3:]  # 去掉数字前缀
            key_name = key_name.replace('-', '_').replace(' ', '_').lower()
            
            # 生成显示名称
            display_name = example['name'].replace('_', ' ').title()
            if display_name.startswith(('01 ', '02 ', '03 ', '04 ', '05 ', '06 ', '07 ', '08 ', '09 ')):
                display_name = display_name[3:]  # 去掉数字前缀
            
            dict_entry = f'''            "{key_name}": {{
                "name": "{display_name}",
                "description": "{display_name}示例",
                "category": "{example['category']}",
                "path": "{example['path']}"
            }},'''
            
            dict_entries.append(dict_entry)
            print(f"  - {example['path']} -> {key_name}")
        
        print("\n生成的字典条目：")
        print("="*60)
        for entry in dict_entries:
            print(entry)
        
        print("\n请将这些条目添加到 run_hardcoded.py 中的 self.examples 字典中")
        
        # 生成对应的方法存根
        print("\n需要添加的方法存根：")
        print("="*60)
        for example in missing_examples:
            key_name = example['name']
            if key_name.startswith(('01_', '02_', '03_', '04_', '05_', '06_', '07_', '08_', '09_')):
                key_name = key_name[3:]  # 去掉数字前缀
            key_name = key_name.replace('-', '_').replace(' ', '_').lower()
            
            method_name = f"create_{key_name}_simulation"
            method_stub = f'''    def {method_name}(self):
        """创建{example['name']}仿真"""
        print("构建{example['name']}示例...")
        
        # TODO: 实现具体的仿真构建逻辑
        # 可以参考配置文件: {example['path']}/config.yml
        
        # 创建核心组件
        message_bus = MessageBus()
        builder = SimulationBuilder()
        
        # 创建仿真环境
        sim_config = {{
            'start_time': 0,
            'end_time': 300.0,
            'dt': 1.0
        }}
        harness = SimulationHarness(config=sim_config)
        
        print("注意：此示例的硬编码实现尚未完成")
        print("建议使用智能运行器模式运行此示例")
        
        return harness
'''
            print(method_stub)

def main():
    extender = HardcodedExtender()
    extender.generate_missing_examples_dict()

if __name__ == "__main__":
    main()