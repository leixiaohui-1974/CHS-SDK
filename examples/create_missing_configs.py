#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import yaml
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ConfigGenerator:
    def __init__(self):
        self.examples_dir = Path(__file__).parent
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
    
    def create_unified_config(self, example):
        """为示例创建unified_config.yml"""
        config_yml = example['full_path'] / "config.yml"
        components_yml = example['full_path'] / "components.yml"
        unified_config_yml = example['full_path'] / "unified_config.yml"
        
        if unified_config_yml.exists():
            print(f"  unified_config.yml 已存在，跳过")
            return
        
        unified_config = {
            'metadata': {
                'name': f"{example['name']} - 统一配置",
                'description': f"统一配置文件，用于 {example['path']} 示例",
                'version': '1.0',
                'category': example['category']
            }
        }
        
        # 读取config.yml
        if config_yml.exists():
            try:
                with open(config_yml, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                if config_data:
                    unified_config.update(config_data)
            except Exception as e:
                print(f"    警告：读取config.yml失败: {e}")
        
        # 如果config.yml中没有components，尝试从components.yml读取
        if 'components' not in unified_config and components_yml.exists():
            try:
                with open(components_yml, 'r', encoding='utf-8') as f:
                    components_data = yaml.safe_load(f)
                if components_data and 'components' in components_data:
                    unified_config['components'] = components_data['components']
                if components_data and 'controllers' in components_data:
                    unified_config['controllers'] = components_data['controllers']
                if components_data and 'connections' in components_data:
                    unified_config['connections'] = components_data['connections']
                if components_data and 'control' in components_data:
                    unified_config['control'] = components_data['control']
            except Exception as e:
                print(f"    警告：读取components.yml失败: {e}")
        
        # 写入unified_config.yml
        try:
            with open(unified_config_yml, 'w', encoding='utf-8') as f:
                yaml.dump(unified_config, f, default_flow_style=False, allow_unicode=True, indent=2)
            print(f"  创建 unified_config.yml 成功")
        except Exception as e:
            print(f"  创建 unified_config.yml 失败: {e}")
    
    def create_universal_config(self, example):
        """为示例创建universal_config.yml"""
        config_yml = example['full_path'] / "config.yml"
        components_yml = example['full_path'] / "components.yml"
        universal_config_yml = example['full_path'] / "universal_config.yml"
        
        if universal_config_yml.exists():
            print(f"  universal_config.yml 已存在，跳过")
            return
        
        universal_config = {
            'project': {
                'name': f"{example['name']}",
                'description': f"通用配置文件，用于 {example['path']} 示例",
                'version': '1.0',
                'category': example['category']
            },
            'runtime': {
                'mode': 'simulation',
                'logging_level': 'INFO'
            }
        }
        
        # 读取config.yml
        if config_yml.exists():
            try:
                with open(config_yml, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                if config_data:
                    # 将simulation配置映射到runtime
                    if 'simulation' in config_data:
                        universal_config['simulation'] = config_data['simulation']
                    
                    # 保留其他配置
                    for key, value in config_data.items():
                        if key not in ['simulation']:
                            universal_config[key] = value
            except Exception as e:
                print(f"    警告：读取config.yml失败: {e}")
        
        # 如果config.yml中没有components，尝试从components.yml读取
        if 'components' not in universal_config and components_yml.exists():
            try:
                with open(components_yml, 'r', encoding='utf-8') as f:
                    components_data = yaml.safe_load(f)
                if components_data:
                    universal_config.update(components_data)
            except Exception as e:
                print(f"    警告：读取components.yml失败: {e}")
        
        # 写入universal_config.yml
        try:
            with open(universal_config_yml, 'w', encoding='utf-8') as f:
                yaml.dump(universal_config, f, default_flow_style=False, allow_unicode=True, indent=2)
            print(f"  创建 universal_config.yml 成功")
        except Exception as e:
            print(f"  创建 universal_config.yml 失败: {e}")
    
    def generate_all_configs(self):
        """为所有示例生成缺失的配置文件"""
        print("开始为所有示例生成缺失的配置文件...")
        print("="*60)
        
        for example in self.all_examples:
            print(f"\n处理示例: {example['path']}")
            
            # 创建unified_config.yml
            self.create_unified_config(example)
            
            # 创建universal_config.yml
            self.create_universal_config(example)
        
        print(f"\n配置文件生成完成！")
        print(f"处理了 {len(self.all_examples)} 个示例")

def main():
    generator = ConfigGenerator()
    generator.generate_all_configs()

if __name__ == "__main__":
    main()