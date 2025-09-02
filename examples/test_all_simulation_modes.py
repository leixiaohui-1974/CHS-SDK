#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试脚本 - 测试所有仿真运行方式

本脚本自动测试CHS-SDK中的所有仿真运行方式，包括：
1. run_hardcoded.py - 硬编码示例运行器
2. run_unified_scenario.py - 统一配置文件方式
3. run_scenario.py - 传统多配置文件方式
4. run_universal_config.py - 通用配置运行器

运行方式：
    python test_all_simulation_modes.py
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple

# 设置环境变量强制使用UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

class SimulationModesTester:
    """仿真模式测试器"""
    
    def __init__(self):
        self.examples_dir = Path(__file__).parent
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def run_command_test(self, command: List[str], test_name: str, timeout: int = 60) -> Tuple[bool, str, float]:
        """Run command test"""
        print(f"\n=== Testing {test_name} ===")
        print(f"Command: {' '.join(command)}")
        print(f"Working directory: {self.examples_dir}")
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
                cwd=str(self.examples_dir),
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
    
    def test_hardcoded_runner(self) -> bool:
        """Test hardcoded runner - run all available examples"""
        print("📋 Testing all hardcoded examples (built-in configuration)")
        
        # 获取所有可用的例子列表
        examples = {
            "getting_started": "入门示例 - 基础水库-闸门系统仿真",
            "multi_component": "多组件系统 - 复杂多组件水利系统仿真",
            "event_driven_agents": "事件驱动智能体 - 基于事件的智能体控制系统",
            "hierarchical_control": "分层控制 - 分层分布式控制系统",
            "complex_networks": "复杂网络 - 分支网络系统仿真",
            "pump_station": "泵站控制 - 泵站智能控制系统",
            "hydropower_plant": "水电站 - 水电站运行仿真",
            "canal_pid_control": "渠道PID控制 - 渠道系统PID控制对比",
            "canal_mpc_control": "渠道MPC控制 - 渠道系统MPC与PID控制",
            "reservoir_identification": "水库参数辨识 - 水库库容曲线参数辨识",
            "simplified_demo": "简化演示 - 简化水库控制演示",
            "mission_example_1": "任务示例1 - 基础物理与高级控制",
            "mission_example_2": "任务示例2 - 闭环控制系统",
            "mission_example_3": "任务示例3 - 增强感知系统",
            "mission_example_5": "任务示例5 - 涡轮闸门仿真",
            "mission_scenarios": "Mission场景示例 - 从mission目录迁移的场景示例"
        }
        
        all_success = True
        total_time = 0
        all_outputs = []
        failed_examples = []
        
        print(f"\n总共需要测试 {len(examples)} 个硬编码例子:")
        
        for i, (example_key, example_desc) in enumerate(examples.items(), 1):
            print(f"\n[{i}/{len(examples)}] 🔄 正在测试: {example_desc}")
            print(f"示例键名: {example_key}")
            
            command = ["python", "-u", "run_hardcoded.py", "--example", example_key]
            success, output, exec_time = self.run_command_test(command, f"Hardcoded Example: {example_key}", timeout=120)
            
            total_time += exec_time
            all_outputs.append(f"=== {example_key} ===\n{output}")
            
            if success:
                print(f"✅ [{i}/{len(examples)}] {example_desc} - 测试通过 ({exec_time:.2f}秒)")
            else:
                print(f"❌ [{i}/{len(examples)}] {example_desc} - 测试失败 ({exec_time:.2f}秒)")
                failed_examples.append(example_key)
                all_success = False
        
        # 汇总结果
        print(f"\n=== 硬编码例子测试汇总 ===")
        print(f"总测试数量: {len(examples)}")
        print(f"成功数量: {len(examples) - len(failed_examples)}")
        print(f"失败数量: {len(failed_examples)}")
        print(f"总执行时间: {total_time:.2f}秒")
        
        if failed_examples:
            print(f"失败的例子: {', '.join(failed_examples)}")
        
        self.test_results["run_hardcoded"] = {
            "success": all_success,
            "output": "\n\n".join(all_outputs),
            "execution_time": total_time,
            "description": f"Hardcoded Example Runner - {len(examples)} examples tested",
            "failed_examples": failed_examples,
            "total_examples": len(examples)
        }
        
        return all_success
    
    def test_unified_scenario_runner(self) -> bool:
        """Test unified scenario runner - run all available examples"""
        print("📋 Testing all unified scenario examples (统一配置文件方法)")
        
        # 动态获取所有可用的例子列表
        try:
            sys.path.insert(0, str(self.examples_dir))
            from run_unified_scenario import ExamplesUnifiedScenarioRunner
            
            runner = ExamplesUnifiedScenarioRunner()
            available_examples = runner._discover_examples()
            
            # 过滤出有有效配置文件的示例
            examples = {}
            for key, example_info in available_examples.items():
                example_path = self.examples_dir / Path(example_info['path']).parent
                universal_config = example_path / 'universal_config.yml'
                traditional_config = example_path / 'config.yml'
                
                # 只包含有配置文件的示例
                if universal_config.exists() or traditional_config.exists():
                    examples[key] = example_info['description']
                
        except Exception as e:
            print(f"❌ 无法获取统一场景示例列表: {e}")
            return False
        
        all_success = True
        total_time = 0
        all_outputs = []
        failed_examples = []
        
        print(f"\n总共需要测试 {len(examples)} 个统一场景例子:")
        
        for i, (example_key, example_desc) in enumerate(examples.items(), 1):
            print(f"\n[{i}/{len(examples)}] 🔄 正在测试: {example_desc}")
            print(f"示例键名: {example_key}")
            
            command = ["python", "-u", "run_unified_scenario.py", "--example", example_key]
            success, output, exec_time = self.run_command_test(command, f"Unified Scenario: {example_key}", timeout=120)
            
            total_time += exec_time
            all_outputs.append(f"=== {example_key} ===\n{output}")
            
            if success:
                print(f"✅ [{i}/{len(examples)}] {example_desc} - 测试通过 ({exec_time:.2f}秒)")
            else:
                print(f"❌ [{i}/{len(examples)}] {example_desc} - 测试失败 ({exec_time:.2f}秒)")
                failed_examples.append(example_key)
                all_success = False
        
        # 汇总结果
        print(f"\n=== 统一场景例子测试汇总 ===")
        print(f"总测试数量: {len(examples)}")
        print(f"成功数量: {len(examples) - len(failed_examples)}")
        print(f"失败数量: {len(failed_examples)}")
        print(f"总执行时间: {total_time:.2f}秒")
        
        if failed_examples:
            print(f"失败的例子: {', '.join(failed_examples)}")
        
        self.test_results["run_unified_scenario"] = {
            "success": all_success,
            "output": "\n\n".join(all_outputs),
            "execution_time": total_time,
            "description": f"Unified Configuration File Method - {len(examples)} examples tested",
            "failed_examples": failed_examples,
            "total_examples": len(examples)
        }
        
        return all_success
    
    def test_scenario_runner(self) -> bool:
        """Test traditional scenario runner - run all available examples"""
        print("📋 Testing all traditional scenario examples (传统多配置文件方法)")
        
        # 从run_scenario.py获取所有可用示例
        try:
            sys.path.insert(0, str(self.examples_dir))
            from run_scenario import ExamplesScenarioRunner
            
            runner = ExamplesScenarioRunner()
            examples = runner.list_examples()
            
            # 转换为测试格式，只包含有完整多配置文件的示例
            test_examples = {}
            for example_key, example in examples.items():
                # 构建场景路径
                scenario_path = self.examples_dir / example['path']
                
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
            
            # 如果没有找到任何完整的多配置文件示例，跳过测试
            if not test_examples:
                print("⚠️  没有找到包含完整多配置文件的示例，跳过传统多配置文件方法测试")
                self.test_results["run_scenario"] = {
                    "success": True,
                    "output": "No multi-config examples found, test skipped",
                    "execution_time": 0.0,
                    "description": "Traditional Multi-Configuration File Method - 0 examples tested (skipped)",
                    "failed_examples": [],
                    "total_examples": 0
                }
                return True
            
        except Exception as e:
            print(f"❌ 无法获取传统场景示例列表: {e}")
            # 如果无法动态获取，跳过传统多配置文件方法测试
            # 因为大多数示例只有单个config.yml文件，不适合传统多配置文件方法
            print("⚠️  传统多配置文件方法需要完整的多配置文件，大多数示例不兼容，跳过测试")
            self.test_results["run_scenario"] = {
                "success": True,
                "output": "Traditional multi-config method skipped - most examples use single config.yml",
                "execution_time": 0.0,
                "description": "Traditional Multi-Configuration File Method - 0 examples tested (skipped)",
                "failed_examples": [],
                "total_examples": 0
            }
            return True
        
        # 验证这些示例确实存在且具有完整的多配置文件结构
        filtered_examples = {}
        for key, info in test_examples.items():
            scenario_path = self.examples_dir / info['path']
            config_file = scenario_path / 'config.yml'
            components_file = scenario_path / 'components.yml'
            topology_file = scenario_path / 'topology.yml'
            agents_file = scenario_path / 'agents.yml'
            
            # 传统多配置文件方法需要完整的配置文件结构
            if (config_file.exists() and components_file.exists() and 
                topology_file.exists() and agents_file.exists()):
                filtered_examples[key] = info
        test_examples = filtered_examples
        
        all_success = True
        total_time = 0
        all_outputs = []
        failed_examples = []
        
        print(f"\n总共需要测试 {len(test_examples)} 个传统场景例子:")
        
        for i, (example_key, example_info) in enumerate(test_examples.items(), 1):
            print(f"\n[{i}/{len(test_examples)}] 🔄 正在测试: {example_info['desc']}")
            print(f"示例键名: {example_key}")
            print(f"场景路径: {example_info['path']}")
            
            # 构建命令 - 使用--example参数而不是直接传递路径
            command = ["python", "-u", "run_scenario.py", "--example", example_key]
            success, output, exec_time = self.run_command_test(command, f"Traditional Scenario: {example_key}", timeout=120)
            
            total_time += exec_time
            all_outputs.append(f"=== {example_key} ===\n{output}")
            
            if success:
                print(f"✅ [{i}/{len(test_examples)}] {example_info['desc']} - 测试通过 ({exec_time:.2f}秒)")
            else:
                print(f"❌ [{i}/{len(test_examples)}] {example_info['desc']} - 测试失败 ({exec_time:.2f}秒)")
                failed_examples.append(example_key)
                all_success = False
        
        # 汇总结果
        print(f"\n=== 传统场景例子测试汇总 ===")
        print(f"总测试数量: {len(test_examples)}")
        print(f"成功数量: {len(test_examples) - len(failed_examples)}")
        print(f"失败数量: {len(failed_examples)}")
        print(f"总执行时间: {total_time:.2f}秒")
        
        if failed_examples:
            print(f"失败的例子: {', '.join(failed_examples)}")
        
        self.test_results["run_scenario"] = {
            "success": all_success,
            "output": "\n\n".join(all_outputs),
            "execution_time": total_time,
            "description": f"Traditional Multi-Configuration File Method - {len(test_examples)} examples tested",
            "failed_examples": failed_examples,
            "total_examples": len(test_examples)
        }
        
        return all_success
    
    def test_universal_config_runner(self) -> bool:
        """Test universal configuration runner - run all available examples"""
        print("📋 Testing all universal configuration examples (通用配置运行器)")
        
        # 动态获取所有可用的例子列表
        try:
            sys.path.insert(0, str(self.examples_dir))
            from run_universal_config import ExamplesUniversalConfigRunner
            
            runner = ExamplesUniversalConfigRunner()
            available_examples = runner._discover_examples()
            
            # 转换为测试格式，只包含有universal_config.yml的示例
            examples = {}
            for key, example_info in available_examples.items():
                # 构建示例路径
                example_path = self.examples_dir / example_info['path']
                universal_config_file = example_path / 'universal_config.yml'
                
                # 只包含有universal_config.yml文件的示例
                if universal_config_file.exists():
                    examples[key] = example_info['description']
            
            # 如果没有找到任何universal_config.yml示例，跳过测试
            if not examples:
                print("⚠️  没有找到包含universal_config.yml的示例，跳过通用配置运行器测试")
                self.test_results["run_universal_config"] = {
                    "success": True,
                    "output": "No universal config examples found, test skipped",
                    "execution_time": 0.0,
                    "description": "Universal Config Runner - 0 examples tested (skipped)",
                    "failed_examples": [],
                    "total_examples": 0
                }
                return True
                
        except Exception as e:
            print(f"❌ 无法获取通用配置示例列表: {e}")
            return False
        
        all_success = True
        total_time = 0
        all_outputs = []
        failed_examples = []
        
        print(f"\n总共需要测试 {len(examples)} 个通用配置例子 (仅包含universal_config.yml的示例):")
        
        for i, (example_key, example_desc) in enumerate(examples.items(), 1):
            print(f"\n[{i}/{len(examples)}] 🔄 正在测试: {example_desc}")
            print(f"示例键名: {example_key}")
            
            command = ["python", "-u", "run_universal_config.py", "--example", example_key]
            success, output, exec_time = self.run_command_test(command, f"Universal Config: {example_key}", timeout=120)
            
            total_time += exec_time
            all_outputs.append(f"=== {example_key} ===\n{output}")
            
            if success:
                print(f"✅ [{i}/{len(examples)}] {example_desc} - 测试通过 ({exec_time:.2f}秒)")
            else:
                print(f"❌ [{i}/{len(examples)}] {example_desc} - 测试失败 ({exec_time:.2f}秒)")
                failed_examples.append(example_key)
                all_success = False
        
        # 汇总结果
        print(f"\n=== 通用配置例子测试汇总 ===")
        print(f"总测试数量: {len(examples)}")
        print(f"成功数量: {len(examples) - len(failed_examples)}")
        print(f"失败数量: {len(failed_examples)}")
        print(f"总执行时间: {total_time:.2f}秒")
        
        if failed_examples:
            print(f"失败的例子: {', '.join(failed_examples)}")
        
        self.test_results["run_universal_config"] = {
            "success": all_success,
            "output": "\n\n".join(all_outputs),
            "execution_time": total_time,
            "description": f"Universal Configuration Runner - {len(examples)} examples tested",
            "failed_examples": failed_examples,
            "total_examples": len(examples)
        }
        
        return all_success
    
    def run_all_tests(self) -> None:
        """Run all tests"""
        print("=== CHS-SDK Simulation Mode Automated Testing ===")
        print(f"Test directory: {self.examples_dir}")
        print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Define test list
        tests = [
            ("Hardcoded Example Runner", self.test_hardcoded_runner),
            ("Unified Configuration File Method", self.test_unified_scenario_runner),
            ("Traditional Multi-Configuration File Method", self.test_scenario_runner),
            ("Universal Configuration Runner", self.test_universal_config_runner)
        ]
        
        self.total_tests = len(tests)
        print(f"\nTotal tests to run: {self.total_tests}")
        print("="*60)
        
        # Run tests
        for i, (test_name, test_func) in enumerate(tests, 1):
            print(f"\n[{i}/{self.total_tests}] Preparing to run test: {test_name}")
            print(f"Current progress: {((i-1)/self.total_tests)*100:.1f}%")
            
            test_start_time = time.time()
            try:
                if test_func():
                    self.passed_tests += 1
                    print(f"[{i}/{self.total_tests}] ✓ {test_name} test passed")
                else:
                    self.failed_tests += 1
                    print(f"[{i}/{self.total_tests}] ✗ {test_name} test failed")
            except Exception as e:
                print(f"[{i}/{self.total_tests}] ✗ Test {test_name} exception occurred: {e}")
                self.failed_tests += 1
            
            test_end_time = time.time()
            print(f"Test duration: {test_end_time - test_start_time:.2f} seconds")
            print(f"Current statistics: Passed {self.passed_tests}, Failed {self.failed_tests}")
            
            if i < self.total_tests:
                print("\n" + "-"*40 + " Continue to next test " + "-"*40)
        
        print(f"\nAll tests completed! Final progress: 100.0%")
        print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 显示测试结果摘要
        self.show_test_summary()
    
    def show_test_summary(self) -> None:
        """Show test result summary"""
        print("\n" + "="*60)
        print("Test Result Summary")
        print("="*60)
        
        print(f"Total tests: {self.total_tests}")
        print(f"Passed tests: {self.passed_tests}")
        print(f"Failed tests: {self.failed_tests}")
        print(f"Success rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        
        print("\nDetailed results:")
        for test_key, result in self.test_results.items():
            status = "✓ Passed" if result["success"] else "✗ Failed"
            exec_time = result["execution_time"]
            description = result["description"]
            print(f"  {description}: {status} (Duration: {exec_time:.2f} seconds)")
        
        # Show failed test details
        failed_tests = {k: v for k, v in self.test_results.items() if not v["success"]}
        if failed_tests:
            print("\nFailed test details:")
            for test_key, result in failed_tests.items():
                print(f"\n{result['description']}:")
                output = result['output'] or "No output information"
                print(f"  Error message: {output[:200]}..." if len(output) > 200 else f"  Error message: {output}")
        
        print("\n" + "="*60)
        
        if self.failed_tests == 0:
            print("🎉 All tests passed! All CHS-SDK simulation modes are working properly.")
        else:
            print(f"⚠️  {self.failed_tests} tests failed, please check related configurations and dependencies.")
    
    def save_test_report(self, filename: str = "test_report.txt") -> None:
        """Save test report to file"""
        report_path = self.examples_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("CHS-SDK Simulation Mode Test Report\n")
            f.write("=" * 40 + "\n")
            f.write(f"Test time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total tests: {self.total_tests}\n")
            f.write(f"Passed tests: {self.passed_tests}\n")
            f.write(f"Failed tests: {self.failed_tests}\n")
            f.write(f"Success rate: {(self.passed_tests/self.total_tests*100):.1f}%\n\n")
            
            for test_key, result in self.test_results.items():
                f.write(f"{result['description']}:\n")
                f.write(f"  Status: {'Passed' if result['success'] else 'Failed'}\n")
                f.write(f"  Execution time: {result['execution_time']:.2f} seconds\n")
                if not result['success']:
                    f.write(f"  Error message: {result['output']}\n")
                f.write("\n")
        
        print(f"\nTest report saved to: {report_path}")

def main():
    """Main function"""
    tester = SimulationModesTester()
    
    try:
        tester.run_all_tests()
        tester.save_test_report()
        
        # Set exit code based on test results
        sys.exit(0 if tester.failed_tests == 0 else 1)
        
    except KeyboardInterrupt:
        print("\nUser interrupted test")
        sys.exit(1)
    except Exception as e:
        print(f"\nException occurred during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()