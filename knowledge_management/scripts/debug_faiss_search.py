#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试FAISS搜索问题
检查向量索引和搜索结果
"""

import asyncio
import logging
import numpy as np
from pathlib import Path
import sys
import json

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.knowledge.knowledge_base import KnowledgeBase

async def debug_faiss_search():
    """
    调试FAISS搜索问题
    """
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("FAISSDebug")
    
    try:
        logger.info("开始调试FAISS搜索问题...")
        
        kb_path = project_root / "knowledge_base"
        kb = KnowledgeBase(kb_path)
        await kb.initialize()
        
        # 1. 检查知识库基本状态
        logger.info("\n=== 知识库状态检查 ===")
        stats = kb.get_statistics()
        logger.info(f"知识库已初始化: {stats.get('is_initialized', False)}")
        logger.info(f"总文档数: {stats.get('total_documents', 0)}")
        
        # 2. 检查语义搜索引擎
        if hasattr(kb.search_engine, 'semantic_search') and kb.search_engine.semantic_search:
            semantic_engine = kb.search_engine.semantic_search
            logger.info("\n=== 语义搜索引擎状态 ===")
            logger.info(f"引擎已初始化: {semantic_engine.is_initialized}")
            logger.info(f"文档数量: {len(semantic_engine.documents)}")
            logger.info(f"元数据数量: {len(semantic_engine.metadata)}")
            
            if semantic_engine.index:
                logger.info(f"FAISS索引类型: {type(semantic_engine.index).__name__}")
                logger.info(f"索引中的向量数量: {semantic_engine.index.ntotal}")
                logger.info(f"向量维度: {semantic_engine.index.d}")
            else:
                logger.warning("FAISS索引未初始化")
            
            # 3. 检查文档内容样本
            logger.info("\n=== 文档内容样本 ===")
            for i, doc in enumerate(semantic_engine.documents[:5]):
                if isinstance(doc, dict):
                    content = doc.get('content', '')[:100]
                    title = doc.get('title', 'N/A')
                else:
                    content = str(doc)[:100]
                    title = 'N/A'
                
                metadata = semantic_engine.metadata[i] if i < len(semantic_engine.metadata) else {}
                doc_type = metadata.get('doc_type', 'N/A')
                
                logger.info(f"文档 {i+1}:")
                logger.info(f"  标题: {title}")
                logger.info(f"  类型: {doc_type}")
                logger.info(f"  内容: {content}...")
            
            # 4. 直接测试FAISS搜索
            logger.info("\n=== 直接FAISS搜索测试 ===")
            
            if semantic_engine.model and semantic_engine.index:
                test_queries = ["agent", "智能体", "configuration", "water"]
                
                for query in test_queries:
                    logger.info(f"\n测试查询: '{query}'")
                    
                    # 生成查询向量
                    query_embedding = semantic_engine.model.encode([query], convert_to_numpy=True)
                    query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
                    
                    # 直接搜索FAISS索引
                    k = min(10, semantic_engine.index.ntotal)
                    if k > 0:
                        scores, indices = semantic_engine.index.search(query_embedding.astype(np.float32), k)
                        
                        logger.info(f"  FAISS返回 {len(scores[0])} 个结果")
                        logger.info(f"  分数范围: {scores[0].min():.6f} ~ {scores[0].max():.6f}")
                        
                        # 显示前5个结果
                        for i, (score, idx) in enumerate(zip(scores[0][:5], indices[0][:5])):
                            if idx < len(semantic_engine.documents):
                                doc = semantic_engine.documents[idx]
                                if isinstance(doc, dict):
                                    title = doc.get('title', 'N/A')
                                    content = doc.get('content', '')[:50]
                                else:
                                    title = 'N/A'
                                    content = str(doc)[:50]
                                
                                logger.info(f"    {i+1}. 分数: {score:.6f}, 索引: {idx}")
                                logger.info(f"       标题: {title}")
                                logger.info(f"       内容: {content}...")
                    else:
                        logger.warning("  索引为空")
            
            # 5. 测试不同的搜索方法
            logger.info("\n=== 搜索方法对比测试 ===")
            
            test_query = "agent"
            
            # 语义搜索
            try:
                semantic_results = await semantic_engine._semantic_search(test_query, None, 5)
                logger.info(f"语义搜索结果: {len(semantic_results)} 个")
                for i, result in enumerate(semantic_results[:3]):
                    score = result.get('score', 0)
                    content = result.get('content', '')[:50]
                    logger.info(f"  {i+1}. 分数: {score:.6f}, 内容: {content}...")
            except Exception as e:
                logger.error(f"语义搜索失败: {str(e)}")
            
            # 关键词搜索
            try:
                keyword_results = await semantic_engine._keyword_search(test_query, None, 5)
                logger.info(f"关键词搜索结果: {len(keyword_results)} 个")
                for i, result in enumerate(keyword_results[:3]):
                    score = result.get('score', 0)
                    content = result.get('content', '')[:50]
                    logger.info(f"  {i+1}. 分数: {score:.6f}, 内容: {content}...")
            except Exception as e:
                logger.error(f"关键词搜索失败: {str(e)}")
            
            # 6. 检查文档格式
            logger.info("\n=== 文档格式检查 ===")
            
            # 检查documents.json文件
            documents_file = kb_path / "documents.json"
            if documents_file.exists():
                with open(documents_file, 'r', encoding='utf-8') as f:
                    docs_data = json.load(f)
                
                logger.info(f"documents.json文件大小: {documents_file.stat().st_size} 字节")
                logger.info(f"文档数据类型: {type(docs_data)}")
                
                if isinstance(docs_data, list) and len(docs_data) > 0:
                    logger.info(f"文档列表长度: {len(docs_data)}")
                    logger.info(f"第一个文档类型: {type(docs_data[0])}")
                    
                    if isinstance(docs_data[0], dict):
                        logger.info(f"第一个文档键: {list(docs_data[0].keys())}")
                        content = docs_data[0].get('content', '')
                        logger.info(f"第一个文档内容长度: {len(content)}")
                        logger.info(f"第一个文档内容预览: {content[:100]}...")
                else:
                    logger.warning("文档数据格式异常")
            else:
                logger.warning("documents.json文件不存在")
        
        await kb.cleanup()
        
        logger.info("\n✅ FAISS搜索调试完成")
        
    except Exception as e:
        logger.error(f"调试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_faiss_search())