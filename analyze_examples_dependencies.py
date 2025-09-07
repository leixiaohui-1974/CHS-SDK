#!/usr/bin/env python3
"""
分析examples目录的依赖关系，用于项目分解。
"""
import os
import re
import ast
from collections import defaultdict, Counter
from pathlib import Path

def extract_imports_from_file(file_path):
    """从Python文件中提取import语句"""
    imports = {
        'standard_lib': [],
        'third_party': [],
        'core_lib': [],
        'local': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用AST解析
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    if module_name.startswith('core_lib'):
                        imports['core_lib'].append(module_name)
                    elif module_name in ['sys', 'os', 'json', 'csv', 'time', 'random', 'abc', 'math', 'collections']:
                        imports['standard_lib'].append(module_name)
                    else:
                        imports['third_party'].append(module_name)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if node.module.startswith('core_lib'):
                        imports['core_lib'].append(node.module)
                    elif node.module in ['sys', 'os', 'json', 'csv', 'time', 'random', 'abc', 'math', 'collections']:
                        imports['standard_lib'].append(node.module)
                    else:
                        imports['third_party'].append(node.module)
                else:
                    # 相对导入
                    imports['local'].append('relative_import')
    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return imports

def analyze_examples_dependencies():
    """分析examples目录的依赖关系"""
    examples_dir = Path("examples")
    
    all_imports = {
        'standard_lib': Counter(),
        'third_party': Counter(),
        'core_lib': Counter(),
        'local': Counter()
    }
    
    file_count = 0
    core_lib_modules = set()
    
    # 遍历所有Python文件
    for py_file in examples_dir.rglob("*.py"):
        if py_file.is_file():
            file_count += 1
            imports = extract_imports_from_file(py_file)
            
            for category, modules in imports.items():
                for module in modules:
                    all_imports[category][module] += 1
                    if category == 'core_lib':
                        core_lib_modules.add(module)
    
    return all_imports, core_lib_modules, file_count

def categorize_core_lib_modules(core_lib_modules):
    """将core_lib模块分类"""
    categories = {
        'physical_objects': [],
        'local_agents': [],
        'central_coordination': [],
        'core_engine': [],
        'core_interfaces': [],
        'io': [],
        'config': [],
        'disturbances': [],
        'other': []
    }
    
    for module in core_lib_modules:
        if 'physical_objects' in module:
            categories['physical_objects'].append(module)
        elif 'local_agents' in module:
            categories['local_agents'].append(module)
        elif 'central_coordination' in module:
            categories['central_coordination'].append(module)
        elif 'core_engine' in module:
            categories['core_engine'].append(module)
        elif 'core.interfaces' in module:
            categories['core_interfaces'].append(module)
        elif 'io' in module:
            categories['io'].append(module)
        elif 'config' in module:
            categories['config'].append(module)
        elif 'disturbances' in module:
            categories['disturbances'].append(module)
        else:
            categories['other'].append(module)
    
    return categories

def main():
    """主函数"""
    print("=== Examples依赖关系分析 ===\n")
    
    all_imports, core_lib_modules, file_count = analyze_examples_dependencies()
    
    print(f"分析的文件数量: {file_count}")
    print(f"core_lib模块数量: {len(core_lib_modules)}\n")
    
    # 1. 标准库依赖
    print("=== 标准库依赖 ===")
    for module, count in all_imports['standard_lib'].most_common(10):
        print(f"  {module}: {count} 次")
    
    # 2. 第三方库依赖
    print("\n=== 第三方库依赖 ===")
    for module, count in all_imports['third_party'].most_common(10):
        print(f"  {module}: {count} 次")
    
    # 3. core_lib模块分类
    print("\n=== core_lib模块分类 ===")
    categories = categorize_core_lib_modules(core_lib_modules)
    
    for category, modules in categories.items():
        if modules:
            print(f"\n{category}:")
            for module in sorted(modules):
                count = all_imports['core_lib'][module]
                print(f"  {module}: {count} 次")
    
    # 4. 最常用的core_lib模块
    print("\n=== 最常用的core_lib模块 (Top 15) ===")
    for module, count in all_imports['core_lib'].most_common(15):
        print(f"  {module}: {count} 次")
    
    # 5. 项目分解建议
    print("\n=== 项目分解建议 ===")
    print("基于依赖分析，建议将项目分解为以下模块：")
    print("\n1. 核心模块 (core_lib):")
    print("   - physical_objects: 物理对象（水库、闸门、管道等）")
    print("   - local_agents: 本地智能体（控制、感知等）")
    print("   - central_coordination: 中央协调（消息总线等）")
    print("   - core_engine: 核心引擎（仿真框架等）")
    print("   - core.interfaces: 核心接口")
    
    print("\n2. 配置和IO模块:")
    print("   - io: 输入输出处理")
    print("   - config: 配置管理")
    
    print("\n3. 扩展模块:")
    print("   - disturbances: 扰动处理")
    
    print("\n4. 外部依赖:")
    print("   - 标准库: sys, os, json, csv, time, random, abc, math, collections")
    print("   - 第三方库: yaml, matplotlib, numpy, pandas, scipy")
    
    print("\n5. Examples模块:")
    print("   - examples: 示例代码和测试用例")
    print("   - 可以独立打包，依赖core_lib")

if __name__ == "__main__":
    main()
