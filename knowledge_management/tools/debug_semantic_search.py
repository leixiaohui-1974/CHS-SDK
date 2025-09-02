#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试语义搜索引擎
"""

import asyncio
import json
from pathlib import Path
from core_lib.knowledge.semantic_search import SemanticSearchEngine

async def debug_semantic_search():
    """调试语义搜索引擎"""
    
    # 初始化语义搜索引擎
    kb_path = Path("knowledge_base")
    config = {
        "enabled": True,
        "model_name": "all-MiniLM-L6-v2",
        "top_k": 10
    }
    
    search_engine = SemanticSearchEngine(kb_path, config)
    
    print("🔧 初始化语义搜索引擎...")
    success = await search_engine.initialize()
    print(f"初始化结果: {success}")
    
    # 测试添加文档
    test_docs = [
        {
            "content": "这是一个水利工程智能体的示例文档，用于控制水库的水位和流量。",
            "title": "水利工程智能体",
            "doc_type": "agent",
            "file_path": "test/agent1.py",
            "tags": ["水利", "智能体", "控制"]
        },
        {
            "content": "Scenario configuration for distributed simulation systems with multi-agent coordination.",
            "title": "Scenario Configuration",
            "doc_type": "config",
            "file_path": "test/config.yaml",
            "tags": ["scenario", "configuration", "simulation"]
        },
        {
            "content": "Agent definition includes parameters, behaviors, and communication protocols.",
            "title": "Agent Definition",
            "doc_type": "documentation",
            "file_path": "test/agent_def.md",
            "tags": ["agent", "definition", "protocol"]
        }
    ]
    
    print(f"\n📝 添加 {len(test_docs)} 个测试文档...")
    add_success = await search_engine.add_documents(test_docs)
    print(f"添加结果: {add_success}")
    
    # 检查统计信息
    stats = search_engine.get_statistics()
    print(f"\n📊 统计信息:")
    print(f"  文档数量: {stats.get('total_documents', 0)}")
    print(f"  索引大小: {stats.get('index_size_mb', 0):.2f} MB")
    
    # 检查documents.json文件
    documents_file = kb_path / "documents.json"
    if documents_file.exists():
        with open(documents_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"\n📄 documents.json 内容:")
        print(f"  文档数量: {data.get('total_documents', 0)}")
        print(f"  最后更新: {data.get('last_updated', 'Unknown')}")
        print(f"  实际文档列表长度: {len(data.get('documents', []))}")
    else:
        print("\n❌ documents.json 文件不存在")
    
    # 测试搜索
    print("\n🔍 测试搜索功能...")
    test_queries = [
        "水利工程智能体",
        "scenario configuration",
        "agent definition"
    ]
    
    for query in test_queries:
        results = await search_engine.search(query, search_type="semantic", top_k=3)
        print(f"  查询 '{query}': 找到 {len(results)} 个结果")
        for i, result in enumerate(results[:2]):
            print(f"    {i+1}. {result.get('metadata', {}).get('title', 'Unknown')} (分数: {result.get('score', 0):.3f})")
    
    # 清理
    await search_engine.cleanup()
    print("\n✅ 调试完成")

if __name__ == "__main__":
    asyncio.run(debug_semantic_search())