#!/usr/bin/env python3
"""
修复 core_lib 中 duration 和 end_time 混用问题的脚本
"""

import os
import re
from pathlib import Path

def fix_duration_end_time_conflict():
    """修复 duration 和 end_time 混用问题"""
    
    core_lib_dir = Path("../core_lib")
    fixes_applied = []
    
    # 1. 修复 universal_config.py
    universal_config_file = core_lib_dir / "models" / "universal_config.py"
    if universal_config_file.exists():
        with open(universal_config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换 duration 为 end_time
        original_content = content
        content = re.sub(r"'duration'", "'end_time'", content)
        content = re.sub(r'"duration"', '"end_time"', content)
        content = re.sub(r"duration字段", "end_time字段", content)
        content = re.sub(r"duration必须大于0", "end_time必须大于0", content)
        
        if content != original_content:
            with open(universal_config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_applied.append(f"修复 {universal_config_file}")
    
    # 2. 修复 simulation_harness.py 以支持 duration 作为备选
    harness_file = core_lib_dir / "core_engine" / "testing" / "simulation_harness.py"
    if harness_file.exists():
        with open(harness_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 在 end_time 检查后添加 duration 支持
        old_check = """        # end_time is required - no default value
        if 'end_time' not in config:
            raise ValueError("'end_time' is required in simulation configuration")
        self.end_time = config['end_time']"""
        
        new_check = """        # end_time is required - no default value
        if 'end_time' not in config:
            if 'duration' in config:
                # 支持 duration 作为 end_time 的备选参数
                config['end_time'] = config['duration']
            else:
                raise ValueError("'end_time' is required in simulation configuration")
        self.end_time = config['end_time']"""
        
        if old_check in content:
            content = content.replace(old_check, new_check)
            with open(harness_file, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_applied.append(f"修复 {harness_file}")
    
    # 3. 修复 simulation_builder.py
    builder_file = core_lib_dir / "core_engine" / "testing" / "simulation_builder.py"
    if builder_file.exists():
        with open(builder_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 在 end_time 检查后添加 duration 支持
        old_check = """        # end_time is required - no default value
        if 'end_time' not in config:
            raise ValueError("'end_time' is required in simulation configuration")"""
        
        new_check = """        # end_time is required - no default value
        if 'end_time' not in config:
            if 'duration' in config:
                # 支持 duration 作为 end_time 的备选参数
                config['end_time'] = config['duration']
            else:
                raise ValueError("'end_time' is required in simulation configuration")"""
        
        if old_check in content:
            content = content.replace(old_check, new_check)
            with open(builder_file, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_applied.append(f"修复 {builder_file}")
    
    # 4. 修复 enhanced_simulation_harness.py
    enhanced_harness_file = core_lib_dir / "core_engine" / "testing" / "enhanced_simulation_harness.py"
    if enhanced_harness_file.exists():
        with open(enhanced_harness_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加 duration 支持
        old_line = "        self.end_time = config.get('end_time', 100)"
        new_line = "        # 支持 duration 作为 end_time 的备选参数\n        if 'end_time' not in config and 'duration' in config:\n            config['end_time'] = config['duration']\n        self.end_time = config.get('end_time', 100)"
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            with open(enhanced_harness_file, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_applied.append(f"修复 {enhanced_harness_file}")
    
    # 5. 修复 enhanced_yaml_loader.py
    yaml_loader_file = core_lib_dir / "config" / "enhanced_yaml_loader.py"
    if yaml_loader_file.exists():
        with open(yaml_loader_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加 duration 支持
        old_line = "'end_time': time_config.get('end_time', 100.0),"
        new_line = "'end_time': time_config.get('end_time', time_config.get('duration', 100.0)),"
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            with open(yaml_loader_file, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_applied.append(f"修复 {yaml_loader_file}")
    
    # 6. 更新配置文件模板
    config_template_file = core_lib_dir / "config" / "universal_config_template.yml"
    if config_template_file.exists():
        with open(config_template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 确保使用 end_time
        if 'duration:' in content and 'end_time:' not in content:
            content = re.sub(r'duration:\s*\d+\.?\d*', 'end_time: 100.0', content)
            with open(config_template_file, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_applied.append(f"更新 {config_template_file}")
    
    # 7. 更新示例配置文件
    example_config_file = core_lib_dir / "config" / "example_universal_config.yml"
    if example_config_file.exists():
        with open(example_config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 确保使用 end_time
        if 'duration:' in content and 'end_time:' not in content:
            content = re.sub(r'duration:\s*\d+\.?\d*', 'end_time: 100.0', content)
            with open(example_config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_applied.append(f"更新 {example_config_file}")
    
    # 输出修复结果
    print("=== Duration 和 End_time 混用问题修复报告 ===")
    print(f"总共修复了 {len(fixes_applied)} 个文件：")
    for fix in fixes_applied:
        print(f"  ✓ {fix}")
    
    if not fixes_applied:
        print("  没有发现需要修复的文件")
    
    print("\n修复完成！现在 core_lib 支持：")
    print("1. 优先使用 end_time 参数")
    print("2. 向后兼容 duration 参数（自动转换为 end_time）")
    print("3. 统一的参数验证和错误处理")
    
    return fixes_applied

if __name__ == "__main__":
    fixes = fix_duration_end_time_conflict()
