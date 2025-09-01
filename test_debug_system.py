#!/usr/bin/env python3
"""
简化的调试系统测试
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core_lib.debug.log_manager import get_log_manager, LogLevel
from core_lib.debug.debug_collector import (
    get_collector_manager, collect_debug_data,
    start_timer, end_timer, record_metric
)

def test_basic_logging():
    """测试基础日志功能"""
    print("\n=== 测试基础日志功能 ===")
    
    logger = get_log_manager()
    
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    logger.debug("这是一条调试日志")
    
    print("✅ 基础日志测试完成")

def test_data_collection():
    """测试数据收集功能"""
    print("\n=== 测试数据收集功能 ===")
    
    # 测试手动数据收集
    collect_debug_data("performance", "test_metric", 42.5, {"unit": "ms"})
    collect_debug_data("state", "simulation_step", 1, {"status": "running"})
    
    # 测试计时器
    start_timer("test_operation")
    time.sleep(0.1)
    duration = end_timer("test_operation")
    print(f"操作耗时: {duration:.3f}秒")
    
    # 测试指标记录
    record_metric("cpu_usage", 75.5, "percent")
    record_metric("memory_usage", 1024, "MB")
    
    print("✅ 数据收集测试完成")

def test_performance_monitoring():
    """测试性能监控"""
    print("\n=== 测试性能监控 ===")
    
    manager = get_collector_manager()
    
    # 启动性能收集
    manager.start_auto_collect(1.0)
    
    # 模拟一些工作
    for i in range(3):
        start_timer(f"task_{i}")
        time.sleep(0.05)  # 模拟工作
        duration = end_timer(f"task_{i}")
        record_metric(f"task_{i}_result", i * 10 + 5, "units")
        print(f"任务 {i} 完成，耗时: {duration:.3f}秒")
    
    # 等待收集
    time.sleep(1.5)
    
    # 获取性能统计
    perf_collector = manager.get_performance_collector()
    if perf_collector:
        print("\n性能统计:")
        for i in range(3):
            stats = perf_collector.get_metric_stats(f"timer_task_{i}")
            if stats:
                print(f"  任务 {i}: {stats}")
    
    manager.close()
    print("✅ 性能监控测试完成")

def main():
    """主测试函数"""
    print("🚀 开始调试系统测试")
    
    try:
        test_basic_logging()
        test_data_collection()
        test_performance_monitoring()
        
        print("\n🎉 所有测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())