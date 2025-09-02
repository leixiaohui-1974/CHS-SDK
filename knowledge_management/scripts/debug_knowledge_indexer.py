#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试知识索引器
"""

import asyncio
import json
from pathlib import Path
from core_lib.knowledge.knowledge_indexer import KnowledgeIndexer
from core_lib.knowledge.semantic_search import SemanticSearchEngine

async def debug_knowledge_indexer():
    """调试知识索引器"""
    
    # 初始化语义搜索引擎
    kb_path = Path("knowledge_base")
    config = {
        "enabled": True,
        "model_name": "all-MiniLM-L6-v2",
        "top_k": 10
    }
    
    search_engine = SemanticSearchEngine(kb_path, config)
    await search_engine.initialize()
    
    # 初始化知识索引器
    project_root = Path(".")
    indexer_config = {
        "enabled": True,
        "supported_file_types": [".py", ".yml", ".yaml", ".md", ".txt"],
        "exclude_dirs": ["__pycache__", ".git", "node_modules", "venv", "env", ".venv"]
    }
    
    indexer = KnowledgeIndexer(project_root, indexer_config, search_engine)
    
    print("🔧 开始知识索引器调试...")
    
    # 强制重建索引
    print("\n📝 强制重建索引...")
    success = await indexer.build_index(force_rebuild=True)
    print(f"构建结果: {success}")
    
    # 检查索引器统计信息
    indexer_stats = indexer.get_statistics()
    print(f"\n📊 索引器统计信息:")
    print(f"  项目根目录: {indexer_stats['project_root']}")
    print(f"  支持的文件类型: {indexer_stats['supported_file_types']}")
    print(f"  跟踪的文件数: {indexer_stats['tracked_files']}")
    print(f"  最后扫描时间: {indexer_stats['last_scan_time']}")
    
    # 检查语义搜索引擎统计信息
    search_stats = search_engine.get_statistics()
    print(f"\n🔍 语义搜索引擎统计信息:")
    print(f"  文档数量: {search_stats.get('total_documents', 0)}")
    print(f"  索引大小: {search_stats.get('index_size_mb', 0):.2f} MB")
    
    # 检查documents.json文件
    documents_file = kb_path / "documents.json"
    if documents_file.exists():
        with open(documents_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"\n📄 documents.json 内容:")
        print(f"  文档数量: {data.get('total_documents', 0)}")
        print(f"  最后更新: {data.get('last_updated', 'Unknown')}")
        print(f"  实际文档列表长度: {len(data.get('documents', []))}")
        
        # 显示前几个文档的标题
        documents = data.get('documents', [])
        if documents:
            print(f"\n📋 前5个文档标题:")
            for i, doc in enumerate(documents[:5]):
                if isinstance(doc, dict):
                    metadata = doc.get('metadata', {})
                    title = metadata.get('title', 'Unknown')
                    doc_type = metadata.get('doc_type', 'Unknown')
                    print(f"  {i+1}. {title} ({doc_type})")
                else:
                    print(f"  {i+1}. 文档格式错误: {type(doc)}")
                    if i == 0:  # 只显示第一个错误文档的内容
                        print(f"      内容: {str(doc)[:100]}...")
    else:
        print("\n❌ documents.json 文件不存在")
    
    # 测试搜索
    print("\n🔍 测试搜索功能...")
    test_queries = [
        "智能体",
        "agent",
        "configuration",
        "scenario"
    ]
    
    for query in test_queries:
        results = await search_engine.search(query, search_type="semantic", top_k=3)
        print(f"  查询 '{query}': 找到 {len(results)} 个结果")
        for i, result in enumerate(results[:2]):
            metadata = result.get('metadata', {})
            title = metadata.get('title', 'Unknown')
            score = result.get('score', 0)
            print(f"    {i+1}. {title} (分数: {score:.3f})")
    
    # 清理
    await search_engine.cleanup()
    await indexer.cleanup()
    print("\n✅ 调试完成")

if __name__ == "__main__":
    asyncio.run(debug_knowledge_indexer())