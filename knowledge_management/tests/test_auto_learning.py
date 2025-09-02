#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 自动学习系统测试脚本
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.knowledge.auto_learning import create_auto_learning_system

def test_auto_learning():
    """测试自动学习系统"""
    print("=== CHS-SDK 自动学习系统测试 ===")
    
    try:
        # 创建自动学习系统
        print("1. 创建自动学习系统...")
        auto_learner = create_auto_learning_system(
            project_root=str(project_root),
            knowledge_base_config="core_lib/knowledge/auto_learning_config.yml"
        )
        print("✓ 自动学习系统创建成功")
        
        # 启动监控
        print("\n2. 启动文件监控...")
        auto_learner.start_monitoring()
        print("✓ 文件监控启动成功")
        
        # 获取初始状态
        print("\n3. 获取系统状态...")
        stats = auto_learner.get_learning_stats()
        print(f"✓ 已处理文件: {stats.files_processed}")
        print(f"✓ 已索引文件: {stats.files_indexed}")
        print(f"✓ 失败文件: {stats.files_failed}")
        
        # 运行一段时间
        print("\n4. 运行监控 30 秒...")
        for i in range(6):
            time.sleep(5)
            stats = auto_learner.get_learning_stats()
            print(f"[{i*5+5}s] 处理: {stats.files_processed}, 索引: {stats.files_indexed}, 失败: {stats.files_failed}")
        
        # 停止监控
        print("\n5. 停止监控...")
        auto_learner.stop_monitoring()
        print("✓ 监控已停止")
        
        # 最终状态
        print("\n6. 最终状态:")
        stats = auto_learner.get_learning_stats()
        print(f"✓ 总处理文件: {stats.files_processed}")
        print(f"✓ 总索引文件: {stats.files_indexed}")
        print(f"✓ 总失败文件: {stats.files_failed}")
        
        print("\n=== 测试完成 ===")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_auto_learning()
    sys.exit(0 if success else 1)