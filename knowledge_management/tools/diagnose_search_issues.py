#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索效果诊断脚本
分析知识库搜索效果不佳的原因
"""

import asyncio
import logging
import json
from pathlib import Path
import sys
import numpy as np
from typing import Dict, List, Any

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.knowledge.knowledge_base import KnowledgeBase

async def diagnose_search_issues():
    """
    诊断搜索效果问题
    """
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("SearchDiagnosis")
    
    try:
        logger.info("开始搜索效果诊断...")
        
        # 知识库路径
        kb_path = project_root / "knowledge_base"
        
        # 创建知识库实例
        kb = KnowledgeBase(kb_path)
        
        # 初始化知识库
        logger.info("初始化知识库...")
        await kb.initialize()
        
        # 1. 检查知识库基本状态
        logger.info("\n=== 知识库状态检查 ===")
        stats = kb.get_statistics()
        logger.info(f"知识库是否已初始化: {stats.get('is_initialized', False)}")
        logger.info(f"总文档数: {stats.get('total_documents', 0)}")
        logger.info(f"文档类型分布: {stats.get('document_types', {})}")
        logger.info(f"文件类型分布: {stats.get('file_types', {})}")
        
        # 2. 检查向量索引状态
        logger.info("\n=== 向量索引状态检查 ===")
        if hasattr(kb.search_engine, 'semantic_search') and kb.search_engine.semantic_search:
            semantic_engine = kb.search_engine.semantic_search
            if hasattr(semantic_engine, 'vector_index') and semantic_engine.vector_index:
                index = semantic_engine.vector_index
                logger.info(f"向量索引类型: {type(index).__name__}")
                if hasattr(index, 'ntotal'):
                    logger.info(f"索引中的向量数量: {index.ntotal}")
                if hasattr(index, 'd'):
                    logger.info(f"向量维度: {index.d}")
            else:
                logger.warning("向量索引未初始化")
        else:
            logger.warning("语义搜索引擎未初始化")
        
        # 3. 测试不同类型的搜索查询
        logger.info("\n=== 搜索测试 ===")
        
        test_queries = [
            ("agent", "keyword", "简单关键词搜索"),
            ("水利仿真", "semantic", "中文语义搜索"),
            ("water simulation", "semantic", "英文语义搜索"),
            ("class", "keyword", "代码相关搜索"),
            ("configuration", "keyword", "配置相关搜索"),
            ("FloodControlAgent", "keyword", "具体智能体搜索"),
            ("如何配置智能体", "semantic", "自然语言问题"),
            ("agent configuration", "hybrid", "混合搜索测试")
        ]
        
        for query, search_type, description in test_queries:
            logger.info(f"\n--- {description} ---")
            logger.info(f"查询: '{query}' (类型: {search_type})")
            
            try:
                results = await kb.search(query, search_type=search_type, top_k=5)
                logger.info(f"结果数量: {len(results)}")
                
                if results:
                    logger.info("前3个结果:")
                    for i, result in enumerate(results[:3], 1):
                        title = result.get('title', 'N/A')
                        score = result.get('score', 0)
                        doc_type = result.get('doc_type', 'N/A')
                        file_path = result.get('file_path', 'N/A')
                        content_preview = result.get('content', '')[:100] + '...' if result.get('content') else 'N/A'
                        
                        logger.info(f"  {i}. {title}")
                        logger.info(f"     类型: {doc_type}, 评分: {score:.3f}")
                        logger.info(f"     文件: {Path(file_path).name if file_path != 'N/A' else 'N/A'}")
                        logger.info(f"     内容: {content_preview}")
                else:
                    logger.warning("  没有找到结果")
                    
            except Exception as e:
                logger.error(f"  搜索失败: {str(e)}")
        
        # 4. 检查特定文档类型的搜索
        logger.info("\n=== 按文档类型搜索测试 ===")
        
        doc_type_tests = [
            ("agent", {"doc_type": "agent_definition"}, "智能体定义"),
            ("config", {"doc_type": "agent_configuration"}, "智能体配置"),
            ("class", {"doc_type": "class_definition"}, "类定义"),
            ("function", {"doc_type": "function_definition"}, "函数定义"),
            ("documentation", {"doc_type": "documentation"}, "文档")
        ]
        
        for query, filters, description in doc_type_tests:
            logger.info(f"\n--- {description}搜索 ---")
            try:
                results = await kb.search(query, search_type="keyword", filters=filters, top_k=3)
                logger.info(f"结果数量: {len(results)}")
                
                if results:
                    for i, result in enumerate(results, 1):
                        title = result.get('title', 'N/A')
                        score = result.get('score', 0)
                        logger.info(f"  {i}. {title} (评分: {score:.3f})")
                else:
                    logger.warning("  没有找到结果")
                    
            except Exception as e:
                logger.error(f"  搜索失败: {str(e)}")
        
        # 5. 检查搜索配置
        logger.info("\n=== 搜索配置检查 ===")
        if hasattr(kb, 'config'):
            search_config = kb.config.get('search', {})
            logger.info(f"搜索配置: {json.dumps(search_config, indent=2, ensure_ascii=False)}")
        
        if hasattr(kb.search_engine, 'config'):
            engine_config = kb.search_engine.config
            logger.info(f"搜索引擎配置: {json.dumps(engine_config, indent=2, ensure_ascii=False)}")
        
        # 6. 检查文档内容质量
        logger.info("\n=== 文档内容质量检查 ===")
        
        # 随机检查一些文档的内容
        sample_results = await kb.search("*", search_type="keyword", top_k=5)
        if sample_results:
            logger.info("随机文档内容样本:")
            for i, result in enumerate(sample_results[:3], 1):
                content = result.get('content', '')
                title = result.get('title', 'N/A')
                logger.info(f"  {i}. {title}")
                logger.info(f"     内容长度: {len(content)} 字符")
                logger.info(f"     内容预览: {content[:200]}...")
                
                # 检查内容是否有意义
                if len(content.strip()) < 10:
                    logger.warning(f"     警告: 文档内容过短")
                if not content.strip():
                    logger.warning(f"     警告: 文档内容为空")
        
        # 7. 性能和配置建议
        logger.info("\n=== 诊断结果和建议 ===")
        
        total_docs = stats.get('total_documents', 0)
        if total_docs == 0:
            logger.error("❌ 严重问题: 知识库中没有文档")
            logger.info("建议: 运行 python build_complete_knowledge_base.py 重新构建知识库")
        elif total_docs < 100:
            logger.warning("⚠️  警告: 文档数量较少，可能影响搜索效果")
            logger.info("建议: 检查文件扫描配置，确保包含所有相关文件")
        else:
            logger.info(f"✅ 文档数量正常: {total_docs} 个文档")
        
        # 检查向量索引
        if hasattr(kb.search_engine, 'semantic_search') and kb.search_engine.semantic_search:
            if hasattr(kb.search_engine.semantic_search, 'vector_index') and kb.search_engine.semantic_search.vector_index:
                index = kb.search_engine.semantic_search.vector_index
                if hasattr(index, 'ntotal') and index.ntotal > 0:
                    logger.info(f"✅ 向量索引正常: {index.ntotal} 个向量")
                else:
                    logger.error("❌ 向量索引为空")
                    logger.info("建议: 重新构建向量索引")
            else:
                logger.error("❌ 向量索引未初始化")
                logger.info("建议: 检查语义搜索引擎配置")
        
        # 搜索结果质量检查
        empty_results = 0
        for query, search_type, _ in test_queries:
            try:
                results = await kb.search(query, search_type=search_type, top_k=1)
                if not results:
                    empty_results += 1
            except:
                empty_results += 1
        
        if empty_results > len(test_queries) * 0.5:
            logger.error(f"❌ 搜索效果差: {empty_results}/{len(test_queries)} 个查询无结果")
            logger.info("可能原因:")
            logger.info("  1. 向量索引损坏或未正确构建")
            logger.info("  2. 搜索阈值设置过高")
            logger.info("  3. 文档内容质量问题")
            logger.info("  4. 嵌入模型问题")
        elif empty_results > 0:
            logger.warning(f"⚠️  部分搜索无结果: {empty_results}/{len(test_queries)} 个查询")
            logger.info("建议: 调整搜索参数或重新索引")
        else:
            logger.info("✅ 搜索功能正常")
        
        # 清理资源
        await kb.cleanup()
        logger.info("\n诊断完成！")
        return True
        
    except Exception as e:
        logger.error(f"诊断过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(diagnose_search_issues())
    if success:
        print("\n🔍 搜索诊断完成！")
        print("\n请查看上述诊断结果，根据建议进行优化。")
    else:
        print("\n❌ 诊断失败！")
        sys.exit(1)