#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重建后的知识库是否能正确搜索智能体信息
"""

import asyncio
from pathlib import Path
from core_lib.knowledge.knowledge_base import KnowledgeBase

async def test_agent_search():
    """测试智能体搜索功能"""
    print("🔍 测试重建后的知识库智能体搜索功能")
    print("=" * 60)
    
    # 初始化知识库
    project_root = Path.cwd()
    kb = KnowledgeBase(str(project_root))
    await kb.initialize()
    
    try:
        # 测试查询列表
        test_queries = [
            "水库有哪些智能体？",
            "智能体",
            "agent",
            "水库控制",
            "HydropowerStationAgent",
            "ReservoirPerceptionAgent",
            "pump control",
            "gate control"
        ]
        
        for query in test_queries:
            print(f"\n🔍 搜索查询: '{query}'")
            print("-" * 40)
            
            # 语义搜索
            results = await kb.search(query, search_type="semantic", top_k=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    metadata = result.get('metadata', {})
                    title = metadata.get('title', 'N/A')
                    doc_type = metadata.get('doc_type', 'N/A')
                    file_path = metadata.get('file_path', 'N/A')
                    score = result.get('score', 0)
                    
                    print(f"  {i}. {title}")
                    print(f"     类型: {doc_type}")
                    print(f"     文件: {Path(file_path).name if file_path != 'N/A' else 'N/A'}")
                    print(f"     相关度: {score:.3f}")
                    
                    # 显示内容预览
                    content = result.get('content', '')
                    preview = content[:100] + '...' if len(content) > 100 else content
                    print(f"     预览: {preview}")
                    print()
            else:
                print(f"  ❌ 未找到与'{query}'相关的结果")
        
        # 获取知识库统计信息
        print("\n📊 知识库统计信息:")
        print("=" * 40)
        stats = kb.get_statistics()
        print(f"总文档数: {stats.get('total_documents', 'N/A')}")
        print(f"文档类型分布: {stats.get('document_types', {})}")
        print(f"文件类型分布: {stats.get('file_types', {})}")
        
    finally:
        await kb.cleanup()
        print("\n✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(test_agent_search())