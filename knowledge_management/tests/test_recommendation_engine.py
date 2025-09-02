#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试推荐引擎功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.knowledge.knowledge_base import KnowledgeBase

async def test_recommendation_engine():
    """测试推荐引擎功能"""
    print("🔍 测试推荐引擎功能")
    print("=" * 50)
    
    # 初始化知识库
    kb = KnowledgeBase(str(project_root))
    await kb.initialize()
    
    try:
        # 获取知识库统计信息
        stats = kb.get_statistics()
        print(f"\n📊 知识库统计:")
        print(f"  - 初始化状态: {stats.get('is_initialized', False)}")
        print(f"  - 项目根目录: {stats.get('project_root', 'N/A')}")
        
        # 检查推荐引擎状态
        rec_stats = stats.get('recommendation_engine', {})
        print(f"\n🤖 推荐引擎状态:")
        print(f"  - 初始化状态: {rec_stats.get('is_initialized', False)}")
        print(f"  - 用户历史数量: {rec_stats.get('user_history_count', 0)}")
        print(f"  - 文档向量数量: {rec_stats.get('document_vectors_count', 0)}")
        
        # 测试不同类型的推荐
        test_contexts = [
            {
                "context": {"query": "智能体开发", "current_file": "agent.py"},
                "type": "agent",
                "description": "智能体开发推荐"
            },
            {
                "context": {"query": "配置文件", "current_file": "config.yml"},
                "type": "config",
                "description": "配置文件推荐"
            },
            {
                "context": {"query": "模板", "current_file": "template.yml"},
                "type": "template",
                "description": "模板推荐"
            }
        ]
        
        for test in test_contexts:
            print(f"\n🎯 {test['description']}:")
            print(f"  上下文: {test['context']}")
            
            try:
                recommendations = await kb.get_recommendations(
                    context=test['context'],
                    recommendation_type=test['type']
                )
                
                if recommendations:
                    print(f"  找到 {len(recommendations)} 个推荐:")
                    for i, rec in enumerate(recommendations[:3], 1):
                        metadata = rec.get('metadata', {})
                        title = metadata.get('title', '') or Path(metadata.get('file_path', '')).stem or 'N/A'
                        score = rec.get('score', 0)
                        file_path = metadata.get('file_path', 'N/A')
                        print(f"    {i}. {title} (相关度: {score:.3f})")
                        print(f"       文件: {Path(file_path).name if file_path != 'N/A' else 'N/A'}")
                else:
                    print("  ❌ 未找到推荐结果")
                    
            except Exception as e:
                print(f"  ❌ 推荐失败: {str(e)}")
        
        # 测试添加用户历史记录
        print(f"\n📝 测试添加用户历史记录:")
        try:
            # 模拟用户搜索历史
            search_results = await kb.search("智能体", search_type="semantic", top_k=3)
            if search_results:
                print(f"  搜索到 {len(search_results)} 个结果")
                
                # 再次测试推荐
                print(f"\n🔄 重新测试推荐功能:")
                recommendations = await kb.get_recommendations(
                    context={"query": "智能体开发", "current_file": "agent.py"},
                    recommendation_type="agent"
                )
                
                if recommendations:
                    print(f"  找到 {len(recommendations)} 个推荐")
                else:
                    print(f"  仍然没有推荐结果")
            
        except Exception as e:
            print(f"  ❌ 测试失败: {str(e)}")
        
    finally:
        await kb.cleanup()
        print(f"\n🧹 测试完成，资源已清理")

if __name__ == "__main__":
    asyncio.run(test_recommendation_engine())