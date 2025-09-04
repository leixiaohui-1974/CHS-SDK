#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置文件到自然语言转换功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.nlp.config_to_language_converter import ConfigToLanguageConverter

def test_config_to_language():
    """测试配置文件到自然语言转换"""
    print("测试配置文件到自然语言转换...")
    
    converter = ConfigToLanguageConverter()
    
    # 测试我们刚生成的配置文件
    config_file = "test_output/unified_config/unified_config.yml"
    
    if os.path.exists(config_file):
        try:
            print(f"处理配置文件: {config_file}")
            result = converter.convert_config_to_language(config_file)
            
            print("✓ 转换成功！")
            print(f"配置类型: {result.technical_details.get('config_type', '未知')}")
            print(f"组件数量: {result.technical_details.get('components_count', '未知')}")
            print(f"仿真时长: {result.technical_details.get('simulation_duration', '未知')}")
            print(f"时间步长: {result.technical_details.get('time_step', '未知')}")
            print(f"\n建模描述 (前200字符):")
            print(result.modeling_description[:200] + "...")
            print(f"\n情景描述 (前200字符):")
            print(result.scenario_description[:200] + "...")
            print(f"\n总结:")
            print(result.summary)
            
            # 保存完整的自然语言描述
            output_file = "test_output/config_to_language_result.md"
            converter.save_description_to_file(result, output_file)
            print(f"\n完整描述已保存到: {output_file}")
            
            return True
            
        except Exception as e:
            print(f"✗ 转换失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print(f"配置文件不存在: {config_file}")
        return False

if __name__ == '__main__':
    success = test_config_to_language()
    print(f"\n测试结果: {'通过' if success else '失败'}")
    sys.exit(0 if success else 1)