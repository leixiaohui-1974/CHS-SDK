#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强制重建知识库索引
解决搜索效果不佳的问题
"""

import asyncio
import logging
from pathlib import Path
import sys
import os

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.knowledge.knowledge_base import KnowledgeBase
from core_lib.knowledge.knowledge_indexer import KnowledgeIndexer
from core_lib.knowledge.semantic_search import SemanticSearchEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ForceRebuild')

async def force_rebuild_knowledge_base():
    """
    强制重建知识库索引
    """
    try:
        logger.info("开始强制重建知识库索引...")
        
        # 删除现有索引文件
        kb_path = project_root / "knowledge_base"
        index_files = [
            kb_path / "vector_index.faiss",
            kb_path / "documents.json", 
            kb_path / "search_metadata.json",
            kb_path / "index_metadata.json"
        ]
        
        for index_file in index_files:
            if index_file.exists():
                index_file.unlink()
                logger.info(f"删除索引文件: {index_file}")
        
        # 初始化知识库（强制重建）
        kb = KnowledgeBase(project_root=project_root)
        success = await kb.initialize(force_rebuild=True)
        
        if success:
            logger.info("知识库重建成功！")
            
            # 检查重建后的状态
            stats = kb.get_statistics()
            logger.info(f"知识库统计信息: {stats}")
            
            # 测试搜索功能
            logger.info("\n=== 测试搜索功能 ===")
            test_queries = [
                "智能体架构",
                "agent", 
                "水系统控制",
                "configuration",
                "洪水控制"
            ]
            
            for query in test_queries:
                logger.info(f"\n搜索查询: '{query}'")
                
                # 语义搜索
                semantic_results = await kb.search(query, search_type="semantic", top_k=3)
                logger.info(f"语义搜索结果数: {len(semantic_results)}")
                
                # 关键词搜索
                keyword_results = await kb.search(query, search_type="keyword", top_k=3)
                logger.info(f"关键词搜索结果数: {len(keyword_results)}")
                
                # 混合搜索
                hybrid_results = await kb.search(query, search_type="hybrid", top_k=3)
                logger.info(f"混合搜索结果数: {len(hybrid_results)}")
                
                # 显示第一个结果的详细信息
                if hybrid_results:
                    result = hybrid_results[0]
                    logger.info(f"最佳匹配: {result.get('title', 'N/A')} (分数: {result.get('score', 0):.3f})")
                    logger.info(f"内容预览: {result.get('content', '')[:100]}...")
        
        else:
            logger.error("知识库重建失败！")
            
        # 清理资源
        await kb.cleanup()
        
    except Exception as e:
        logger.error(f"重建过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(force_rebuild_knowledge_base())