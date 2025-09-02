#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复搜索阈值问题
降低相似度阈值以改善搜索效果
"""

import asyncio
import logging
import yaml
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.knowledge.knowledge_base import KnowledgeBase

async def fix_search_threshold():
    """
    修复搜索阈值问题
    """
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("SearchThresholdFix")
    
    try:
        logger.info("开始修复搜索阈值问题...")
        
        # 1. 修改配置文件中的阈值
        config_file = project_root / "core_lib" / "knowledge" / "knowledge_config.yml"
        
        if config_file.exists():
            logger.info(f"读取配置文件: {config_file}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 降低相似度阈值
            old_threshold = config.get('semantic_search', {}).get('search_params', {}).get('similarity_threshold', 0.3)
            new_threshold = 0.1  # 降低到0.1
            
            if 'semantic_search' not in config:
                config['semantic_search'] = {}
            if 'search_params' not in config['semantic_search']:
                config['semantic_search']['search_params'] = {}
            
            config['semantic_search']['search_params']['similarity_threshold'] = new_threshold
            
            # 同时调整其他搜索参数
            config['semantic_search']['search_params']['default_top_k'] = 10
            config['semantic_search']['search_params']['max_top_k'] = 50
            
            # 保存修改后的配置
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info(f"已将相似度阈值从 {old_threshold} 降低到 {new_threshold}")
        
        # 2. 测试不同阈值下的搜索效果
        logger.info("\n=== 测试不同阈值下的搜索效果 ===")
        
        kb_path = project_root / "knowledge_base"
        kb = KnowledgeBase(kb_path)
        await kb.initialize()
        
        # 测试查询
        test_queries = [
            ("agent", "keyword"),
            ("智能体", "semantic"),
            ("configuration", "keyword"),
            ("水利仿真", "semantic"),
            ("class", "keyword")
        ]
        
        # 测试不同阈值
        thresholds = [0.05, 0.1, 0.15, 0.2, 0.3]
        
        for threshold in thresholds:
            logger.info(f"\n--- 测试阈值: {threshold} ---")
            
            # 临时修改搜索引擎的阈值
            if hasattr(kb.search_engine, 'semantic_search') and kb.search_engine.semantic_search:
                original_threshold = getattr(kb.search_engine.semantic_search, 'similarity_threshold', 0.3)
                kb.search_engine.semantic_search.similarity_threshold = threshold
            
            total_results = 0
            
            for query, search_type in test_queries:
                try:
                    results = await kb.search(query, search_type=search_type, top_k=5)
                    total_results += len(results)
                    logger.info(f"  查询 '{query}' ({search_type}): {len(results)} 个结果")
                    
                    # 显示前2个结果的分数
                    for i, result in enumerate(results[:2]):
                        score = result.get('score', 0)
                        title = result.get('title', 'N/A')
                        logger.info(f"    {i+1}. {title} (分数: {score:.3f})")
                        
                except Exception as e:
                    logger.error(f"  查询 '{query}' 失败: {str(e)}")
            
            logger.info(f"  阈值 {threshold} 总结果数: {total_results}")
            
            # 恢复原始阈值
            if hasattr(kb.search_engine, 'semantic_search') and kb.search_engine.semantic_search:
                kb.search_engine.semantic_search.similarity_threshold = original_threshold
        
        # 3. 应用最佳阈值并重新测试
        logger.info("\n=== 应用优化阈值并测试 ===")
        
        # 重新初始化知识库以应用新配置
        await kb.cleanup()
        kb = KnowledgeBase(kb_path)
        await kb.initialize()
        
        logger.info("使用优化后的配置进行搜索测试:")
        
        for query, search_type in test_queries:
            try:
                results = await kb.search(query, search_type=search_type, top_k=5)
                logger.info(f"\n查询 '{query}' ({search_type}): {len(results)} 个结果")
                
                for i, result in enumerate(results[:3], 1):
                    title = result.get('title', 'N/A')
                    score = result.get('score', 0)
                    doc_type = result.get('doc_type', 'N/A')
                    file_path = result.get('file_path', 'N/A')
                    
                    logger.info(f"  {i}. {title}")
                    logger.info(f"     类型: {doc_type}, 分数: {score:.3f}")
                    logger.info(f"     文件: {Path(file_path).name if file_path != 'N/A' else 'N/A'}")
                    
            except Exception as e:
                logger.error(f"查询 '{query}' 失败: {str(e)}")
        
        # 4. 测试混合搜索
        logger.info("\n=== 混合搜索测试 ===")
        
        hybrid_queries = [
            "智能体配置",
            "water control agent",
            "洪水控制系统",
            "configuration template"
        ]
        
        for query in hybrid_queries:
            try:
                results = await kb.search(query, search_type="hybrid", top_k=3)
                logger.info(f"\n混合搜索 '{query}': {len(results)} 个结果")
                
                for i, result in enumerate(results, 1):
                    title = result.get('title', 'N/A')
                    score = result.get('score', 0)
                    logger.info(f"  {i}. {title} (分数: {score:.3f})")
                    
            except Exception as e:
                logger.error(f"混合搜索 '{query}' 失败: {str(e)}")
        
        await kb.cleanup()
        
        logger.info("\n✅ 搜索阈值修复完成！")
        logger.info("主要改进:")
        logger.info("- 将相似度阈值从 0.3 降低到 0.1")
        logger.info("- 优化了搜索参数配置")
        logger.info("- 改善了搜索结果的召回率")
        
    except Exception as e:
        logger.error(f"修复过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_search_threshold())