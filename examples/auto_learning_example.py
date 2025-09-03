#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 自动学习系统使用示例

该示例展示了如何使用CHS-SDK的自动学习功能来监控项目代码变更并自动更新知识库。
"""

import os
import sys
import time
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core_lib.knowledge.knowledge_base import KnowledgeBase
from core_lib.knowledge.auto_learning import create_auto_learning_system


async def basic_auto_learning_example():
    """
    基础自动学习示例
    """
    print("=== CHS-SDK 自动学习系统基础示例 ===")
    
    # 创建知识库实例（启用自动学习）
    kb = KnowledgeBase(
        project_root=str(project_root)
    )
    
    try:
        # 初始化知识库
        await kb.initialize()
        print("✓ 知识库初始化完成")
        
        # 检查自动学习状态
        if kb.auto_learner:
            print("✓ 自动学习系统已启动")
            
            # 获取学习统计信息
            stats = kb.auto_learner.get_learning_stats()
            print(f"  - 监控文件数: {stats.total_files_monitored}")
            print(f"  - 已处理文件: {stats.files_processed}")
            print(f"  - 已索引文件: {stats.files_indexed}")
            
            # 模拟运行一段时间
            print("\n正在监控文件变更（运行30秒）...")
            for i in range(30):
                await asyncio.sleep(1)
                if i % 10 == 9:
                    stats = kb.auto_learner.get_learning_stats()
                    print(f"  状态更新 - 已处理: {stats.files_processed} 个文件")
        else:
            print("⚠ 自动学习系统未启用")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        # 清理资源
        await kb.cleanup()
        print("✓ 资源清理完成")


async def advanced_auto_learning_example():
    """
    高级自动学习示例
    """
    print("\n=== CHS-SDK 自动学习系统高级示例 ===")
    
    # 直接创建自动学习系统
    auto_learner = create_auto_learning_system(
        project_root=str(project_root)
    )
    
    try:
        # 启动自动学习
        auto_learner.start_monitoring()
        print("✓ 自动学习系统启动")
        
        # 执行Git同步
        print("\n正在同步Git变更...")
        auto_learner.sync_with_git()
        
        # 获取Git变更文件列表
        changed_files = auto_learner.get_git_changes()
        if changed_files:
            print(f"发现 {len(changed_files)} 个Git变更文件:")
            for file_path in changed_files[:5]:  # 只显示前5个
                print(f"  - {file_path}")
            if len(changed_files) > 5:
                print(f"  ... 还有 {len(changed_files) - 5} 个文件")
        else:
            print("未发现Git变更文件")
        
        # 强制重建索引（演示用）
        print("\n正在强制重建知识库索引...")
        auto_learner.force_rebuild_index()
        print("✓ 索引重建完成")
        
        # 监控一段时间
        print("\n正在监控文件变更（运行20秒）...")
        for i in range(20):
            await asyncio.sleep(1)
            if i % 5 == 4:
                stats = auto_learner.get_learning_stats()
                print(f"  统计信息 - 处理: {stats.files_processed}, 索引: {stats.files_indexed}, 失败: {stats.files_failed}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        # 停止自动学习
        auto_learner.stop_monitoring()
        print("✓ 自动学习系统已停止")


def manual_file_change_example():
    """
    手动文件变更示例
    """
    print("\n=== 手动文件变更示例 ===")
    
    # 创建测试文件
    test_file = project_root / "temp_test_file.py"
    
    try:
        # 创建自动学习系统
        auto_learner = create_auto_learning_system(str(project_root))
        auto_learner.start_monitoring()
        
        print("✓ 自动学习系统启动")
        
        # 创建测试文件
        print("\n创建测试文件...")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""
#!/usr/bin/env python3
# 这是一个测试文件，用于演示自动学习功能

class TestAgent:
    \"\"\"测试智能体\"\"\"
    
    def __init__(self):
        self.name = "TestAgent"
    
    def process(self, data):
        \"\"\"处理数据\"\"\"
        return f"Processed: {data}"
""")
        
        print(f"✓ 创建文件: {test_file}")
        
        # 等待文件被处理
        time.sleep(3)
        
        # 修改测试文件
        print("\n修改测试文件...")
        with open(test_file, 'a', encoding='utf-8') as f:
            f.write("""
    
    def analyze(self, data):
        \"\"\"分析数据\"\"\"
        return f"Analyzed: {data}"
""")
        
        print("✓ 修改文件内容")
        
        # 等待文件被处理
        time.sleep(3)
        
        # 获取统计信息
        stats = auto_learner.get_learning_stats()
        print(f"\n统计信息:")
        print(f"  - 已处理文件: {stats.files_processed}")
        print(f"  - 已索引文件: {stats.files_indexed}")
        print(f"  - 失败文件数: {stats.files_failed}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        # 清理
        auto_learner.stop_monitoring()
        
        # 删除测试文件
        if test_file.exists():
            test_file.unlink()
            print(f"✓ 删除测试文件: {test_file}")
        
        print("✓ 清理完成")


def configuration_example():
    """
    配置示例
    """
    print("\n=== 自动学习配置示例 ===")
    
    # 自定义配置
    custom_config = {
        'monitor_patterns': ['*.py', '*.yml'],
        'ignore_patterns': ['__pycache__', '.git'],
        'batch_size': 5,
        'processing_interval': 3.0,
        'debounce_time': 1.0,
        'max_workers': 2,
        'enable_git_integration': True,
        'learning_threshold': 0.05
    }
    
    print("自定义配置:")
    for key, value in custom_config.items():
        print(f"  {key}: {value}")
    
    try:
        # 使用自定义配置创建自动学习系统
        from core_lib.knowledge.auto_learning import AutoLearningSystem
        from core_lib.knowledge.knowledge_indexer import KnowledgeIndexer
        from core_lib.knowledge.semantic_search import SemanticSearchEngine
        from core_lib.knowledge.recommendation_engine import RecommendationEngine
        
        # 创建组件
        indexer = KnowledgeIndexer(str(project_root))
        search_engine = SemanticSearchEngine()
        recommendation_engine = RecommendationEngine()
        
        # 创建自动学习系统
        auto_learner = AutoLearningSystem(
            project_root=str(project_root),
            knowledge_indexer=indexer,
            semantic_search=search_engine,
            recommendation_engine=recommendation_engine
        )
        
        # 应用自定义配置
        auto_learner.config.update(custom_config)
        
        print("\n✓ 使用自定义配置创建自动学习系统")
        
        # 启动并运行一段时间
        auto_learner.start_monitoring()
        print("✓ 自动学习系统启动")
        
        time.sleep(5)
        
        stats = auto_learner.get_learning_stats()
        print(f"\n运行结果:")
        print(f"  - 监控文件数: {stats.total_files_monitored}")
        print(f"  - 已处理文件: {stats.files_processed}")
        
        auto_learner.stop_monitoring()
        print("✓ 自动学习系统已停止")
        
    except Exception as e:
        print(f"❌ 错误: {e}")


async def main():
    """
    主函数
    """
    print("CHS-SDK 自动学习系统示例")
    print("=" * 50)
    
    try:
        # 基础示例
        await basic_auto_learning_example()
        
        # 高级示例
        await advanced_auto_learning_example()
        
        # 手动文件变更示例
        manual_file_change_example()
        
        # 配置示例
        configuration_example()
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"\n运行示例时发生错误: {e}")
    
    print("\n=== 示例运行完成 ===")


if __name__ == '__main__':
    # 检查依赖
    try:
        import watchdog
        import git
    except ImportError as e:
        print(f"缺少依赖: {e}")
        print("请安装依赖: pip install watchdog gitpython")
        sys.exit(1)
    
    # 运行示例
    asyncio.run(main())