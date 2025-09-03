#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确模拟测试脚本行为的调试脚本
"""

import subprocess
import time
import os
from pathlib import Path

def run_command_test(command, test_name, timeout=120):
    """完全模拟测试脚本的 run_command_test 方法"""
    examples_dir = Path.cwd()
    
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

def main():
    print("🔍 精确模拟测试脚本行为")
    print("=" * 60)
    
    # 测试 agent_based_06_centralized_emergency_override
    example_key = "agent_based_06_centralized_emergency_override"
    command = ["python", "-u", "run_scenario.py", "--example", example_key]
    
    success, output, exec_time = run_command_test(command, f"Traditional Scenario: {example_key}", timeout=120)
    
    print("\n" + "=" * 60)
    print("🎯 测试结果:")
    print(f"成功: {success}")
    print(f"执行时间: {exec_time:.2f}秒")
    print(f"输出长度: {len(output)} 字符")
    
    if success:
        print("✅ 测试通过")
    else:
        print("❌ 测试失败")
        print(f"错误信息: {output[:500]}..." if len(output) > 500 else f"错误信息: {output}")

if __name__ == "__main__":
    main()