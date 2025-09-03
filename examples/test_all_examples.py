#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动测试所有示例的脚本
"""

import sys
import os
from pathlib import Path
import io

# 设置环境变量强制UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 设置标准输出编码为UTF-8
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples.run_hardcoded import ExamplesHardcodedRunner

def test_all_examples():
    """测试所有示例"""
    runner = ExamplesHardcodedRunner()
    
    # 测试的示例列表（基于完整的examples目录结构）
    test_examples = [
        # agent_based 系列示例
        ("agent_based_03_event_driven_agents", "事件驱动智能体"),
        ("agent_based_06_centralized_emergency_override", "集中式紧急覆盖"),
        ("agent_based_09_agent_based_distributed_control", "基于智能体的分布式控制"),
        ("agent_based_12_pid_control_comparison", "PID控制比较"),
        
        # canal_model 系列示例
        ("canal_model_canal_model_comparison", "渠道模型对比"),
        ("canal_model_canal_mpc_pid_control", "运河MPC PID控制"),
        ("canal_model_canal_pid_control", "运河PID控制"),
        ("canal_model_complex_fault_scenario_example", "复杂故障场景"),
        ("canal_model_hierarchical_distributed_control_example", "分层分布式控制"),
        ("canal_model_structured_control_example", "结构化控制"),
        
        # demo 系列示例
        ("demo_simplified_reservoir_control", "简化水库控制演示"),
        
        # distributed_digital_twin_simulation 系列示例
        ("distributed_digital_twin_simulation/run_simulation", "分布式数字孪生仿真"),
        ("distributed_digital_twin_simulation/run_disturbance_simulation", "分布式数字孪生干扰仿真"),
        ("distributed_digital_twin_simulation/run_comparison_experiment", "分布式数字孪生对比实验"),
        ("distributed_digital_twin_simulation/test_simple_inflow_disturbance", "简单入流干扰测试"),
        ("distributed_digital_twin_simulation/test_inflow_disturbance", "入流干扰测试"),
        ("distributed_digital_twin_simulation/test_network_disturbance", "网络干扰测试"),
        ("distributed_digital_twin_simulation/test_actuator_failure_disturbance", "执行器故障干扰测试"),
        ("distributed_digital_twin_simulation/test_comprehensive_disturbance", "综合干扰测试"),
        ("distributed_digital_twin_simulation/test_multiple_disturbance_types", "多种干扰类型测试"),
        ("distributed_digital_twin_simulation/comprehensive_disturbance_test_suite", "综合干扰测试套件"),
        ("distributed_digital_twin_simulation/parameter_identification_analysis", "参数辨识分析"),
        ("distributed_digital_twin_simulation/physical_digital_twin_comparison", "物理数字孪生对比"),
        ("distributed_digital_twin_simulation/robustness_validation", "鲁棒性验证"),
        ("distributed_digital_twin_simulation/optimized_control_validation", "优化控制验证"),
        
        # identification 系列示例
        ("identification_01_reservoir_storage_curve", "水库库容曲线辨识"),
        ("identification_02_gate_discharge_coefficient", "闸门流量系数辨识"),
        ("identification_03_pipe_roughness", "管道糙率辨识"),
        
        # llm_integration 系列示例
        ("llm_integration", "LLM集成示例"),
        
        # mission_example 系列示例
        ("mission_example_1", "任务示例1"),
        ("mission_example_2", "任务示例2"),
        ("mission_example_3", "任务示例3"),
        ("mission_example_5", "任务示例5"),
        
        # mission_scenarios 系列示例
        ("mission_scenarios", "Mission场景示例"),
        
        # non_agent_based 系列示例
        ("non_agent_based_01_getting_started", "入门示例"),
        ("non_agent_based_02_multi_component_systems", "多组件系统"),
        ("non_agent_based_07_pipe_and_valve", "管道与阀门"),
        ("non_agent_based_08_non_agent_simulation", "非智能体仿真"),
        
        # notebooks 系列示例
        ("notebooks_07_centralized_setpoint_optimization", "集中式设定点优化"),
        ("notebooks_10_canal_system", "渠道系统笔记本"),
        ("notebooks_11_control_and_agents", "控制与智能体笔记本"),
        
        # watertank 系列示例
        ("watertank_01_simulation", "水箱仿真"),
        
        # watertank_refactored 系列示例
        ("watertank_refactored_01_simple_simulation", "水箱简单仿真"),
        ("watertank_refactored_02_parameter_identification", "水箱参数辨识"),
        ("watertank_refactored_03_pid_control_inlet", "水箱PID入口控制"),
        ("watertank_refactored_04_pid_control_outlet", "水箱PID出口控制"),
        ("watertank_refactored_05_joint_control", "水箱联合控制"),
        ("watertank_refactored_06_sensor_disturbance", "水箱传感器干扰"),
        ("watertank_refactored_07_actuator_disturbance", "水箱执行器干扰")
    ]
    
    results = {}
    
    print("=== 开始自动测试所有示例 ===")
    print(f"总共需要测试 {len(test_examples)} 个示例\n")
    
    for i, (example_key, example_name) in enumerate(test_examples, 1):
        print(f"[{i}/{len(test_examples)}] 测试示例: {example_name} ({example_key})")
        
        try:
            success = runner.run_example(example_key)
            results[example_key] = {
                'name': example_name,
                'success': success,
                'error': None
            }
            status = "[PASS]" if success else "[FAIL]"
            print(f"Result: {status}\n")
            
        except Exception as e:
            results[example_key] = {
                'name': example_name,
                'success': False,
                'error': str(e)
            }
            print(f"Result: [ERROR] - {str(e)}\n")
    
    # 输出总结
    print("=== TEST SUMMARY ===")
    successful = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    print(f"Total tests: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success rate: {successful/total*100:.1f}%\n")
    
    # 详细结果
    print("Detailed results:")
    for example_key, result in results.items():
        status = "[PASS]" if result['success'] else "[FAIL]"
        print(f"  {status} {result['name']} ({example_key})")
        if result['error']:
            print(f"    Error: {result['error']}")
    
    return results

if __name__ == "__main__":
    test_all_examples()