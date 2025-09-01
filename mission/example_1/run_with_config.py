#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 1 - 配置文件驱动入口
演示纯物理组件（渠道和闸门）动态行为

这个脚本使用根目录的通用run_scenario.py来运行仿真。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入根目录的run_scenario模块
from run_scenario import main as run_scenario_main

def main():
    """
    运行Mission Example 1的配置文件驱动仿真
    """
    # 获取当前示例目录
    example_dir = Path(__file__).resolve().parent
    
    # 设置命令行参数，指向当前目录
    original_argv = sys.argv.copy()
    sys.argv = ['run_scenario.py', str(example_dir)]
    
    try:
        # 调用通用的scenario runner
        run_scenario_main()
    finally:
        # 恢复原始命令行参数
        sys.argv = original_argv

if __name__ == "__main__":
    main()