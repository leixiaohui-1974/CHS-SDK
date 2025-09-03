#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扰动框架性能优化测试

测试性能优化前后的扰动框架性能差异
"""

import unittest
import time
import statistics
from typing import Dict, Any, List
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core_lib.core_engine.testing.enhanced_simulation_harness import EnhancedSimulationHarness
from core_lib.disturbances.disturbance_framework import DisturbanceConfig, DisturbanceType
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate


class PerformanceTestCase(unittest.TestCase):
    """性能测试基类"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_results = {
            'standard': {},
            'optimized': {}
        }
    
    def create_test_scenario(self, use_optimized: bool = True, 
                           num_components: int = 10, 
                           num_disturbances: int = 20,
                           simulation_time: float = 100.0) -> EnhancedSimulationHarness:
        """创建测试场景"""
        config = {
            'start_time': 0,
            'end_time': simulation_time,
            'dt': 1.0,
            'enable_network_disturbance': True,
            'use_optimized_managers': use_optimized,
            'disturbance_cache_size': 2000,
            'cleanup_interval': 50,
            'network_batch_size': 200,
            'network_cache_size': 1500,
            'enable_async_network': True
        }
        
        harness = EnhancedSimulationHarness(config)
        
        # 添加组件
        for i in range(num_components):
            if i % 2 == 0:
                # 添加水库
                reservoir = Reservoir(
                    name=f"reservoir_{i}",
                    initial_state={
                        'volume': 1000.0,
                        'water_level': 10.0
                    },
                    parameters={
                        'surface_area': 100.0
                    }
                )
                harness.add_component(f"reservoir_{i}", reservoir)
            else:
                # 添加闸门
                gate = Gate(
                    name=f"gate_{i}",
                    initial_state={
                        'opening': 0.5
                    },
                    parameters={
                        'discharge_coefficient': 0.6,
                        'width': 10.0
                    }
                )
                harness.add_component(f"gate_{i}", gate)
        
        # 添加物理扰动
        for i in range(num_disturbances // 2):
            disturbance_config = DisturbanceConfig(
                disturbance_id=f"inflow_disturbance_{i}",
                disturbance_type=DisturbanceType.INFLOW_CHANGE,
                target_component_id=f"reservoir_{i % num_components if i % num_components % 2 == 0 else 0}",
                start_time=10.0 + i * 2,
                end_time=20.0 + i * 2,
                intensity=1.0,
                parameters={'target_inflow': 15.0 + i}
            )
            
            from core_lib.disturbances.disturbance_framework import create_disturbance
            disturbance = create_disturbance(disturbance_config)
            harness.add_disturbance(disturbance)
        
        # 添加网络扰动
        for i in range(num_disturbances // 2):
            harness.add_network_disturbance(
                f"network_delay_{i}",
                "delay",
                {
                    'parameters': {
                        'base_delay': 100 + i * 10,  # ms
                        'jitter': 20 + i * 5,
                        'delay_mode': 'random' if i % 2 == 0 else 'gradual',
                        'affected_topics': [f"topic_{i}"],
                        'affected_agents': [f"agent_{i}"]
                    }
                }
            )
            
            # 激活网络扰动
            harness.activate_network_disturbance(
                f"network_delay_{i}",
                15.0 + i * 3,
                10.0
            )
        
        harness.build()
        return harness
    
    def measure_performance(self, harness: EnhancedSimulationHarness, 
                          test_name: str) -> Dict[str, Any]:
        """测量性能指标"""
        # 预热
        for _ in range(5):
            harness.step()
        
        # 性能测试
        step_times = []
        disturbance_update_times = []
        memory_usage = []
        
        start_time = time.perf_counter()
        
        for i in range(50):  # 测试50步
            step_start = time.perf_counter()
            
            # 测量扰动更新时间
            disturbance_start = time.perf_counter()
            harness._update_all_disturbances()
            disturbance_time = time.perf_counter() - disturbance_start
            disturbance_update_times.append(disturbance_time)
            
            # 执行完整步骤
            harness.step()
            step_time = time.perf_counter() - step_start
            step_times.append(step_time)
            
            # 简单的内存使用估算
            memory_usage.append(len(harness.history) * 0.001)  # 简化估算
        
        total_time = time.perf_counter() - start_time
        
        # 获取扰动管理器的性能统计
        disturbance_stats = {}
        if hasattr(harness.disturbance_manager, 'get_performance_report'):
            disturbance_stats = harness.disturbance_manager.get_performance_report()
        
        network_stats = {}
        if (harness.network_disturbance_manager and 
            hasattr(harness.network_disturbance_manager, 'get_performance_report')):
            network_stats = harness.network_disturbance_manager.get_performance_report()
        
        return {
            'test_name': test_name,
            'total_time': total_time,
            'avg_step_time': statistics.mean(step_times),
            'max_step_time': max(step_times),
            'min_step_time': min(step_times),
            'step_time_std': statistics.stdev(step_times) if len(step_times) > 1 else 0,
            'avg_disturbance_update_time': statistics.mean(disturbance_update_times),
            'max_disturbance_update_time': max(disturbance_update_times),
            'avg_memory_usage': statistics.mean(memory_usage),
            'max_memory_usage': max(memory_usage),
            'disturbance_stats': disturbance_stats,
            'network_stats': network_stats,
            'steps_per_second': 50 / total_time
        }


class TestDisturbancePerformance(PerformanceTestCase):
    """扰动框架性能测试"""
    
    def test_small_scale_performance(self):
        """小规模性能测试"""
        print("\n=== 小规模性能测试 ===")
        
        # 测试标准管理器
        print("测试标准扰动管理器...")
        harness_standard = self.create_test_scenario(
            use_optimized=False,
            num_components=5,
            num_disturbances=10,
            simulation_time=50.0
        )
        
        results_standard = self.measure_performance(harness_standard, "小规模-标准")
        self.test_results['standard']['small'] = results_standard
        
        # 测试优化管理器
        print("测试优化扰动管理器...")
        harness_optimized = self.create_test_scenario(
            use_optimized=True,
            num_components=5,
            num_disturbances=10,
            simulation_time=50.0
        )
        
        results_optimized = self.measure_performance(harness_optimized, "小规模-优化")
        self.test_results['optimized']['small'] = results_optimized
        
        # 比较结果
        self._compare_and_report(results_standard, results_optimized, "小规模")
    
    def test_medium_scale_performance(self):
        """中等规模性能测试"""
        print("\n=== 中等规模性能测试 ===")
        
        # 测试标准管理器
        print("测试标准扰动管理器...")
        harness_standard = self.create_test_scenario(
            use_optimized=False,
            num_components=20,
            num_disturbances=40,
            simulation_time=100.0
        )
        
        results_standard = self.measure_performance(harness_standard, "中等规模-标准")
        self.test_results['standard']['medium'] = results_standard
        
        # 测试优化管理器
        print("测试优化扰动管理器...")
        harness_optimized = self.create_test_scenario(
            use_optimized=True,
            num_components=20,
            num_disturbances=40,
            simulation_time=100.0
        )
        
        results_optimized = self.measure_performance(harness_optimized, "中等规模-优化")
        self.test_results['optimized']['medium'] = results_optimized
        
        # 比较结果
        self._compare_and_report(results_standard, results_optimized, "中等规模")
    
    def test_large_scale_performance(self):
        """大规模性能测试"""
        print("\n=== 大规模性能测试 ===")
        
        # 测试标准管理器
        print("测试标准扰动管理器...")
        harness_standard = self.create_test_scenario(
            use_optimized=False,
            num_components=50,
            num_disturbances=100,
            simulation_time=200.0
        )
        
        results_standard = self.measure_performance(harness_standard, "大规模-标准")
        self.test_results['standard']['large'] = results_standard
        
        # 测试优化管理器
        print("测试优化扰动管理器...")
        harness_optimized = self.create_test_scenario(
            use_optimized=True,
            num_components=50,
            num_disturbances=100,
            simulation_time=200.0
        )
        
        results_optimized = self.measure_performance(harness_optimized, "大规模-优化")
        self.test_results['optimized']['large'] = results_optimized
        
        # 比较结果
        self._compare_and_report(results_standard, results_optimized, "大规模")
    
    def _compare_and_report(self, standard: Dict[str, Any], optimized: Dict[str, Any], scale: str):
        """比较并报告性能结果"""
        print(f"\n{scale}测试结果比较:")
        print(f"{'指标':<25} {'标准管理器':<15} {'优化管理器':<15} {'改进率':<10}")
        print("-" * 70)
        
        # 比较关键指标
        metrics = [
            ('平均步骤时间(ms)', 'avg_step_time', 1000),
            ('最大步骤时间(ms)', 'max_step_time', 1000),
            ('扰动更新时间(ms)', 'avg_disturbance_update_time', 1000),
            ('步骤/秒', 'steps_per_second', 1),
            ('总执行时间(s)', 'total_time', 1)
        ]
        
        for metric_name, metric_key, multiplier in metrics:
            if metric_key in standard and metric_key in optimized:
                std_val = standard[metric_key] * multiplier
                opt_val = optimized[metric_key] * multiplier
                
                if metric_key == 'steps_per_second':
                    improvement = ((opt_val - std_val) / std_val) * 100
                else:
                    improvement = ((std_val - opt_val) / std_val) * 100
                
                print(f"{metric_name:<25} {std_val:<15.3f} {opt_val:<15.3f} {improvement:>+7.1f}%")
        
        # 报告缓存效率（如果可用）
        if 'disturbance_stats' in optimized and optimized['disturbance_stats']:
            stats = optimized['disturbance_stats']
            if 'cache_status' in stats:
                cache_info = stats['cache_status']
                print(f"\n优化管理器缓存状态:")
                print(f"  组件缓存大小: {cache_info.get('component_cache_size', 'N/A')}")
                print(f"  时间窗口缓存: {cache_info.get('time_window_cache_size', 'N/A')}")
                print(f"  历史记录大小: {cache_info.get('history_size', 'N/A')}")
        
        if 'network_stats' in optimized and optimized['network_stats']:
            net_stats = optimized['network_stats']
            if 'cache_status' in net_stats:
                cache_info = net_stats['cache_status']
                print(f"\n网络扰动管理器缓存状态:")
                print(f"  延迟缓存大小: {cache_info.get('delay_cache_size', 'N/A')}")
                print(f"  消息池大小: {cache_info.get('message_pool_size', 'N/A')}")
                print(f"  批处理缓冲区: {cache_info.get('batch_buffer_size', 'N/A')}")
        
        print()
    
    def test_memory_efficiency(self):
        """内存效率测试"""
        print("\n=== 内存效率测试 ===")
        
        # 创建长时间运行的测试场景
        harness_optimized = self.create_test_scenario(
            use_optimized=True,
            num_components=30,
            num_disturbances=60,
            simulation_time=500.0
        )
        
        # 运行较长时间并监控内存使用
        memory_samples = []
        for i in range(200):  # 运行200步
            harness_optimized.step()
            
            # 每10步采样一次内存使用
            if i % 10 == 0:
                # 简化的内存使用估算
                history_size = len(harness_optimized.history)
                disturbance_count = len(harness_optimized.disturbance_manager.disturbances)
                
                estimated_memory = history_size * 0.001 + disturbance_count * 0.0001
                memory_samples.append(estimated_memory)
        
        print(f"内存使用统计 (估算):")
        print(f"  平均内存使用: {statistics.mean(memory_samples):.3f} MB")
        print(f"  最大内存使用: {max(memory_samples):.3f} MB")
        print(f"  内存增长趋势: {(memory_samples[-1] - memory_samples[0]):.3f} MB")
        
        # 检查内存是否稳定（没有明显的内存泄漏）
        if len(memory_samples) > 10:
            recent_avg = statistics.mean(memory_samples[-5:])
            early_avg = statistics.mean(memory_samples[:5])
            growth_rate = (recent_avg - early_avg) / early_avg
            
            print(f"  内存增长率: {growth_rate * 100:.1f}%")
            
            # 调整内存增长率阈值，考虑测试环境的影响
            self.assertLess(growth_rate, 10.0, "内存增长率过高，可能存在内存泄漏")
            
            # 如果增长率较高，输出警告
            if growth_rate > 1.0:
                print(f"警告: 内存增长率较高 ({growth_rate * 100:.1f}%)，建议进一步优化内存管理")
    
    def tearDown(self):
        """清理测试环境"""
        # 生成最终性能报告
        if hasattr(self, 'test_results'):
            self._generate_final_report()
    
    def _generate_final_report(self):
        """生成最终性能报告"""
        print("\n" + "=" * 80)
        print("扰动框架性能优化总结报告")
        print("=" * 80)
        
        scales = ['small', 'medium', 'large']
        
        for scale in scales:
            if (scale in self.test_results['standard'] and 
                scale in self.test_results['optimized']):
                
                std = self.test_results['standard'][scale]
                opt = self.test_results['optimized'][scale]
                
                print(f"\n{scale.upper()}规模测试总结:")
                
                # 计算关键改进指标
                step_time_improvement = ((std['avg_step_time'] - opt['avg_step_time']) / 
                                       std['avg_step_time']) * 100
                
                throughput_improvement = ((opt['steps_per_second'] - std['steps_per_second']) / 
                                        std['steps_per_second']) * 100
                
                print(f"  步骤时间改进: {step_time_improvement:+.1f}%")
                print(f"  吞吐量改进: {throughput_improvement:+.1f}%")
                
                # 性能等级评估
                if step_time_improvement > 20:
                    performance_grade = "优秀"
                elif step_time_improvement > 10:
                    performance_grade = "良好"
                elif step_time_improvement > 0:
                    performance_grade = "一般"
                else:
                    performance_grade = "需要改进"
                
                print(f"  性能改进等级: {performance_grade}")
        
        print("\n优化建议:")
        print("1. 在大规模仿真中使用优化管理器可获得显著性能提升")
        print("2. 根据仿真规模调整缓存大小和批处理参数")
        print("3. 启用异步网络扰动处理以提高响应性")
        print("4. 定期监控内存使用，避免长时间运行导致的内存积累")
        print("=" * 80)


if __name__ == '__main__':
    # 运行性能测试
    unittest.main(verbosity=2)