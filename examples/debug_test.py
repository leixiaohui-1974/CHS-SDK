#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试测试脚本 - 验证subprocess行为
"""

import subprocess
import sys
from pathlib import Path

def test_command(command):
    """测试单个命令"""
    print(f"测试命令: {' '.join(command)}")
    
    try:
        # 方法1: 使用run
        print("\n=== 使用subprocess.run ===")
        result = subprocess.run(
            command,
            cwd=str(Path(__file__).parent),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=60
        )
        print(f"返回码: {result.returncode}")
        print(f"标准输出长度: {len(result.stdout)}")
        print(f"标准错误长度: {len(result.stderr)}")
        print("\n=== 完整标准输出 ===")
        print(result.stdout)
        print("\n=== 完整标准错误 ===")
        print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("命令超时")
    except Exception as e:
        print(f"异常: {e}")

if __name__ == "__main__":
    # 测试一个已知会成功的命令
    test_command(["python", "run_unified_scenario.py", "--example", "mission_example_3_01_enhanced_perception"])