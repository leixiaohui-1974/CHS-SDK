#!/usr/bin/env python3
"""
批量替换 core_lib 中的 dt 参数为 time_step
"""
import os
import re
from pathlib import Path

def replace_dt_in_file(file_path):
    """在单个文件中替换 dt 参数"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 替换函数定义中的 dt: float 参数
        content = re.sub(r'\bdt:\s*float\b', 'time_step: float', content)
        
        # 替换函数调用中的 dt= 参数
        content = re.sub(r'\bdt\s*=', 'time_step=', content)
        
        # 替换函数参数中的单独 dt
        content = re.sub(r'def\s+[^(]+\([^)]*\bdt\b(?!\w)', 
                        lambda m: m.group(0).replace('dt', 'time_step'), content)
        
        # 替换 step(action, dt) 调用
        content = re.sub(r'\.step\s*\(\s*([^,]+),\s*dt\s*\)', r'.step(\1, time_step)', content)
        
        # 替换 compute_control_action(..., dt) 调用  
        content = re.sub(r'compute_control_action\s*\(\s*([^,]+),\s*dt\s*\)', 
                        r'compute_control_action(\1, time_step)', content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {file_path}")
            return True
        return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """主函数"""
    core_lib_path = Path("core_lib")
    
    if not core_lib_path.exists():
        print("core_lib directory not found!")
        return
    
    updated_files = 0
    total_files = 0
    
    # 遍历所有 Python 文件
    for py_file in core_lib_path.rglob("*.py"):
        total_files += 1
        if replace_dt_in_file(py_file):
            updated_files += 1
    
    print(f"\nProcessed {total_files} files, updated {updated_files} files")

if __name__ == "__main__":
    main()
