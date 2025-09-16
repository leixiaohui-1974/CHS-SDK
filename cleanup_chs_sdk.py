#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 精简脚本

删除与 core_lib 无关的 Python 脚本，只保留基于 core_lib 的模块和案例。

核心保留内容：
1. core_lib/ - 核心库模块
2. api/ - API 服务（依赖 core_lib）
3. examples/ - 示例案例（基于 core_lib）
4. run_scenario.py - 主要运行脚本
5. run_unified_scenario.py - 统一运行脚本
6. 必要的配置和数据文件

删除内容：
1. 独立的分析脚本
2. 测试脚本（非核心功能）
3. 演示脚本（非核心功能）
4. 临时文件
5. 重复的配置文件
"""

import os
import shutil
from pathlib import Path
import re

def has_core_lib_dependency(file_path):
    """检查文件是否依赖 core_lib"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否导入 core_lib
        if re.search(r'^from core_lib|^import core_lib', content, re.MULTILINE):
            return True
        
        # 检查是否在 examples 目录中（通常基于 core_lib）
        if 'examples' in str(file_path):
            return True
            
        return False
    except Exception:
        return False

def should_keep_file(file_path):
    """判断文件是否应该保留"""
    file_path = Path(file_path)
    
    # 保留核心目录
    if file_path.parts[0] in ['core_lib', 'api', 'examples', 'docs']:
        return True
    
    # 保留核心运行脚本
    if file_path.name in ['run_scenario.py', 'run_unified_scenario.py']:
        return True
    
    # 保留配置文件和数据文件
    if file_path.suffix in ['.yml', '.yaml', '.json', '.csv', '.md', '.txt', '.conf', '.html']:
        return True
    
    # 保留 Docker 和部署文件
    if file_path.name in ['Dockerfile', 'docker-compose.yml', 'requirements.txt']:
        return True
    
    # 保留图片文件
    if file_path.suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
        return True
    
    # 对于 Python 文件，检查是否依赖 core_lib
    if file_path.suffix == '.py':
        return has_core_lib_dependency(file_path)
    
    return False

def get_files_to_delete():
    """获取需要删除的文件列表"""
    files_to_delete = []
    directories_to_delete = []
    
    # 根目录下的文件
    for item in Path('.').iterdir():
        if item.is_file():
            if not should_keep_file(item):
                files_to_delete.append(item)
        elif item.is_dir() and item.name not in ['core_lib', 'api', 'examples', 'docs', '__pycache__', '.git']:
            # 检查目录是否包含需要保留的文件
            has_keepable_files = False
            for subitem in item.rglob('*'):
                if subitem.is_file() and should_keep_file(subitem):
                    has_keepable_files = True
                    break
            
            if not has_keepable_files:
                directories_to_delete.append(item)
    
    return files_to_delete, directories_to_delete

def main():
    """主函数"""
    print("🔍 CHS-SDK 精简分析")
    print("=" * 50)
    
    # 获取要删除的文件
    files_to_delete, directories_to_delete = get_files_to_delete()
    
    print(f"📁 发现 {len(files_to_delete)} 个文件需要删除")
    print(f"📁 发现 {len(directories_to_delete)} 个目录需要删除")
    
    if not files_to_delete and not directories_to_delete:
        print("✅ 没有需要删除的文件，项目已经精简")
        return
    
    print("\n🗑️  将要删除的文件:")
    for file_path in files_to_delete[:20]:  # 只显示前20个
        print(f"  - {file_path}")
    if len(files_to_delete) > 20:
        print(f"  ... 还有 {len(files_to_delete) - 20} 个文件")
    
    print("\n🗑️  将要删除的目录:")
    for dir_path in directories_to_delete:
        print(f"  - {dir_path}/")
    
    # 确认删除
    response = input("\n❓ 确认删除这些文件吗？(y/N): ").strip().lower()
    if response != 'y':
        print("❌ 取消删除操作")
        return
    
    # 执行删除
    deleted_files = 0
    deleted_dirs = 0
    
    print("\n🗑️  开始删除文件...")
    
    # 删除文件
    for file_path in files_to_delete:
        try:
            file_path.unlink()
            deleted_files += 1
            print(f"  ✅ 删除文件: {file_path}")
        except Exception as e:
            print(f"  ❌ 删除失败: {file_path} - {e}")
    
    # 删除目录
    for dir_path in directories_to_delete:
        try:
            shutil.rmtree(dir_path)
            deleted_dirs += 1
            print(f"  ✅ 删除目录: {dir_path}/")
        except Exception as e:
            print(f"  ❌ 删除失败: {dir_path}/ - {e}")
    
    print(f"\n📊 删除完成:")
    print(f"  - 删除文件: {deleted_files} 个")
    print(f"  - 删除目录: {deleted_dirs} 个")
    
    # 验证核心功能
    print("\n🔍 验证核心功能...")
    core_files = [
        'core_lib',
        'api',
        'examples',
        'run_scenario.py',
        'run_unified_scenario.py'
    ]
    
    for core_file in core_files:
        if Path(core_file).exists():
            print(f"  ✅ {core_file} 存在")
        else:
            print(f"  ❌ {core_file} 缺失")
    
    print("\n✅ CHS-SDK 精简完成！")

if __name__ == "__main__":
    main()
