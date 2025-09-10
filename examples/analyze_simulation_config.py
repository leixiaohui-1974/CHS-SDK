#!/usr/bin/env python3
"""
分析 examples 目录中 duration 和 end_time 参数的使用情况
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def analyze_simulation_config():
    """分析仿真配置参数使用情况"""
    
    examples_dir = Path(".")
    results = {
        'duration_files': defaultdict(list),
        'end_time_files': defaultdict(list),
        'mixed_files': defaultdict(list),
        'config_files': defaultdict(list),
        'python_files': defaultdict(list)
    }
    
    # 统计计数器
    duration_count = 0
    end_time_count = 0
    mixed_count = 0
    config_files_count = 0
    python_files_count = 0
    
    # 遍历所有文件
    for file_path in examples_dir.rglob("*"):
        if file_path.is_file():
            file_ext = file_path.suffix.lower()
            relative_path = file_path.relative_to(examples_dir)
            
            # 检查配置文件
            if file_ext in ['.yml', '.yaml', '.json']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    has_duration = 'duration' in content
                    has_end_time = 'end_time' in content
                    
                    if has_duration or has_end_time:
                        config_files_count += 1
                        results['config_files'][str(relative_path)] = {
                            'duration': has_duration,
                            'end_time': has_end_time,
                            'mixed': has_duration and has_end_time
                        }
                        
                        if has_duration and has_end_time:
                            mixed_count += 1
                            results['mixed_files'][str(relative_path)] = True
                        elif has_duration:
                            duration_count += 1
                            results['duration_files'][str(relative_path)] = True
                        elif has_end_time:
                            end_time_count += 1
                            results['end_time_files'][str(relative_path)] = True
                            
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
            
            # 检查Python文件
            elif file_ext == '.py':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    has_duration = 'duration' in content
                    has_end_time = 'end_time' in content
                    
                    if has_duration or has_end_time:
                        python_files_count += 1
                        results['python_files'][str(relative_path)] = {
                            'duration': has_duration,
                            'end_time': has_end_time,
                            'mixed': has_duration and has_end_time
                        }
                        
                        if has_duration and has_end_time:
                            mixed_count += 1
                            results['mixed_files'][str(relative_path)] = True
                        elif has_duration:
                            duration_count += 1
                            results['duration_files'][str(relative_path)] = True
                        elif has_end_time:
                            end_time_count += 1
                            results['end_time_files'][str(relative_path)] = True
                            
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    # 生成报告
    print("=== 仿真配置参数使用情况分析报告 ===\n")
    
    print(f"总文件数统计:")
    print(f"  - 配置文件 (YAML/JSON): {config_files_count}")
    print(f"  - Python文件: {python_files_count}")
    print(f"  - 总计: {config_files_count + python_files_count}\n")
    
    print(f"参数使用统计:")
    print(f"  - 仅使用 duration: {duration_count}")
    print(f"  - 仅使用 end_time: {end_time_count}")
    print(f"  - 同时使用两者: {mixed_count}\n")
    
    print("=== 仅使用 duration 的文件 ===")
    for file_path in sorted(results['duration_files'].keys()):
        print(f"  - {file_path}")
    
    print(f"\n=== 仅使用 end_time 的文件 ===")
    for file_path in sorted(results['end_time_files'].keys()):
        print(f"  - {file_path}")
    
    print(f"\n=== 同时使用 duration 和 end_time 的文件 ===")
    for file_path in sorted(results['mixed_files'].keys()):
        print(f"  - {file_path}")
    
    # 按目录分组统计
    print(f"\n=== 按目录分组统计 ===")
    dir_stats = defaultdict(lambda: {'duration': 0, 'end_time': 0, 'mixed': 0})
    
    for file_path, info in results['config_files'].items():
        dir_name = str(Path(file_path).parent)
        if info['mixed']:
            dir_stats[dir_name]['mixed'] += 1
        elif info['duration']:
            dir_stats[dir_name]['duration'] += 1
        elif info['end_time']:
            dir_stats[dir_name]['end_time'] += 1
    
    for file_path, info in results['python_files'].items():
        dir_name = str(Path(file_path).parent)
        if info['mixed']:
            dir_stats[dir_name]['mixed'] += 1
        elif info['duration']:
            dir_stats[dir_name]['duration'] += 1
        elif info['end_time']:
            dir_stats[dir_name]['end_time'] += 1
    
    for dir_name in sorted(dir_stats.keys()):
        stats = dir_stats[dir_name]
        total = stats['duration'] + stats['end_time'] + stats['mixed']
        if total > 0:
            print(f"  {dir_name}:")
            print(f"    - duration: {stats['duration']}")
            print(f"    - end_time: {stats['end_time']}")
            print(f"    - mixed: {stats['mixed']}")
            print(f"    - total: {total}")
    
    return results

if __name__ == "__main__":
    results = analyze_simulation_config()
