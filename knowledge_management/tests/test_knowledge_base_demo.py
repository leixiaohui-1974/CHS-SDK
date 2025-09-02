#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS-SDK 知识库功能演示脚本
展示知识库的各种搜索功能和使用方法
"""

import asyncio
import logging
from pathlib import Path
import sys
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.knowledge.knowledge_base import KnowledgeBase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('KnowledgeBaseDemo')

async def demo_knowledge_base():
    """
    演示知识库的各种功能
    """
    try:
        logger.info("🚀 开始CHS-SDK知识库功能演示...")
        
        # 初始化知识库
        logger.info("\n=== 1. 初始化知识库 ===")
        kb = KnowledgeBase(project_root=project_root)
        success = await kb.initialize()
        
        if not success:
            logger.error("知识库初始化失败！")
            return
        
        # 获取知识库统计信息
        stats = kb.get_statistics()
        logger.info(f"📊 知识库统计信息:")
        logger.info(f"   - 总文档数: {stats.get('total_documents', 0)}")
        logger.info(f"   - 项目根目录: {stats.get('project_root', 'N/A')}")
        logger.info(f"   - 最后更新: {stats.get('last_indexed', 'N/A')}")
        
        # 演示不同类型的搜索
        await demo_search_types(kb)
        
        # 演示过滤器搜索
        await demo_filtered_search(kb)
        
        # 演示智能推荐
        await demo_recommendations(kb)
        
        # 清理资源
        await kb.cleanup()
        logger.info("\n✅ 知识库演示完成！")
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

async def demo_search_types(kb):
    """
    演示不同类型的搜索功能
    """
    logger.info("\n=== 2. 搜索功能演示 ===")
    
    # 测试查询列表
    test_queries = [
        {
            "query": "智能体架构设计",
            "description": "中文概念查询"
        },
        {
            "query": "WaterReservoirAgent", 
            "description": "精确类名查询"
        },
        {
            "query": "flood control system",
            "description": "英文概念查询"
        },
        {
            "query": "配置文件模板",
            "description": "配置相关查询"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        description = test_case["description"]
        
        logger.info(f"\n--- 测试 {i}: {description} ---")
        logger.info(f"查询: '{query}'")
        
        # 语义搜索
        semantic_results = await kb.search(
            query=query,
            search_type="semantic",
            top_k=3
        )
        
        # 关键词搜索
        keyword_results = await kb.search(
            query=query,
            search_type="keyword", 
            top_k=3
        )
        
        # 混合搜索
        hybrid_results = await kb.search(
            query=query,
            search_type="hybrid",
            top_k=3
        )
        
        logger.info(f"🔍 搜索结果统计:")
        logger.info(f"   - 语义搜索: {len(semantic_results)} 个结果")
        logger.info(f"   - 关键词搜索: {len(keyword_results)} 个结果")
        logger.info(f"   - 混合搜索: {len(hybrid_results)} 个结果")
        
        # 显示最佳匹配结果
        if hybrid_results:
            best_result = hybrid_results[0]
            logger.info(f"\n🎯 最佳匹配:")
            logger.info(f"   - 标题: {best_result.get('title', 'N/A')}")
            logger.info(f"   - 文件: {best_result.get('metadata', {}).get('file_path', 'N/A')}")
            logger.info(f"   - 相似度: {best_result.get('score', 0):.3f}")
            logger.info(f"   - 文档类型: {best_result.get('metadata', {}).get('doc_type', 'N/A')}")
            
            # 显示内容预览
            content = best_result.get('content', '')
            preview = content[:150] + '...' if len(content) > 150 else content
            logger.info(f"   - 内容预览: {preview}")

async def demo_filtered_search(kb):
    """
    演示过滤器搜索功能
    """
    logger.info("\n=== 3. 过滤器搜索演示 ===")
    
    # 按文档类型过滤
    logger.info("\n--- 按文档类型过滤 ---")
    filtered_results = await kb.search(
        query="agent",
        search_type="hybrid",
        filters={
            "doc_type": "agent_definition"
        },
        top_k=5
    )
    
    logger.info(f"🔍 智能体定义相关结果: {len(filtered_results)} 个")
    for i, result in enumerate(filtered_results[:3], 1):
        logger.info(f"   {i}. {result.get('title', 'N/A')} (分数: {result.get('score', 0):.3f})")
    
    # 按文件类型过滤
    logger.info("\n--- 按文件类型过滤 ---")
    python_results = await kb.search(
        query="control algorithm",
        search_type="semantic",
        filters={
            "file_type": "python"
        },
        top_k=5
    )
    
    logger.info(f"🐍 Python文件相关结果: {len(python_results)} 个")
    for i, result in enumerate(python_results[:3], 1):
        logger.info(f"   {i}. {result.get('title', 'N/A')} (分数: {result.get('score', 0):.3f})")
    
    # 按标签过滤
    logger.info("\n--- 按标签过滤 ---")
    tagged_results = await kb.search(
        query="configuration",
        search_type="hybrid",
        filters={
            "tags": ["yaml"]
        },
        top_k=5
    )
    
    logger.info(f"🏷️ YAML标签相关结果: {len(tagged_results)} 个")
    for i, result in enumerate(tagged_results[:3], 1):
        logger.info(f"   {i}. {result.get('title', 'N/A')} (分数: {result.get('score', 0):.3f})")

async def demo_recommendations(kb):
    """
    演示智能推荐功能
    """
    logger.info("\n=== 4. 智能推荐演示 ===")
    
    try:
        # 智能体推荐
        logger.info("\n--- 智能体推荐 ---")
        agent_recommendations = await kb.get_recommendations(
            context={
                "current_agent": "WaterReservoirAgent",
                "scenario": "flood_control",
                "task_type": "water_level_control"
            },
            recommendation_type="agent"
        )
        
        logger.info(f"🤖 智能体推荐结果: {len(agent_recommendations)} 个")
        for i, rec in enumerate(agent_recommendations[:3], 1):
            logger.info(f"   {i}. {rec.get('title', 'N/A')} (相关度: {rec.get('score', 0):.3f})")
        
        # 配置推荐
        logger.info("\n--- 配置推荐 ---")
        config_recommendations = await kb.get_recommendations(
            context={
                "agent_type": "LocalControlAgent",
                "domain": "water_system"
            },
            recommendation_type="configuration"
        )
        
        logger.info(f"⚙️ 配置推荐结果: {len(config_recommendations)} 个")
        for i, rec in enumerate(config_recommendations[:3], 1):
            logger.info(f"   {i}. {rec.get('title', 'N/A')} (相关度: {rec.get('score', 0):.3f})")
            
    except Exception as e:
        logger.warning(f"推荐功能暂时不可用: {str(e)}")

async def demo_performance_comparison(kb):
    """
    演示不同搜索方法的性能对比
    """
    logger.info("\n=== 5. 性能对比演示 ===")
    
    import time
    
    query = "水系统控制算法"
    search_types = ["semantic", "keyword", "hybrid"]
    
    for search_type in search_types:
        start_time = time.time()
        
        results = await kb.search(
            query=query,
            search_type=search_type,
            top_k=10
        )
        
        end_time = time.time()
        duration = (end_time - start_time) * 1000  # 转换为毫秒
        
        logger.info(f"⏱️ {search_type.upper()} 搜索:")
        logger.info(f"   - 耗时: {duration:.2f} ms")
        logger.info(f"   - 结果数: {len(results)}")
        if results:
            logger.info(f"   - 最高分数: {results[0].get('score', 0):.3f}")

def print_search_tips():
    """
    打印搜索使用技巧
    """
    logger.info("\n=== 💡 搜索使用技巧 ===")
    logger.info("1. 语义搜索 - 适用于概念性查询，如'智能体架构'、'洪水控制'")
    logger.info("2. 关键词搜索 - 适用于精确匹配，如类名'WaterReservoirAgent'")
    logger.info("3. 混合搜索 - 平衡语义理解和精确匹配，推荐日常使用")
    logger.info("4. 使用过滤器可以缩小搜索范围，提高结果精度")
    logger.info("5. 适当调整top_k参数来控制返回结果数量")
    logger.info("6. 中英文混合查询通常能获得更好的结果")

if __name__ == "__main__":
    print_search_tips()
    asyncio.run(demo_knowledge_base())