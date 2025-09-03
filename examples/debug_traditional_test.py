#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试传统多配置文件方法测试的脚本
"""

import subprocess
import sys
import os
from pathlib import Path
import time

def run_command_test(command, test_name, timeout=60):
    """完全模拟测试脚本的 run_command_test 方法"""
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

def test_traditional_scenario_runner():
    """完全模拟测试脚本的传统多配置文件方法测试"""
    examples_dir = Path(__file__).parent
    
    print("=== 调试传统多配置文件方法测试 ===")
    print("📋 Testing all traditional scenario examples (传统多配置文件方法)")
    
    # 从run_scenario.py获取所有可用示例
    try:
        sys.path.insert(0, str(examples_dir))
        from run_scenario import ExamplesScenarioRunner
        
        runner = ExamplesScenarioRunner()
        examples = runner.list_examples()
        
        # 转换为测试格式，只包含有完整多配置文件的示例
        test_examples = {}
        for example_key, example in examples.items():
            # 构建场景路径
            scenario_path = examples_dir / example['path']
            
            # 检查是否有传统多配置文件方法需要的文件
            config_file = scenario_path / 'config.yml'
            components_file = scenario_path / 'components.yml'
            topology_file = scenario_path / 'topology.yml'
            
            # 只包含有完整多配置文件的示例（至少要有config.yml和components.yml）
            if config_file.exists() and components_file.exists():
                test_examples[example_key] = {
                    'desc': f"{example['name']} - {example['description']}",
                    'path': str(scenario_path),
                    'config': 'config.yml'
                }
        
        print(f"\n找到 {len(test_examples)} 个符合条件的示例")
        
        # 验证这些示例确实存在且具有完整的多配置文件结构
        filtered_examples = {}
        for key, info in test_examples.items():
            scenario_path = examples_dir / info['path']
            config_file = scenario_path / 'config.yml'
            components_file = scenario_path / 'components.yml'
            topology_file = scenario_path / 'topology.yml'
            agents_file = scenario_path / 'agents.yml'
            
            # 传统多配置文件方法需要完整的配置文件结构
            if (config_file.exists() and components_file.exists() and 
                topology_file.exists() and agents_file.exists()):
                filtered_examples[key] = info
                print(f"  ✅ {key}: 完整配置文件")
            else:
                print(f"  ❌ {key}: 缺少配置文件")
                
        test_examples = filtered_examples
        print(f"\n最终测试列表: {len(test_examples)} 个示例")
        
        # 检查 agent_based_06_centralized_emergency_override 是否在列表中
        target_example = "agent_based_06_centralized_emergency_override"
        if target_example in test_examples:
            print(f"\n🎯 目标示例 {target_example} 在测试列表中")
            
            # 测试这个特定示例
            example_info = test_examples[target_example]
            print(f"\n[1/1] 🔄 正在测试: {example_info['desc']}")
            print(f"示例键名: {target_example}")
            print(f"场景路径: {example_info['path']}")
            
            # 构建命令 - 使用--example参数而不是直接传递路径
            command = ["python", "-u", "run_scenario.py", "--example", target_example]
            success, output, exec_time = run_command_test(command, f"Traditional Scenario: {target_example}", timeout=120)
            
            if success:
                print(f"✅ [1/1] {example_info['desc']} - 测试通过 ({exec_time:.2f}秒)")
                return True
            else:
                print(f"❌ [1/1] {example_info['desc']} - 测试失败 ({exec_time:.2f}秒)")
                print(f"\n失败输出: {output}")
                return False
        else:
            print(f"\n❌ 目标示例 {target_example} 不在测试列表中")
            print("\n测试列表中的示例:")
            for key in sorted(test_examples.keys()):
                print(f"  {key}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_traditional_scenario_runner()
    print(f"\n最终结果: {'成功' if success else '失败'}")
    sys.exit(0 if success else 1)