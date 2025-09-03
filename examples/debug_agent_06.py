#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 agent_based_06_centralized_emergency_override 示例的测试脚本
"""

import subprocess
import sys
import os
from pathlib import Path
import time

def run_command_test(command, test_name, timeout=60):
    """模拟测试脚本的 run_command_test 方法"""
    examples_dir = Path(__file__).parent
    
    print(f"\n=== Testing {test_name} ===")
    print(f"Command: {' '.join(command)}")
    print(f"Working directory: {examples_dir}")
    print(f"Timeout setting: {timeout} seconds")
    print("Starting execution...")
    
    start_time = time.time()
    try:
        # 设置子进程环境变量，强制使用UTF-8编码
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        
        # 使用subprocess.run来简化处理并确保正确的编码
        result = subprocess.run(
            command,
            cwd=str(examples_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            encoding='utf-8',
            errors='replace',  # 替换无法解码的字符，避免乱码
            env=env  # 传递环境变量
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"Execution completed, time taken: {execution_time:.2f} seconds")
        print(f"Return code: {result.returncode}")
        print(f"Standard output length: {len(result.stdout)} characters")
        print(f"Standard error length: {len(result.stderr)} characters")
        
        # 清理输出中的特殊字符，避免乱码
        clean_stdout = result.stdout.replace('\x00', '').strip() if result.stdout else ""
        clean_stderr = result.stderr.replace('\x00', '').strip() if result.stderr else ""
        
        if result.returncode == 0:
            print(f"✓ Test passed")
            if clean_stdout:
                print(f"Standard output: {clean_stdout[:200]}..." if len(clean_stdout) > 200 else f"Standard output: {clean_stdout}")
            return True, clean_stdout, execution_time
        else:
            print(f"✗ Test failed (return code: {result.returncode})")
            error_output = clean_stderr or clean_stdout or "No error output"
            if error_output:
                print(f"Error output: {error_output[:200]}..." if len(error_output) > 200 else f"Error output: {error_output}")
            return False, error_output, execution_time
            
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        print(f"✗ Test timeout (>{timeout} seconds)")
        return False, "Test timeout", execution_time
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"✗ Test exception: {e}")
        return False, str(e), execution_time

def test_agent_06():
    """测试 agent_based_06_centralized_emergency_override 示例"""
    print("=== 调试 agent_based_06_centralized_emergency_override ===")
    
    # 测试命令 - 完全模拟测试脚本的逻辑
    command = ["python", "-u", "run_scenario.py", "--example", "agent_based_06_centralized_emergency_override"]
    
    success, output, exec_time = run_command_test(command, "Traditional Scenario: agent_based_06_centralized_emergency_override", timeout=120)
    
    print(f"\n=== 最终结果 ===")
    print(f"成功: {success}")
    print(f"执行时间: {exec_time:.2f}秒")
    print(f"输出长度: {len(output)}字符")
    
    if not success:
        print(f"\n=== 失败详情 ===")
        print(output)
    
    return success

if __name__ == "__main__":
    success = test_agent_06()
    print(f"\n最终退出码: {0 if success else 1}")
    sys.exit(0 if success else 1)