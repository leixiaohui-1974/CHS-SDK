#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自然语言处理功能测试脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.nlp.config_to_language_converter import ConfigToLanguageConverter
from core_lib.nlp.language_to_config_converter import LanguageToConfigConverter
from core_lib.config.unified_config_manager import ConfigType

def test_language_to_config():
    """测试自然语言到配置文件转换"""
    print("测试自然语言到配置文件转换...")
    
    converter = LanguageToConfigConverter()
    
    # 测试描述
    description = """
仿真名称：简单水库系统
仿真时长：3600秒
时间步长：1.0秒

系统组件：
- 水库1：水库，容量1000立方米，初始水位5米
- 闸门1：闸门，最大流量50立方米每秒
- 传感器1：传感器，监测水位

系统连接：
- 水库1连接闸门1

控制策略：
- 采用PID控制策略
    """
    
    try:
        # 转换为统一配置文件
        result = converter.convert_language_to_config(
            description, 
            ConfigType.UNIFIED_SINGLE,
            "test_output/unified_config"
        )
        
        print("✓ 统一配置文件转换成功")
        print(f"  生成的配置包含: {list(result.keys())}")
        
        # 转换为通用配置文件
        result2 = converter.convert_language_to_config(
            description, 
            ConfigType.UNIVERSAL_CONFIG,
            "test_output/universal_config"
        )
        
        print("✓ 通用配置文件转换成功")
        print(f"  生成的配置包含: {list(result2.keys())}")
        
        return True
        
    except Exception as e:
        print(f"✗ 转换失败: {e}")
        return False

def test_config_to_language():
    """测试配置文件到自然语言转换"""
    print("\n测试配置文件到自然语言转换...")
    
    # 查找可用的配置文件
    config_files = [
        "examples/watertank/base/config.yml",
        "examples/demo/unified_config.yml",
        "config/universal_config.yml"
    ]
    
    converter = ConfigToLanguageConverter()
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                print(f"  处理配置文件: {config_file}")
                description = converter.convert_config_to_language(config_file)
                
                print(f"    ✓ 转换成功")
                print(f"    配置类型: {description.config_type}")
                print(f"    仿真名称: {description.simulation_name}")
                print(f"    建模描述长度: {len(description.modeling_description)} 字符")
                
                return True
                
            except Exception as e:
                print(f"    ✗ 转换失败: {e}")
        else:
            print(f"  配置文件不存在: {config_file}")
    
    return False

def main():
    """主测试函数"""
    print("CHS-SDK 自然语言处理功能测试")
    print("=" * 50)
    
    # 确保输出目录存在
    os.makedirs("test_output", exist_ok=True)
    
    # 测试结果
    results = []
    
    # 测试自然语言到配置文件转换
    results.append(test_language_to_config())
    
    # 测试配置文件到自然语言转换
    results.append(test_config_to_language())
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"自然语言到配置转换: {'✓ 通过' if results[0] else '✗ 失败'}")
    print(f"配置到自然语言转换: {'✓ 通过' if results[1] else '✗ 失败'}")
    
    if all(results):
        print("\n🎉 所有测试通过！自然语言处理功能正常工作。")
    else:
        print("\n⚠️  部分测试失败，请检查相关功能。")
    
    return all(results)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)