#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试示例列表发现的脚本
"""

import sys
from pathlib import Path

def test_examples_discovery():
    """测试示例发现功能"""
    examples_dir = Path(__file__).parent
    
    print("=== 调试示例发现功能 ===")
    print(f"工作目录: {examples_dir}")
    
    # 导入 ExamplesScenarioRunner
    sys.path.insert(0, str(examples_dir))
    from run_scenario import ExamplesScenarioRunner
    
    runner = ExamplesScenarioRunner()
    examples = runner.list_examples()
    
    print(f"\n总共发现 {len(examples)} 个示例")
    
    # 检查 agent_based_06_centralized_emergency_override 是否在列表中
    target_example = "agent_based_06_centralized_emergency_override"
    
    if target_example in examples:
        print(f"\n✅ 找到目标示例: {target_example}")
        example_info = examples[target_example]
        print(f"  名称: {example_info['name']}")
        print(f"  描述: {example_info['description']}")
        print(f"  类别: {example_info['category']}")
        print(f"  路径: {example_info['path']}")
        print(f"  配置文件: {example_info['config_path']}")
        
        # 检查配置文件是否存在
        config_path = Path(example_info['config_path'])
        if config_path.exists():
            print(f"  配置文件存在: ✅")
        else:
            print(f"  配置文件不存在: ❌")
            
        # 检查其他必需文件
        example_dir = examples_dir / example_info['path']
        required_files = ['config.yml', 'components.yml', 'topology.yml', 'agents.yml']
        
        print(f"\n  检查必需文件:")
        for file_name in required_files:
            file_path = example_dir / file_name
            exists = file_path.exists()
            print(f"    {file_name}: {'✅' if exists else '❌'}")
            
    else:
        print(f"\n❌ 未找到目标示例: {target_example}")
        print("\n所有可用示例:")
        for key in sorted(examples.keys()):
            if "agent_based" in key:
                print(f"  {key}")
    
    return target_example in examples

if __name__ == "__main__":
    success = test_examples_discovery()
    sys.exit(0 if success else 1)