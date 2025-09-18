# -*- coding: utf-8 -*-

"""
CHS-SDK 标准导入工具

该模块提供了标准的Python导入机制，用于替代项目中的手动路径操作。
使用标准的包导入结构，确保代码的可移植性和维护性。

使用方法:
    from core_lib.utils.standard_imports import setup_project_imports
    setup_project_imports(__file__)
"""

import sys
import os
from pathlib import Path
from typing import Optional


def setup_project_imports(file_path: str, 
                         project_name: str = "CHS-SDK",
                         core_lib_name: str = "core_lib") -> Path:
    """
    设置项目导入路径的标准方法
    
    Args:
        file_path: 调用文件的 __file__ 变量
        project_name: 项目根目录名称，默认为 "CHS-SDK"
        core_lib_name: 核心库目录名称，默认为 "core_lib"
        
    Returns:
        Path: 项目根目录路径
        
    Example:
        from core_lib.utils.standard_imports import setup_project_imports
        project_root = setup_project_imports(__file__)
    """
    current_file = Path(file_path).resolve()
    
    # 向上查找项目根目录
    project_root = find_project_root(current_file, project_name)
    
    if project_root is None:
        raise RuntimeError(f"无法找到项目根目录 '{project_name}'，请检查项目结构")
    
    # 添加项目根目录到 Python 路径（如果尚未添加）
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    return project_root


def find_project_root(start_path: Path, 
                     project_name: str = "CHS-SDK",
                     max_depth: int = 10) -> Optional[Path]:
    """
    从给定路径向上查找项目根目录
    
    Args:
        start_path: 开始查找的路径
        project_name: 项目根目录名称
        max_depth: 最大查找深度
        
    Returns:
        Path: 项目根目录路径，如果未找到则返回 None
    """
    current = start_path.parent if start_path.is_file() else start_path
    depth = 0
    
    while depth < max_depth:
        # 检查当前目录是否为项目根目录
        if current.name == project_name:
            return current
            
        # 检查是否包含项目特征文件/目录
        if has_project_markers(current):
            return current
            
        # 向上一级目录
        parent = current.parent
        if parent == current:  # 已到达文件系统根目录
            break
        current = parent
        depth += 1
    
    return None


def has_project_markers(path: Path) -> bool:
    """
    检查目录是否包含项目标识文件/目录
    
    Args:
        path: 要检查的目录路径
        
    Returns:
        bool: 如果包含项目标识则返回 True
    """
    # CHS-SDK 项目的特征标识
    markers = [
        "core_lib",           # 核心库目录
        "run_scenario.py",    # 主运行脚本
        "requirements.txt",   # 依赖文件
        "examples",           # 示例目录
        "README.md"           # 说明文件
    ]
    
    return any((path / marker).exists() for marker in markers)


def ensure_core_lib_available():
    """
    确保 core_lib 可以被导入
    
    这个函数会自动检测并设置 core_lib 的导入路径
    """
    try:
        import core_lib
    except ImportError:
        # 尝试自动设置项目路径
        caller_frame = sys._getframe(1)
        caller_file = caller_frame.f_globals.get('__file__')
        
        if caller_file:
            setup_project_imports(caller_file)
            try:
                import core_lib
            except ImportError as e:
                raise ImportError(
                    f"无法导入 core_lib: {e}。"
                    f"请检查项目结构或手动调用 setup_project_imports(__file__)"
                )
        else:
            raise ImportError(
                "无法自动检测调用文件路径。"
                "请手动调用 setup_project_imports(__file__)"
            )


def get_project_structure_info(project_root: Path) -> dict:
    """
    获取项目结构信息
    
    Args:
        project_root: 项目根目录路径
        
    Returns:
        dict: 项目结构信息
    """
    info = {
        "project_root": str(project_root),
        "core_lib_path": str(project_root / "core_lib"),
        "examples_path": str(project_root / "examples"),
        "python_path_entries": [path for path in sys.path if project_root.name in path]
    }
    
    return info


# 为了向后兼容性，提供一些常用的快捷函数
def quick_setup(file_path: str) -> Path:
    """
    快速设置项目导入（向后兼容）
    
    Args:
        file_path: 调用文件的 __file__ 变量
        
    Returns:
        Path: 项目根目录路径
    """
    return setup_project_imports(file_path)


def get_core_lib_path(file_path: str) -> Path:
    """
    获取 core_lib 目录路径
    
    Args:
        file_path: 调用文件的 __file__ 变量
        
    Returns:
        Path: core_lib 目录路径
    """
    project_root = setup_project_imports(file_path)
    return project_root / "core_lib"


# 自动设置（仅在直接导入此模块时）
if __name__ != "__main__":
    try:
        # 尝试自动设置，但不强制
        caller_frame = sys._getframe(1) if len(sys._getframe().f_back.f_locals) > 0 else None
        if caller_frame:
            caller_file = caller_frame.f_globals.get('__file__')
            if caller_file and Path(caller_file).suffix == '.py':
                setup_project_imports(caller_file)
    except (AttributeError, IndexError, RuntimeError):
        # 静默忽略自动设置失败
        pass