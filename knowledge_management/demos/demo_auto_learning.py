#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 自动学习系统演示脚本
展示如何在实际项目中使用自动学习功能
"""

import sys
import time
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.knowledge.auto_learning import create_auto_learning_system

async def demo_auto_learning():
    """演示自动学习系统的功能"""
    print("=== CHS-SDK 自动学习系统演示 ===")
    print("这个演示将展示自动学习系统如何实时监控项目文件变化")
    print("并自动更新知识库索引\n")
    
    try:
        # 1. 创建自动学习系统
        print("1. 初始化自动学习系统...")
        auto_learner = create_auto_learning_system(
            project_root=str(project_root),
            knowledge_base_config="core_lib/knowledge/auto_learning_config.yml"
        )
        print("✓ 自动学习系统初始化完成")
        
        # 2. 启动文件监控
        print("\n2. 启动实时文件监控...")
        auto_learner.start_monitoring()
        print("✓ 文件监控已启动，正在监控项目文件变化")
        
        # 3. 显示初始状态
        print("\n3. 当前系统状态:")
        stats = auto_learner.get_learning_stats()
        print(f"   - 已处理文件: {stats.files_processed}")
        print(f"   - 已索引文件: {stats.files_indexed}")
        print(f"   - 失败文件: {stats.files_failed}")
        
        # 4. 创建一个测试文件来演示实时学习
        print("\n4. 创建测试文件演示实时学习...")
        test_file = project_root / "demo_test_agent.py"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('''
# -*- coding: utf-8 -*-
"""
演示智能体类
这是一个用于演示自动学习功能的测试智能体
"""

class DemoAgent:
    """
    演示智能体
    
    这个智能体用于展示CHS-SDK的自动学习功能
    当文件被创建或修改时，系统会自动检测并更新知识库
    """
    
    def __init__(self, name: str, config: dict):
        """
        初始化演示智能体
        
        Args:
            name: 智能体名称
            config: 配置参数
        """
        self.name = name
        self.config = config
        self.status = "initialized"
    
    def start(self):
        """启动智能体"""
        self.status = "running"
        print(f"演示智能体 {self.name} 已启动")
    
    def stop(self):
        """停止智能体"""
        self.status = "stopped"
        print(f"演示智能体 {self.name} 已停止")
    
    def process_data(self, data):
        """
        处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据
        """
        # 简单的数据处理逻辑
        return f"Processed: {data}"
''')
        
        print(f"✓ 创建测试文件: {test_file.name}")
        
        # 5. 等待文件被检测和处理
        print("\n5. 等待自动学习系统检测文件变化...")
        for i in range(10):
            await asyncio.sleep(1)
            stats = auto_learner.get_learning_stats()
            print(f"   [{i+1}s] 处理: {stats.files_processed}, 索引: {stats.files_indexed}, 失败: {stats.files_failed}")
            
            # 检查是否检测到新文件
            if stats.files_processed > 60:  # 之前测试显示有60个文件
                print("✓ 检测到新文件并已处理")
                break
        
        # 6. 修改文件演示增量更新
        print("\n6. 修改测试文件演示增量更新...")
        with open(test_file, 'a', encoding='utf-8') as f:
            f.write('''
    
    def get_status(self):
        """
        获取智能体状态
        
        Returns:
            str: 当前状态
        """
        return self.status
    
    def update_config(self, new_config: dict):
        """
        更新配置
        
        Args:
            new_config: 新的配置参数
        """
        self.config.update(new_config)
        print(f"智能体 {self.name} 配置已更新")
''')
        
        print("✓ 文件已修改，等待系统检测...")
        
        # 7. 等待修改被检测
        for i in range(5):
            await asyncio.sleep(1)
            stats = auto_learner.get_learning_stats()
            print(f"   [{i+1}s] 处理: {stats.files_processed}, 索引: {stats.files_indexed}, 失败: {stats.files_failed}")
        
        # 8. 清理测试文件
        print("\n8. 清理测试文件...")
        test_file.unlink()
        print("✓ 测试文件已删除")
        
        # 9. 停止监控
        print("\n9. 停止自动学习系统...")
        auto_learner.stop_monitoring()
        print("✓ 自动学习系统已停止")
        
        # 10. 最终统计
        print("\n10. 最终统计信息:")
        stats = auto_learner.get_learning_stats()
        print(f"    - 总处理文件: {stats.files_processed}")
        print(f"    - 总索引文件: {stats.files_indexed}")
        print(f"    - 总失败文件: {stats.files_failed}")
        
        print("\n=== 演示完成 ===")
        print("\n自动学习系统功能总结:")
        print("✓ 实时监控项目文件变化")
        print("✓ 自动检测新增、修改、删除的文件")
        print("✓ 智能提取代码结构和文档信息")
        print("✓ 增量更新知识库索引")
        print("✓ 支持多种文件类型 (.py, .yml, .md, .txt)")
        print("✓ 提供详细的处理统计信息")
        
        return True
        
    except Exception as e:
        print(f"✗ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(demo_auto_learning())
    sys.exit(0 if success else 1)